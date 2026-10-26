import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive, ref } from 'vue'
import { mount } from '@vue/test-utils'
import {
  contentExtent,
  stepZoom,
  useCanvasZoom,
} from '@/LWD-views/WarehouseManager/floorplan/composables/useCanvasZoom'
import {
  categoriesStorageKey,
  useInventorySync,
} from '@/LWD-views/WarehouseManager/floorplan/composables/useInventorySync'

describe('floor plan canvas sizing', () => {
  it('measures the furthest section, rack or cell grid at each zoom level', () => {
    const sections = [{ x: 0, y: 0, w: 300, h: 200 }, { x: 900, y: 50, w: 400, h: 1500 }]
    expect(contentExtent('FLOOR', sections, [], null)).toEqual({ right: 1470, bottom: 1800 })

    const racks = [{ x: 10, y: 20, w: 100, h: 60 }]
    expect(contentExtent('SECTION', [], racks, null)).toEqual({ right: 280, bottom: 330 })

    expect(contentExtent('RACK', [], [], { rows: 2, cols: 3 })).toEqual({ right: 598, bottom: 474 })
    expect(contentExtent('RACK', [], [], null)).toEqual({ right: 170, bottom: 250 })
  })

  it('zooms in quarter steps between 50% and 300%', () => {
    expect(stepZoom(1, 1)).toBe(1.25)
    expect(stepZoom(3, 1)).toBe(3)
    expect(stepZoom(0.5, -1)).toBe(0.5)
    expect(stepZoom(1, -1)).toBe(0.75)
  })

  it('grows the canvas past the base size when content overflows it, and recenters', () => {
    const zoom = reactive({ state: { level: 'FLOOR' } })
    const currentSections = ref([{ x: 2500, y: 0, w: 200, h: 100 }])
    const scrollTo = vi.fn()
    const canvas = useCanvasZoom({
      zoom,
      currentSections,
      activeRacks: ref([]),
      activeRack: ref(null),
      canvasRef: ref({ scrollTo }),
    })

    expect(canvas.canvasWidth.value).toBe(2870)
    expect(canvas.canvasHeight.value).toBe(1400)

    canvas.zoomCanvas(1)
    expect(canvas.canvasZoomPercent.value).toBe(125)
    expect(canvas.canvasHeight.value).toBe(1750)

    canvas.recenterCanvas()
    expect(canvas.canvasZoomPercent.value).toBe(100)
    expect(scrollTo).toHaveBeenCalledWith({ left: 0, top: 0, behavior: 'smooth' })
  })
})

describe('floor plan inventory sync', () => {
  afterEach(() => window.localStorage.clear())

  function setup({ warehouseId = 'wh-1', groups = [] } = {}) {
    const store = {
      floors: [{ id: 1 }],
      presetColors: ['#111111', '#222222'],
      groupsByFloor: vi.fn(() => groups),
      addGroup: vi.fn(),
      syncInventoryToFloorPlan: vi.fn(async () => {}),
    }
    const authStore = { authToken: 'tok', currentWarehouse: warehouseId ? { id: warehouseId } : null, currentUser: null }
    let sync
    const wrapper = mount(defineComponent({
      setup() {
        sync = useInventorySync({ store, authStore, activeFloor: ref(1) })
        return () => null
      },
    }))
    return { store, sync, wrapper }
  }

  it('adds custom inventory categories as floor groups, skipping names already on the floor', () => {
    window.localStorage.setItem(categoriesStorageKey('wh-1'), JSON.stringify(['Cold Storage', ' Bulk ', '', 7]))
    const { store, sync } = setup({ groups: [{ name: 'bulk' }] })

    sync.syncInventoryCategoriesToFloor()

    expect(store.addGroup).toHaveBeenCalledTimes(1)
    expect(store.addGroup).toHaveBeenCalledWith(1, { name: 'Cold Storage', color: '#111111', internalGap: 2, externalGap: 10 })
  })

  it('ignores a corrupt category list', () => {
    window.localStorage.setItem(categoriesStorageKey('wh-1'), '{not json')
    const { store, sync } = setup()
    sync.syncInventoryCategoriesToFloor()
    expect(store.addGroup).not.toHaveBeenCalled()
  })

  it('re-syncs on inventory events for this warehouse only, and stops listening on unmount', async () => {
    const { store, wrapper } = setup()

    window.dispatchEvent(new CustomEvent('warehouse-inventory-updated', { detail: { warehouseId: 'wh-2' } }))
    await Promise.resolve()
    expect(store.syncInventoryToFloorPlan).not.toHaveBeenCalled()

    window.dispatchEvent(new CustomEvent('warehouse-inventory-updated', { detail: { warehouseId: 'wh-1' } }))
    await Promise.resolve()
    expect(store.syncInventoryToFloorPlan).toHaveBeenCalledWith('tok', 'wh-1')

    wrapper.unmount()
    window.dispatchEvent(new CustomEvent('warehouse-inventory-updated', { detail: { warehouseId: 'wh-1' } }))
    await Promise.resolve()
    expect(store.syncInventoryToFloorPlan).toHaveBeenCalledTimes(1)
  })
})
