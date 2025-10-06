<template>
  <div class="toast-container">
    <div 
      v-for="toast in toasts" 
      :key="toast.id" 
      :class="['toast', toast.type]"
    >
      <i :class="getIconClass(toast.type)"></i>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const toasts = ref([])
let toastId = 0

const getIconClass = (type) => {
  const icons = {
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle'
  }
  return icons[type] || icons.info
}

const showToast = (message, type = 'info') => {
  const id = ++toastId
  const toast = { id, message, type }
  
  toasts.value.push(toast)
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }, 5000)
}

// Global toast function
window.showToast = showToast

onMounted(() => {
  // Listen for custom toast events
  document.addEventListener('show-toast', (event) => {
    showToast(event.detail.message, event.detail.type)
  })
})

onUnmounted(() => {
  document.removeEventListener('show-toast', showToast)
})
</script>
