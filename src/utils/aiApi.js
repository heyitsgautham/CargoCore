/**
 * aiApi.js
 * Typed wrapper around the backend /api/v1/ai/* endpoints.
 * Uses the project's existing authenticated fetch helper so token
 * refresh and error handling work exactly like the rest of the app.
 */
import { apiUrl, authenticatedJsonRequest } from '@/config/api'

const BASE = 'api/v1/ai'

async function publicJsonRequest(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData

  if (options.body !== undefined && options.body !== null && !isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(apiUrl(path), {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  if (response.status === 204) return null
  return response.json()
}

/**
 * Send a chat message.
 * @param {string} message
 * @param {string|null} sessionId - pass null to start a new conversation
 * @param {{ context?: string|null, orderId?: string|null }|null} options
 * @returns {Promise<{ session_id: string, message: string, intent: string, sql_generated: string|null }>}
 */
export async function sendChat(message, sessionId = null, options = null) {
  return authenticatedJsonRequest(`${BASE}/chat`, {
    method: 'POST',
    body: JSON.stringify({
      message,
      session_id: sessionId,
      context: options?.context || null,
      order_id: options?.orderId || null,
    }),
  })
}

/**
 * List all chat sessions for the current user.
 * @returns {Promise<{ sessions: Array }>}
 */
export async function fetchSessions() {
  return authenticatedJsonRequest(`${BASE}/sessions`, { method: 'GET' })
}

/**
 * Load the full message history for a session.
 * @param {string} sessionId
 * @returns {Promise<{ session_id: string, messages: Array }>}
 */
export async function fetchConversation(sessionId) {
  return authenticatedJsonRequest(`${BASE}/conversations/${sessionId}`, { method: 'GET' })
}

/**
 * Escalate a conversation to a human agent.
 * @param {string} conversationId
 * @param {string} reason
 */
export async function escalateConversation(conversationId, reason) {
  return authenticatedJsonRequest(`${BASE}/escalate/${conversationId}`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

/**
 * Analyse a room image for a moving estimate (no auth required by the route).
 * @param {File} file
 */
export async function analyseRoomImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return authenticatedJsonRequest(`${BASE}/estimate-image`, {
    method: 'POST',
    body: formData,
  })
}

export async function submitPublicContactForm(payload) {
  return publicJsonRequest(`${BASE}/contact-submissions/public`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchContactSubmissions() {
  return authenticatedJsonRequest(`${BASE}/contact-submissions`, { method: 'GET' })
}

export async function updateContactSubmission(submissionId, payload) {
  return authenticatedJsonRequest(`${BASE}/contact-submissions/${submissionId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function replyContactSubmission(submissionId, message) {
  return authenticatedJsonRequest(`${BASE}/contact-submissions/${submissionId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function deleteContactSubmission(submissionId) {
  return authenticatedJsonRequest(`${BASE}/contact-submissions/${submissionId}`, {
    method: 'DELETE',
  })
}

export async function fetchSupportDashboard() {
  return authenticatedJsonRequest(`${BASE}/support/dashboard`, { method: 'GET' })
}

export async function fetchSupportSettings() {
  return authenticatedJsonRequest(`${BASE}/support/settings`, { method: 'GET' })
}

export async function updateSupportSettings(payload) {
  return authenticatedJsonRequest(`${BASE}/support/settings`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function fetchSupportAnalytics(timeRange = '7D') {
  const query = `?range=${encodeURIComponent(timeRange)}`
  return authenticatedJsonRequest(`${BASE}/support/analytics${query}`, { method: 'GET' })
}

export async function executeSupportAnalyticsInsight(insightId, timeRange = '7D') {
  const query = `?range=${encodeURIComponent(timeRange)}`
  return authenticatedJsonRequest(`${BASE}/support/analytics/insights/${insightId}/execute${query}`, {
    method: 'POST',
  })
}

export async function fetchSupportSessions(search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  return authenticatedJsonRequest(`${BASE}/support/sessions${query}`, { method: 'GET' })
}

export async function fetchSupportSession(sessionId) {
  return authenticatedJsonRequest(`${BASE}/support/sessions/${sessionId}`, { method: 'GET' })
}

export async function takeOverSupportSession(sessionId) {
  return authenticatedJsonRequest(`${BASE}/support/sessions/${sessionId}/take-over`, {
    method: 'POST',
  })
}

export async function replyToSupportSession(sessionId, message) {
  return authenticatedJsonRequest(`${BASE}/support/sessions/${sessionId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function escalateSupportSession(sessionId, reason) {
  return authenticatedJsonRequest(`${BASE}/support/sessions/${sessionId}/escalate`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

// ── Escalation Center ──────────────────────────────────────────────────────

export async function fetchEscalationCenter(statusFilter = '') {
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : ''
  return authenticatedJsonRequest(`${BASE}/escalation-center${query}`, { method: 'GET' })
}

export async function resolveEscalationCenter(escalationId) {
  return authenticatedJsonRequest(`${BASE}/escalation-center/${escalationId}/resolve`, {
    method: 'PUT',
  })
}

// ── Support Tickets ────────────────────────────────────────────────────────

export async function fetchTickets() {
  return authenticatedJsonRequest(`${BASE}/tickets`, { method: 'GET' })
}

export async function fetchRecoveryTicketsCount() {
  return authenticatedJsonRequest(`${BASE}/recovery-tickets/count`, { method: 'GET' })
}

export async function createTicket(payload) {
  return authenticatedJsonRequest(`${BASE}/tickets`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateTicket(ticketId, payload) {
  return authenticatedJsonRequest(`${BASE}/tickets/${ticketId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function replyTicket(ticketId, message) {
  return authenticatedJsonRequest(`${BASE}/tickets/${ticketId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function deleteTicket(ticketId) {
  return authenticatedJsonRequest(`${BASE}/tickets/${ticketId}`, { method: 'DELETE' })
}

// ── AI Support — Reverse Logistics (Damage Reports) ───────────────────────

export async function fetchSupportDamageReports() {
  return authenticatedJsonRequest(`${BASE}/support/damage-reports`, { method: 'GET' })
}

export async function createSupportDamageReport(payload) {
  return authenticatedJsonRequest(`${BASE}/support/damage-reports`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateDamageReportNotes(reportId, supportNotes) {
  return authenticatedJsonRequest(`${BASE}/support/damage-reports/${reportId}/notes`, {
    method: 'PUT',
    body: JSON.stringify({ support_notes: supportNotes }),
  })
}

export async function sendSupportMessage(reportId, text) {
  return authenticatedJsonRequest(`${BASE}/support/damage-reports/${reportId}/message`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

// ── AI Support — Refund Center ────────────────────────────────────────────

export async function fetchSupportRefundCases() {
  return authenticatedJsonRequest(`${BASE}/support/refund-cases`, { method: 'GET' })
}

export async function flagRefundCaseUrgent(caseId, isUrgent, urgentReason = null) {
  return authenticatedJsonRequest(`${BASE}/support/refund-cases/${caseId}/urgent`, {
    method: 'PUT',
    body: JSON.stringify({ is_urgent: isUrgent, urgent_reason: urgentReason }),
  })
}

// ── AI Support — Customer History ─────────────────────────────────────────

export async function fetchCustomerHistory(userId) {
  return authenticatedJsonRequest(`${BASE}/support/customer-history/${userId}`, { method: 'GET' })
}

// ── AI System Settings ─────────────────────────────────────────────────────

export async function fetchAISettings() {
  return authenticatedJsonRequest(`${BASE}/support/settings`, { method: 'GET' })
}

export async function updateAISettings(payload) {
  return authenticatedJsonRequest(`${BASE}/support/settings`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

// ── Knowledge Base CRUD ────────────────────────────────────────────────────

export async function fetchKnowledgeArticles({ activeOnly = true, audience = null } = {}) {
  const params = new URLSearchParams({ active_only: activeOnly })
  if (audience) params.set('audience', audience)
  return authenticatedJsonRequest(`${BASE}/knowledge-articles?${params}`, { method: 'GET' })
}

export async function fetchKnowledgeArticle(articleId) {
  return authenticatedJsonRequest(`${BASE}/knowledge-articles/${articleId}`, { method: 'GET' })
}

export async function createKnowledgeArticle(payload) {
  return authenticatedJsonRequest(`${BASE}/knowledge-articles`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateKnowledgeArticle(articleId, payload) {
  return authenticatedJsonRequest(`${BASE}/knowledge-articles/${articleId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function deleteKnowledgeArticle(articleId) {
  return authenticatedJsonRequest(`${BASE}/knowledge-articles/${articleId}`, {
    method: 'DELETE',
  })
}

export async function likeKnowledgeArticle(articleId) {
  return authenticatedJsonRequest(`${BASE}/knowledge-articles/${articleId}/like`, {
    method: 'POST',
  })
}
