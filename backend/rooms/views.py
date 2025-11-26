from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Room, EditHistory
from .serializers import RoomSerializer, RoomDetailSerializer, EditHistorySerializer
from .permissions import IsRoomOwner


class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing rooms
    """
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve/list, basic for create/update"""
        if self.action in ['retrieve', 'list']:
            return RoomDetailSerializer
        return RoomSerializer
    
    def get_permissions(self):
        """Apply IsRoomOwner permission for update/destroy actions"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsRoomOwner()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set the owner to the current user when creating a room"""
        serializer.save(owner=self.request.user)
    
    def get_queryset(self):
        """Return only rooms owned by the current user"""
        return Room.objects.filter(owner=self.request.user)


class EditHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing edit history (read-only)
    """
    queryset = EditHistory.objects.all().order_by('-timestamp')
    serializer_class = EditHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by document if document query param is provided"""
        queryset = super().get_queryset()
        document_id = self.request.query_params.get('document', None)
        if document_id is not None:
            queryset = queryset.filter(document_id=document_id)
        return queryset
