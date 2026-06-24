from django.urls import path
from .consumers import NotificationConsumer

# notifications routing
websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()
    )
]
