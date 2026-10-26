export function hasCoordinates(lat, lng) {
  return Number.isFinite(lat) && Number.isFinite(lng)
}

/**
 * Spreads markers that share one anchor along a golden-angle spiral,
 * so crises without their own coordinates do not stack on one point.
 */
export function buildApproximateCoords(baseCoords, index) {
  if (!Array.isArray(baseCoords) || baseCoords.length !== 2) return null
  const angle = index * 137.508 * (Math.PI / 180)
  const distance = 0.02 + index * 0.01
  return [baseCoords[0] + Math.sin(angle) * distance, baseCoords[1] + Math.cos(angle) * distance]
}
