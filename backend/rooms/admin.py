from django.contrib import admin
from .models import Room, Document, EditHistory

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'owner', 'created_at', 'updated_at']
    search_fields = ['title', 'owner__email']
    list_filter = ['created_at']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'language', 'created_at', 'updated_at']
    search_fields = ['room__title']
    list_filter = ['language']

@admin.register(EditHistory)
class EditHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'user', 'timestamp']
    search_fields = ['document__room__title', 'user__email']
    list_filter = ['timestamp']

