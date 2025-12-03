import { defineStore } from 'pinia';
import roomsApi from '../api/rooms';

export const useRoomStore = defineStore('room', {
    state: () => ({
        currentRoom: null,
        document: null,
        onlineUsers: [],
        editHistory: [],
    }),
    actions: {
        async fetchRoom(roomId) {
            try {
                const response = await roomsApi.getRoom(roomId);
                this.currentRoom = response.data;
                this.document = response.data.document;
            } catch (error) {
                throw error;
            }
        },
        async updateTitle(roomId, title) {
            try {
                const response = await roomsApi.updateRoom(roomId, { title });
                this.currentRoom = response.data;
            } catch (error) {
                throw error;
            }
        },
        async loadHistory(documentId) {
            try {
                const response = await roomsApi.getHistory(documentId);
                this.editHistory = response.data;
            } catch (error) {
                console.error('Failed to load history:', error);
            }
        },
        setOnlineUsers(users) {
            this.onlineUsers = users;
        },
        addOnlineUser(user) {
            if (!this.onlineUsers.find(u => u.id === user.id)) {
                this.onlineUsers.push(user);
            }
        },
        removeOnlineUser(userId) {
            this.onlineUsers = this.onlineUsers.filter(u => u.id !== userId);
        },
    },
});
