import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { stubFetch } from '../helpers/fetchRouter'
import { useWarehouseFloorStore } from '@/stores/warehouseFloorStore'

const item = (id, category, extra = {}) => ({
  id,
  sku: `SKU-${id}`,
  name: `Item ${id}`,
  quantity_on_hand: 5,
  unit: 'boxes',
  category,
  ...extra,
})

describe('warehouse floor store', () => {
  beforeEach(() => setActivePinia(createPinia()))
  afterEach(() => vi.unstubAllGlobals())

  it('builds one category group, section and rack per inventory category, with every item in a cell', async () => {
    const router = stubFetch([
      [
        'GET',
        '/api/v1/inventory',
        { items: [item('a', 'Cargo'), item('b', 'Cargo'), item('c', 'Cold')], total: 3 },
      ],
    ])
    const store = useWarehouseFloorStore()

    await store.initializeFromAPI('tok', 'wh-1')

    expect(router.calls[0].url).toContain('warehouse_id=wh-1')
    expect(store.groups.map((g) => g.name).sort()).toEqual(['Cargo', 'Cold'])
    expect(store.sectionsByFloor(1)).toHaveLength(2)
    expect(store.products).toHaveLength(3)
    const cargo = store.groups.find((g) => g.name === 'Cargo')
    const cargoSection = store.sectionsByGroup(cargo.id)[0]
    expect(
      store
        .productsBySection(cargoSection.id)
        .map((p) => p.sku)
        .sort(),
    ).toEqual(['SKU-a', 'SKU-b'])
    const [first] = store.products
    expect(store.getCellProduct(first.rackId, first.cell)).toBe(first)
    expect(store.isLoading).toBe(false)
    expect(store.loadError).toBe('')
  })

  it('reports a load error instead of throwing when inventory cannot be fetched', async () => {
    stubFetch([['GET', '/api/v1/inventory', { status: 500, body: { detail: 'down' } }]])
    const store = useWarehouseFloorStore()

    await store.initializeFromAPI('tok')

    expect(store.loadError).toMatch(/Could not load inventory/)
    expect(store.isLoading).toBe(false)
  })

  it('gives every new section and rack its own id and label', () => {
    const store = useWarehouseFloorStore()
    const first = store.addSection(1)
    const second = store.addSection(1)
    expect(first).not.toBe(second)
    expect(store.sectionsByFloor(1).map((s) => s.label)).toEqual(['SEC-101', 'SEC-102'])

    store.addRack(first)
    expect(store.racksBySection(first)).toHaveLength(1)

    store.deleteSection(first)
    expect(store.sectionMap.get(first)).toBeUndefined()
    expect(store.racks.some((r) => r.sectionId === first)).toBe(false)
  })

  it('adds and removes floors and categories', () => {
    const store = useWarehouseFloorStore()
    const floorId = store.addFloor()
    expect(store.floors.map((f) => f.id)).toContain(floorId)
    store.renameFloor(floorId, 'Mezzanine')
    expect(store.floors.find((f) => f.id === floorId).label).toBe('Mezzanine')

    store.addGroup(floorId, { name: 'Fragile', color: '#f00', internalGap: 2, externalGap: 10 })
    const [group] = store.groupsByFloor(floorId)
    expect(store.getGroupName(group.id)).toBe('Fragile')
    store.updateGroup(group.id, { name: 'Glass' })
    expect(store.getGroupName(group.id)).toBe('Glass')
    store.deleteGroup(group.id)
    expect(store.groupsByFloor(floorId)).toEqual([])

    expect(store.deleteFloor(floorId)).toBeTruthy()
    expect(store.floors.map((f) => f.id)).not.toContain(floorId)
  })

  it('saves the layout to the warehouse and reloads it', async () => {
    let saved = null
    stubFetch([
      [
        'PUT',
        '/floor-plan',
        (body) => {
          saved = body.floor_plan_json
          return { ok: true }
        },
      ],
      ['GET', /\/api\/v1\/warehouses\/wh-1$/, () => ({ id: 'wh-1', floor_plan_json: saved })],
    ])
    const store = useWarehouseFloorStore()
    store.addSection(1)

    await store.saveFloorPlan('tok', 'wh-1')
    expect(store.isSaving).toBe(false)

    setActivePinia(createPinia())
    const fresh = useWarehouseFloorStore()
    await fresh.loadFloorPlan('tok', 'wh-1')
    expect(fresh.sectionsByFloor(1).map((s) => s.label)).toEqual(['SEC-101'])
  })
})
