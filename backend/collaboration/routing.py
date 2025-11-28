from django.urls import path
from .consumers import CollaborationConsumer

# WebSocket URL patterns will be defined here
websocket_urlpatterns = [
    path('ws/room/<uuid:room_id>/', CollaborationConsumer.as_asgi()),
]
