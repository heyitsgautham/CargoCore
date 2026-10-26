// Location pings, shift start and end, vehicle return, fuel receipts, audit log and cashout.
import { authHeaders, extractErrorMessage, fetchWithNetworkHelp } from './client.js'

// ── Location Tracking ──────────────────────────────────────────────────────

export async function updateDriverLocation(latitude, longitude) {
    const body = {
        latitude,
        longitude,
        timestamp: new Date().toISOString()
    }

    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(body)
    })

    // Location updates are fire-and-forget, don't throw errors
    return res.ok
}

// ── Shift Management ───────────────────────────────────────────────────────

export async function startShift() {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/shift/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })

    if (!res.ok) throw new Error('Failed to start shift')
    return await res.json()
}

export async function endShift() {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/shift/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })

    if (!res.ok) throw new Error('Failed to end shift')
    return await res.json()
}

export async function returnVehicle({ odometerKm = null, fuelLevelPct = null, notes = null, conditionPhoto = null } = {}) {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/return-vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
            odometer_km: odometerKm,
            fuel_level_pct: fuelLevelPct,
            notes: notes || null,
            condition_photo: conditionPhoto || null,
        }),
    })
    if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to return vehicle')
    }
    return await res.json()
}

// ── Fuel Receipt ───────────────────────────────────────────────────────────────

export async function submitFuelReceipt({ amount, liters, station, photoBase64 = null }) {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/fuel-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
            amount: parseFloat(amount),
            liters: parseFloat(liters),
            station: station || '',
            photo_base64: photoBase64,
        })
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to submit fuel receipt' }))
        throw new Error(extractErrorMessage(error, 'Failed to submit fuel receipt'))
    }
    return await res.json()
}

// ── Audit Log ──────────────────────────────────────────────────────────────────

export async function getDriverAuditLog() {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/audit', {
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })
    if (!res.ok) throw new Error('Failed to fetch audit log')
    return await res.json()
}

// ── Cashout ────────────────────────────────────────────────────────────────────

export async function requestCashout(amount) {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/cashout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ amount: parseFloat(amount) })
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to request cashout' }))
        throw new Error(extractErrorMessage(error, 'Failed to request cashout'))
    }
    return await res.json()
}
