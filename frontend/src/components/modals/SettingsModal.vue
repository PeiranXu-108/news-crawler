<template>
  <div class="modal active" @click="handleBackdropClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Settings</h3>
        <button @click="$emit('close')" class="modal-close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="settings-section">
          <h4>Summary Generation</h4>
          <div class="form-group">
            <label for="summaryStrategy">Strategy</label>
            <select v-model="settings.summaryStrategy" id="summaryStrategy">
              <option value="rss_first">RSS First (use RSS summary if available)</option>
              <option value="ai_generated">AI Generated (use AI model)</option>
              <option value="hybrid">Hybrid (combine RSS and AI)</option>
              <option value="simple">Simple (extract from text)</option>
            </select>
          </div>
        </div>
        
        <div class="settings-section">
          <h4>API Configuration</h4>
          <div class="form-group">
            <label for="apiBaseUrl">API Base URL</label>
            <input v-model="settings.apiBaseUrl" type="url" id="apiBaseUrl">
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" type="button" class="btn btn-secondary">Cancel</button>
        <button @click="saveSettings" type="button" class="btn btn-primary">Save Settings</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { newsApi } from '../../services/api'

const settings = ref({
  summaryStrategy: 'rss_first',
  apiBaseUrl: 'http://localhost:8000'
})

const saveSettings = async () => {
  try {
    if (settings.value.summaryStrategy) {
      await newsApi.setSummaryStrategy(settings.value.summaryStrategy)
    }
    
    if (settings.value.apiBaseUrl && settings.value.apiBaseUrl !== newsApi.baseURL) {
      newsApi.baseURL = settings.value.apiBaseUrl
      newsApi.disconnectWebSocket()
      newsApi.connectWebSocket()
    }
    
    emit('close')
  } catch (error) {
    console.error('Failed to save settings:', error)
  }
}

const handleBackdropClick = (event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const emit = defineEmits(['close'])
</script>
