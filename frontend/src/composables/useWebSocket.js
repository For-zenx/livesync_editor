import { ref, onUnmounted } from 'vue';

export function useWebSocket() {
    const socket = ref(null);
    const isConnected = ref(false);
    const error = ref(null);
    const messageHandlers = ref([]);
    let reconnectInterval = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;

    const connect = (roomId, token) => {
        if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket already connected or connecting');
            return;
        }

        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const url = `${wsUrl}/ws/room/${roomId}/?token=${token}`;

        console.log(`Connecting to WebSocket: ${url}`);
        socket.value = new WebSocket(url);

        socket.value.onopen = () => {
            console.log('WebSocket connected');
            isConnected.value = true;
            error.value = null;
            reconnectAttempts = 0;
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        };

        socket.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                messageHandlers.value.forEach((handler) => handler(data));
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        socket.value.onclose = (event) => {
            console.log('WebSocket disconnected', event.code, event.reason);
            isConnected.value = false;
            socket.value = null;

            if (!event.wasClean) {
                attemptReconnect(roomId, token);
            }
        };

        socket.value.onerror = (e) => {
            console.error('WebSocket error:', e);
            error.value = 'Connection error';
        };
    };

    const attemptReconnect = (roomId, token) => {
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            console.error('Max reconnect attempts reached');
            error.value = 'Unable to reconnect to server';
            return;
        }

        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                reconnectAttempts++;
                console.log(`Attempting reconnect ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}...`);
                connect(roomId, token);
            }, 3000); // Try every 3 seconds
        }
    };

    const disconnect = () => {
        if (socket.value) {
            socket.value.close();
            socket.value = null;
            isConnected.value = false;
        }
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    const sendMessage = (type, payload) => {
        if (socket.value && socket.value.readyState === WebSocket.OPEN) {
            socket.value.send(JSON.stringify({ type, ...payload }));
        } else {
            console.warn('Cannot send message: WebSocket is not connected');
        }
    };

    const onMessage = (callback) => {
        messageHandlers.value.push(callback);
    };

    onUnmounted(() => {
        disconnect();
    });

    return {
        socket,
        isConnected,
        error,
        connect,
        disconnect,
        sendMessage,
        onMessage,
    };
}
