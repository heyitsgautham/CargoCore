// The dashboard's Leaflet map instance: fitting it to the points that matter and
// telling Leaflet to re-measure after the side panels slide in or out.
import { nextTick, ref } from 'vue'
import { validPoints } from '@/utils/mapBounds'

export function useMapViewport(collectPoints) {
    const map = ref(null)

    function fitMapBounds() {
        nextTick(() => {
            setTimeout(() => {
                if (!map.value?.leafletObject) return
                const leafletMap = map.value.leafletObject
                const fitted = validPoints(collectPoints())
                if (fitted.length > 1) leafletMap.fitBounds(fitted, { padding: [50, 50], maxZoom: 14 })
                else if (fitted.length === 1) leafletMap.setView(fitted[0], 13)
            }, 600)
        })
    }

    function invalidateMapSize() {
        nextTick(() => {
            setTimeout(() => {
                if (map.value?.leafletObject) {
                    map.value.leafletObject.invalidateSize()
                }
            }, 350) // Wait for panel transition to complete
        })
    }

    return { map, fitMapBounds, invalidateMapSize }
}
