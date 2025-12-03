import client from './client';

export default {
    register(data) {
        return client.post('/api/auth/register/', data);
    },
    login(credentials) {
        return client.post('/api/auth/login/', credentials);
    },
    getProfile() {
        return client.get('/api/auth/profile/');
    },
};
