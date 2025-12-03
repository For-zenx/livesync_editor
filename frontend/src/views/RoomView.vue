<template>
  <div class="room-view">
    <div class="room-header">
      <router-link to="/" class="back-btn">← Back to Rooms</router-link>
      <h1>{{ roomStore.currentRoom?.title || 'Loading...' }}</h1>
    </div>
    <div class="room-content">
      <p>Room editor will be implemented in the next phase (Monaco Editor integration)</p>
      <p>Room ID: {{ roomId }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useRoomStore } from '../stores/room';

const route = useRoute();
const roomStore = useRoomStore();
const roomId = route.params.id;

onMounted(async () => {
  try {
    await roomStore.fetchRoom(roomId);
  } catch (err) {
    console.error('Failed to load room:', err);
  }
});

onUnmounted(() => {
  // Cleanup if needed
});
</script>

<style scoped>
.room-view {
  min-height: 100vh;
  background: #f5f7fa;
}

.room-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.back-btn {
  display: inline-block;
  color: #667eea;
  text-decoration: none;
  margin-bottom: 10px;
  font-weight: 600;
}

.back-btn:hover {
  text-decoration: underline;
}

.room-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.room-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}
</style>
