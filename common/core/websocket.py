import json
import typing

from asgiref.sync import async_to_sync, sync_to_async
from channels.auth import get_user, logout
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer as _AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.db.models import Model

from common.forms import model_to_dict
from common.utils.json import CJsonEncoder

__all__ = (
    'push',
    'get_group_name',
    'get_global_group_name',
    'AsyncJsonWebsocketConsumer',
    'AsyncJsonModelBasedWebsocketConsumer',
    'GlobalAsyncJsonWebsocketConsumer',
)


class Method:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    ALL = (CREATE, UPDATE, DELETE)


def push(group_name: str, method: str, data: typing.Union[dict, list],
         type: str = 'send.data'):
    """
    Push data through websocket
    :param group_name:
    :param type: send.data -> function send_data() in consumer
    :param method: create/update/delete
    :param data: objects could be dumps by JSON (dict, list, ...)
    :return:
    """
    assert method.upper() in Method.ALL
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name, {'type': type, 'data': data, 'method': method.upper()})


def push_with_model(instance, user, method, data=None, **kwargs):
    if not data:
        data = model_to_dict(instance)
    group_name = get_group_name(user.id, instance._meta.model)
    push(group_name, method, data, **kwargs)


def get_group_name(identifier_id, model: typing.Union[str, Model], identifier_name=None):
    if not isinstance(model, str):
        model = model._meta.model_name
    if identifier_name is None:
        identifier_name = 'user'

    return ('%(identifier_name)s_%(identifier_id)s_%(resource_type)s' %
            {'identifier_name': identifier_name,
             'identifier_id': identifier_id, 'resource_type': model
             })


def get_global_group_name(user_id):
    return 'user_%(user_id)s_global' % {'user_id': user_id}


class AsyncJsonModelBasedWebsocketConsumer(_AsyncJsonWebsocketConsumer):
    """
    Used for websocket
    """
    # model must be evaluated.
    model = None
    # The identifier refers to as variable of URL in routing.py
    identifier_id = None
    identifier_name = None

    @classmethod
    def _check(cls):
        if cls.model is None:
            raise AttributeError('You should evaluate for class attribute "model".')
        if cls.identifier_id is None:
            raise AttributeError('You should evaluate for class attribute "identifier_id".')

    def __new__(cls, *args, **kwargs):
        cls._check()
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        identifier_id = self.scope['url_route']['kwargs'][self.identifier_id]
        self.group_name = get_group_name(identifier_id, self.model, identifier_name=self.identifier_name)

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def send_data(self, text=None):
        user = await get_user(self.scope)
        if not user.is_authenticated:
            await logout(self.scope)
            await database_sync_to_async(self.scope["session"].save)()
            return
        if text:
            data = text
        else:
            data = await self.get_data()
        await self.send_json(data)

    async def disconnect(self, code):
        # Called when the socket closes
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_data(self):
        return json.dumps(
            model_to_dict(self.model.objects.all()),
            cls=CJsonEncoder
        )


class AsyncJsonWebsocketConsumer(_AsyncJsonWebsocketConsumer):
    user_identifier = 'user_id'

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, cls=CJsonEncoder)


class GlobalAsyncJsonWebsocketConsumer(_AsyncJsonWebsocketConsumer):
    """
    DO NOT create a model named Global!
    """
    user_identifier = 'user_id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_id = self.scope['url_route']['kwargs'][self.user_identifier]
        self.group_name = get_global_group_name(user_id)

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def send_data(self, text=None):
        user = await get_user(self.scope)
        if not user.is_authenticated:
            await logout(self.scope)
            await database_sync_to_async(self.scope["session"].save)()
            return
        if text:
            data = text
        else:
            data = '{}'
        await self.send_json(data)

    async def disconnect(self, code):
        # Called when the socket closes
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
