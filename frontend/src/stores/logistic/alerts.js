/**
 * Network alerts: load, raise and resolve.
 */

import { apiRequest, authHeaders } from './api'

export function useLogisticAlerts({ alerts, refresh, closeModal }) {
    async function fetchAlerts() {
        try {
            const data = await apiRequest('/logistics/alerts', { headers: authHeaders() })
            if (Array.isArray(data)) {
                alerts.value = data.map(alert => ({
                    id: String(alert.id),
                    type: alert.type,
                    title: alert.title,
                    description: alert.description,
                    severity: alert.severity,
                    icon: alert.icon || 'warning',
                    timestamp: alert.timestamp,
                    location: alert.location,
                    recommendation: alert.recommendation,
                    ...(alert.impact || {}),
                }))
            }
        } catch (_) {}
    }

    async function addAlert(alert) {
        await apiRequest('/logistics/alerts', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(alert),
        })
        await refresh()
    }

    async function resolveAlert(id) {
        await apiRequest(`/logistics/alerts/${id}/resolve`, {
            method: 'POST',
            headers: authHeaders(),
        })
        alerts.value = alerts.value.filter((item) => item.id !== id)
        closeModal()
    }

    return { fetchAlerts, addAlert, resolveAlert }
}
