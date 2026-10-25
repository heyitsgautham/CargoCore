// Road geometry for driver-to-destination routes from the public OSRM server,
// cached per coordinate pair, with a straight line when OSRM fails or times out.
import { ref, watch } from 'vue'

const routeCache = new Map()

export async function fetchOsrmRoute(lat1, lon1, lat2, lon2) {
    const cacheKey = `${lat1.toFixed(5)},${lon1.toFixed(5)}|${lat2.toFixed(5)},${lon2.toFixed(5)}`
    if (routeCache.has(cacheKey)) return routeCache.get(cacheKey)
    try {
        const url = `https://router.project-osrm.org/route/v1/driving/${lon1},${lat1};${lon2},${lat2}?overview=full&geometries=geojson`
        const controller = new AbortController()
        const timer = setTimeout(() => controller.abort(), 8000)
        const res = await fetch(url, { signal: controller.signal })
        clearTimeout(timer)
        if (!res.ok) throw new Error('OSRM error')
        const data = await res.json()
        if (data.code !== 'Ok' || !data.routes?.[0]) throw new Error('No route')
        // OSRM returns [lon, lat]; Leaflet wants [lat, lon]
        const coords = data.routes[0].geometry.coordinates.map(([lon, lat]) => [lat, lon])
        routeCache.set(cacheKey, coords)
        return coords
    } catch {
        return [[lat1, lon1], [lat2, lon2]]
    }
}

/** Road coordinates keyed by route id, fetched as new routes appear. */
export function useRoadRoutes(routes) {
    const roadCoords = ref({})
    watch(routes, (current) => {
        for (const route of current) {
            if (roadCoords.value[route.id]) continue
            const [lat1, lon1] = route.from
            const [lat2, lon2] = route.to
            fetchOsrmRoute(lat1, lon1, lat2, lon2).then(coords => {
                roadCoords.value = { ...roadCoords.value, [route.id]: coords }
            })
        }
    }, { immediate: true, deep: false })
    return roadCoords
}
