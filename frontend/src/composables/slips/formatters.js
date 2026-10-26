/**
 * Number, date, address and logistics-estimate formatters shared by the HTML slips.
 */

export function inr(n) {
  return `₹${Number(n || 0).toLocaleString('en-IN')}`
}

export function fmtShort(value) {
  if (!value) return 'TBD'
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function fmtLong(value) {
  if (!value) return fmtShort(new Date())
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
}

export function fmtTime(value) {
  if (!value) return 'TBD'
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }).toUpperCase()
}

export function num(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export function cleanText(value, fallback = '—') {
  const text = String(value ?? '').trim()
  return text || fallback
}

export { escapeHtml } from '@/utils/html'

export function compactAddress(address, fallback = '—') {
  const parts = String(address ?? '')
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
  return parts.length ? parts.join(', ') : fallback
}

export function routeLabel(address, fallback = '—') {
  const parts = String(address ?? '')
    .split(',')
    .map(part => part.trim())
    .filter(Boolean)
  if (!parts.length) return fallback
  return parts.slice(0, 2).join(', ')
}

export function haversineKm(lat1, lon1, lat2, lon2) {
  const values = [lat1, lon1, lat2, lon2].map(Number)
  if (values.some(value => !Number.isFinite(value))) return null
  const [aLat, aLon, bLat, bLon] = values
  const toRad = (deg) => (deg * Math.PI) / 180
  const earthRadiusKm = 6371
  const dLat = toRad(bLat - aLat)
  const dLon = toRad(bLon - aLon)
  const q =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLon / 2) ** 2
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(q))
}

export function estimateDistanceKm(order) {
  const direct = num(
    order?.distanceKm ??
    order?.distance_km ??
    order?.totalDistance ??
    order?.total_distance ??
    order?.routeDistanceKm,
    NaN
  )
  if (Number.isFinite(direct) && direct > 0) return direct

  const geo = haversineKm(order?.pickupLat, order?.pickupLng, order?.deliveryLat, order?.deliveryLng)
  if (geo && geo > 0) return geo * 1.24
  return null
}

export function formatDistance(distanceKm) {
  if (!distanceKm || !Number.isFinite(distanceKm)) return 'Route based on dispatch plan'
  return `Distance: ${distanceKm.toFixed(distanceKm >= 100 ? 0 : 1)} km`
}

export function estimateLoadMinutes(order) {
  return Math.max(30, 45 + num(order?.laborCount) * 15)
}

export function estimateUnloadMinutes(order) {
  return Math.max(25, 35 + num(order?.laborCount) * 10)
}

export function estimateTravelMinutes(distanceKm, vehicleType = '') {
  if (!distanceKm || !Number.isFinite(distanceKm)) return 45
  const speed = /truck|xl|heavy/i.test(vehicleType) ? 28 : /van/i.test(vehicleType) ? 34 : 30
  return Math.max(25, Math.round((distanceKm / speed) * 60))
}

export function formatDuration(minutes) {
  if (!Number.isFinite(minutes) || minutes <= 0) return 'TBD'
  const hours = minutes / 60
  return hours >= 1 ? `${hours.toFixed(1)} hrs` : `${Math.round(minutes)} min`
}

export function estimateFuelLiters(distanceKm, vehicleType = '') {
  if (!distanceKm || !Number.isFinite(distanceKm)) return null
  const efficiency = /truck|xl|heavy/i.test(vehicleType) ? 5.5 : /van/i.test(vehicleType) ? 9 : 7
  return Math.max(1, Math.round((distanceKm / efficiency) * 10) / 10)
}

export function vehicleCapacityLabel(vehicleType = '', weight = 0) {
  if (/truck|xl|heavy/i.test(vehicleType) || weight > 1800) return '3.5 Tons'
  if (/van/i.test(vehicleType) || weight > 900) return '2.0 Tons'
  return '1.0 Ton'
}

export function estimateBoxes(order) {
  const explicit = num(order?.boxCount ?? order?.boxes ?? order?.itemsCount ?? order?.itemCount, NaN)
  if (Number.isFinite(explicit) && explicit > 0) return explicit
  const volume = num(order?.volume ?? order?.cargoVolume ?? order?.cargo_volume_m3, NaN)
  if (Number.isFinite(volume) && volume > 0) return Math.max(1, Math.round(volume * 8))
  const weight = num(order?.weight)
  return Math.max(1, Math.round(weight / 35) || 1)
}

