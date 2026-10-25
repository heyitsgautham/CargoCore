/**
 * Delivery zones around each hub.
 */

import { apiRequest, authHeaders } from './api'

export function useLogisticZones({ hubs, refresh }) {
    async function createZone(zoneData) {
        // Ensure we have a valid warehouse_id (required, cannot be null)
        const warehouseId = zoneData.hubId && zoneData.hubId !== 'all'
            ? zoneData.hubId
            : (hubs.value[0]?.id || null)

        if (!warehouseId) {
            throw new Error('A warehouse must be selected to create a zone')
        }

        const created = await apiRequest('/logistics/zones', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                warehouse_id: warehouseId,
                name: zoneData.name,
                zone_type: zoneData.type,
                radius_km: parseFloat(zoneData.radius) || 1.0,
                status: zoneData.status || 'Active',
                color_token: zoneData.color || 'blue',
                lat: zoneData.lat ?? null,
                lng: zoneData.lng ?? null,
            }),
        })
        await refresh()
        return created
    }

    async function updateZone(zoneId, zoneData) {
        await apiRequest(`/logistics/zones/${zoneId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: zoneData.name,
                zone_type: zoneData.type,
                radius_km: parseFloat(zoneData.radius) || 1.0,
                status: zoneData.status || 'Active',
                color_token: zoneData.color || 'blue',
                lat: zoneData.lat ?? null,
                lng: zoneData.lng ?? null,
            }),
        })
        await refresh()
    }

    async function deleteZone(zoneId) {
        await apiRequest(`/logistics/zones/${zoneId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        await refresh()
    }

    return { createZone, updateZone, deleteZone }
}
