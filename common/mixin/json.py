import json
import typing

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet, Model
from django.http import JsonResponse
from django.utils.functional import Promise
from django.utils.translation import ugettext_lazy as _

from common.forms import queryset_to_list, Serializer, model_to_dict
from common.utils.json import CJsonEncoder

__all__ = [
    'ret_format',
    'exception_to_response',
    'ResponseMixin',
    'FormValidationMixin'
]


def ret_format(
        result: bool = True,
        messages: typing.Union[str, list] = None,
        level: str = None,
        code: int = 200,
        data: typing.Union[str, list, dict] = None,
        default_msg=True, **kwargs):
    """
    Jsonable return HTTP data
    :param result: bool
    :param messages: str|list, messages display on page
    :param level: str, message level, it will be set to True when result is
    success, otherwise it is False
    :param code: message code
    :param data: Json|dict|list|QuerySet, extra data
    :param default_msg: when default_msg is True and messages is None, it will
    return a default message (succeeded or failed)
    :return: dict
    """
    assert isinstance(result, bool)
    if not result and code == 200:
        result = False
        code = code if code else 400
        level = level if level else 'error'
    elif result and code != 200:
        result = False
    if messages:
        # str/Promise
        if isinstance(messages, Promise):
            messages = [messages]
        elif isinstance(messages, str):
            messages = [_(messages)]
        else:
            # tuple/list
            assert isinstance(messages, (list, tuple))
            for msg in messages:
                # item in messages must be str or Promise object
                #print(type(msg))
                assert isinstance(msg, (str, Promise))

            # i18n here if necessary
            messages = [_(m) if isinstance(m, str) else m for m in messages]
    else:
        if default_msg:
            messages = [_('Operation succeeded')] if result else [_('Operation failed')]
    if not level:
        level = 'success' if result else 'error'
    assert level in ('success', 'info', 'warning', 'error')
    assert isinstance(code, int)
    if data is not None:
        if isinstance(data, QuerySet):
            data = Serializer(
                data, use_natural_foreign_keys=True, **kwargs
            ).to_python()
        elif isinstance(data, Model):
            data = model_to_dict(data, **kwargs)
        elif isinstance(data, dict):
            data = json.dumps(data, cls=CJsonEncoder)
            data = json.loads(data)
        elif isinstance(data, list):
            if data and isinstance(data[0], Model):
                data = Serializer(
                    data, use_natural_foreign_keys=True, **kwargs
                ).to_python()
        elif isinstance(data, str):
            data = json.loads(data)

    _data = [] if isinstance(data, list) else {}
    return {'result': result,
            'messages': messages or [],
            'level': level,
            'code': code,
            'data': data or _data}


def exception_to_response(exception, data=None, **kwargs):
    """
    used in middleware or somewhere special
    """
    if callable(exception):
        exception = exception()
    return JsonResponse(
        ret_format(result=False,
                   messages=kwargs.get('messages') or str(exception),
                   level=kwargs.get('level') or exception.level,
                   code=kwargs.get('code') or exception.code,
                   data=data, **kwargs)
    )


