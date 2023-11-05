from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from group_chat import consumers

# 定义websocket连接的路由规则，并将其指定为ASGI应用的入口点
application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/chat/<int:group_id>/", consumers.GroupChatConsumer.as_asgi()),

    ]),
})
