import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchEscalationCenter, resolveEscalationCenter } from '@/utils/aiApi'

export const useEscalationStore = defineStore('escalation', () => {
  const escalations = ref([])
  const openCount = ref(0)
  const resolvedCount = ref(0)
  const loading = ref(false)
  const error = ref('')

  const openEscalations = computed(() => escalations.value.filter(e => e.status === 'OPEN'))
  const resolvedEscalations = computed(() => escalations.value.filter(e => e.status === 'RESOLVED'))

  async function load(statusFilter = '') {
    loading.value = true
    error.value = ''
    try {
      const response = await fetchEscalationCenter(statusFilter)
      escalations.value = response.escalations || []
      openCount.value = response.open_count ?? 0
      resolvedCount.value = response.resolved_count ?? 0
    } catch (err) {
      error.value = err.message || 'Failed to load escalations'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resolve(escalationId) {
    await resolveEscalationCenter(escalationId)
    const idx = escalations.value.findIndex(e => e.id === escalationId)
    if (idx !== -1) {
      escalations.value[idx] = {
        ...escalations.value[idx],
        status: 'RESOLVED',
        resolved_at: new Date().toISOString(),
      }
      openCount.value = Math.max(0, openCount.value - 1)
      resolvedCount.value += 1
    }
  }

  return {
    escalations,
    openCount,
    resolvedCount,
    openEscalations,
    resolvedEscalations,
    loading,
    error,
    load,
    resolve,
  }
})
