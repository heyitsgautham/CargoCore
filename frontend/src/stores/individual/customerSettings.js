/**
 * Normalise customer settings from the API into the values the settings screen offers.
 */

export function normalizeLanguageSetting(value) {
    const normalized = String(value || '').trim().toLowerCase()
    const aliases = {
        en: 'en',
        english: 'en',
        hi: 'hi',
        hindi: 'hi',
        ta: 'ta',
        tamil: 'ta',
        te: 'te',
        telugu: 'te',
        bn: 'bn',
        bengali: 'bn',
        mr: 'mr',
        marathi: 'mr',
    }
    return aliases[normalized] || 'en'
}

export function normalizeCurrencySetting(value) {
    const normalized = String(value || '').trim().toUpperCase()
    if (normalized.includes('USD')) return 'USD'
    if (normalized.includes('EUR')) return 'EUR'
    return 'INR'
}

export function normalizePaymentSetting(value) {
    const normalized = String(value || '').trim().toLowerCase()
    if (normalized.includes('partial')) return 'Partial'
    if (normalized.includes('cash') || normalized === 'cod') return 'COD'
    return 'Full Payment'
}

export function normalizeCustomerSettings(settings = {}) {
    return {
        language: normalizeLanguageSetting(settings.language),
        currency: normalizeCurrencySetting(settings.currency),
        default_payment: normalizePaymentSetting(settings.default_payment),
        notification_prefs: {
            push: settings.notification_prefs?.push ?? true,
            sms: settings.notification_prefs?.sms ?? true,
            email: settings.notification_prefs?.email ?? true,
            geofence: settings.notification_prefs?.geofence ?? true,
            promo: settings.notification_prefs?.promo ?? false,
        },
        privacy_prefs: {
            location: settings.privacy_prefs?.location ?? true,
            analytics: settings.privacy_prefs?.analytics ?? true,
            marketing: settings.privacy_prefs?.marketing ?? false,
        },
    }
}

export function syncStoredAuthUser(patch = {}) {
    if (typeof window === 'undefined') return
    const authData = JSON.parse(localStorage.getItem('auth_user') || 'null') || {}
    localStorage.setItem('auth_user', JSON.stringify({
        ...authData,
        ...patch,
    }))
}
