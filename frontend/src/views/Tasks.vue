<template>
  <section class="section active">
    <div class="section-header">
      <h2>Tasks</h2>
      <div class="section-actions">
        <button @click="$emit('showNewTask')" class="btn btn-primary">
          <i class="fas fa-plus"></i>
          New Task
        </button>
        <button @click="refreshTasks" class="btn btn-outline">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
      </div>
    </div>
    
    <div class="filters">
      <select v-model="statusFilter" @change="updateStatusFilter" class="filter-select">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
    </div>
    
    <div class="task-list">
      <div v-if="filteredTasks.length === 0" class="text-center">
        <p>No tasks found</p>
      </div>
      <div v-else>
        <TaskItem 
          v-for="task in filteredTasks" 
          :key="task.id" 
          :task="task"
          @retry="retryTask"
          @delete="deleteTask"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '../stores/news'
import TaskItem from '../components/TaskItem.vue'

const emit = defineEmits(['showNewTask'])

const newsStore = useNewsStore()

const statusFilter = ref('')

const filteredTasks = computed(() => newsStore.filteredTasks)

const updateStatusFilter = () => {
  newsStore.setFilters({ status: statusFilter.value })
}

const refreshTasks = async () => {
  try {
    await newsStore.loadTasks()
  } catch (error) {
    console.error('Failed to refresh tasks:', error)
  }
}

const retryTask = async (taskId) => {
  try {
    await newsStore.retryTask(taskId)
  } catch (error) {
    console.error('Failed to retry task:', error)
  }
}

const deleteTask = async (taskId) => {
  if (!confirm('Are you sure you want to delete this task and all its articles?')) {
    return
  }
  
  try {
    await newsStore.deleteTask(taskId)
  } catch (error) {
    console.error('Failed to delete task:', error)
  }
}

onMounted(() => {
  refreshTasks()
})
</script>
