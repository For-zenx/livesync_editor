from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User
from rooms.models import Room, Document
from config.asgi import application
import json


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
        
        # Generate JWT token
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
        
        # Should receive user_joined event
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'user_joined')
        self.assertEqual(response['user']['email'], self.user.email)
        
        await communicator.disconnect()
    
    async def test_connect_unauthenticated(self):
        """Test WebSocket connection without token"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/'
        )
        
        connected, _ = await communicator.connect()
        # Should still connect but with AnonymousUser
        # The consumer will close if room doesn't exist or user is anonymous
        
        await communicator.disconnect()
    
    async def test_text_update(self):
        """Test text_update event and database save"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Receive user_joined event
        await communicator.receive_json_from()
        
        # Send text_update
        await communicator.send_json_to({
            'type': 'text_update',
            'content': 'Hello WebSocket!'
        })
        
        # Receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'text_update')
        self.assertEqual(response['content'], 'Hello WebSocket!')
        self.assertEqual(response['user']['email'], self.user.email)
        
        # Verify database save
        document = await database_sync_to_async(
            lambda: Document.objects.get(room=self.room)
        )()
        self.assertEqual(document.content, 'Hello WebSocket!')
        
        await communicator.disconnect()
    
    async def test_cursor_move(self):
        """Test cursor_move event broadcast"""
        await self.asyncSetUp()
        
        communicator = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator.connect()
        
        # Receive user_joined event
        await communicator.receive_json_from()
        
        # Send cursor_move
        await communicator.send_json_to({
            'type': 'cursor_move',
            'position': 42
        })
        
        # Receive broadcast
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'cursor_move')
        self.assertEqual(response['position'], 42)
        self.assertIn('color', response)
        
        await communicator.disconnect()
    
    async def test_user_presence(self):
        """Test user_joined and user_left events"""
        await self.asyncSetUp()
        
        # Connect first client
        communicator1 = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={self.token}'
        )
        
        await communicator1.connect()
        
        # Receive user_joined for first client
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_joined')
        
        # Create second user and token
        user2 = await database_sync_to_async(User.objects.create_user)(
            email='testuser2@example.com',
            password='testpass123',
            first_name='Test2',
            last_name='User2'
        )
        token2 = str(AccessToken.for_user(user2))
        
        # Connect second client
        communicator2 = WebsocketCommunicator(
            application,
            f'/ws/room/{self.room.id}/?token={token2}'
        )
        
        await communicator2.connect()
        
        # First client should receive user_joined for second client
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_joined')
        self.assertEqual(response['user']['email'], user2.email)
        
        # Disconnect second client
        await communicator2.disconnect()
        
        # First client should receive user_left
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_left')
        self.assertEqual(response['user']['email'], user2.email)
        
        await communicator1.disconnect()
