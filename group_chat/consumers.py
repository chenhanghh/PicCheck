import json
from channels.generic.websocket import AsyncWebsocketConsumer
from common.models import User
from .models import Group, GroupMessage
from django.utils.text import slugify
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken


class GroupChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        # 从websocket连接的URL路由参数中获取聊天室id
        raw_group_id = self.scope['url_route']['kwargs']['group_id']
        print(raw_group_id)

        # 确保group_id适用于频道组的规则
        self.group_id = slugify(raw_group_id)
        print(self.group_id)

        # 将当前 WebSocket 连接添加到聊天室的 Channel Group 中，以便将消息广播给相同聊天室的所有连接。
        await self.channel_layer.group_add(self.group_id, self.channel_name)

        # 接受websocket连接
        await self.accept()

        jwt_token = self.scope.get('query_string').decode().split('=')[1]
        user = await self.get_user_from_jwttoken(jwt_token)
        if user:
            self.scope['user'] = user
        else:
            await self.close()
            return

    # 断开聊天室
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_id, self.channel_name)

    @database_sync_to_async
    def get_user_from_jwttoken(self, jwt_token):
        try:
            token = AccessToken(jwt_token)
            user = token.payload.get('user_id')
            # 获取用户对象
            user = User.objects.get(id=user)
            return user
        except Exception as e:
            print("JWT解析失败:", str(e))

    @database_sync_to_async
    def save_message(self, message_type, message_data):
        group = Group.objects.get(id=self.group_id)
        user = self.scope.get('user')
        if user:
            if message_type == 'text':
                group_message = GroupMessage(group=group, sender=user, text_content=message_data, message_type=message_type)
                group_message.save()
            elif message_type == 'image':
                group_message = GroupMessage(group=group, sender=user, image_content=message_data, message_type=message_type)
                group_message.save()
            elif message_type == 'video':
                group_message = GroupMessage(group=group, sender=user, video_content=message_data, message_type=message_type)
                group_message.save()
            elif message_type == 'file':
                group_message = GroupMessage(group=group, sender=user, file_content=message_data, message_type=message_type)
                group_message.save()
            elif message_type == 'voice':
                group_message = GroupMessage(group=group, sender=user, voice_content=message_data, message_type=message_type)
                group_message.save()
            elif message_type == 'link':
                group_message = GroupMessage(group=group, sender=user, link_content=message_data, message_type=message_type)
                group_message.save()

    # 从websocket接收消息
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('message_type', 'text')
        message_data = text_data_json.get('message_data', '')

        await self.save_message(message_type, message_data)

        # 广播
        await self.channel_layer.group_send(
            self.group_id,
            {
                'type': 'chat.message',
                'message_type': message_type,
                'message_data': message_data,
            }
        )

    # 接收消息
    async def chat_message(self, event):
        message_type = event['message_type']
        message_data = event['message_data']

        await self.send(text_data=json.dumps({
            'message_type': message_type,
            'message_data': message_data,
        }))
