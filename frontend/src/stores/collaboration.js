import { defineStore } from 'pinia';
import { useWebSocket } from '../composables/useWebSocket';
import { useRoomStore } from './room';

export const useCollaborationStore = defineStore('collaboration', {
    state: () => ({
        cursors: {},
        isConnected: false,
        ws: null,
    }),
    actions: {
        connectToRoom(roomId, token) {
            const { socket, isConnected, connect, disconnect, sendMessage, onMessage } = useWebSocket();

            this.ws = { socket, isConnected, connect, disconnect, sendMessage, onMessage };

            connect(roomId, token);

            // Sync connection state
            // We need to watch the ref from composable, but here we can just poll or rely on events
            // For simplicity, we'll rely on the composable's internal state management 
            // and just expose the sendMessage wrapper

            onMessage((data) => {
                this.handleMessage(data);
            });
        },
        disconnect() {
            if (this.ws) {
                this.ws.disconnect();
                this.ws = null;
                this.isConnected = false;
                this.cursors = {};
            }
        },
        sendTextUpdate(content) {
            if (this.ws) {
                this.ws.sendMessage('text_update', { content });
            }
        },
        sendCursorMove(position) {
            if (this.ws) {
                this.ws.sendMessage('cursor_move', { position });
            }
        },
        handleMessage(data) {
            const roomStore = useRoomStore();

            switch (data.type) {
                case 'text_update':
                    // Handled by component usually, but we could update store document content here
                    if (roomStore.document) {
                        roomStore.document.content = data.content;
                    }
                    break;
                case 'cursor_move':
                    this.updateCursor(data);
                    break;
                case 'user_joined':
                    roomStore.addOnlineUser(data.user);
                    break;
                case 'user_left':
                    roomStore.removeOnlineUser(data.user_id);
                    delete this.cursors[data.user_id];
                    break;
                case 'room_users':
                    roomStore.setOnlineUsers(data.users);
                    break;
                case 'title_update':
                    if (roomStore.currentRoom) {
                        roomStore.currentRoom.title = data.title;
                    }
                    break;
            }
        },
        updateCursor(data) {
            this.cursors[data.user_id] = {
                position: data.position,
                color: data.color,
                user: data.user
            };
        },
    },
});
