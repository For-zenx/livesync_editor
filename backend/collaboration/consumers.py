import json
import random
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rooms.models import Room, Document, EditHistory
from accounts.models import User


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time collaboration in rooms
    """
    active_users = {}
    pending_history_saves = {}
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope['user']
        self.history_save_task = None
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        try:
            room_exists = await self.verify_room_exists()
            if not room_exists:
                await self.close()
                return
        except Exception as e:
            await self.send_error(f"Error verifying room: {str(e)}")
            await self.close()
            return
        
        self.user_color = self.generate_random_color()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        if self.room_group_name not in self.active_users:
            self.active_users[self.room_group_name] = {}
        
        self.active_users[self.room_group_name][self.user.id] = {
            'user_id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'color': self.user_color,
            'last_seen': datetime.now().isoformat(),
            'status': 'active'
        }
        
        await self.send_document_sync()
        
        await self.broadcast_to_group({
            'type': 'user_joined',
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'color': self.user_color
            },
            'active_users': list(self.active_users[self.room_group_name].values()),
            'timestamp': datetime.now().isoformat()
        })
    
    async def disconnect(self, close_code):
        if self.history_save_task and not self.history_save_task.done():
            self.history_save_task.cancel()
        
        if hasattr(self, 'user') and self.user.is_authenticated:
            if self.room_group_name in self.active_users:
                if self.user.id in self.active_users[self.room_group_name]:
                    del self.active_users[self.room_group_name][self.user.id]
                
                if not self.active_users[self.room_group_name]:
                    del self.active_users[self.room_group_name]
            
            await self.broadcast_to_group({
                'type': 'user_left',
                'user': {
                    'id': self.user.id,
                    'email': self.user.email
                },
                'active_users': list(self.active_users.get(self.room_group_name, {}).values()),
                'timestamp': datetime.now().isoformat()
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
            elif event_type == 'heartbeat':
                await self.handle_heartbeat(data)
            elif event_type == 'get_online_users':
                await self.get_online_users()
            elif event_type == 'request_sync':
                await self.send_document_sync()
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_text_update(self, data):
        content = data.get('content', '')
        
        try:
            await self.save_document_content(content)
            
            if self.history_save_task and not self.history_save_task.done():
                self.history_save_task.cancel()
            
            self.history_save_task = asyncio.create_task(
                self.debounced_history_save(content)
            )
            
            if self.room_group_name in self.active_users and self.user.id in self.active_users[self.room_group_name]:
                self.active_users[self.room_group_name][self.user.id]['status'] = 'typing'
                self.active_users[self.room_group_name][self.user.id]['last_seen'] = datetime.now().isoformat()
            
            await self.broadcast_to_group({
                'type': 'text_update',
                'content': content,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            await self.send_error(f"Error updating text: {str(e)}")
    
    async def debounced_history_save(self, content):
        """Save to edit history after 5 seconds of no activity"""
        try:
            await asyncio.sleep(5)
            await self.create_edit_history(content)
        except asyncio.CancelledError:
            pass
    
    async def handle_cursor_move(self, data):
        position = data.get('position', 0)
        line = data.get('line', 0)
        column = data.get('column', 0)
        selection_start = data.get('selection_start')
        selection_end = data.get('selection_end')
        
        cursor_data = {
            'type': 'cursor_move',
            'position': position,
            'line': line,
            'column': column,
            'user': {
                'id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'color': self.user_color
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if selection_start is not None and selection_end is not None:
            cursor_data['selection'] = {
                'start': selection_start,
                'end': selection_end
            }
        
        await self.broadcast_to_group(cursor_data)
    
    async def handle_title_update(self, data):
        title = data.get('title', '').strip()
        
        if not title:
            await self.send_error('Title cannot be empty')
            return
        
        try:
            await self.update_room_title(title)
            
            await self.broadcast_to_group({
                'type': 'title_update',
                'title': title,
                'user': {
                    'id': self.user.id,
                    'email': self.user.email
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            await self.send_error(f"Error updating title: {str(e)}")
    
    async def handle_heartbeat(self, data):
        if self.room_group_name in self.active_users and self.user.id in self.active_users[self.room_group_name]:
            self.active_users[self.room_group_name][self.user.id]['last_seen'] = datetime.now().isoformat()
            self.active_users[self.room_group_name][self.user.id]['status'] = data.get('status', 'active')
    
    async def get_online_users(self):
        active_users_list = list(self.active_users.get(self.room_group_name, {}).values())
        
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': active_users_list,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_document_sync(self):
        """Send full document state to client"""
        try:
            doc_data = await self.get_document_data()
            
            await self.send(text_data=json.dumps({
                'type': 'document_sync',
                'document': doc_data,
                'active_users': list(self.active_users.get(self.room_group_name, {}).values()),
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            await self.send_error(f"Error syncing document: {str(e)}")
    
    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
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
    def get_document_data(self):
        """Get full document data for sync"""
        try:
            room = Room.objects.get(id=self.room_id)
            document = room.document
            return {
                'content': document.content,
                'title': room.title,
                'language': document.language,
                'room_id': str(room.id),
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat()
            }
        except Room.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_document_content(self, content):
        try:
            room = Room.objects.get(id=self.room_id)
            document = room.document
            document.content = content
            document.save()
        except Room.DoesNotExist:
            raise Exception("Room not found")
    
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
            raise Exception("Room not found")
    
    def generate_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
