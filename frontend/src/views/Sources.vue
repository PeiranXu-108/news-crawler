<template>
  <section class="section active">
    <div class="section-header">
      <h2>RSS Sources</h2>
      <div class="section-actions">
        <button @click="$emit('showAddSource')" class="btn btn-primary">
          <i class="fas fa-plus"></i>
          Add Source
        </button>
        <button @click="refreshSources" class="btn btn-outline">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
      </div>
    </div>
    
    <div class="sources-list">
      <div v-if="sources.length === 0" class="text-center">
        <p>No sources found</p>
      </div>
      <div v-else>
        <SourceItem 
          v-for="source in sources" 
          :key="source.id" 
          :source="source"
          @edit="editSource"
          @delete="deleteSource"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useNewsStore } from '../stores/news'
import SourceItem from '../components/SourceItem.vue'

const emit = defineEmits(['showAddSource'])

const newsStore = useNewsStore()

const sources = computed(() => newsStore.sources)

const refreshSources = async () => {
  try {
    await newsStore.loadSources()
  } catch (error) {
    console.error('Failed to refresh sources:', error)
  }
}

const editSource = (source) => {
  // TODO: Implement edit source functionality
  console.log('Edit source:', source)
}

const deleteSource = async (sourceId) => {
  if (!confirm('Are you sure you want to delete this RSS source?')) {
    return
  }
  
  try {
    await newsStore.deleteSource(sourceId)
  } catch (error) {
    console.error('Failed to delete source:', error)
  }
}

onMounted(() => {
  refreshSources()
})
</script>
