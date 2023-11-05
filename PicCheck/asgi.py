"""
ASGI config for PicCheck project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from group_chat import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PicCheck.settings')

# application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path("ws/chat/<int:group_id>/", consumers.GroupChatConsumer.as_asgi()),
    ])
})
