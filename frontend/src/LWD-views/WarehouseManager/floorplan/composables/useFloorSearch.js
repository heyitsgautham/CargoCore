import { ref, watch } from 'vue'

/**
 * Token-based search index with animated progressive drill-down navigation.
 *
 * When a product is focused it animates through:
 *   FLOOR (highlight section) → SECTION (highlight rack) → RACK (highlight cell)
 *
 * @param {Object} store - The warehouseFloorStore instance
 * @param {Object} zoom  - The useZoomStateMachine instance
 */
export function useFloorSearch(store, zoom) {
    const searchQuery = ref('')
    const searchResults = ref([])
    const highlightedSectionIds = ref([])
    const highlightedRackIds = ref([])
    const highlightedCellKeys = ref([]) // "rackId:cellIndex"
    const highlightedProducts = ref([])
    const searchPaths = ref([])
    const currentPathIdx = ref(0)
    const isDrillAnimating = ref(false)

    let searchTimer = null
    let drillAbort = null // AbortController for cancelling in-progress drill-down

    // ── Search Index ────────────────────────────────────────────
    const searchIndex = new Map() // token → Set<product>

    function buildIndex() {
        searchIndex.clear()
        for (const p of store.products) {
            const tokens = tokenize(p)
            for (const t of tokens) {
                if (!searchIndex.has(t)) searchIndex.set(t, new Set())
                searchIndex.get(t).add(p)
            }
        }
    }

    function tokenize(product) {
        const rack = store.rackMap.get(product.rackId)
        const section = rack ? store.sectionMap.get(rack.sectionId) : null
        return [
            ...product.name.toLowerCase().split(/\s+/),
            product.sku.toLowerCase(),
            product.orderId.toLowerCase(),
            product.rma?.toLowerCase(),
            section?.label?.toLowerCase()
        ].filter(Boolean)
    }

    // Rebuild index when products change
    watch(() => store.products.length, buildIndex, { immediate: true })

    // ── Helpers ──────────────────────────────────────────────────
    /** Cancellable delay, rejects with 'aborted' when the signal fires or already has */
    function delay(ms, signal) {
        return new Promise((resolve, reject) => {
            if (signal.aborted) return reject('aborted')
            const id = setTimeout(resolve, ms)
            signal.addEventListener('abort', () => { clearTimeout(id); reject('aborted') })
        })
    }

    function throwIfAborted(signal) {
        if (signal.aborted) throw 'aborted'
    }

    /**
     * Animated drill-down to one search result, cancelling any drill-down in progress.
     *   Step 1, FLOOR level, highlight the target section
     *   Step 2, SECTION level, highlight the target rack
     *   Step 3, RACK level, highlight the target cell
     * A cancel during a zoom tween stops before the next highlight is drawn.
     */
    async function drillDown(entry, pauseMs) {
        if (drillAbort) drillAbort.abort()
        drillAbort = new AbortController()
        const signal = drillAbort.signal

        isDrillAnimating.value = true
        try {
            await zoom.zoomToFloor()
            throwIfAborted(signal)
            clearHighlights()
            highlightedSectionIds.value = [entry.sectionId]
            highlightedProducts.value = [entry.product]
            await delay(pauseMs, signal)

            await zoom.zoomToSection(entry.sectionId)
            throwIfAborted(signal)
            highlightedSectionIds.value = []
            highlightedRackIds.value = [entry.rackId]
            await delay(pauseMs, signal)

            await zoom.zoomToRack(entry.rackId)
            throwIfAborted(signal)
            highlightedRackIds.value = []
            highlightedCellKeys.value = [`${entry.rackId}:${entry.product.cell}`]
        } catch {
            // A newer search, navigation or clear cancelled this drill-down.
        } finally {
            if (!signal.aborted) isDrillAnimating.value = false
        }
    }

    // ── Search Execution ────────────────────────────────────────
    function onSearch() {
        clearTimeout(searchTimer)
        // Don't clear highlights while typing – only when query is empty
        if (!searchQuery.value.trim()) {
            searchResults.value = []
            return
        }
        searchTimer = setTimeout(() => {
            const q = searchQuery.value.toLowerCase().trim()

            // Collect all products that match any token prefix
            const matched = new Set()
            for (const [token, prods] of searchIndex) {
                if (token.includes(q)) {
                    prods.forEach(p => matched.add(p))
                }
            }

            // Fallback: direct field search for partial matches not in tokens
            for (const p of store.products) {
                if (
                    p.sku.toLowerCase().includes(q) ||
                    p.name.toLowerCase().includes(q) ||
                    p.orderId.toLowerCase().includes(q) ||
                    (p.rma && p.rma.toLowerCase().includes(q))
                ) {
                    matched.add(p)
                }
            }

            searchResults.value = [...matched].map(p => {
                const rack = store.rackMap.get(p.rackId)
                const section = rack ? store.sectionMap.get(rack.sectionId) : null
                return {
                    product: p,
                    rackId: p.rackId,
                    sectionId: rack?.sectionId,
                    sectionLabel: section?.label || '?',
                    rackLabel: rack?.label || '?',
                    floorId: section?.floorId || 1
                }
            })
        }, 200)
    }

    /** Focus on a search result from the dropdown and keep the rest for next and previous. */
    async function focusSearchResult(result, activeFloorId, setFloor) {
        if (result.floorId !== activeFloorId) setFloor(result.floorId)

        // Keep the query text and the result list, but close the dropdown.
        highlightedProducts.value = searchResults.value.map(s => s.product)
        searchPaths.value = [...searchResults.value]
        currentPathIdx.value = searchResults.value.indexOf(result)
        searchResults.value = []

        await drillDown(result, 1200)
    }

    /** Navigate to the next search result */
    function nextResult(activeFloorId, setFloor) {
        if (!searchPaths.value.length) return
        currentPathIdx.value = (currentPathIdx.value + 1) % searchPaths.value.length
        navigateToPath(searchPaths.value[currentPathIdx.value], activeFloorId, setFloor)
    }

    /** Navigate to the previous search result */
    function prevResult(activeFloorId, setFloor) {
        if (!searchPaths.value.length) return
        currentPathIdx.value = (currentPathIdx.value - 1 + searchPaths.value.length) % searchPaths.value.length
        navigateToPath(searchPaths.value[currentPathIdx.value], activeFloorId, setFloor)
    }

    async function navigateToPath(entry, activeFloorId, setFloor) {
        if (entry.floorId !== activeFloorId) setFloor(entry.floorId)
        highlightedProducts.value = [entry.product]
        await drillDown(entry, 1000)
    }

    function clearSearchNav() {
        if (drillAbort) drillAbort.abort()
        isDrillAnimating.value = false
        searchQuery.value = ''
        searchPaths.value = []
        currentPathIdx.value = 0
        clearHighlights()
    }

    function clearHighlights() {
        highlightedSectionIds.value = []
        highlightedRackIds.value = []
        highlightedCellKeys.value = []
        highlightedProducts.value = []
    }

    /** Get highlighted products for a specific section */
    function getHighlightProductsForSection(sectionId) {
        return highlightedProducts.value.filter(p => {
            const rack = store.rackMap.get(p.rackId)
            return rack?.sectionId === sectionId
        })
    }

    /** Get highlighted products for a specific rack */
    function getHighlightProductsForRack(rackId) {
        return highlightedProducts.value.filter(p => p.rackId === rackId)
    }

    return {
        searchQuery,
        searchResults,
        highlightedSectionIds,
        highlightedRackIds,
        highlightedCellKeys,
        highlightedProducts,
        searchPaths,
        currentPathIdx,
        isDrillAnimating,
        onSearch,
        focusSearchResult,
        nextResult,
        prevResult,
        clearSearchNav,
        clearHighlights,
        getHighlightProductsForSection,
        getHighlightProductsForRack,
        buildIndex
    }
}
