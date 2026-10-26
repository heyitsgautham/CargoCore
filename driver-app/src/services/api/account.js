// Driver sign-in, profile, vehicles, dashboard and crew check-in.
import { authHeaders, extractErrorMessage, fetchWithNetworkHelp, setAccessToken, setRefreshToken } from './client.js'

function normalizeVehiclePayload(v) {
    if (!v) return null
    return {
        id: v.id,
        vehicleId: v.code,
        vehicleCode: v.code,
        plateNumber: v.license_plate || v.code,
        status: v.status,
        model: v.model,
        type: v.type || v.vehicle_type,
        fuelLevel: v.fuel_level_pct ?? 0,
        capacity: v.cargo_capacity_tons ?? 0,
        range: v.range_km ?? 0,
        seats: v.seat_capacity ?? 0,
        odometer: v.mileage || 0,
        telemetryStatus: v.telemetry_status || 'READY',
        telemetryLastSeen: v.telemetry_last_seen || null,
        nextService: v.next_service || null,
        maintenanceIssue: v.maintenance_issue || null,
        fuelEfficiency: v.fuel_efficiency || null,
    }
}

// ── Authentication ─────────────────────────────────────────────────────────

export async function loginDriver(username, password) {
    const res = await fetchWithNetworkHelp('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: username,
            password
        })
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(extractErrorMessage(error, 'Authentication failed'))
    }

    const data = await res.json()

    const role = data.user?.role

    // Verify the user is a driver
    if (role !== 'DRIVER' && role !== 'driver') {
        throw new Error('Access denied. This is a driver-only application.')
    }

    setAccessToken(data.access_token)
    if (data.refresh_token) setRefreshToken(data.refresh_token)
    return data
}

export async function getDriverProfile() {
    const res = await fetchWithNetworkHelp('/api/v1/auth/me', {
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })

    if (!res.ok) throw new Error('Failed to fetch driver profile')
    return await res.json()
}

// ── Driver Operations ──────────────────────────────────────────────────────

export async function getDriverVehicles() {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/vehicles', {
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })
    
    if (!res.ok) {
        console.error('Failed to fetch vehicles')
        return []
    }
    
    const vehicles = await res.json()
    return vehicles.map(normalizeVehiclePayload)
}

export async function getDriverDashboard() {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/dashboard', {
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })

    if (!res.ok) throw new Error('Failed to fetch driver dashboard')
    const payload = await res.json()

    return {
        ...payload,
        current_vehicle: normalizeVehiclePayload(payload.current_vehicle),
    }
}

export async function bindDriverVehicle({ vehicleId = null, vehicleCode = null } = {}) {
    const res = await fetchWithNetworkHelp('/api/v1/logistics/drivers/me/bind-vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
            vehicle_id: vehicleId,
            vehicle_code: vehicleCode,
        })
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to bind vehicle' }))
        throw new Error(extractErrorMessage(error, 'Failed to bind vehicle'))
    }
    return normalizeVehiclePayload(await res.json())
}

export async function checkInCrewMember(labourerId) {
    const res = await fetchWithNetworkHelp(`/api/v1/logistics/drivers/me/crew/${labourerId}/check-in`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() }
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to check in crew member' }))
        throw new Error(extractErrorMessage(error, 'Failed to check in crew member'))
    }
    return await res.json()
}