export function summarizeSpecialItems(order) {
  const notes = String(order?.specialInstructions || order?.notes || '').toLowerCase()
  const tags = []
  if (notes.includes('fragile')) tags.push('Fragile')
  if (notes.includes('priority')) tags.push('Priority')
  if (notes.includes('perishable')) tags.push('Perishable')
  if (num(order?.laborCount) > 0) tags.push(`${num(order?.laborCount)} crew`)
  return tags.length ? tags.join(' • ') : cleanText(order?.cargoType || order?.type, 'Standard cargo')
}

export function routeViaLabel(order, vehicleNo) {
  const pickup = routeLabel(order?.pickupAddr, '')
  const delivery = routeLabel(order?.deliveryAddr, '')
  if (pickup && delivery) return `Via dispatch route from ${pickup} to ${delivery}`
  return `Assigned vehicle: ${vehicleNo}`
}

export function buildTripSchedule(order) {
  const base = new Date(order?.scheduledAt || order?.eta || order?.createdAt || order?.lastUpdated || Date.now())
  const distanceKm = estimateDistanceKm(order)
  const loadMinutes = estimateLoadMinutes(order)
  const unloadMinutes = estimateUnloadMinutes(order)
  const travelMinutes = estimateTravelMinutes(distanceKm, order?.vehicleType || order?.vehicle)
  const pickup = new Date(base.getTime())
  const delivery = new Date(base.getTime() + (loadMinutes + travelMinutes) * 60_000)
  const depot = new Date(delivery.getTime() + (unloadMinutes + Math.round(travelMinutes * 0.55)) * 60_000)
  return {
    pickupTime: fmtTime(pickup),
    deliveryTime: fmtTime(delivery),
    returnTime: fmtTime(depot),
    loadTime: `${loadMinutes} minutes`,
    unloadTime: `${unloadMinutes} minutes`,
    totalDuration: formatDuration(loadMinutes + unloadMinutes + travelMinutes),
    routeMeta: `${formatDistance(distanceKm)} | Est. Time: ${formatDuration(travelMinutes)}`,
    totalDistance: distanceKm ? `${distanceKm.toFixed(distanceKm >= 100 ? 0 : 1)} km` : 'TBD',
    fuelEstimate: estimateFuelLiters(distanceKm, order?.vehicleType || order?.vehicle),
  }
}

export function assetCode(label, index) {
  const prefix = String(label || '')
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('') || 'AK'
  return `${prefix}-${String(index + 1).padStart(3, '0')}`
}

export function defaultAssetQuantities(order) {
  const weight = Math.max(0, num(order?.weight))
  const laborCount = Math.max(0, num(order?.laborCount))
  return {
    'Moving Boxes': Math.max(6, Math.round(weight / 35) || 6),
    'Bubble Wrap (rolls)': Math.max(1, Math.ceil(weight / 250) || 1),
    'Moving Blankets': Math.max(2, laborCount * 2 || 2),
    'Dollies / Hand Trucks': Math.max(1, Math.ceil(weight / 350) || 1),
    'Tape Rolls': Math.max(2, laborCount + 1 || 2),
    'Stretch Wrap (rolls)': Math.max(1, Math.ceil(weight / 400) || 1),
    'Furniture Pads': Math.max(2, laborCount * 2 || 2),
  }
}

export function buildAssetEquipment(order) {
  const defaults = defaultAssetQuantities(order)
  const provided = Array.isArray(order?.assetItems) ? order.assetItems : []

  const normalized = provided.map((item, index) => {
    const label = cleanText(item?.label || item?.name, `Asset ${index + 1}`)
    const qty = Math.max(0, num(item?.qty ?? item?.sentOut ?? item?.count, defaults[label] || 0))
    return {
      label,
      id: cleanText(item?.id || item?.assetId, assetCode(label, index)),
      qty: qty || defaults[label] || 0,
      cond: cleanText(item?.cond || item?.condition || item?.status, 'Ready'),
    }
  }).filter(item => item.qty > 0)

  if (normalized.length) return normalized

  return Object.entries(defaults).map(([label, qty], index) => ({
    label,
    id: assetCode(label, index),
    qty,
    cond: 'Ready',
  }))
}
