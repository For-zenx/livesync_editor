from rest_framework.permissions import BasePermission


class IsRoomOwner(BasePermission):
    """
    Custom permission to only allow owners of a room to edit/delete it.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if the user is the owner of the room"""
        return obj.owner == request.user
