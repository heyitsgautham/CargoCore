import { beforeEach, describe, expect, it, vi } from 'vitest'
import apiClient, {
  API_BASE_URL,
  apiUrl,
  authenticatedJsonRequest,
  clearAuthSession,
  consumeAuthError,
  getStoredAccessToken,
  getStoredRefreshToken,
  getStoredUser,
  storeAuthSession,
} from '@/config/api'

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
})

describe('apiUrl', () => {
  it('joins relative paths onto the API base without doubling slashes', () => {
    expect(apiUrl('/api/v1/orders')).toBe(`${API_BASE_URL}/api/v1/orders`)
    expect(apiUrl('api/v1/orders')).toBe(`${API_BASE_URL}/api/v1/orders`)
  })

  it('passes absolute URLs through untouched', () => {
    expect(apiUrl('https://maps.example.com/x')).toBe('https://maps.example.com/x')
  })

  it('rewrites localhost to 127.0.0.1 in the base URL', () => {
    expect(API_BASE_URL).not.toContain('localhost')
  })
})

describe('auth session storage', () => {
  it('stores tokens and the user, and announces the change', () => {
    const listener = vi.fn()
    window.addEventListener('auth:session-changed', listener)
    sessionStorage.setItem('auth_error', 'old error')

    storeAuthSession({ accessToken: 'a1', refreshToken: 'r1', user: { id: 7, role: 'VENDOR' } })

    expect(getStoredAccessToken()).toBe('a1')
    expect(getStoredRefreshToken()).toBe('r1')
    expect(getStoredUser()).toEqual({ id: 7, role: 'VENDOR' })
    expect(sessionStorage.getItem('auth_error')).toBeNull()
    expect(listener).toHaveBeenCalledTimes(1)
    window.removeEventListener('auth:session-changed', listener)
  })

  it('keeps existing tokens when a field is omitted', () => {
    storeAuthSession({ accessToken: 'a1', refreshToken: 'r1' })
    storeAuthSession({ accessToken: 'a2' })

    expect(getStoredAccessToken()).toBe('a2')
    expect(getStoredRefreshToken()).toBe('r1')
  })

  it('clears every auth key', () => {
    storeAuthSession({ accessToken: 'a', refreshToken: 'r', user: { id: 1 } })
    clearAuthSession()

    expect(getStoredAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
    expect(getStoredUser()).toBeNull()
  })

  it('returns null for a corrupt stored user', () => {
    localStorage.setItem('auth_user', '{oops')
    expect(getStoredUser()).toBeNull()
  })

  it('consumeAuthError reads the message once', () => {
    sessionStorage.setItem('auth_error', 'Session expired')
    expect(consumeAuthError()).toBe('Session expired')
    expect(consumeAuthError()).toBe('')
  })
})

describe('authenticatedJsonRequest', () => {
  it('sends the bearer token and a JSON content type for bodies', async () => {
    storeAuthSession({ accessToken: 'tok' })
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    const data = await authenticatedJsonRequest('api/v1/orders', {
      method: 'POST',
      body: JSON.stringify({ a: 1 }),
    })

    expect(data).toEqual({ ok: true })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe(`${API_BASE_URL}/api/v1/orders`)
    expect(init.headers.get('Authorization')).toBe('Bearer tok')
    expect(init.headers.get('Content-Type')).toBe('application/json')
  })

  it('does not force a JSON content type on FormData uploads', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, {}))
    vi.stubGlobal('fetch', fetchMock)

    await authenticatedJsonRequest('api/v1/upload', { method: 'POST', body: new FormData() })

    expect(fetchMock.mock.calls[0][1].headers.has('Content-Type')).toBe(false)
  })

  it('returns null for 204 No Content', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(204, null)))
    await expect(authenticatedJsonRequest('api/v1/x', { method: 'DELETE' })).resolves.toBeNull()
  })

  it('throws the first validation message from a FastAPI 422 response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse(422, { detail: [{ msg: 'field required' }] })),
    )
    await expect(authenticatedJsonRequest('api/v1/x')).rejects.toThrow('field required')
  })

  it('throws the HTTP status when the error body has no detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(500, {})))
    await expect(authenticatedJsonRequest('api/v1/x')).rejects.toThrow('HTTP 500')
  })

  it('refreshes an expired access token once and retries the request', async () => {
    storeAuthSession({ accessToken: 'old', refreshToken: 'refresh-1' })
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'new', refresh_token: 'refresh-2' }))
      .mockResolvedValueOnce(jsonResponse(200, { orders: [] }))
    vi.stubGlobal('fetch', fetchMock)

    const data = await authenticatedJsonRequest('api/v1/orders')

    expect(data).toEqual({ orders: [] })
    expect(fetchMock.mock.calls[1][0]).toBe(`${API_BASE_URL}/api/v1/auth/refresh`)
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ refresh_token: 'refresh-1' })
    expect(fetchMock.mock.calls[2][1].headers.get('Authorization')).toBe('Bearer new')
    expect(getStoredAccessToken()).toBe('new')
    expect(getStoredRefreshToken()).toBe('refresh-2')
  })

  it('clears the session and remembers the error when no refresh token exists', async () => {
    window.history.replaceState({}, '', '/login')
    storeAuthSession({ accessToken: 'old', user: { role: 'DRIVER' } })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(401, {})))

    await expect(authenticatedJsonRequest('api/v1/orders')).rejects.toThrow(
      'Session expired. Please sign in again.',
    )
    expect(getStoredAccessToken()).toBeNull()
    expect(consumeAuthError()).toBe('Session expired. Please sign in again.')
  })
})

describe('apiClient', () => {
  it('wraps responses in { data } and JSON-encodes request bodies', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { id: 3 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiClient.put('api/v1/items/3', { qty: 2 })).resolves.toEqual({ data: { id: 3 } })
    expect(fetchMock.mock.calls[0][1].method).toBe('PUT')
    expect(fetchMock.mock.calls[0][1].body).toBe('{"qty":2}')

    await apiClient.get('api/v1/items')
    await apiClient.post('api/v1/items', { qty: 1 })
    await apiClient.delete('api/v1/items/3')
    expect(fetchMock.mock.calls.map((call) => call[1].method)).toEqual([
      'PUT',
      'GET',
      'POST',
      'DELETE',
    ])
  })
})
