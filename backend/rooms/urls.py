from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, EditHistoryViewSet

router = DefaultRouter()
router.register(r'', RoomViewSet, basename='room')
router.register(r'history', EditHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]
