from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User
from rooms.models import Room, Document
from config.asgi import application
import json
import asyncio


class WebSocketTests(TestCase):
    """Test WebSocket functionality"""
    
    async def asyncSetUp(self):
        """Set up test data"""
        self.user = await database_sync_to_async(User.objects.create_user)(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.room = await database_sync_to_async(Room.objects.create)(
            owner=self.user,
            title='Test Room'
        )
        
        await database_sync_to_async(Document.objects.create)(
            room=self.room
        )
        
        token = AccessToken.for_user(self.user)
        self.token = str(token)
    
    async def test_connect_authenticated(self):
        """Test WebSocket connection with valid token"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # First message is document_sync
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'document_sync')
        self.assertIn('document', response)
        self.assertIn('active_users', response)
        
        # Second message is user_joined
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'user_joined')
        self.assertEqual(response['user']['email'], self.user.email)
        
        await communicator.disconnect()
    
    async def test_document_sync(self):
        """Test document sync on connect"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'document_sync')
        self.assertIn('document', response)
        self.assertEqual(response['document']['title'], 'Test Room')
        self.assertIn('content', response['document'])
        self.assertIn('language', response['document'])
        
        await communicator.disconnect()
    
    async def test_request_sync(self):
        """Test manual sync request"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        # Request manual sync
        await communicator.send_json_to({
            'type': 'request_sync'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'document_sync')
        self.assertIn('document', response)
        
        await communicator.disconnect()
    
    async def test_text_update(self):
        """Test text_update event and database save"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        await communicator.send_json_to({
            'type': 'text_update',
            'content': 'Hello WebSocket!'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'text_update')
        self.assertEqual(response['content'], 'Hello WebSocket!')
        self.assertEqual(response['user']['email'], self.user.email)
        self.assertIn('timestamp', response)
        
        # Verify database save
        document = await database_sync_to_async(
            lambda: Document.objects.get(room=self.room)
        )()
        self.assertEqual(document.content, 'Hello WebSocket!')
        
        await communicator.disconnect()
    
    async def test_cursor_move_enhanced(self):
        """Test enhanced cursor_move with line, column, and selection"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        await communicator.send_json_to({
            'type': 'cursor_move',
            'position': 42,
            'line': 5,
            'column': 10,
            'selection_start': 40,
            'selection_end': 50
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'cursor_move')
        self.assertEqual(response['position'], 42)
        self.assertEqual(response['line'], 5)
        self.assertEqual(response['column'], 10)
        self.assertIn('selection', response)
        self.assertEqual(response['selection']['start'], 40)
        self.assertEqual(response['selection']['end'], 50)
        self.assertIn('color', response)
        
        await communicator.disconnect()
    
    async def test_heartbeat(self):
        """Test heartbeat mechanism"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        await communicator.send_json_to({
            'type': 'heartbeat',
            'status': 'typing'
        })
        
        await asyncio.sleep(0.1)
        
        await communicator.send_json_to({
            'type': 'get_online_users'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'online_users')
        self.assertIn('users', response)
        self.assertEqual(len(response['users']), 1)
        self.assertEqual(response['users'][0]['status'], 'typing')
        
        await communicator.disconnect()
    
    async def test_get_online_users(self):
        """Test get_online_users action"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        await communicator.send_json_to({
            'type': 'get_online_users'
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'online_users')
        self.assertIn('users', response)
        self.assertEqual(len(response['users']), 1)
        self.assertEqual(response['users'][0]['email'], self.user.email)
        
        await communicator.disconnect()
    
    async def test_error_handling(self):
        """Test error handling for invalid title"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Skip initial messages
        await communicator.receive_json_from()
        await communicator.receive_json_from()
        
        await communicator.send_json_to({
            'type': 'title_update',
            'title': ''
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('message', response)
        
        await communicator.disconnect()
