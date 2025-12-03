<template>
  <div class="home-container">
    <header class="header">
      <h1>LiveSync Editor</h1>
      <div class="header-actions">
        <span class="user-info">{{ authStore.user?.email }}</span>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
      </div>
    </header>

    <main class="main-content">
      <div class="content-header">
        <h2>My Rooms</h2>
        <button @click="showCreateModal = true" class="btn-primary">
          + Create Room
        </button>
      </div>

      <div v-if="loading" class="loading">Loading rooms...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="rooms.length === 0" class="empty-state">
        <p>No rooms yet. Create your first room to get started!</p>
      </div>
      <div v-else class="rooms-grid">
        <RoomCard
          v-for="room in rooms"
          :key="room.id"
          :room="room"
          @delete="handleDeleteRoom"
        />
      </div>
    </main>

    <!-- Create Room Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <h3>Create New Room</h3>
        <form @submit.prevent="handleCreateRoom">
          <div class="form-group">
            <label for="roomTitle">Room Title</label>
            <input
              id="roomTitle"
              v-model="newRoomTitle"
              type="text"
              required
              placeholder="Enter room title"
              :disabled="creating"
            />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" :disabled="creating" class="btn-primary">
              {{ creating ? 'Creating...' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import roomsApi from '../api/rooms';
import RoomCard from '../components/RoomCard.vue';

const router = useRouter();
const authStore = useAuthStore();

const rooms = ref([]);
const loading = ref(false);
const error = ref('');
const showCreateModal = ref(false);
const newRoomTitle = ref('');
const creating = ref(false);

const fetchRooms = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await roomsApi.getRooms();
    rooms.value = response.data;
  } catch (err) {
    error.value = 'Failed to load rooms. Please try again.';
  } finally {
    loading.value = false;
  }
};

const handleCreateRoom = async () => {
  creating.value = true;
  try {
    const response = await roomsApi.createRoom({ title: newRoomTitle.value });
    rooms.value.unshift(response.data);
    showCreateModal.value = false;
    newRoomTitle.value = '';
  } catch (err) {
    alert('Failed to create room. Please try again.');
  } finally {
    creating.value = false;
  }
};

const handleDeleteRoom = async (roomId) => {
  if (!confirm('Are you sure you want to delete this room?')) return;
  
  try {
    await roomsApi.deleteRoom(roomId);
    rooms.value = rooms.value.filter(r => r.id !== roomId);
  } catch (err) {
    alert('Failed to delete room. Please try again.');
  }
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};

onMounted(() => {
  fetchRooms();
});
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.content-header h2 {
  margin: 0;
  font-size: 28px;
  color: #333;
}

.btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #667eea;
  color: white;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  background-color: #fee;
  color: #c33;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin: 0 0 20px 0;
  font-size: 22px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
</style>
