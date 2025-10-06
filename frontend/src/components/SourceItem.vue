<template>
  <div class="source-item">
    <div class="source-info">
      <h4>{{ source.name }}</h4>
      <div class="source-url">{{ source.url_template }}</div>
      <div class="task-meta">
        <span>Priority: {{ source.priority }}</span>
        <span>Query Support: {{ source.supports_query ? 'Yes' : 'No' }}</span>
        <span>Status: {{ source.is_active ? 'Active' : 'Inactive' }}</span>
      </div>
    </div>
    <div class="source-actions">
      <button @click="$emit('edit', source)" class="btn btn-outline">
        <i class="fas fa-edit"></i>
      </button>
      <button @click="$emit('delete', source.id)" class="btn btn-danger">
        <i class="fas fa-trash"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  source: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])
</script>
