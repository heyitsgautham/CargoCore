/**
 * Bounds helpers for maps rendered by @vue-leaflet.
 *
 * @vue-leaflet bundles its own copy of Leaflet, so a LatLngBounds built with the
 * 'leaflet' import fails that copy's instanceof check and fitBounds throws
 * "Bounds are not valid". These helpers give the map plain [lat, lng] pairs.
 */

function isCoordinate(value) {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
}

/** Keep only points whose latitude and longitude are both usable numbers. */
export function validPoints(points = []) {
  return points.filter(([lat, lng]) => isCoordinate(lat) && isCoordinate(lng)).map(([lat, lng]) => [Number(lat), Number(lng)])
}

/** South-west and north-east corners around the points, grown by padFactor on each side like LatLngBounds.pad. */
export function paddedCornerPairs(points, padFactor = 0) {
  const usable = validPoints(points)
  const lats = usable.map(([lat]) => lat)
  const lngs = usable.map(([, lng]) => lng)
  const [south, north, west, east] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)]
  const latPad = (north - south) * padFactor
  const lngPad = (east - west) * padFactor
  return [
    [south - latPad, west - lngPad],
    [north + latPad, east + lngPad],
  ]
}
