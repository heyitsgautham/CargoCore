/**
 * HTTP helpers shared by the logistics manager store and its slices.
 */

import { authenticatedJsonRequest, getStoredAccessToken } from '@/config/api'

export function authHeaders(extra = {}) {
    const token = getStoredAccessToken()
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...extra,
    }
}

export async function apiRequest(path, options = {}) {
    return authenticatedJsonRequest(`api/v1${path}`, options)
}
