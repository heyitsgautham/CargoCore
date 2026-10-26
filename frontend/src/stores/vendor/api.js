// Base URL and auth headers for the vendor store's API calls.
import { API_BASE_URL } from '@/config/api'

export const API_BASE = `${API_BASE_URL}/api/v1`
const VENDOR_WALLET_TOPUP_OFFSET_KEY = 'vendor_wallet_topup_offset'

export function clearLegacyWalletTopupOffset() {
    if (typeof window === 'undefined') return
    localStorage.removeItem(VENDOR_WALLET_TOPUP_OFFSET_KEY)
}

export function getAuthHeaders(json = false) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    return {
        ...(json ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
}
