<template>
  <section class="section active">
    <div class="section-header">
      <h2>Dashboard</h2>
      <div class="section-actions">
        <button @click="refreshDashboard" class="btn btn-outline">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
      </div>
    </div>
    
    <div class="dashboard-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-tasks"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.totalTasks }}</h3>
          <p>Total Tasks</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-newspaper"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.totalArticles }}</h3>
          <p>Total Articles</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.runningTasks }}</h3>
          <p>Running Tasks</p>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-rss"></i>
        </div>
        <div class="stat-content">
          <h3>{{ stats.activeSources }}</h3>
          <p>Active Sources</p>
        </div>
      </div>
    </div>

    <div class="recent-tasks">
      <h3>Recent Tasks</h3>
      <div class="task-list">
        <div v-if="recentTasks.length === 0" class="text-center">
          <p>No recent tasks</p>
        </div>
        <div v-else>
          <TaskItem 
            v-for="task in recentTasks" 
            :key="task.id" 
            :task="task"
            @retry="retryTask"
            @delete="deleteTask"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useNewsStore } from '../stores/news'
import TaskItem from '../components/TaskItem.vue'

const newsStore = useNewsStore()

const recentTasks = computed(() => newsStore.tasks.slice(0, 5))
const stats = computed(() => newsStore.stats)

const refreshDashboard = async () => {
  try {
    await newsStore.loadTasks()
    await newsStore.loadArticles()
    await newsStore.loadSources()
  } catch (error) {
    console.error('Failed to refresh dashboard:', error)
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
  refreshDashboard()
})
</script>
