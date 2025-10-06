<template>
  <section class="section active">
    <div class="section-header">
      <h2>Articles</h2>
      <div class="section-actions">
        <button @click="refreshArticles" class="btn btn-outline">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
        <button @click="exportArticles" class="btn btn-secondary">
          <i class="fas fa-download"></i>
          Export
        </button>
      </div>
    </div>
    
    <div class="filters">
      <input 
        v-model="searchTerm" 
        @input="updateSearchFilter" 
        type="text" 
        placeholder="Search articles..." 
        class="filter-input"
      >
      <select v-model="sourceFilter" @change="updateSourceFilter" class="filter-select">
        <option value="">All Sources</option>
        <option v-for="source in uniqueSources" :key="source" :value="source">
          {{ source }}
        </option>
      </select>
      <select v-model="taskFilter" @change="updateTaskFilter" class="filter-select">
        <option value="">All Tasks</option>
        <option v-for="task in tasks" :key="task.id" :value="task.id">
          {{ task.query }} ({{ task.id }})
        </option>
      </select>
    </div>
    
    <div class="articles-list">
      <div v-if="filteredArticles.length === 0" class="text-center">
        <p>No articles found</p>
      </div>
      <div v-else>
        <ArticleItem 
          v-for="article in filteredArticles" 
          :key="article.id" 
          :article="article"
          @click="showArticleDetail(article)"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '../stores/news'
import ArticleItem from '../components/ArticleItem.vue'

const emit = defineEmits(['showArticle'])

const newsStore = useNewsStore()

const searchTerm = ref('')
const sourceFilter = ref('')
const taskFilter = ref('')

const filteredArticles = computed(() => newsStore.filteredArticles)
const tasks = computed(() => newsStore.tasks)
const uniqueSources = computed(() => {
  const sources = [...new Set(newsStore.articles.map(a => a.source))]
  return sources.sort()
})

const updateSearchFilter = () => {
  newsStore.setFilters({ search: searchTerm.value })
}

const updateSourceFilter = () => {
  newsStore.setFilters({ source: sourceFilter.value })
}

const updateTaskFilter = () => {
  newsStore.setFilters({ task: taskFilter.value })
}

const refreshArticles = async () => {
  try {
    await newsStore.loadArticles()
  } catch (error) {
    console.error('Failed to refresh articles:', error)
  }
}

const showArticleDetail = (article) => {
  emit('showArticle', article)
}

const exportArticles = async () => {
  try {
    const articles = await newsStore.loadArticles()
    const dataStr = JSON.stringify(articles, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(dataBlob)
    link.download = `news-articles-${new Date().toISOString().split('T')[0]}.json`
    link.click()
  } catch (error) {
    console.error('Failed to export articles:', error)
  }
}

onMounted(() => {
  refreshArticles()
})
</script>
