/**
 * The logistics manager's notifications and broadcasts to staff and drivers.
 */

import { apiRequest, authHeaders } from './api'
import { asArray, asStringId } from './mappers'

export function useLogisticNotifications({ notifications }) {
    async function markNotificationRead(id) {
        await apiRequest(`/logistics/notifications/${id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ read: true }),
        })
        const item = notifications.value.find((entry) => entry.id === id)
        if (item) item.read = true
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach((item) => { item.read = true })
        await apiRequest('/logistics/notifications/mark-all-read', { method: 'POST', headers: authHeaders() }).catch(() => {})
    }

    async function clearNotifications() {
        await apiRequest('/logistics/notifications', { method: 'DELETE', headers: authHeaders() })
        notifications.value = []
    }

    async function fetchNotifications() {
        const data = await apiRequest('/logistics/notifications', { headers: authHeaders() })
        notifications.value = asArray(data).map((item) => ({
            id: asStringId(item.id),
            title: item.title,
            message: item.message,
            time: item.time,
            createdAt: item.created_at,
            read: item.read,
            type: item.type,
        }))
    }

    async function sendBroadcast(payload) {
        return await apiRequest('/logistics/notifications/broadcast', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload),
        })
    }

    return { fetchNotifications, markNotificationRead, markAllNotificationsRead, clearNotifications, sendBroadcast }
}
