import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchSupportDamageReports,
  createSupportDamageReport,
  updateDamageReportNotes,
  fetchCustomerHistory,
} from '@/utils/aiApi'

export const useReverseLogisticsStore = defineStore('reverseLogistics', () => {
  const reports = ref([])
  const stats = ref({ total: 0, reported: 0, photo_review: 0, pickup_inspection: 0, under_review: 0 })
  const loading = ref(false)
  const error = ref('')
  const initialized = ref(false)

  // Customer history cache: { [userId]: historyObject }
  const customerHistoryCache = ref({})

  const reportedCount = computed(() => reports.value.filter((r) => r.status === 'reported').length)
  const photoReviewCount = computed(() => reports.value.filter((r) => r.flow_type === 'photo_review').length)
  const pickupInspectionCount = computed(() => reports.value.filter((r) => r.flow_type === 'pickup_inspection').length)
  const underReviewCount = computed(() => reports.value.filter((r) => ['under_review', 'Under Review'].includes(r.status)).length)

  async function load(force = false) {
    if (initialized.value && !force) return
    loading.value = true
    error.value = ''
    try {
      const response = await fetchSupportDamageReports()
      reports.value = response.reports || []
      stats.value = response.stats || {}
      initialized.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load damage reports'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    await load(true)
  }

  async function createReport(payload) {
    const created = await createSupportDamageReport(payload)
    reports.value.unshift(created)
    stats.value.total = (stats.value.total || 0) + 1
    stats.value.reported = (stats.value.reported || 0) + 1
    return created
  }

  async function updateNotes(reportId, supportNotes) {
    const updated = await updateDamageReportNotes(reportId, supportNotes)
    const idx = reports.value.findIndex((r) => r.id === updated.id)
    if (idx !== -1) {
      reports.value.splice(idx, 1, updated)
    }
    return updated
  }

  async function loadCustomerHistory(userId) {
    if (customerHistoryCache.value[userId]) return customerHistoryCache.value[userId]
    try {
      const history = await fetchCustomerHistory(userId)
      customerHistoryCache.value[userId] = history
      return history
    } catch {
      return null
    }
  }

  // Check if a duplicate damage report exists for the same order_id
  function findDuplicate(orderId) {
    if (!orderId) return null
    return reports.value.find((r) => r.order_id === orderId) || null
  }

  return {
    reports,
    stats,
    loading,
    error,
    initialized,
    reportedCount,
    photoReviewCount,
    pickupInspectionCount,
    underReviewCount,
    customerHistoryCache,
    load,
    refresh,
    createReport,
    updateNotes,
    loadCustomerHistory,
    findDuplicate,
  }
})
