<template>
  <div class="modal active" @click="handleBackdropClick">
    <div class="modal-content large" @click.stop>
      <div class="modal-header">
        <h3>{{ article?.title || 'Article Title' }}</h3>
        <button @click="$emit('close')" class="modal-close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="article-meta">
          <span class="article-source">{{ article?.source || 'Source' }}</span>
          <span class="article-date">{{ formatDate(article?.published) || 'Date' }}</span>
          <a v-if="article?.url" :href="article.url" target="_blank" class="article-link">
            <i class="fas fa-external-link-alt"></i>
            View Original
          </a>
        </div>
        <div class="article-summary" v-html="article?.summary || 'No summary available'"></div>
        <div class="article-content" v-html="article?.text || 'No content available'"></div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" type="button" class="btn btn-secondary">Close</button>
        <button @click="regenerateSummary" type="button" class="btn btn-primary">
          <i class="fas fa-sync-alt"></i>
          Regenerate Summary
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { newsApi } from '../../services/api'
import { useNewsStore } from '../../stores/news'

const newsStore = useNewsStore()

const props = defineProps({
  article: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const formatDate = (dateString) => {
  return newsApi.formatDate(dateString)
}

const regenerateSummary = async () => {
  if (!props.article?.id) return
  
  try {
    await newsStore.regenerateArticleSummary(props.article.id)
  } catch (error) {
    console.error('Failed to regenerate summary:', error)
  }
}

const handleBackdropClick = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}
</script>
