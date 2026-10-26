import { computed, ref } from 'vue'

const BASE_W = 2000
const BASE_H = 1400
const CONTENT_OFFSET_TOP = 100
const CONTENT_OFFSET_LEFT = 20
const CONTENT_PADDING = 150
const MIN_ZOOM = 0.5
const MAX_ZOOM = 3
const ZOOM_STEP = 0.25

/** Right and bottom edge of the drawn content at the current zoom level, padding included. */
export function contentExtent(level, sections, racks, rack) {
    let maxRight = 0
    let maxBottom = 0

    if (level === 'FLOOR') {
        for (const sec of sections) {
            maxRight = Math.max(maxRight, sec.x + sec.w)
            maxBottom = Math.max(maxBottom, sec.y + sec.h)
        }
    } else if (level === 'SECTION') {
        for (const r of racks) {
            maxRight = Math.max(maxRight, r.x + r.w)
            maxBottom = Math.max(maxBottom, r.y + r.h)
        }
    } else if (level === 'RACK' && rack) {
        maxRight = 40 + rack.cols * 124 + 16
        maxBottom = 40 + rack.rows * 84 + 16
    }

    return {
        right: maxRight + CONTENT_OFFSET_LEFT + CONTENT_PADDING,
        bottom: maxBottom + CONTENT_OFFSET_TOP + CONTENT_PADDING,
    }
}

export function stepZoom(current, dir) {
    return dir > 0 ? Math.min(MAX_ZOOM, current + ZOOM_STEP) : Math.max(MIN_ZOOM, current - ZOOM_STEP)
}

/**
 * Canvas zoom for the floor plan.
 * Zooming changes the scrollable area size, and the browser scrollbars handle navigation.
 */
export function useCanvasZoom({ zoom, currentSections, activeRacks, activeRack, canvasRef }) {
    const canvasZoom = ref(1)

    const extent = computed(() =>
        contentExtent(zoom.state.level, currentSections.value, activeRacks.value, activeRack.value))

    const canvasWidth = computed(() => {
        const base = zoom.state.level === 'FLOOR' ? BASE_W : 600
        return Math.round(Math.max(base, extent.value.right) * canvasZoom.value)
    })
    const canvasHeight = computed(() => {
        const base = zoom.state.level === 'FLOOR' ? BASE_H : 500
        return Math.round(Math.max(base, extent.value.bottom) * canvasZoom.value)
    })
    const canvasZoomPercent = computed(() => Math.round(canvasZoom.value * 100))

    function zoomCanvas(dir) {
        canvasZoom.value = stepZoom(canvasZoom.value, dir)
    }

    function recenterCanvas() {
        canvasZoom.value = 1
        canvasRef.value?.scrollTo({ left: 0, top: 0, behavior: 'smooth' })
    }

    return { canvasZoom, canvasWidth, canvasHeight, canvasZoomPercent, zoomCanvas, recenterCanvas }
}
