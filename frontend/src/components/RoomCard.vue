<template>
  <div class="room-card">
    <div class="room-header">
      <h3>{{ room.title }}</h3>
      <button
        v-if="isOwner"
        @click.stop="handleDelete"
        class="delete-btn"
        title="Delete room"
      >
        ×
      </button>
    </div>
    <div class="room-meta">
      <p class="owner">Owner: {{ room.owner?.email || 'Unknown' }}</p>
      <p class="date">Updated: {{ formatDate(room.updated_at) }}</p>
    </div>
    <div class="room-actions">
      <router-link :to="`/room/${room.id}`" class="enter-btn">
        Enter Room →
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';

const props = defineProps({
  room: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['delete']);

const authStore = useAuthStore();

const isOwner = computed(() => {
  return authStore.user?.id === props.room.owner?.id;
});

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  
  return date.toLocaleDateString();
};

const handleDelete = () => {
  emit('delete', props.room.id);
};
</script>

<style scoped>
.room-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.room-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.room-header h3 {
  margin: 0;
  font-size: 20px;
  color: #333;
  flex: 1;
  word-break: break-word;
}

.delete-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  line-height: 1;
}

.delete-btn:hover {
  background: #fee;
  color: #c33;
}

.room-meta {
  margin-bottom: 16px;
}

.room-meta p {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

.owner {
  font-weight: 500;
}

.date {
  color: #999;
}

.room-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.enter-btn {
  display: inline-block;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
}

.enter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
