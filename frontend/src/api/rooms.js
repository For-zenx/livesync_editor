import client from './client';

export default {
    getRooms() {
        return client.get('/api/rooms/');
    },
    getRoom(id) {
        return client.get(`/api/rooms/${id}/`);
    },
    createRoom(data) {
        return client.post('/api/rooms/', data);
    },
    updateRoom(id, data) {
        return client.patch(`/api/rooms/${id}/`, data);
    },
    deleteRoom(id) {
        return client.delete(`/api/rooms/${id}/`);
    },
    getHistory(documentId) {
        return client.get(`/api/rooms/history/`, {
            params: { document: documentId },
        });
    },
};
