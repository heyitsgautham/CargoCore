// The customer's notification feed: load, mark read and clear.
import { apiUrl } from '@/config/api'

export function useCustomerNotifications({ notifications }) {
    async function fetchNotifications() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/notifications'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (!res.ok) return
            const data = await res.json()
            notifications.value = (Array.isArray(data) ? data : []).map((item) => ({
                id: item.id,
                title: item.title,
                message: item.message,
                time: item.time,
                createdAt: item.created_at,
                read: item.read,
                type: item.type,
            }))
        } catch (e) {
            console.warn('[individualStore] fetchNotifications error:', e)
        }
    }

    async function markNotificationRead(id) {
        const n = notifications.value.find(n => n.id === id)
        if (n) n.read = true
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl(`api/v1/customer/notifications/${id}`), {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify({ read: true }),
            })
        } catch (e) { /* best-effort */ }
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach(n => { n.read = true })
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl('api/v1/customer/notifications/mark-all-read'), {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
        } catch (e) { /* best-effort */ }
    }

    async function clearNotifications() {
        notifications.value = []
        try {
            const token = localStorage.getItem('auth_token')
            await fetch(apiUrl('api/v1/customer/notifications'), {
                method: 'DELETE',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
        } catch (e) { /* best-effort */ }
    }

    return { fetchNotifications, markNotificationRead, markAllNotificationsRead, clearNotifications }
}
