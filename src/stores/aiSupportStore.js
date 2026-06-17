import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  executeSupportAnalyticsInsight,
  escalateSupportSession,
  fetchSupportAnalytics,
  fetchSupportDashboard,
  fetchSupportSettings,
  fetchSupportSession,
  fetchSupportSessions,
  replyToSupportSession,
  takeOverSupportSession,
  updateSupportSettings,
} from '@/utils/aiApi'

const SUPPORT_INBOX_ROLES = new Set(['INDIVIDUAL', 'VENDOR'])

function isSupportInboxSession(session) {
  const role = String(session?.user_role || '').trim().toUpperCase()
  return SUPPORT_INBOX_ROLES.has(role)
}

function filterSupportInboxSessions(items = []) {
  return items.filter((item) => isSupportInboxSession(item))
}

export const useAiSupportStore = defineStore('ai-support', () => {
  const dashboard = ref(null)
  const analytics = ref(null)
  const supportSettings = ref(null)
  const sessions = ref([])
  const selectedSession = ref(null)
  const loadingDashboard = ref(false)
  const loadingAnalytics = ref(false)
  const loadingSettings = ref(false)
  const loadingSessions = ref(false)
  const loadingSessionDetail = ref(false)
  const actionInFlight = ref(false)
  const executingInsightId = ref('')
  const error = ref('')
  const sessionsLoaded = ref(false)

  const unreadNotificationsCount = computed(() => {
    return sessions.value.filter((session) => session.escalation?.status === 'OPEN').length
  })

  async function loadDashboard() {
    loadingDashboard.value = true
    error.value = ''
    try {
      dashboard.value = await fetchSupportDashboard()
    } catch (err) {
      error.value = err.message || 'Failed to load support dashboard'
      throw err
    } finally {
      loadingDashboard.value = false
    }
  }

  async function loadAnalytics(timeRange = '7D') {
    loadingAnalytics.value = true
    error.value = ''
    try {
      analytics.value = await fetchSupportAnalytics(timeRange)
      return analytics.value
    } catch (err) {
      error.value = err.message || 'Failed to load analytics'
      throw err
    } finally {
      loadingAnalytics.value = false
    }
  }

  async function loadSupportSettings() {
    loadingSettings.value = true
    error.value = ''
    try {
      supportSettings.value = await fetchSupportSettings()
      return supportSettings.value
    } catch (err) {
      error.value = err.message || 'Failed to load support settings'
      throw err
    } finally {
      loadingSettings.value = false
    }
  }

  async function loadSessions(search = '') {
    loadingSessions.value = true
    error.value = ''
    try {
      const response = await fetchSupportSessions(search)
      sessions.value = filterSupportInboxSessions(response.sessions || [])
      if (
        selectedSession.value?.session?.session_id
        && !sessions.value.some((item) => item.session_id === selectedSession.value.session.session_id)
      ) {
        selectedSession.value = null
      }
      sessionsLoaded.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load live conversations'
      throw err
    } finally {
      loadingSessions.value = false
    }
  }

  async function loadSessionDetail(sessionId) {
    if (!sessionId) return null
    loadingSessionDetail.value = true
    error.value = ''
    try {
      const detail = await fetchSupportSession(sessionId)
      if (!isSupportInboxSession(detail?.session)) {
        selectedSession.value = null
        return null
      }
      selectedSession.value = detail
      _upsertSession(detail.session)
      return detail
    } catch (err) {
      error.value = err.message || 'Failed to load conversation detail'
      throw err
    } finally {
      loadingSessionDetail.value = false
    }
  }

  async function takeOver(sessionId) {
    actionInFlight.value = true
    try {
      const detail = await takeOverSupportSession(sessionId)
      if (!isSupportInboxSession(detail?.session)) {
        selectedSession.value = null
        return null
      }
      selectedSession.value = detail
      _upsertSession(detail.session)
      return detail
    } finally {
      actionInFlight.value = false
    }
  }

  async function sendReply(sessionId, message) {
    actionInFlight.value = true
    try {
      const detail = await replyToSupportSession(sessionId, message)
      if (!isSupportInboxSession(detail?.session)) {
        selectedSession.value = null
        return null
      }
      selectedSession.value = detail
      _upsertSession(detail.session)
      return detail
    } finally {
      actionInFlight.value = false
    }
  }

  async function escalate(sessionId, reason) {
    actionInFlight.value = true
    try {
      await escalateSupportSession(sessionId, reason)
      const detail = await fetchSupportSession(sessionId)
      if (!isSupportInboxSession(detail?.session)) {
        selectedSession.value = null
        return null
      }
      selectedSession.value = detail
      _upsertSession(detail.session)
      return detail
    } finally {
      actionInFlight.value = false
    }
  }

  async function executeInsight(insightId, timeRange = '7D') {
    executingInsightId.value = insightId
    error.value = ''
    try {
      const result = await executeSupportAnalyticsInsight(insightId, timeRange)
      await loadAnalytics(timeRange)
      return result
    } catch (err) {
      error.value = err.message || 'Failed to execute analytics insight'
      throw err
    } finally {
      executingInsightId.value = ''
    }
  }

  async function saveSupportSettings(payload) {
    loadingSettings.value = true
    error.value = ''
    try {
      supportSettings.value = await updateSupportSettings(payload)
      return supportSettings.value
    } catch (err) {
      error.value = err.message || 'Failed to save support settings'
      throw err
    } finally {
      loadingSettings.value = false
    }
  }

  function _upsertSession(session) {
    if (!isSupportInboxSession(session)) return
    const index = sessions.value.findIndex((item) => item.session_id === session.session_id)
    if (index === -1) {
      sessions.value.unshift(session)
    } else {
      sessions.value.splice(index, 1, session)
    }
  }

  function clearSelectedSession() {
    selectedSession.value = null
  }

  return {
    dashboard,
    analytics,
    supportSettings,
    sessions,
    selectedSession,
    loadingDashboard,
    loadingAnalytics,
    loadingSettings,
    loadingSessions,
    loadingSessionDetail,
    actionInFlight,
    executingInsightId,
    error,
    unreadNotificationsCount,
    sessionsLoaded,
    clearSelectedSession,
    loadDashboard,
    loadAnalytics,
    loadSupportSettings,
    loadSessions,
    loadSessionDetail,
    takeOver,
    sendReply,
    escalate,
    executeInsight,
    saveSupportSettings,
  }
})
