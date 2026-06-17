/**
 * useRates — fetch platform-wide rate config from backend.
 * Falls back to hardcoded defaults if backend is unreachable.
 *
 * Usage:
 *   const { rates, ratesReady } = useRates()
 *   // rates.value.perKmRate, rates.value.customerLaborRate, etc.
 */
import { ref } from 'vue'
import { getStoredAccessToken } from '@/config/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DEFAULTS = {
    baseBookingFee: 220,
    perKmRate: 12,
    minimumCharge: 500,
    expressMultiplier: 1.5,
    customerLaborRate: 250,
    customerPackingFee: 200,
    insurancePct: 3,
    materials: [
        { id: 'box', name: 'Box', rate: 50, unit: 'pcs' },
        { id: 'bubbleWrap', name: 'Bubble Wrap', rate: 20, unit: 'm' },
        { id: 'crate', name: 'Crate Rental', rate: 200, unit: 'pcs' },
    ],
    individualBookingFee: 300,
    individualLaborRate: 800,
    individualPackingPct: 20,
    individualDistanceRates: { miniTruck: 18, tempo: 25, lcv: 35, hcv: 50 },
    smallPackagePerKgRate: 120,
    smallPackagePerKmRate: 12,
    driver: { baseSalary: 25000, hra: 5000, da: 2000, performanceBonus: 3000, kmRate: 15, fuelIncentive: 500, ratingMultiplier: 1.1 },
    labor: { baseSalary: 18000, hra: 3500, da: 1500, performanceBonus: 2000, hourlyWage: 150, overtimeMul: 1.5, fieldAllowance: 200 },
    managers: { warehouseBase: 65000, warehouseHra: 15000, warehouseDa: 5000, warehouseBonus: 10000, dispatcherBase: 45000, dispatcherHra: 10000, dispatcherDa: 4000, dispatcherBonus: 8000 },
    fuel: { maxClaimPerKm: 12.5, benchmarkMileage: 8.5 },
    dynamic: { peak: 1.2, emergency: 2.5 },
}

// Helper to normalize old object format to new array format
function normalizeMaterials(data) {
    if (!data || !data.materials) return data
    // If it's already an array, return as-is
    if (Array.isArray(data.materials)) return data
    // Convert old object format to array
    const oldMaterials = data.materials
    data.materials = [
        { id: 'box', name: 'Box', rate: oldMaterials.box ?? 50, unit: 'pcs' },
        { id: 'bubbleWrap', name: 'Bubble Wrap', rate: oldMaterials.bubbleWrap ?? 20, unit: 'm' },
        { id: 'crate', name: 'Crate Rental', rate: oldMaterials.crate ?? 200, unit: 'pcs' },
    ]
    return data
}

// Module-level cache so all consumers stay in sync after governance updates.
let _cached = null
let _fetchPromise = null
const sharedRates = ref({ ...DEFAULTS })
const sharedRatesReady = ref(false)

function ensureRatesLoaded() {
    if (_cached) {
        sharedRates.value = { ...normalizeMaterials(_cached) }
        sharedRatesReady.value = true
    }

    if (!_fetchPromise) {
        const headers = { 'Content-Type': 'application/json' }
        const token = getStoredAccessToken()
        if (token) headers['Authorization'] = `Bearer ${token}`

        _fetchPromise = fetch(`${API_BASE}/api/v1/rates`, { headers })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data) {
                    _cached = normalizeMaterials(data)
                    sharedRates.value = { ..._cached }
                    sharedRatesReady.value = true
                }
            })
            .catch(() => { /* use defaults */ })
    }
}

export function useRates() {
    ensureRatesLoaded()

    async function saveRates(updated) {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/rates`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify(updated),
        })
        if (!res.ok) throw new Error('Failed to save rates')
        const saved = await res.json()
        _cached = normalizeMaterials(saved)
        _fetchPromise = null  // Reset so next call refetches
        sharedRates.value = { ..._cached }
        sharedRatesReady.value = true
        return saved
    }

    async function refreshRates() {
        _cached = null
        _fetchPromise = null
        sharedRatesReady.value = false
        
        const headers = { 'Content-Type': 'application/json' }
        const token = getStoredAccessToken()
        if (token) headers['Authorization'] = `Bearer ${token}`

        try {
            const res = await fetch(`${API_BASE}/api/v1/rates`, { headers })
            if (res.ok) {
                const data = await res.json()
                _cached = normalizeMaterials(data)
                sharedRates.value = { ..._cached }
                sharedRatesReady.value = true
            }
        } catch (e) {
            console.error('Failed to refresh rates:', e)
        }
    }

    return { rates: sharedRates, ratesReady: sharedRatesReady, saveRates, refreshRates }
}
