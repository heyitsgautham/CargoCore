import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchSupportRefundCases,
  flagRefundCaseUrgent,
  fetchCustomerHistory,
} from '@/utils/aiApi'

export const useRefundStore = defineStore('refund', () => {
  const cases = ref([])
  const stats = ref({ total_refunded_value: 0, pending_decision: 0, urgent_count: 0 })
  const loading = ref(false)
  const error = ref('')
  const initialized = ref(false)

  // Customer history cache: { [userId]: historyObject }
  const customerHistoryCache = ref({})

  // Chargeback risk: LM rejected claim AND customer sentiment is Negative
  const chargebackRiskCount = computed(
    () =>
      cases.value.filter(
        (c) => c.status === 'Rejected' && c.sentiment === 'Negative',
      ).length,
  )

  const urgentCount = computed(() => cases.value.filter((c) => c.is_urgent).length)

  async function load(force = false) {
    if (initialized.value && !force) return
    loading.value = true
    error.value = ''
    try {
      const response = await fetchSupportRefundCases()
      cases.value = response.cases || []
      stats.value = response.stats || {}
      initialized.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load refund cases'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    await load(true)
  }

  async function flagUrgent(caseId, isUrgent, urgentReason) {
    const updated = await flagRefundCaseUrgent(caseId, isUrgent, urgentReason || null)
    const idx = cases.value.findIndex((c) => c.id === updated.id)
    if (idx !== -1) {
      cases.value.splice(idx, 1, updated)
    }
    return updated
  }

  async function loadCustomerHistory(userId) {
    if (!userId) return null
    if (customerHistoryCache.value[userId]) return customerHistoryCache.value[userId]
    try {
      const history = await fetchCustomerHistory(userId)
      customerHistoryCache.value[userId] = history
      return history
    } catch {
      return null
    }
  }

  return {
    cases,
    stats,
    loading,
    error,
    initialized,
    chargebackRiskCount,
    urgentCount,
    customerHistoryCache,
    load,
    refresh,
    flagUrgent,
    loadCustomerHistory,
  }
})
