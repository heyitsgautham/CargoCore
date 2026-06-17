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
    /** Cancellable delay – rejects with 'aborted' when signal fires */
    function delay(ms, signal) {
        return new Promise((resolve, reject) => {
            const id = setTimeout(resolve, ms)
            signal?.addEventListener('abort', () => { clearTimeout(id); reject('aborted') })
        })
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

    /**
     * Focus on a specific search result with animated drill-down:
     *   Step 1 – FLOOR level, highlight the target section (pulse)
     *   Step 2 – SECTION level, highlight the target rack
     *   Step 3 – RACK level, highlight the target cell
     */
    async function focusSearchResult(result, activeFloorId, setFloor, _containerSize) {
        // Cancel any previous drill-down animation
        if (drillAbort) drillAbort.abort()
        drillAbort = new AbortController()
        const signal = drillAbort.signal

        // Switch floor if needed
        if (result.floorId !== activeFloorId) {
            setFloor(result.floorId)
        }

        // Keep search query visible & store paths for next/prev navigation
        highlightedProducts.value = searchResults.value.map(s => s.product)
        searchPaths.value = [...searchResults.value]
        currentPathIdx.value = searchResults.value.indexOf(result)
        // Close the dropdown but keep the query text
        searchResults.value = []

        isDrillAnimating.value = true

        try {
            // ── Step 1: Floor level — highlight the section ──
            await zoom.zoomToFloor()
            clearHighlights()
            highlightedSectionIds.value = [result.sectionId]
            highlightedProducts.value = [result.product]
            await delay(1200, signal)

            // ── Step 2: Section level — highlight the rack ──
            await zoom.zoomToSection(result.sectionId)
            highlightedSectionIds.value = []
            highlightedRackIds.value = [result.rackId]
            highlightedProducts.value = [result.product]
            await delay(1200, signal)

            // ── Step 3: Rack level — highlight the cell ──
            await zoom.zoomToRack(result.rackId)
            highlightedRackIds.value = []
            highlightedCellKeys.value = [`${result.rackId}:${result.product.cell}`]
            highlightedProducts.value = [result.product]

        } catch (_) {
            // Drill-down was aborted (user started a new search / navigation)
        } finally {
            isDrillAnimating.value = false
        }
    }

    /** Navigate to the next search result (with drill-down animation) */
    function nextResult(activeFloorId, setFloor) {
        if (!searchPaths.value.length) return
        currentPathIdx.value = (currentPathIdx.value + 1) % searchPaths.value.length
        navigateToPath(searchPaths.value[currentPathIdx.value], activeFloorId, setFloor)
    }

    /** Navigate to the previous search result (with drill-down animation) */
    function prevResult(activeFloorId, setFloor) {
        if (!searchPaths.value.length) return
        currentPathIdx.value = (currentPathIdx.value - 1 + searchPaths.value.length) % searchPaths.value.length
        navigateToPath(searchPaths.value[currentPathIdx.value], activeFloorId, setFloor)
    }

    /** Navigate and animate to a specific path entry */
    async function navigateToPath(entry, activeFloorId, setFloor) {
        // Cancel any previous drill-down animation
        if (drillAbort) drillAbort.abort()
        drillAbort = new AbortController()
        const signal = drillAbort.signal

        if (entry.floorId !== activeFloorId) setFloor(entry.floorId)
        highlightedProducts.value = [entry.product]

        isDrillAnimating.value = true

        try {
            // Step 1: Floor – highlight section
            await zoom.zoomToFloor()
            clearHighlights()
            highlightedSectionIds.value = [entry.sectionId]
            highlightedProducts.value = [entry.product]
            await delay(1000, signal)

            // Step 2: Section – highlight rack
            await zoom.zoomToSection(entry.sectionId)
            highlightedSectionIds.value = []
            highlightedRackIds.value = [entry.rackId]
            highlightedProducts.value = [entry.product]
            await delay(1000, signal)

            // Step 3: Rack – highlight cell
            await zoom.zoomToRack(entry.rackId)
            highlightedRackIds.value = []
            highlightedCellKeys.value = [`${entry.rackId}:${entry.product.cell}`]
            highlightedProducts.value = [entry.product]

        } catch (_) {
            // aborted
        } finally {
            isDrillAnimating.value = false
        }
    }

    function clearSearchNav() {
        if (drillAbort) drillAbort.abort()
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
