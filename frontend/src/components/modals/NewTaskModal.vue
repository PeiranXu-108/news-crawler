<template>
  <div class="modal active" @click="handleBackdropClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Create New Crawl Task</h3>
        <button @click="$emit('close')" class="modal-close">&times;</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="taskQuery">Search Query *</label>
            <input 
              v-model="form.query" 
              type="text" 
              id="taskQuery" 
              required 
              placeholder="Enter keywords to search for..."
            >
          </div>
          
          <div class="form-group">
            <label for="taskSince">Since Date</label>
            <input v-model="form.since" type="date" id="taskSince">
          </div>
          
          <div class="form-group">
            <label for="taskLimit">Article Limit</label>
            <input 
              v-model.number="form.limit" 
              type="number" 
              id="taskLimit" 
              min="1" 
              max="1000"
            >
          </div>
          
          <div class="form-group">
            <label for="customFeeds">Custom RSS Feeds (optional)</label>
            <textarea 
              v-model="form.customFeeds" 
              id="customFeeds" 
              placeholder="Enter RSS feed URLs, one per line"
            ></textarea>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" type="button" class="btn btn-secondary">Cancel</button>
        <button @click="handleSubmit" type="button" class="btn btn-primary">Create Task</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useNewsStore } from '../../stores/news'

const newsStore = useNewsStore()

const form = ref({
  query: '',
  since: '',
  limit: 50,
  customFeeds: ''
})

const handleSubmit = async () => {
  try {
    const taskData = {
      query: form.value.query,
      since: form.value.since || null,
      limit: form.value.limit,
      custom_feeds: form.value.customFeeds ? 
        form.value.customFeeds.split('\n').filter(url => url.trim()) : null
    }

    await newsStore.createTask(taskData)
    emit('close')
  } catch (error) {
    console.error('Failed to create task:', error)
  }
}

const handleBackdropClick = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const emit = defineEmits(['close'])
</script>
