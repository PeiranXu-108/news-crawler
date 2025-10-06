<template>
  <div class="modal active" @click="handleBackdropClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Add RSS Source</h3>
        <button @click="$emit('close')" class="modal-close">&times;</button>
      </div>
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="sourceName">Source Name *</label>
            <input 
              v-model="form.name" 
              type="text" 
              id="sourceName" 
              required 
              placeholder="e.g., CNN News"
            >
          </div>
          
          <div class="form-group">
            <label for="sourceUrl">RSS URL *</label>
            <input 
              v-model="form.url_template" 
              type="url" 
              id="sourceUrl" 
              required 
              placeholder="https://example.com/rss"
            >
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="form.supports_query" type="checkbox">
              <span class="checkmark"></span>
              Supports query parameters (use {query} placeholder)
            </label>
          </div>
          
          <div class="form-group">
            <label for="sourcePriority">Priority</label>
            <input 
              v-model.number="form.priority" 
              type="number" 
              id="sourcePriority" 
              min="0" 
              max="100"
            >
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" type="button" class="btn btn-secondary">Cancel</button>
        <button @click="handleSubmit" type="button" class="btn btn-primary">Add Source</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useNewsStore } from '../../stores/news'

const newsStore = useNewsStore()

const form = ref({
  name: '',
  url_template: '',
  supports_query: false,
  priority: 0
})

const handleSubmit = async () => {
  try {
    await newsStore.createSource(form.value)
    emit('close')
  } catch (error) {
    console.error('Failed to create source:', error)
  }
}

const handleBackdropClick = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const emit = defineEmits(['close'])
</script>
