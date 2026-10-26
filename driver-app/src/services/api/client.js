// HTTP client for the driver app: API base URL, stored tokens, refresh on 401 and network error messages.
import { Capacitor } from '@capacitor/core'

function trimTrailingSlash(url) {
    return url.replace(/\/+$/, '')
}

function resolveApiBase() {
    const configured = trimTrailingSlash(
        import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    )

    if (!Capacitor.isNativePlatform()) {
        return configured
    }

    const androidOverride = import.meta.env.VITE_API_BASE_URL_ANDROID
    if (androidOverride) {
        return trimTrailingSlash(androidOverride)
    }

    try {
        const parsed = new URL(configured)
        if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            parsed.hostname = '10.0.2.2'
            return trimTrailingSlash(parsed.toString())
        }
    } catch {
        // Keep the configured value if parsing fails.
    }

    return configured
}

const API_BASE = resolveApiBase()
const ACCESS_TOKEN_STORAGE_KEY = 'cargo-core:driver-access-token'
const SESSION_EXPIRY_KEY = 'cargo-core:driver-session-expiry'
const SESSION_DURATION_MS = 12 * 60 * 60 * 1000 // 12 hours — full shift

// FastAPI validation errors return detail as an array of {loc, msg, type} objects.
// This helper always returns a plain string regardless of the shape of the error body.
export function extractErrorMessage(error, fallback = 'Request failed') {
    if (!error) return fallback
    const detail = error.detail ?? error.message ?? null
    if (!detail) return fallback
    if (Array.isArray(detail)) {
        return detail.map((e) => e.msg || JSON.stringify(e)).join('; ') || fallback
    }
    return String(detail) || fallback
}

function isProbablyNetworkError(error) {
    const message = String(error?.message || error || '')
    return /failed to fetch|networkerror|load failed/i.test(message)
}

function buildNetworkErrorMessage() {
    const baseMessage = `Unable to reach backend at ${API_BASE}.`

    if (Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android') {
        return `${baseMessage} On a real Android phone, run "adb reverse tcp:8000 tcp:8000" or set VITE_API_BASE_URL_ANDROID to "http://<your-computer-ip>:8000" and start the backend with "--host 0.0.0.0".`
    }

    return `${baseMessage} Check that the backend is running and the API URL is correct.`
}

export async function fetchWithNetworkHelp(path, options, timeoutMs = 10000) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
        return await fetch(`${API_BASE}${path}`, { ...options, signal: controller.signal })
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new Error(`Request timed out after ${timeoutMs / 1000}s. Check your connection.`)
        }
        if (isProbablyNetworkError(error)) {
            throw new Error(buildNetworkErrorMessage())
        }
        throw error
    } finally {
        clearTimeout(timer)
    }
}

function readStoredToken() {
    try {
        const expiry = parseInt(window.localStorage.getItem(SESSION_EXPIRY_KEY) || '0', 10)
        if (expiry && Date.now() > expiry) {
            window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
            window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
            window.localStorage.removeItem(SESSION_EXPIRY_KEY)
            return null
        }
        return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
    } catch {
        return null
    }
}

function writeStoredToken(token) {
    try {
        window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token)
        window.localStorage.setItem(SESSION_EXPIRY_KEY, String(Date.now() + SESSION_DURATION_MS))
    } catch {
        // Ignore storage failures on constrained devices.
    }
}

function removeStoredToken() {
    try {
        window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
        window.localStorage.removeItem(SESSION_EXPIRY_KEY)
    } catch {
        // Ignore storage failures on constrained devices.
    }
}

const REFRESH_TOKEN_STORAGE_KEY = 'cargo-core:driver-refresh-token'

function readStoredRefreshToken() {
    try { return window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY) } catch { return null }
}
function writeStoredRefreshToken(token) {
    try { window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token) } catch {}
}
function removeStoredRefreshToken() {
    try { window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY) } catch {}
}

// Store token in memory, but hydrate from local storage so native activity restarts
// do not force a relogin.
let accessToken = readStoredToken()
let refreshToken = readStoredRefreshToken()

export function setAccessToken(token) {
    accessToken = token
    if (token) { writeStoredToken(token) } else { removeStoredToken() }
}

export function setRefreshToken(token) {
    refreshToken = token
    if (token) { writeStoredRefreshToken(token) } else { removeStoredRefreshToken() }
}

export function getAccessToken() { return accessToken }

export function clearAccessToken() {
    accessToken = null
    refreshToken = null
    removeStoredToken()
    removeStoredRefreshToken()
}

export function authHeaders() {
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
}

// Auto-refresh access token when a 401 is received
let _isRefreshing = false
async function tryRefreshToken() {
    if (!refreshToken || _isRefreshing) return false
    _isRefreshing = true
    try {
        const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (!res.ok) return false
        const data = await res.json()
        setAccessToken(data.access_token)
        if (data.refresh_token) setRefreshToken(data.refresh_token)
        return true
    } catch {
        return false
    } finally {
        _isRefreshing = false
    }
}

export async function fetchWithAuth(path, options, timeoutMs = 10000) {
    let res = await fetchWithNetworkHelp(path, { ...options, ...{ headers: { ...options?.headers, ...authHeaders() } } }, timeoutMs)
    if (res.status === 401) {
        const refreshed = await tryRefreshToken()
        if (refreshed) {
            res = await fetchWithNetworkHelp(path, { ...options, ...{ headers: { ...options?.headers, ...authHeaders() } } }, timeoutMs)
        }
    }
    return res
}
