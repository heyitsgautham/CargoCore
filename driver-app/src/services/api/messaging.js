// Dispatch and manager chat, driver notifications and crisis alerts.
import { extractErrorMessage, fetchWithAuth } from './client.js'

// ── Dispatch Chat ──────────────────────────────────────────────────────────────

export async function getDispatchThread() {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/dispatch-thread', {
        headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`Failed to load dispatch thread (${res.status})`)
    return await res.json()
}

export async function sendDispatchMessage(text) {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/dispatch-thread/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: `Server error ${res.status}` }))
        throw new Error(extractErrorMessage(error, `Failed to send (${res.status})`))
    }
    return await res.json()
}

export async function getManagerThread() {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/manager-thread', {
        headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`Failed to load manager thread (${res.status})`)
    return await res.json()
}

export async function sendManagerMessage(text) {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/manager-thread/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: `Server error ${res.status}` }))
        throw new Error(extractErrorMessage(error, `Failed to send (${res.status})`))
    }
    return await res.json()
}

// ── Driver Notifications ───────────────────────────────────────────────────────

export async function getDriverNotifications() {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/notifications', {
        headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) return []
    return await res.json()
}

// ── Crisis Alert ───────────────────────────────────────────────────────────────

export async function sendCrisisAlert({ type, latitude, longitude, description }) {
    const res = await fetchWithAuth('/api/v1/logistics/drivers/me/crisis-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type,
            latitude,
            longitude,
            description
        })
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to send crisis alert' }))
        throw new Error(extractErrorMessage(error, 'Failed to send crisis alert'))
    }
    return await res.json()
}
