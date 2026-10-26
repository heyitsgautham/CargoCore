// Tracking a service move's driver, messaging its crew, and cancelling or completing it.
import { API_BASE_URL } from '@/config/api'

export function useMoveCrewActions({
    authHeaders,
    completedToday,
    crewChatMove,
    crewMessages,
    crewMsg,
    crewThreadId,
    moveMenu,
    serviceMoves,
    showCrewChat,
    showTrackingModal,
    store,
    trackedDriver,
    trackingLoading,
    trackingMove,
}) {
    async function trackMove(move) {
        // Toggle off if already tracking this move
        if (trackingMove.value?.id === move.id && showTrackingModal.value) {
            showTrackingModal.value = false
            move.tracking = false
            return
        }
        trackingLoading.value = true
        move.tracking = true
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/tracking/orders/${move.orderId}/driver`, {
                headers: authHeaders(),
            })
            trackedDriver.value = res.ok ? await res.json() : null
        } catch (_) {
            trackedDriver.value = null
        } finally {
            trackingLoading.value = false
        }
        trackingMove.value = move
        showTrackingModal.value = true
    }

    function toggleMoveMenu(move) { moveMenu.value = moveMenu.value === move.id ? null : move.id }

    async function contactCrew(move) {
        crewChatMove.value = move
        crewMessages.value = []
        crewThreadId.value = null
        showCrewChat.value = true

        // Find the driver's existing contact/thread from the store
        const driverId = move.crew[0]?.driverId
        const contact = driverId
            ? store.dispatcherContacts.find(c => c.id === String(driverId))
            : store.dispatcherContacts.find(c => c.name === move.crew[0]?.name)

        if (contact?.threadId) {
            crewThreadId.value = String(contact.threadId)
            crewMessages.value = (contact.messages || []).map(m => ({
                id: m.id || Date.now(),
                from: m.from || m.sender || 'driver',
                text: m.text || '',
            }))
        } else if (contact) {
            // No thread yet — create one
            const thread = await store.createChatForContact(contact.name, contact.phone)
            if (thread?.id) crewThreadId.value = String(thread.id)
        }
    }

    async function sendCrewMsg() {
        const text = crewMsg.value.trim()
        if (!text) return
        crewMsg.value = ''

        if (crewThreadId.value) {
            const updated = await store.sendDispatchMessage(crewThreadId.value, text)
            if (updated) {
                crewMessages.value = (updated.messages || []).map(m => ({
                    id: m.id || Date.now(),
                    from: m.from || m.sender || 'driver',
                    text: m.text || '',
                }))
                return
            }
        }
        // Fallback: show locally if no thread
        crewMessages.value.push({ id: Date.now(), from: 'dispatch', text })
    }

    async function cancelMove(move) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/v1/orders/${move.orderId}/cancel`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ reason: 'Cancelled by dispatcher' }),
            })
            if (res.ok) {
                serviceMoves.value = serviceMoves.value.filter(m => m.id !== move.id)
            }
        } catch (err) {
            console.error('Failed to cancel move:', err)
        }
        moveMenu.value = null
    }

    async function completeMove(move) {
        try {
            // Use the transition endpoint (correct backend route)
            const res = await fetch(`${API_BASE_URL}/api/v1/orders/${move.orderId}/transition`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ next_status: 'DELIVERED' }),
            })
            if (res.ok) {
                move.status = 'Completed'
                move.statusClass = 'bg-green-500/20 text-green-400'
                move.progress = 100
                completedToday.value++
                serviceMoves.value = serviceMoves.value.filter(m => m.id !== move.id)
            }
        } catch (err) {
            console.error('Failed to complete move:', err)
        }
        moveMenu.value = null
    }

    return {
        trackMove,
        toggleMoveMenu,
        contactCrew,
        sendCrewMsg,
        cancelMove,
        completeMove,
    }
}
