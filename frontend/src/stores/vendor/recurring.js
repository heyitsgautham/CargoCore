// Recurring shipment rules and their cost estimate.
import { API_BASE, getAuthHeaders } from './api'

export function useRecurringRules({ recurringRules }) {
    async function fetchRecurringRules() {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load recurring rules.')
        }

        const data = await response.json()
        recurringRules.value = data.map((rule) => ({
            id: rule.id,
            name: rule.name,
            description: rule.description,
            frequency: rule.frequency,
            route: rule.route,
            details: rule.details,
            nextRun: rule.next_run,
            active: !!rule.active,
        }))
        return recurringRules.value
    }

    async function estimateRecurringCost({ hubId = '', hubName, destinationLat, destinationLon, destinationAddress = '' }) {
        const response = await fetch(`${API_BASE}/vendor/recurring/estimate-cost`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                hub_name: hubName || '',
                hub_id: hubId || null,
                destination_lat: destinationLat,
                destination_lon: destinationLon,
                destination_address: destinationAddress,
            }),
        })
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to estimate recurring cost.')
        }
        return await response.json()
    }

    async function addRecurringRule(rule) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                name: rule.name,
                description: rule.description || '',
                frequency: rule.frequency,
                route: rule.route,
                details: rule.details,
                next_run: rule.nextRun,
                active: rule.active ?? true,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create recurring rule.')
        }

        await fetchRecurringRules()
        return response.json()
    }

    async function updateRecurringRule(id, updates) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                name: updates.name,
                description: updates.description || '',
                frequency: updates.frequency,
                route: updates.route,
                details: updates.details,
                next_run: updates.nextRun,
                active: updates.active ?? true,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update recurring rule.')
        }

        await fetchRecurringRules()
    }

    async function toggleRecurringRule(id) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}/toggle`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to toggle recurring rule.')
        }

        await fetchRecurringRules()
    }

    async function deleteRecurringRule(id) {
        const response = await fetch(`${API_BASE}/vendor/recurring-rules/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to delete recurring rule.')
        }

        await fetchRecurringRules()
    }

    return {
        fetchRecurringRules,
        estimateRecurringCost,
        addRecurringRule,
        updateRecurringRule,
        toggleRecurringRule,
        deleteRecurringRule,
     }
}
