import { defineStore } from 'pinia';
import authApi from '../api/auth';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: JSON.parse(localStorage.getItem('user')) || null,
        token: localStorage.getItem('access_token') || null,
        isAuthenticated: !!localStorage.getItem('access_token'),
    }),
    actions: {
        async register(userData) {
            try {
                await authApi.register(userData);
            } catch (error) {
                throw error;
            }
        },
        async login(credentials) {
            try {
                const response = await authApi.login(credentials);
                const { access, refresh } = response.data;

                this.token = access;
                this.isAuthenticated = true;
                localStorage.setItem('access_token', access);
                localStorage.setItem('refresh_token', refresh);

                await this.loadUser();
            } catch (error) {
                throw error;
            }
        },
        async loadUser() {
            try {
                const response = await authApi.getProfile();
                this.user = response.data;
                localStorage.setItem('user', JSON.stringify(this.user));
            } catch (error) {
                this.logout();
            }
        },
        logout() {
            this.user = null;
            this.token = null;
            this.isAuthenticated = false;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
        },
    },
});
