/**
 * useOsrmDistance — fetches road distance from the public OSRM demo server.
 * Falls back to Haversine × 1.35 if the request fails or times out.
 *
 * NOTE: OSRM uses (longitude, latitude) order — opposite of most APIs.
 */

const OSRM_BASE = 'https://router.project-osrm.org/route/v1/driving'
const TIMEOUT_MS = 5000

// Haversine straight-line km
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function fallback(lat1, lon1, lat2, lon2) {
  return Math.max(1, Math.round(haversineKm(lat1, lon1, lat2, lon2) * 1.35 * 10) / 10)
}

/**
 * Fetch road distance in km between two points.
 * @returns {Promise<number>} distance in km (min 1)
 */
export async function fetchRoadDistanceKm(lat1, lon1, lat2, lon2) {
  try {
    const url = `${OSRM_BASE}/${lon1},${lat1};${lon2},${lat2}?overview=false`
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
    const res = await fetch(url, { signal: controller.signal })
    clearTimeout(timer)
    if (!res.ok) return fallback(lat1, lon1, lat2, lon2)
    const data = await res.json()
    if (data.code !== 'Ok' || !data.routes?.[0]) return fallback(lat1, lon1, lat2, lon2)
    const meters = data.routes[0].distance
    return Math.max(1, Math.round((meters / 1000) * 10) / 10)
  } catch {
    return fallback(lat1, lon1, lat2, lon2)
  }
}
