// The dispatcher's drivers: loading them, suspensions and status changes, kept locally and synced to the backend.
import { authenticatedJsonRequest } from '@/config/api'
import { API_BASE, authHeaders } from './api'

export function useDispatchDrivers({ _drivers, _suspendedIds, driversLoading, ls }) {
    function _persistSuspended() {
        localStorage.setItem('cc_dispatcher_suspended', JSON.stringify([..._suspendedIds.value]))
    }

    function _setLocalSuspended(driverId, suspended) {
        const id = String(driverId)
        if (suspended) {
            _suspendedIds.value.add(id)
        } else {
            _suspendedIds.value.delete(id)
        }
        _suspendedIds.value = new Set(_suspendedIds.value)
        _persistSuspended()
    }

    function _updateLocalDriverStatus(driverId, status) {
        const id = String(driverId)
        const update = (driver) => String(driver.id) === id ? { ...driver, status } : driver
        _drivers.value = _drivers.value.map(update)

        if (Array.isArray(ls.drivers)) {
            const idx = ls.drivers.findIndex((driver) => String(driver.id) === id)
            if (idx !== -1) ls.drivers.splice(idx, 1, { ...ls.drivers[idx], status })
        }
    }

    async function _persistDriverStatus(driverId, status) {
        const res = await fetch(`${API_BASE}/api/v1/logistics/drivers/${driverId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ status }),
        })
        if (!res.ok) return false

        const updated = normalizeDriver(await res.json())
        const idx = _drivers.value.findIndex((driver) => String(driver.id) === String(driverId))
        if (idx === -1) {
            _drivers.value.unshift(updated)
        } else {
            _drivers.value[idx] = { ..._drivers.value[idx], ...updated }
        }
        return true
    }

    async function _syncLocalSuspensionsToBackend() {
        const pendingIds = [..._suspendedIds.value]
            .filter((id) => _drivers.value.some((driver) => String(driver.id) === String(id)))
            .filter((id) => !_drivers.value.some((driver) =>
                String(driver.id) === String(id) && String(driver.status || '').toLowerCase() === 'suspended'
            ))
        if (!pendingIds.length) return

        const syncedIds = []
        await Promise.all(pendingIds.map(async (id) => {
            try {
                if (await _persistDriverStatus(id, 'Suspended')) syncedIds.push(id)
            } catch (_) {}
        }))
        syncedIds.forEach((id) => _setLocalSuspended(id, false))
    }

    async function toggleDriverSuspend(driverId) {
        const id = String(driverId)
        const wasSuspended = isDriverSuspended(id)
        const nextSuspended = !wasSuspended
        const nextStatus = nextSuspended ? 'Suspended' : 'Active'

        _setLocalSuspended(id, nextSuspended)
        _updateLocalDriverStatus(id, nextStatus)

        try {
            const saved = await _persistDriverStatus(id, nextStatus)
            if (saved) {
                _setLocalSuspended(id, false)
                await fetchDrivers()
            } else {
                _setLocalSuspended(id, wasSuspended)
                _updateLocalDriverStatus(id, wasSuspended ? 'Suspended' : 'Active')
            }
        } catch (_) {
            _setLocalSuspended(id, wasSuspended)
            _updateLocalDriverStatus(id, wasSuspended ? 'Suspended' : 'Active')
        }
    }

    function isDriverSuspended(driverId) {
        const id = String(driverId)
        return _suspendedIds.value.has(id)
            || _drivers.value.some((driver) => String(driver.id) === id && String(driver.status || '').toLowerCase() === 'suspended')
            || ls.filteredDrivers.some((driver) => String(driver.id) === id && String(driver.status || '').toLowerCase() === 'suspended')
    }

    function normalizeDriver(d) {
        return {
            id: String(d.id || ''),
            hubId: String(d.hub_id || ''),
            name: d.name || '',
            status: d.status || 'Active',
            location: d.location || d.current_location || '',
            vehicle: d.vehicle || '',
            efficiency: d.efficiency ?? d.efficiency_score ?? 0,
            rating: d.rating ?? 0,
            safetyIncidents: d.safety_incidents ?? d.safetyIncidents ?? 0,
            fuelEfficiencyScore: d.fuel_efficiency_score ?? d.fuelEfficiencyScore ?? 0,
            avgSpeed: Number(d.avg_speed ?? d.avgSpeed ?? 0) || 0,
            phone: d.phone || '',
            currentJob: d.current_job ?? d.currentJob ?? '',
            avatarColor: d.avatar_color ?? d.avatarColor ?? 'bg-gray-700',
            chatHistory: d.chat_history ?? d.chatHistory ?? [],
        }
    }

    async function fetchDrivers() {
        driversLoading.value = true
        try {
            const data = await authenticatedJsonRequest('api/v1/logistics/drivers', {
                headers: { ...authHeaders() },
            })
            const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
            _drivers.value = items.map(normalizeDriver)
            await _syncLocalSuspensionsToBackend()
        } catch (_) {
        } finally {
            driversLoading.value = false
        }
    }

    return {
        fetchDrivers,
        toggleDriverSuspend,
        isDriverSuspended,
    }
}
