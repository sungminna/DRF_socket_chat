"""
ASGI config for Mchat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# env var setting
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mchat.settings')

# asgi reset
django_asgi_app = get_asgi_application()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import chat.routing

#router
application = ProtocolTypeRouter({  # redirect http to django asgi application or to ws
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(  # login required
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    )
}) 
