<template>
  <div class="article-item" @click="$emit('click', article)">
    <div class="article-header">
      <div class="article-title">{{ article.title }}</div>
      <div class="article-meta">
        <span class="article-source">{{ article.source }}</span>
        <span class="article-date">{{ formatRelativeTime(article.published) }}</span>
      </div>
    </div>
    <div class="article-summary">{{ truncateText(article.summary || 'No summary available') }}</div>
    <div v-if="article.tags && article.tags.length" class="article-tags">
      <span v-for="tag in article.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>
  </div>
</template>

<script setup>
import { newsApi } from '../services/api'

defineProps({
  article: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

const formatRelativeTime = (dateString) => {
  return newsApi.formatRelativeTime(dateString)
}

const truncateText = (text) => {
  return newsApi.truncateText(text)
}
</script>
