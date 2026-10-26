// The vendor's notification feed, rebuilt from shipments and invoices and synced with the server.
import { API_BASE, getAuthHeaders } from './api'

export function useVendorNotifications({ notifications, overdueInvoices, shipments }) {
    function rebuildNotifications() {
        const autoDebitNotifications = shipments.value
            .filter((shipment) => shipment.autoDebitNote)
            .slice(0, 4)
            .map((shipment) => {
                const message = String(shipment.autoDebitNote || '')
                const lowered = message.toLowerCase()
                const isSkipped = lowered.includes('skipped')
                const isDebt = lowered.includes('negative') || lowered.includes('debt')
                return {
                    id: `autodebit-${shipment.id}`,
                    title: isSkipped ? 'Auto-debit skipped' : (isDebt ? 'Wallet went negative' : 'Auto-debit update'),
                    message: `${shipment.id}: ${message}`,
                    time: shipment.createdAt || shipment.eta,
                    read: false,
                    type: isSkipped ? 'warning' : (isDebt ? 'alert' : 'info'),
                }
            })

        const shipmentNotifications = shipments.value.slice(0, 4).map((shipment, index) => ({
            id: `shipment-${shipment.id}`,
            title: `Shipment ${shipment.status}`,
            message: `${shipment.id} for ${shipment.destination}`,
            time: shipment.eta || shipment.createdAt,
            read: index > 1,
            type: shipment.statusKey === 'cancelled' ? 'alert' : shipment.statusKey === 'delivered' ? 'success' : 'warning',
        }))

        const invoiceNotifications = overdueInvoices.value.slice(0, 2).map((invoice) => ({
            id: `invoice-${invoice.id}`,
            title: 'Invoice Due',
            message: `${invoice.id} is ${invoice.status.toLowerCase()}.`,
            time: invoice.dueDate,
            read: false,
            type: invoice.status === 'Overdue' ? 'alert' : 'warning',
        }))

        notifications.value = [...autoDebitNotifications, ...invoiceNotifications, ...shipmentNotifications]
    }

    async function fetchNotifications() {
        try {
            const res = await fetch(`${API_BASE}/vendor/notifications`, {
                headers: getAuthHeaders(),
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
            console.warn('[vendorStore] fetchNotifications error:', e)
        }
    }

    async function markNotificationRead(id) {
        const notification = notifications.value.find((item) => item.id === id)
        if (notification) notification.read = true
        try {
            await fetch(`${API_BASE}/vendor/notifications/${id}`, {
                method: 'PUT',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ read: true }),
            })
        } catch (e) { /* best-effort */ }
    }

    async function markAllNotificationsRead() {
        notifications.value.forEach((item) => { item.read = true })
        try {
            await fetch(`${API_BASE}/vendor/notifications/mark-all-read`, {
                method: 'POST',
                headers: getAuthHeaders(),
            })
        } catch (e) { /* best-effort */ }
    }

    async function clearNotifications() {
        notifications.value = []
        try {
            await fetch(`${API_BASE}/vendor/notifications`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            })
        } catch (e) { /* best-effort */ }
    }

    return {
        rebuildNotifications,
        fetchNotifications,
        markNotificationRead,
        markAllNotificationsRead,
        clearNotifications,
     }
}
