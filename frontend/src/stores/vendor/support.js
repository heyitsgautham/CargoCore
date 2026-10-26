// Support tickets: load, open, reply and resolve.
import { API_BASE, getAuthHeaders } from './api'

export function useVendorSupport({ tickets }) {
    async function fetchTickets() {
        const response = await fetch(`${API_BASE}/vendor/support-tickets`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load support tickets.')
        }

        const data = await response.json()
        tickets.value = data.map((ticket) => ({
            id: ticket.id,
            backendId: ticket.backend_id || ticket.id.replace(/^TK-/, '').toLowerCase(),
            subject: ticket.subject,
            description: ticket.description,
            orderId: ticket.order_id,
            created: ticket.created,
            priority: ticket.priority,
            status: ticket.status,
            replies: (ticket.replies || []).map((reply) => ({
                from: reply.from_name,
                message: reply.message,
                time: reply.time,
            })),
        }))
        return tickets.value
    }

    async function addTicket(ticket) {
        const response = await fetch(`${API_BASE}/vendor/support-tickets`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                subject: ticket.subject,
                description: ticket.description || ticket.message,
                priority: ticket.priority || 'Medium',
                shipment_id: ticket.shipmentId || ticket.orderId || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create support ticket.')
        }

        await fetchTickets()
        return response.json()
    }

    async function replyTicket(ticketId, message) {
        const ticket = tickets.value.find((item) => item.id === ticketId || item.backendId === ticketId)
        const backendId = ticket?.backendId || ticketId
        const response = await fetch(`${API_BASE}/vendor/support-tickets/${backendId}/reply`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ message }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to reply to ticket.')
        }

        await fetchTickets()
    }

    async function resolveTicket(id) {
        const ticket = tickets.value.find((item) => item.id === id || item.backendId === id)
        const backendId = ticket?.backendId || id
        const response = await fetch(`${API_BASE}/vendor/support-tickets/${backendId}/resolve`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to resolve ticket.')
        }

        await fetchTickets()
    }

    return { fetchTickets, addTicket, replyTicket, resolveTicket }
}
