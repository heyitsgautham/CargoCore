// The customer's profile and settings, kept in step with the stored auth user.
import { apiUrl } from '@/config/api'
import { normalizeCustomerSettings, syncStoredAuthUser } from './customerSettings'

export function useCustomerAccount({
    profileError,
    profileLoading,
    settingsError,
    settingsLoading,
    user,
}) {
    function applyCustomerSettings(settings = {}) {
        const normalized = normalizeCustomerSettings(settings)
        user.value = {
            ...user.value,
            language: normalized.language,
            currency: normalized.currency,
            paymentDefault: normalized.default_payment,
            notificationsEnabled: !!normalized.notification_prefs.push,
            smsAlerts: !!normalized.notification_prefs.sms,
            notificationPrefs: normalized.notification_prefs,
            privacyPrefs: normalized.privacy_prefs,
        }
        syncStoredAuthUser({
            preferred_language: normalized.language,
            preferred_currency: normalized.currency,
            default_payment_method: normalized.default_payment,
            notifications_push: normalized.notification_prefs.push,
            notifications_sms: normalized.notification_prefs.sms,
            notifications_email: normalized.notification_prefs.email,
            notifications_geofence: normalized.notification_prefs.geofence,
            notifications_promo: normalized.notification_prefs.promo,
            privacy_location: normalized.privacy_prefs.location,
            privacy_analytics: normalized.privacy_prefs.analytics,
            privacy_marketing: normalized.privacy_prefs.marketing,
        })
        return normalized
    }

    async function fetchProfile() {
        profileLoading.value = true
        profileError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/profile'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                profileError.value = errData.detail || 'Failed to load profile.'
                return { success: false, message: profileError.value }
            }

            const data = await response.json()
            user.value = {
                ...user.value,
                name: data.profile?.name || user.value.name,
                email: data.profile?.email || user.value.email,
                phone: data.profile?.phone || user.value.phone,
                joiningDate: data.profile?.created_at || user.value.joiningDate,
                altPhone: data.alt_phone || '',
                address: data.address || '',
                language: data.language || user.value.language,
                paymentDefault: data.default_payment || user.value.paymentDefault,
                notificationsEnabled: !!data.notification_prefs?.push,
                smsAlerts: !!data.notification_prefs?.sms,
            }
            return { success: true, data: user.value }
        } catch (error) {
            profileError.value = 'Error connecting to the server.'
            return { success: false, message: profileError.value }
        } finally {
            profileLoading.value = false
        }
    }

    async function saveProfileRemote(updates) {
        profileLoading.value = true
        profileError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/auth/me'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({
                    name: updates.name,
                    phone: updates.phone,
                    date_of_birth: updates.dob,
                    address: updates.address,
                }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                profileError.value = errData.detail || 'Failed to update profile.'
                return { success: false, message: profileError.value }
            }

            const data = await response.json()
            user.value = {
                ...user.value,
                name: data.name || user.value.name,
                email: data.email || user.value.email,
                phone: data.phone || user.value.phone,
                dob: updates.dob ?? user.value.dob,
                address: updates.address ?? user.value.address,
            }

            if (typeof window !== 'undefined') {
                const authData = JSON.parse(localStorage.getItem('auth_user') || 'null') || {}
                localStorage.setItem('auth_user', JSON.stringify({
                    ...authData,
                    name: user.value.name,
                    email: user.value.email,
                    phone: user.value.phone,
                    role: authData.role || 'INDIVIDUAL',
                }))
            }

            return { success: true, data: user.value }
        } catch (error) {
            profileError.value = 'Error connecting to the server.'
            return { success: false, message: profileError.value }
        } finally {
            profileLoading.value = false
        }
    }

    async function fetchSettings() {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/settings'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to load settings.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json()
            const normalizedSettings = applyCustomerSettings(data.settings)
            return { success: true, data: normalizedSettings }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    async function saveSettingsRemote(settings) {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/settings'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(settings),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to save settings.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json()
            const normalizedSettings = applyCustomerSettings(data.settings)
            return { success: true, data: normalizedSettings }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    async function deleteAccountRemote() {
        settingsLoading.value = true
        settingsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/account'), {
                method: 'DELETE',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                settingsError.value = errData.detail || 'Failed to delete account.'
                return { success: false, message: settingsError.value }
            }

            const data = await response.json().catch(() => ({}))
            return { success: true, message: data.message || 'Account deleted successfully.' }
        } catch (error) {
            settingsError.value = 'Error connecting to the server.'
            return { success: false, message: settingsError.value }
        } finally {
            settingsLoading.value = false
        }
    }

    return {
        fetchProfile,
        saveProfileRemote,
        fetchSettings,
        saveSettingsRemote,
        deleteAccountRemote,
     }
}
