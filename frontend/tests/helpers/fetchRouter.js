import { vi } from 'vitest'

/**
 * Stub global fetch with a small router.
 *
 * routes: [[method, pathPattern, reply]] where pathPattern is a string the URL
 * path must contain or a RegExp it must match, and reply is a value or a
 * function (body, url) returning { status, body } or a plain body.
 * Unmatched requests answer 404. Every call is recorded on router.calls.
 */
export function stubFetch(routes = []) {
  const calls = []
  const fetchMock = vi.fn(async (input, init = {}) => {
    const url = String(input)
    const method = (init.method || 'GET').toUpperCase()
    let body = init.body
    if (typeof body === 'string') {
      try {
        body = JSON.parse(body)
      } catch {
        // leave non-JSON bodies as they are
      }
    }
    calls.push({ method, url, body, headers: init.headers })
    const route = routes.find(
      ([m, pattern]) =>
        m === method && (pattern instanceof RegExp ? pattern.test(url) : url.includes(pattern)),
    )
    if (!route) return respond(404, { detail: 'Not Found' })
    let reply = typeof route[2] === 'function' ? await route[2](body, url) : route[2]
    if (!(reply && typeof reply === 'object' && 'status' in reply && 'body' in reply)) {
      reply = { status: 200, body: reply }
    }
    return respond(reply.status, reply.body)
  })
  vi.stubGlobal('fetch', fetchMock)
  return { calls, fetchMock, last: (method) => calls.filter((c) => c.method === method).at(-1) }
}

function respond(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
    blob: async () => new Blob([JSON.stringify(body)]),
  }
}