class ResponseMixin:
    """
    A mixin that can be used to render a JSON response.
    """

    def render_to_json_response(self, result: bool = True, messages=None,
                                level=None, code=200, data=None, default_msg=True,
                                **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        QuerySet data will be transformed into a special format.
        """
        related_sets = None
        many_to_many_fields = None
        if hasattr(self, 'related_sets'):
            related_sets = self.related_sets
        if hasattr(self, 'many_to_many_fields'):
            many_to_many_fields = self.many_to_many_fields
        res_data = self._get_ret_form_data(
            result=result, messages=messages,
            level=level, code=code, data=data,
            default_msg=default_msg,
            related_sets=related_sets,
            many_to_many_fields=many_to_many_fields
        )
        if hasattr(self, 'show_all') and self.show_all is False:
            # for paged list
            _data = res_data['data']
            res_data['data'] = dict(objects=_data, total_length=self.total_length)
        if 'total_length' in res_data['data'] and res_data['data']['total_length'] is None:
            res_data['data']['total_length'] = len(res_data['data']['objects'])
        response = JsonResponse(
            res_data,
            encoder=CJsonEncoder,
            **response_kwargs
        )

        return response

    def _get_ret_form_data(self, **kwargs):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.

        return ret_format(**kwargs)

    def render_to_raw_json_response(self, data, **kwargs):
        # for data table (list)
        if kwargs.get('perms', True):
            for row in data['data']:
                row['perms'] = list(self.request.user.get_all_permissions())
        return JsonResponse(data, encoder=CJsonEncoder)

    @staticmethod
    def model_object_to_dict(obj):
        obj = obj.__dict__
        obj.pop('_state')
        return obj


class FormValidationMixin:
    """
    Mixin to add AJAX support to a form.

    Usage:
    1. Based on form views (e.g. CreateView, UpdateView), put this mixin ahead of form views
    2. Requires JSONResponseMixin
    """

    def form_invalid(self, form):
        # process messages
        if settings.DEBUG:
            msg = list()
            for k, el in form.errors.items():
                for item in el:
                    msg.append('[%s] %s' % (k, item))
        else:
            msg = [' '.join(v) for f, v in form.errors.items()]

        return self.render_to_json_response(
            result=False, messages=msg, level='error'
        )

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        self.object = form.save()
        return self.render_to_json_response(data=self.object)


class BulkDeleteMixin:
    """
    1. This mixin must be used with JSONResponseMixin
    2. pk_url_kwarg is required too. The default pk
    3. model is required
    4. make sure this mixin is ahead of DeleteView
    """

    def get_queryset(self):
        if self.queryset is None:
            if self.model:
                if not hasattr(self, 'pks'):
                    raise ImproperlyConfigured(
                        'pks must be defined before getting queryset')
                if hasattr(self, 'primary_key'):
                    kwargs = {self.primary_key + '__in': self.pks}
                elif self.slug_url_kwarg and self.slug_url_kwarg != 'slug':
                    kwargs = {self.slug_field: self.slug_url_value}
                else:
                    kwargs = {'pk__in': self.pks}

                # set layer type and id, used to deal with LayerResource
                self.model.layer_type = self.request.layer.type
                self.model.layer_id = self.request.layer.id

                return self.model._default_manager.filter(**kwargs)
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.queryset

    def get_validated_queryset(self, **kwargs):
        pks = kwargs.get(self.pk_url_kwarg)
        if not isinstance(pks, list):
            if not (hasattr(self, 'slug_url_kwarg') and self.slug_url_kwarg != 'slug'):
                raise ImproperlyConfigured(
                    _('%(pk_url_kwarg)s is not a proper pk_url_kwarg.') %
                    {'pk_url_kwarg': self.pk_url_kwarg})
            self.slug_url_value = kwargs.get(self.slug_url_kwarg)
        self.pks = pks
        self.queryset = self.get_queryset()

        if not hasattr(self, 'slug_url_value') and self.queryset.count() < len(pks):
            pk = getattr(self, 'primary_key') if hasattr(self, 'primary_key') else 'pk'
            item_pks = [getattr(item, pk) for item in self.queryset]
            not_exist = map(lambda x: str(x), filter(lambda x: x not in item_pks, pks))
            raise self.model.DoesNotExist(','.join(not_exist))
        return self.queryset

    def before_delete(self, *args, **kwargs) -> None:
        """
        Extra validation method or do something (handle queryset) before deleting.
        Write your logic here, before deleting objects.
        """
        pass

    def after_delete(self, *args, **kwargs) -> None:
        """Do something after deleting"""
        pass

    def _prepare_delete(self):
        pass

    def _delete(self):
        """
        Rewrite this method if you dot NOT want to delete queryset
        """
        self.queryset.delete()

    def delete(self, request, *args, **kwargs):
        """
        Multiple OpenStack objects deleting example:

        self.get_validated_queryset(**kwargs)
        for item in self.queryset:
            driver.delete()
            item.delete()
        return self.render_to_json_response()
        """
        self.get_validated_queryset(**kwargs)
        self._prepare_delete()

        self.before_delete(*args, **kwargs)

        # reserve a list of queryset which can be used in next steps
        self.queryset_list = queryset_to_list(self.queryset)
        if not hasattr(self, 'pks') or not self.pks:
            self.pks = list(self.queryset.values_list('pk', flat=True))

        # queryset delete
        self._delete()

        self.after_delete(*args, **kwargs)

        return self.render_to_json_response(data=self.queryset_list)
