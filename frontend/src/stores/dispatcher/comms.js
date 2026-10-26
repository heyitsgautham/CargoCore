// Vehicles, zones, contacts and chat threads the dispatcher works with.
import { authenticatedJsonRequest } from '@/config/api'
import { API_BASE, authHeaders } from './api'

export function useDispatchComms({
    _chats,
    _contacts,
    _vehicles,
    _zones,
    chatsLoading,
    vehiclesLoading,
    zonesLoaded,
}) {
    function normalizeZone(z) {
        return {
            id: String(z.id || ''),
            hubId: z.hub_id || z.hubId ? String(z.hub_id || z.hubId) : null,
            name: z.name || '',
            type: z.type || z.zone_type || '',
            radius: z.radius ?? z.radius_km ?? null,
            status: z.status || 'Active',
            color: z.color || z.color_token || '',
            lat: z.lat ?? null,
            lng: z.lng ?? null,
        }
    }

    async function fetchChats() {
        chatsLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/chats`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _chats.value = await res.json()
            }
        } catch (_) {
        } finally {
            chatsLoading.value = false
        }
    }

    async function fetchZones() {
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/zones', {
                headers: authHeaders(),
            })
            _zones.value = (Array.isArray(data) ? data : []).map(normalizeZone)
            zonesLoaded.value = true
        } catch (_) {
        }
    }

    async function fetchVehicles() {
        vehiclesLoading.value = true
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/vehicles', {
                headers: { ...authHeaders() },
            })
            _vehicles.value = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
        } catch (_) {
        } finally {
            vehiclesLoading.value = false
        }
    }

    async function fetchContacts() {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/dispatch-contacts`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                _contacts.value = await res.json()
            }
        } catch (_) {}
    }

    async function sendDispatchMessage(threadId, text) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/chats/${threadId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ text, sender: 'Dispatcher' }),
        })
        if (!res.ok) return null
        const updated = await res.json()
        // Sync into _chats
        const idx = _chats.value.findIndex((c) => String(c.id) === String(threadId))
        if (idx !== -1) _chats.value[idx] = updated
        else _chats.value.unshift(updated)
        return updated
    }

    async function createChatForContact(name, phone = null) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/chats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ name, phone }),
        })
        if (!res.ok) return null
        const thread = await res.json()
        _chats.value.unshift(thread)
        return thread
    }

    return {
        fetchChats,
        fetchZones,
        fetchVehicles,
        fetchContacts,
        sendDispatchMessage,
        createChatForContact,
    }
}
