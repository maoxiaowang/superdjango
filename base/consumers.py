# from channels.auth import get_user, logout
# from channels.db import database_sync_to_async
# from channels.generic.websocket import AsyncJsonWebsocketConsumer
#
#
# class GlobalConsumer(AsyncJsonWebsocketConsumer):
#     user_identifier = 'user_id'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         user_id = self.scope['url_route']['kwargs'][self.user_identifier]
#         self.group_name = 'user_%s_global' % user_id
#
#     async def connect(self):
#         user = await get_user(self.scope)
#         if user.is_authenticated:
#             user.is_online = True
#             await database_sync_to_async(user.save)()
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()
#
#     async def send_data(self, text=None):
#         user = await get_user(self.scope)
#         if not user.is_authenticated:
#             await logout(self.scope)
#             await database_sync_to_async(self.scope["session"].save)()
#             return
#         if text:
#             data = text
#         else:
#             data = '{}'
#         await self.send_json(data)
#
#     async def disconnect(self, code):
#         user = await get_user(self.scope)
#         if user.is_authenticated:
#             user.is_online = False
#             await database_sync_to_async(user.save)()
#         # Called when the socket closes
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
