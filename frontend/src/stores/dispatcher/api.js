// Base URL and auth headers for the dispatcher store's API calls.
import { API_BASE_URL, getStoredAccessToken } from '@/config/api'

export const API_BASE = API_BASE_URL

export function authHeaders() {
    const token = getStoredAccessToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
}
