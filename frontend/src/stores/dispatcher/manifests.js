// Driver manifests: load, save and push to the driver app.
import { API_BASE, authHeaders } from './api'

export function useDispatchManifests({ manifests, manifestsLoading }) {
    function _mapManifest(m) {
        const statusClass =
            m.status === 'Dispatched'
                ? 'bg-green-500/10 text-green-500 border-green-500/20'
                : m.status === 'Draft'
                ? 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
        return {
            id: m.route_id,
            backendId: String(m.id),
            driver: m.driver_name,
            vehicle: m.vehicle_code || 'Auto-assigned',
            hub: m.hub_name || '—',
            orders: m.orders_count,
            weight: m.total_weight,
            totalDistance: m.total_distance,
            stopCount: m.stop_count,
            totalVolume: m.total_volume,
            estDuration: m.est_duration || '—',
            status: m.status,
            statusClass,
            fragileCount: m.fragile_count,
            perishableCount: 0,
            codCount: m.cod_count,
            crew: (m.crew_list || []).map(c => ({ name: c.name, role: c.role })),
            stops: [],
            pushed: m.pushed,
            printed: false,
        }
    }

    async function fetchManifests() {
        manifestsLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const data = await res.json()
                manifests.value = data.map(_mapManifest)
            }
        } catch (_) {
        } finally {
            manifestsLoading.value = false
        }
    }

    async function saveManifest(payload) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(payload),
            })
            if (res.ok) {
                const created = await res.json()
                manifests.value.unshift(_mapManifest(created))
                return _mapManifest(created)
            }
        } catch (_) {}
        return null
    }

    async function pushManifestToDriver(backendId) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/logistics/manifests/${backendId}/push`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const updated = await res.json()
                const idx = manifests.value.findIndex(m => m.backendId === backendId)
                if (idx !== -1) manifests.value[idx] = _mapManifest(updated)
                return true
            }
        } catch (_) {}
        return false
    }

    return { fetchManifests, saveManifest, pushManifestToDriver }
}
