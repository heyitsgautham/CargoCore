/**
 * Hub lifecycle: add, edit, archive, restore and delete warehouses.
 */

import { apiRequest, authHeaders } from './api'

export function useLogisticHubs({ activeWarehouse, refresh }) {
    async function addHub(hubData) {
        await apiRequest('/warehouses', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: hubData.name,
                address: hubData.location,
                capacity_limit: hubData.capacity || 1000,
                hub_status: hubData.status || null,
            }),
        })
        await refresh()
    }

    async function updateHub(hubData) {
        await apiRequest(`/warehouses/${hubData.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: hubData.name,
                address: hubData.location,
                capacity_limit: hubData.capacity || 1000,
                is_active: !['Inactive', 'Archived'].includes(hubData.status),
                hub_status: hubData.status || null,
            }),
        })
        await refresh()
    }

    async function archiveHub(hubId) {
        await apiRequest(`/warehouses/${hubId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                is_active: false,
                hub_status: 'Archived',
            }),
        })
        if (activeWarehouse.value === String(hubId)) activeWarehouse.value = 'all'
        await refresh()
    }

    async function restoreHub(hubId) {
        await apiRequest(`/warehouses/${hubId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                is_active: true,
                hub_status: 'Active',
            }),
        })
        await refresh()
    }

    async function deleteHub(hubId) {
        await apiRequest(`/warehouses/${hubId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        if (activeWarehouse.value === String(hubId)) activeWarehouse.value = 'all'
        await refresh()
    }

    return { addHub, updateHub, archiveHub, restoreHub, deleteHub }
}
