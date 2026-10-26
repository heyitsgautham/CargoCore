import { apiUrl } from '@/config/api'

const MAX_REPORTS_PER_PAGE = 20
let sent = 0
let lastKey = ''

/**
 * Send one browser error to POST /api/v1/client-errors so it lands in the API's logs.
 * Repeats of the same message back to back are dropped, and a page sends at most 20 reports.
 * Reporting never throws; a failed report is ignored.
 */
export function reportClientError(error, { scope = 'app', level = 'error', context = {} } = {}) {
    const message = String(error?.message || error || 'Unknown error').slice(0, 2000)
    const key = `${scope}:${message}`
    if (key === lastKey || sent >= MAX_REPORTS_PER_PAGE) return false
    lastKey = key
    sent += 1

    const body = {
        level,
        message,
        scope: scope.replace(/[^A-Za-z0-9_.:/-]/g, '-').slice(0, 80),
        stack: error?.stack ? String(error.stack).slice(0, 8000) : null,
        url: typeof window !== 'undefined' ? window.location.href.slice(0, 2000) : null,
        release: import.meta.env.VITE_RELEASE || null,
        context,
    }
    try {
        fetch(apiUrl('api/v1/client-errors'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            keepalive: true,
        }).catch(() => {})
    } catch {
        // reporting must never break the page
    }
    return true
}

/** Report uncaught Vue, window and promise errors from this app. */
export function installErrorReporting(app) {
    const previous = app.config.errorHandler
    app.config.errorHandler = (err, instance, info) => {
        reportClientError(err, { scope: instance?.$options?.name || instance?.$options?.__name || 'vue', context: { info } })
        if (previous) previous(err, instance, info)
        else console.error(err)
    }
    if (typeof window !== 'undefined') {
        window.addEventListener('error', (event) => reportClientError(event.error || event.message, { scope: 'window' }))
        window.addEventListener('unhandledrejection', (event) => reportClientError(event.reason, { scope: 'promise' }))
    }
}

export function resetErrorReporterForTests() {
    sent = 0
    lastKey = ''
}
