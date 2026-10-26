// Company settings, team members and API keys.
import { API_BASE, getAuthHeaders } from './api'

export function useVendorCompany({ companySettings }) {
    async function fetchSettings() {
        const response = await fetch(`${API_BASE}/vendor/settings`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load vendor settings.')
        }

        const data = await response.json()
        companySettings.value = {
            ...companySettings.value,
            companyName: data.settings?.company_name || '',
            taxId: data.settings?.tax_id || '',
            contactPerson: data.settings?.contact_person || data.settings?.company_name || '',
            phone: data.settings?.phone || '',
            email: data.settings?.email || '',
            address: data.settings?.address || '',
            notifications: {
                email: !!data.settings?.notification_prefs?.email,
                sms: !!data.settings?.notification_prefs?.sms,
                push: !!data.settings?.notification_prefs?.push,
                orderUpdates: !!data.settings?.notification_prefs?.orderUpdates,
                invoiceAlerts: !!data.settings?.notification_prefs?.invoiceAlerts,
                promotions: !!data.settings?.notification_prefs?.promotions,
            },
        }
        return data
    }

    async function fetchTeamMembers() {
        const response = await fetch(`${API_BASE}/vendor/team-members`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load team members.')
        }

        // Read the body first: companySettings.value is evaluated before an awaited
        // right-hand side, and fetchSettings may swap the object in the meantime.
        const teamMembers = await response.json()
        companySettings.value.teamMembers = teamMembers
        return companySettings.value.teamMembers
    }

    async function fetchApiKeys() {
        const response = await fetch(`${API_BASE}/vendor/api-keys`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load API keys.')
        }

        const apiKeys = await response.json()
        companySettings.value.apiKeys = apiKeys
        return companySettings.value.apiKeys
    }

    async function updateCompanySettings(updates) {
        const response = await fetch(`${API_BASE}/vendor/settings`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                company_name: updates.companyName,
                tax_id: updates.taxId,
                contact_person: updates.contactPerson,
                phone: updates.phone,
                email: updates.email || companySettings.value.email,
                address: updates.address ?? companySettings.value.address,
                notification_prefs: companySettings.value.notifications,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update company settings.')
        }

        await fetchSettings()
        return true
    }

    async function addTeamMember(member) {
        const response = await fetch(`${API_BASE}/vendor/team-members`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify(member),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to add team member.')
        }

        await fetchTeamMembers()
        return response.json()
    }

    async function removeTeamMember(id) {
        const response = await fetch(`${API_BASE}/vendor/team-members/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to remove team member.')
        }

        await fetchTeamMembers()
    }

    async function generateApiKey(name) {
        const response = await fetch(`${API_BASE}/vendor/api-keys`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ name }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to generate API key.')
        }

        const key = await response.json()
        await fetchApiKeys()
        return key
    }

    async function revokeApiKey(id) {
        const response = await fetch(`${API_BASE}/vendor/api-keys/${id}/revoke`, {
            method: 'POST',
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to revoke API key.')
        }

        await fetchApiKeys()
    }

    return {
        fetchSettings,
        updateCompanySettings,
        fetchTeamMembers,
        addTeamMember,
        removeTeamMember,
        fetchApiKeys,
        generateApiKey,
        revokeApiKey,
     }
}
