import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

// gsap tweens finish at once so level changes are synchronous in tests.
vi.mock('gsap', () => ({
  default: {
    to: (target, opts) => {
      target.value = opts.value
      opts.onComplete?.()
    },
  },
}))

const { useZoomStateMachine } = await import('@/LWD-views/WarehouseManager/floorplan/composables/useZoomStateMachine')
const { useFloorSearch } = await import('@/LWD-views/WarehouseManager/floorplan/composables/useFloorSearch')

describe('floor plan zoom state machine', () => {
  it('drills floor to section to rack and steps back one level at a time', async () => {
    const zoom = useZoomStateMachine()

    await zoom.zoomToSection('s1')
    expect(zoom.state).toMatchObject({ level: 'SECTION', activeSectionId: 's1', activeRackId: null, isTransitioning: false })

    await zoom.zoomToRack('r1')
    expect(zoom.state).toMatchObject({ level: 'RACK', activeSectionId: 's1', activeRackId: 'r1' })

    expect(await zoom.levelBack()).toBe('SECTION')
    expect(zoom.state.activeRackId).toBeNull()
    expect(await zoom.levelBack()).toBe('FLOOR')
    expect(zoom.state.activeSectionId).toBeNull()
    expect(await zoom.levelBack()).toBe('FLOOR')
  })

  it('resets pan and scale on a level change', async () => {
    const zoom = useZoomStateMachine()
    zoom.startPan({ clientX: 0, clientY: 0 })
    zoom.onPanMove({ clientX: 40, clientY: -10 })
    zoom.endPan()
    zoom.zoomIn()
    expect(zoom.canvasTransform.value).toBe('translate(40px, -10px) scale(1.12)')

    await zoom.zoomToFloor()
    expect(zoom.canvasTransform.value).toBe('translate(0px, 0px) scale(1)')
    expect(zoom.transitionStyle.value).toEqual({ opacity: 1, transition: 'none' })
  })

  it('ignores pan moves once the drag ends', () => {
    const zoom = useZoomStateMachine()
    zoom.startPan({ clientX: 10, clientY: 10 })
    zoom.endPan()
    zoom.onPanMove({ clientX: 99, clientY: 99 })
    expect([zoom.panX.value, zoom.panY.value]).toEqual([0, 0])
  })

  it('clamps button and wheel zoom, and wheel zoom keeps the point under the cursor fixed', () => {
    const zoom = useZoomStateMachine()
    for (let i = 0; i < 30; i++) zoom.zoomOut()
    expect(zoom.scale.value).toBe(0.2)
    for (let i = 0; i < 30; i++) zoom.zoomIn()
    expect(zoom.zoomPercent.value).toBe(400)

    zoom.zoomReset()
    const container = { getBoundingClientRect: () => ({ left: 100, top: 50 }) }
    const preventDefault = vi.fn()
    zoom.onWheel({ deltaY: -1, clientX: 300, clientY: 150, preventDefault }, container)
    expect(preventDefault).toHaveBeenCalled()
    expect(zoom.scale.value).toBeCloseTo(1.12)
    expect(zoom.panX.value).toBeCloseTo(-24)
    expect(zoom.panY.value).toBeCloseTo(-12)

    zoom.recenter()
    expect([zoom.panX.value, zoom.panY.value]).toEqual([0, 0])
  })
})

describe('floor plan search', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  function makeStore() {
    const sections = [
      { id: 's1', label: 'Cold Zone', floorId: 1 },
      { id: 's2', label: 'Bulk', floorId: 2 },
    ]
    const racks = [
      { id: 'r1', sectionId: 's1', label: 'R-01' },
      { id: 'r2', sectionId: 's2', label: 'R-02' },
    ]
    return reactive({
      products: [
        { name: 'Frozen Peas', sku: 'FZ-100', orderId: 'ORD-1', rackId: 'r1', cell: 3 },
        { name: 'Cement Bags', sku: 'CM-200', orderId: 'ORD-2', rackId: 'r2', cell: 0, rma: 'RMA-9' },
      ],
      rackMap: new Map(racks.map(r => [r.id, r])),
      sectionMap: new Map(sections.map(s => [s.id, s])),
    })
  }

  async function search(s, query) {
    s.searchQuery.value = query
    s.onSearch()
    await vi.advanceTimersByTimeAsync(200)
    return s.searchResults.value
  }

  it('matches name, SKU, order, RMA and section label, with the location attached', async () => {
    const s = useFloorSearch(makeStore(), useZoomStateMachine())

    expect((await search(s, 'peas')).map(r => r.product.sku)).toEqual(['FZ-100'])
    expect((await search(s, 'rma-9'))[0]).toMatchObject({ sectionLabel: 'Bulk', rackLabel: 'R-02', floorId: 2 })
    expect((await search(s, 'cold')).map(r => r.product.sku)).toEqual(['FZ-100'])
    expect((await search(s, 'ord')).length).toBe(2)
    expect(await search(s, 'nothing-like-this')).toEqual([])

    s.searchQuery.value = '   '
    s.onSearch()
    expect(s.searchResults.value).toEqual([])
  })

  it('drills down to the matching cell, switching floor first when needed', async () => {
    const zoom = useZoomStateMachine()
    const s = useFloorSearch(makeStore(), zoom)
    const [result] = await search(s, 'cement')
    const setFloor = vi.fn()

    const done = s.focusSearchResult(result, 1, setFloor)
    expect(setFloor).toHaveBeenCalledWith(2)
    expect(s.searchResults.value).toEqual([])
    expect(s.isDrillAnimating.value).toBe(true)
    await vi.advanceTimersByTimeAsync(0)
    expect(s.highlightedSectionIds.value).toEqual(['s2'])

    await vi.advanceTimersByTimeAsync(1200)
    expect(s.highlightedRackIds.value).toEqual(['r2'])
    expect(s.getHighlightProductsForSection('s2')).toHaveLength(1)
    expect(s.getHighlightProductsForRack('r2')).toHaveLength(1)

    await vi.advanceTimersByTimeAsync(1200)
    await done
    expect(zoom.state.level).toBe('RACK')
    expect(s.highlightedCellKeys.value).toEqual(['r2:0'])
    expect(s.isDrillAnimating.value).toBe(false)
  })

  it('cycles through results and clearing stops a drill-down midway', async () => {
    const zoom = useZoomStateMachine()
    const s = useFloorSearch(makeStore(), zoom)
    const results = await search(s, 'ord')
    const setFloor = vi.fn()

    s.focusSearchResult(results[0], 1, setFloor)
    await vi.advanceTimersByTimeAsync(0)
    s.nextResult(1, setFloor)
    expect(s.currentPathIdx.value).toBe(1)
    s.prevResult(1, setFloor)
    expect(s.currentPathIdx.value).toBe(0)

    s.clearSearchNav()
    await vi.advanceTimersByTimeAsync(5000)
    expect(s.searchQuery.value).toBe('')
    expect(s.searchPaths.value).toEqual([])
    expect(s.highlightedCellKeys.value).toEqual([])
    expect(zoom.state.level).toBe('FLOOR')
    expect(s.isDrillAnimating.value).toBe(false)

    s.nextResult(1, setFloor)
    s.prevResult(1, setFloor)
    expect(s.currentPathIdx.value).toBe(0)
  })
})
