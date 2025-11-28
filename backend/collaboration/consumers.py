import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rooms.models import Room, Document, EditHistory
from accounts.models import User


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time collaboration in rooms
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope['user']
        
        # Reject anonymous users
        if not self.user.is_authenticated:
            await self.close()
            return
        
        room_exists = await self.verify_room_exists()
        if not room_exists:
            await self.close()
            return
        
        self.user_color = self.generate_random_color()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.broadcast_to_group({
            'type': 'user_joined',
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'color': self.user_color
            }
        })
    
    async def disconnect(self, close_code):
        # Only broadcast if user was authenticated
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.broadcast_to_group({
                'type': 'user_left',
                'user': {
                    'id': self.user.id,
                    'email': self.user.email
                }
            })
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            event_type = data.get('type')
            if event_type == 'text_update':
                await self.handle_text_update(data)
            elif event_type == 'cursor_move':
                await self.handle_cursor_move(data)
            elif event_type == 'title_update':
                await self.handle_title_update(data)
        except json.JSONDecodeError:
            pass
    
    async def handle_text_update(self, data):
        content = data.get('content', '')
        
        await self.save_document_content(content)
        await self.create_edit_history(content)
        
        await self.broadcast_to_group({
            'type': 'text_update',
            'content': content,
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name
            }
        })
    
    async def handle_cursor_move(self, data):
        position = data.get('position', 0)
        
        await self.broadcast_to_group({
            'type': 'cursor_move',
            'position': position,
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name
            },
            'color': self.user_color
        })
    
    async def handle_title_update(self, data):
        title = data.get('title', '')
        
        await self.update_room_title(title)
        
        await self.broadcast_to_group({
            'type': 'title_update',
            'title': title,
            'user': {
                'id': self.user.id,
                'email': self.user.email
            }
        })
    
    async def broadcast_to_group(self, event):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'message': event
            }
        )
    
    async def room_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    @database_sync_to_async
    def verify_room_exists(self):
        return Room.objects.filter(id=self.room_id).exists()
    
    @database_sync_to_async
    def save_document_content(self, content):
        try:
            room = Room.objects.get(id=self.room_id)
            document = room.document
            document.content = content
            document.save()
        except Room.DoesNotExist:
            pass
    
    @database_sync_to_async
    def create_edit_history(self, content):
        try:
            room = Room.objects.get(id=self.room_id)
            document = room.document
            EditHistory.objects.create(
                document=document,
                user=self.user,
                content=content
            )
        except Room.DoesNotExist:
            pass
    
    @database_sync_to_async
    def update_room_title(self, title):
        try:
            room = Room.objects.get(id=self.room_id)
            room.title = title
            room.save()
        except Room.DoesNotExist:
            pass
    
    def generate_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
