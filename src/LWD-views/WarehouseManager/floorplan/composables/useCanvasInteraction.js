import { ref } from 'vue'

/**
 * Handles drag, resize, and snap-to-grid interactions for canvas elements.
 */
export function useCanvasInteraction({ snapGridSize = 20 } = {}) {
    const isDragging = ref(false)
    const isResizing = ref(false)
    const selectedElement = ref(null)
    const snapToGrid = ref(true)

    let dragOffset = { x: 0, y: 0 }
    let resizeOrigin = { x: 0, y: 0, ow: 0, oh: 0 }

    function snap(v) {
        return snapToGrid.value ? Math.round(v / snapGridSize) * snapGridSize : v
    }

    /** Select and start dragging an element */
    function startDrag(event, element) {
        selectedElement.value = element
        isDragging.value = true
        isResizing.value = false
        dragOffset = {
            x: event.clientX,
            y: event.clientY,
            startX: element.x,
            startY: element.y
        }
    }

    /** Start resizing the selected element */
    function startResize(event, element) {
        selectedElement.value = element
        isResizing.value = true
        isDragging.value = false
        resizeOrigin = {
            x: event.clientX,
            y: event.clientY,
            ow: element.w,
            oh: element.h
        }
    }

    /** Handle mouse move during drag or resize (scale-aware, clamped to bounds) */
    function onMove(event, canvasScale = 1, canvasEl = null) {
        if (!selectedElement.value) return

        if (isDragging.value) {
            const dx = (event.clientX - dragOffset.x) / canvasScale
            const dy = (event.clientY - dragOffset.y) / canvasScale
            let nx = snap(dragOffset.startX + dx)
            let ny = snap(dragOffset.startY + dy)
            // Clamp within canvas bounds
            if (canvasEl) {
                const maxX = canvasEl.clientWidth - (selectedElement.value.w || 80)
                const maxY = canvasEl.clientHeight - (selectedElement.value.h || 80)
                nx = Math.max(0, Math.min(nx, maxX))
                ny = Math.max(0, Math.min(ny, maxY))
            } else {
                nx = Math.max(0, nx)
                ny = Math.max(0, ny)
            }
            selectedElement.value.x = nx
            selectedElement.value.y = ny
        }

        if (isResizing.value) {
            const dx = (event.clientX - resizeOrigin.x) / canvasScale
            const dy = (event.clientY - resizeOrigin.y) / canvasScale
            let nw = snap(resizeOrigin.ow + dx)
            let nh = snap(resizeOrigin.oh + dy)
            // Clamp so element doesn't extend past canvas
            if (canvasEl) {
                nw = Math.min(nw, canvasEl.clientWidth - selectedElement.value.x)
                nh = Math.min(nh, canvasEl.clientHeight - selectedElement.value.y)
            }
            selectedElement.value.w = Math.max(40, nw)
            selectedElement.value.h = Math.max(40, nh)
        }
    }

    /** End drag/resize */
    function onUp() {
        isDragging.value = false
        isResizing.value = false
    }

    /** Select element without dragging */
    function selectElement(element) {
        selectedElement.value = element
    }

    /** Deselect current element */
    function deselect() {
        selectedElement.value = null
    }

    /** Clear all interaction state */
    function reset() {
        isDragging.value = false
        isResizing.value = false
        selectedElement.value = null
    }

    return {
        isDragging,
        isResizing,
        selectedElement,
        snapToGrid,
        startDrag,
        startResize,
        onMove,
        onUp,
        selectElement,
        deselect,
        reset
    }
}
