import django
django.setup()
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import vision.routing  # Import your app's routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vision.settings')

# Define the applications for different protocols
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Django's ASGI application for HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            vision.routing.websocket_urlpatterns  # Your app's WebSocket routing
        )
    ),
})
