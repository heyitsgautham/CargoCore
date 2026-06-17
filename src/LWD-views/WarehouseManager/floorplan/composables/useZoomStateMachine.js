import { reactive, computed, ref } from 'vue'
import gsap from 'gsap'

/**
 * Infinite canvas zoom + pan state machine.
 * 
 * Manages:
 * - Level transitions: FLOOR → SECTION → RACK
 * - Canvas pan (translateX, translateY) via middle-mouse drag or spacebar+drag
 * - Canvas zoom (scale) via wheel or buttons
 * - Recenter to bring content back to view
 */
export function useZoomStateMachine() {
    const state = reactive({
        level: 'FLOOR',
        activeSectionId: null,
        activeRackId: null,
        isTransitioning: false
    })

    // ── Pan + Zoom state ──
    const panX = ref(0)
    const panY = ref(0)
    const scale = ref(1)

    const MIN_SCALE = 0.2
    const MAX_SCALE = 4
    const ZOOM_FACTOR = 0.12

    // Panning state
    const isPanning = ref(false)
    const panStart = ref({ x: 0, y: 0 })

    // Transition animation opacity
    const transitionOpacity = ref(1)

    // ── Level Transitions ──
    function animateTransition(changeFn) {
        state.isTransitioning = true
        return new Promise(resolve => {
            gsap.to(transitionOpacity, {
                value: 0,
                duration: 0.15,
                ease: 'power2.in',
                onComplete: () => {
                    changeFn()
                    // Reset pan+zoom on level change
                    panX.value = 0
                    panY.value = 0
                    scale.value = 1
                    gsap.to(transitionOpacity, {
                        value: 1,
                        duration: 0.25,
                        ease: 'power2.out',
                        onComplete: () => {
                            state.isTransitioning = false
                            resolve()
                        }
                    })
                }
            })
        })
    }

    async function zoomToSection(sectionId) {
        await animateTransition(() => {
            state.level = 'SECTION'
            state.activeSectionId = sectionId
            state.activeRackId = null
        })
    }

    async function zoomToRack(rackId) {
        await animateTransition(() => {
            state.level = 'RACK'
            state.activeRackId = rackId
        })
    }

    async function levelBack() {
        if (state.level === 'RACK') {
            await animateTransition(() => {
                state.level = 'SECTION'
                state.activeRackId = null
            })
            return 'SECTION'
        } else if (state.level === 'SECTION') {
            await animateTransition(() => {
                state.level = 'FLOOR'
                state.activeSectionId = null
                state.activeRackId = null
            })
            return 'FLOOR'
        }
        return state.level
    }

    async function zoomToFloor() {
        await animateTransition(() => {
            state.level = 'FLOOR'
            state.activeSectionId = null
            state.activeRackId = null
        })
    }

    // ── Zoom Controls ──
    function zoomIn() {
        const next = Math.min(scale.value * (1 + ZOOM_FACTOR), MAX_SCALE)
        gsap.to(scale, { value: next, duration: 0.15, ease: 'power2.out' })
    }

    function zoomOut() {
        const next = Math.max(scale.value * (1 - ZOOM_FACTOR), MIN_SCALE)
        gsap.to(scale, { value: next, duration: 0.15, ease: 'power2.out' })
    }

    function zoomReset() {
        gsap.to(scale, { value: 1, duration: 0.2, ease: 'power2.out' })
        gsap.to(panX, { value: 0, duration: 0.2, ease: 'power2.out' })
        gsap.to(panY, { value: 0, duration: 0.2, ease: 'power2.out' })
    }

    /** Recenter — animate pan back to origin */
    function recenter() {
        gsap.to(panX, { value: 0, duration: 0.3, ease: 'power2.out' })
        gsap.to(panY, { value: 0, duration: 0.3, ease: 'power2.out' })
    }

    // ── Wheel Zoom (zooms toward cursor) ──
    function onWheel(e, containerEl) {
        e.preventDefault()
        const delta = e.deltaY > 0 ? -ZOOM_FACTOR : ZOOM_FACTOR
        const newScale = Math.max(MIN_SCALE, Math.min(scale.value * (1 + delta), MAX_SCALE))

        if (containerEl) {
            const rect = containerEl.getBoundingClientRect()
            const mx = e.clientX - rect.left
            const my = e.clientY - rect.top
            // Zoom toward cursor position
            const ratio = newScale / scale.value
            panX.value = mx - ratio * (mx - panX.value)
            panY.value = my - ratio * (my - panY.value)
        }

        scale.value = newScale
    }

    // ── Pan via mouse drag ──
    function startPan(e) {
        isPanning.value = true
        panStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
    }

    function onPanMove(e) {
        if (!isPanning.value) return
        panX.value = e.clientX - panStart.value.x
        panY.value = e.clientY - panStart.value.y
    }

    function endPan() {
        isPanning.value = false
    }

    // ── Computed styles ──
    const transitionStyle = computed(() => ({
        opacity: transitionOpacity.value,
        transition: 'none'
    }))

    const canvasTransform = computed(() =>
        `translate(${panX.value}px, ${panY.value}px) scale(${scale.value})`
    )

    const zoomPercent = computed(() => Math.round(scale.value * 100))

    return {
        state,
        panX,
        panY,
        scale,
        isPanning,
        transitionStyle,
        transitionOpacity,
        canvasTransform,
        zoomPercent,
        zoomIn,
        zoomOut,
        zoomReset,
        recenter,
        onWheel,
        startPan,
        onPanMove,
        endPan,
        zoomToSection,
        zoomToRack,
        levelBack,
        zoomToFloor
    }
}
