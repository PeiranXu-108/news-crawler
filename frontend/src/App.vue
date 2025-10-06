<template>
  <div id="app">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <h1 class="app-title">
          <i class="fas fa-newspaper"></i>
          News Crawler
        </h1>
        <div class="header-actions">
          <button @click="showNewTaskModal" class="btn btn-primary">
            <i class="fas fa-plus"></i>
            New Task
          </button>
          <button @click="showSettingsModal" class="btn btn-secondary">
            <i class="fas fa-cog"></i>
            Settings
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Sidebar -->
      <aside class="sidebar">
        <nav class="nav">
          <ul class="nav-list">
            <li class="nav-item">
              <router-link to="/dashboard" class="nav-link">
                <i class="fas fa-tachometer-alt"></i>
                Dashboard
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/tasks" class="nav-link">
                <i class="fas fa-tasks"></i>
                Tasks
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/articles" class="nav-link">
                <i class="fas fa-newspaper"></i>
                Articles
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/sources" class="nav-link">
                <i class="fas fa-rss"></i>
                RSS Sources
              </router-link>
            </li>
          </ul>
        </nav>
      </aside>

      <!-- Content Area -->
      <div class="content">
        <router-view @showNewTask="showNewTaskModal" @showAddSource="showAddSourceModal" @showArticle="showArticleModal" />
      </div>
    </main>

    <!-- Modals -->
    <NewTaskModal v-if="showNewTask" @close="showNewTask = false" />
    <ArticleModal v-if="showArticle" :article="selectedArticle" @close="showArticle = false" />
    <AddSourceModal v-if="showAddSource" @close="showAddSource = false" />
    <SettingsModal v-if="showSettings" @close="showSettings = false" />

    <!-- Loading Overlay -->
    <LoadingOverlay v-if="isLoading" />

    <!-- Toast Notifications -->
    <ToastContainer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNewsStore } from './stores/news'
import NewTaskModal from './components/modals/NewTaskModal.vue'
import ArticleModal from './components/modals/ArticleModal.vue'
import AddSourceModal from './components/modals/AddSourceModal.vue'
import SettingsModal from './components/modals/SettingsModal.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
import ToastContainer from './components/ToastContainer.vue'

const newsStore = useNewsStore()

// Modal states
const showNewTask = ref(false)
const showArticle = ref(false)
const showAddSource = ref(false)
const showSettings = ref(false)
const selectedArticle = ref(null)
const isLoading = ref(false)

// Methods
const showNewTaskModal = () => {
  showNewTask.value = true
}

const showAddSourceModal = () => {
  showAddSource.value = true
}

const showArticleModal = (article) => {
  selectedArticle.value = article
  showArticle.value = true
}

const showSettingsModal = () => {
  showSettings.value = true
}

// Initialize app
onMounted(async () => {
  try {
    isLoading.value = true
    await newsStore.initialize()
    newsStore.setupWebSocket()
  } catch (error) {
    console.error('Failed to initialize app:', error)
  } finally {
    isLoading.value = false
  }
})
</script>