import { beforeEach, describe, expect, it, vi } from 'vitest'
import { API_BASE_URL } from '@/config/api'
import {
  analyseRoomImage,
  fetchEscalationCenter,
  fetchKnowledgeArticles,
  fetchSupportAnalytics,
  fetchSupportSessions,
  flagRefundCaseUrgent,
  sendChat,
  submitPublicContactForm,
} from '@/utils/aiApi'

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

let fetchMock

beforeEach(() => {
  localStorage.clear()
  fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }))
  vi.stubGlobal('fetch', fetchMock)
})

const lastCall = () => fetchMock.mock.calls.at(-1)

describe('aiApi request shapes', () => {
  it('sendChat posts the message with null session, context and order by default', async () => {
    await sendChat('Where is my order?')

    const [url, init] = lastCall()
    expect(url).toBe(`${API_BASE_URL}/api/v1/ai/chat`)
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({
      message: 'Where is my order?',
      session_id: null,
      context: null,
      order_id: null,
    })
  })

  it('sendChat forwards the session, context and order id', async () => {
    await sendChat('hi', 'sess-1', { context: 'support', orderId: 'ord-9' })
    expect(JSON.parse(lastCall()[1].body)).toMatchObject({
      session_id: 'sess-1',
      context: 'support',
      order_id: 'ord-9',
    })
  })

  it('analyseRoomImage uploads the file as multipart form data', async () => {
    const file = new File(['img'], 'room.jpg', { type: 'image/jpeg' })
    await analyseRoomImage(file)

    const body = lastCall()[1].body
    expect(body).toBeInstanceOf(FormData)
    expect(body.get('file').name).toBe('room.jpg')
  })

  it('encodes optional query parameters only when given', async () => {
    await fetchEscalationCenter()
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/escalation-center`)

    await fetchEscalationCenter('OPEN')
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/escalation-center?status=OPEN`)

    await fetchSupportSessions('a&b')
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/support/sessions?search=a%26b`)

    await fetchSupportAnalytics()
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/support/analytics?range=7D`)
  })

  it('builds knowledge-article filters from options', async () => {
    await fetchKnowledgeArticles()
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/knowledge-articles?active_only=true`)

    await fetchKnowledgeArticles({ activeOnly: false, audience: 'DRIVER' })
    expect(lastCall()[0]).toBe(
      `${API_BASE_URL}/api/v1/ai/knowledge-articles?active_only=false&audience=DRIVER`,
    )
  })

  it('flagRefundCaseUrgent sends the urgency flag and reason', async () => {
    await flagRefundCaseUrgent('case-1', true, 'Customer threatened chargeback')
    expect(lastCall()[0]).toBe(`${API_BASE_URL}/api/v1/ai/support/refund-cases/case-1/urgent`)
    expect(JSON.parse(lastCall()[1].body)).toEqual({
      is_urgent: true,
      urgent_reason: 'Customer threatened chargeback',
    })
  })
})

describe('submitPublicContactForm', () => {
  it('posts without an Authorization header', async () => {
    localStorage.setItem('auth_token', 'should-not-be-sent')
    await submitPublicContactForm({ name: 'A', message: 'Hello' })

    const [url, init] = lastCall()
    expect(url).toBe(`${API_BASE_URL}/api/v1/ai/contact-submissions/public`)
    expect(init.headers.get('Authorization')).toBeNull()
    expect(init.headers.get('Content-Type')).toBe('application/json')
  })

  it('surfaces the backend detail message on failure', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(429, { detail: 'Too many submissions' }))
    await expect(submitPublicContactForm({})).rejects.toThrow('Too many submissions')
  })

  it('falls back to the HTTP status when the body is not JSON', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('not json')
      },
    })
    await expect(submitPublicContactForm({})).rejects.toThrow('HTTP 502')
  })
})
