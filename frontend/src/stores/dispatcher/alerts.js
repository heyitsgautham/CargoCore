// Crisis alerts: load, raise and resolve.
import { API_BASE, authHeaders } from './api'

export function useDispatchAlerts({ _alerts, _alertsLoaded, ls }) {
    async function fetchAlerts() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _alerts.value = await res.json()
                _alertsLoaded.value = true
            }
        } catch (_) {}
    }

    async function createAlert(payload) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(payload),
            })
            if (res.ok) {
                await fetchAlerts()
                return await res.json()
            }
        } catch (_) {}
        return null
    }

    async function resolveAlert(id) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/alerts/${id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _alerts.value = _alerts.value.filter(a => String(a.id) !== String(id))
            }
        } catch (_) {
            ls.resolveAlert(id).catch(() => {})
        }
    }

    return { fetchAlerts, createAlert, resolveAlert }
}
