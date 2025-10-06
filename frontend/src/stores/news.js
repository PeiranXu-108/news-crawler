import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { newsApi } from '../services/api'

export const useNewsStore = defineStore('news', () => {
  // State
  const tasks = ref([])
  const articles = ref([])
  const sources = ref([])
  const currentTask = ref(null)
  const currentArticle = ref(null)
  const filters = ref({
    status: '',
    source: '',
    task: '',
    search: ''
  })
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const filteredTasks = computed(() => {
    if (!filters.value.status) return tasks.value
    return tasks.value.filter(task => task.status === filters.value.status)
  })

  const filteredArticles = computed(() => {
    let filtered = articles.value

    if (filters.value.source) {
      filtered = filtered.filter(article => article.source === filters.value.source)
    }

    if (filters.value.task) {
      filtered = filtered.filter(article => article.task_id === parseInt(filters.value.task))
    }

    if (filters.value.search) {
      const searchTerm = filters.value.search.toLowerCase()
      filtered = filtered.filter(article => 
        article.title.toLowerCase().includes(searchTerm) ||
        article.summary?.toLowerCase().includes(searchTerm) ||
        article.source.toLowerCase().includes(searchTerm)
      )
    }

    return filtered
  })

  const stats = computed(() => ({
    totalTasks: tasks.value.length,
    totalArticles: articles.value.length,
    runningTasks: tasks.value.filter(t => t.status === 'running').length,
    activeSources: sources.value.filter(s => s.is_active).length
  }))

  // Actions
  const initialize = async () => {
    try {
      isLoading.value = true
      await Promise.all([
        loadTasks(),
        loadArticles(),
        loadSources()
      ])
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const loadTasks = async (params = {}) => {
    try {
      const taskParams = { ...params }
      if (filters.value.status) {
        taskParams.status = filters.value.status
      }
      tasks.value = await newsApi.getTasks(taskParams)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const loadArticles = async (params = {}) => {
    try {
      const articleParams = { ...params }
      if (filters.value.source) {
        articleParams.source = filters.value.source
      }
      if (filters.value.task) {
        articleParams.task_id = filters.value.task
      }
      articles.value = await newsApi.getArticles(articleParams)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const loadSources = async () => {
    try {
      sources.value = await newsApi.getRSSSources()
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const createTask = async (taskData) => {
    try {
      isLoading.value = true
      await newsApi.createTask(taskData)
      await loadTasks()
      await loadArticles()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteTask = async (taskId) => {
    try {
      isLoading.value = true
      await newsApi.deleteTask(taskId)
      await loadTasks()
      await loadArticles()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const retryTask = async (taskId) => {
    try {
      isLoading.value = true
      await newsApi.retryTask(taskId)
      await loadTasks()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const createSource = async (sourceData) => {
    try {
      isLoading.value = true
      await newsApi.createRSSSource(sourceData)
      await loadSources()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteSource = async (sourceId) => {
    try {
      isLoading.value = true
      await newsApi.deleteRSSSource(sourceId)
      await loadSources()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const regenerateArticleSummary = async (articleId) => {
    try {
      isLoading.value = true
      await newsApi.regenerateArticleSummary(articleId)
      await loadArticles()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const setFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const clearError = () => {
    error.value = null
  }

  // WebSocket handling
  const setupWebSocket = () => {
    try {
      newsApi.connectWebSocket()
      
      // Listen for WebSocket events
      document.addEventListener('task-progress', handleTaskProgress)
      document.addEventListener('websocket-message', handleWebSocketMessage)
    } catch (err) {
      console.error('Failed to setup WebSocket:', err)
    }
  }

  const handleTaskProgress = (event) => {
    const data = event.detail
    console.log('Task progress update:', data)
    
    // Update task in current list
    const taskIndex = tasks.value.findIndex(t => t.id === data.task_id)
    if (taskIndex !== -1) {
      tasks.value[taskIndex].progress = data.progress
      tasks.value[taskIndex].status = data.status
    }
  }

  const handleWebSocketMessage = (event) => {
    const data = event.detail
    console.log('WebSocket message:', data)
  }

  const disconnectWebSocket = () => {
    newsApi.disconnectWebSocket()
    document.removeEventListener('task-progress', handleTaskProgress)
    document.removeEventListener('websocket-message', handleWebSocketMessage)
  }

  return {
    // State
    tasks,
    articles,
    sources,
    currentTask,
    currentArticle,
    filters,
    isLoading,
    error,
    // Getters
    filteredTasks,
    filteredArticles,
    stats,
    // Actions
    initialize,
    loadTasks,
    loadArticles,
    loadSources,
    createTask,
    deleteTask,
    retryTask,
    createSource,
    deleteSource,
    regenerateArticleSummary,
    setFilters,
    clearError,
    setupWebSocket,
    disconnectWebSocket
  }
})
