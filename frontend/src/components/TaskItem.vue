<template>
  <div class="task-item">
    <div class="task-info">
      <h4>{{ task.query }}</h4>
      <div class="task-meta">
        <span>Created: {{ formatRelativeTime(task.created_at) }}</span>
        <span>Limit: {{ task.limit }}</span>
        <span>Articles: {{ task.processed_articles }}/{{ task.total_articles }}</span>
      </div>
      <div v-if="task.status === 'running'" class="progress-bar">
        <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
      </div>
    </div>
    <div class="task-actions">
      <span class="task-status" :class="task.status">{{ task.status }}</span>
      <button 
        v-if="task.status === 'failed'" 
        @click="$emit('retry', task.id)"
        class="btn btn-outline"
      >
        <i class="fas fa-redo"></i>
      </button>
      <button 
        @click="$emit('delete', task.id)"
        class="btn btn-danger"
      >
        <i class="fas fa-trash"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { newsApi } from '../services/api'

defineProps({
  task: {
    type: Object,
    required: true
  }
})

defineEmits(['retry', 'delete'])

const formatRelativeTime = (dateString) => {
  return newsApi.formatRelativeTime(dateString)
}
</script>
