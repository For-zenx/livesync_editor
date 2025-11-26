from rest_framework import serializers
from .models import Room, Document, EditHistory
from accounts.serializers import UserSerializer


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for document data"""
    class Meta:
        model = Document
        fields = ['id', 'content', 'language', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for room creation and updates"""
    document = DocumentSerializer(read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'owner', 'title', 'created_at', 'updated_at', 'document']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create room and auto-create associated document"""
        room = Room.objects.create(**validated_data)
        Document.objects.create(room=room)
        return room


class RoomDetailSerializer(RoomSerializer):
    """Serializer for room detail with owner information"""
    owner = UserSerializer(read_only=True)
    
    class Meta(RoomSerializer.Meta):
        fields = RoomSerializer.Meta.fields


class EditHistorySerializer(serializers.ModelSerializer):
    """Serializer for edit history with user information"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EditHistory
        fields = ['id', 'user', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']
