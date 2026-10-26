import { nextTick, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

const openSlipWithData = vi.fn()
vi.mock('@/composables/useSlipPrinter', () => ({ useSlipPrinter: () => ({ openSlipWithData }) }))

const { usePickList } = await import('@/LWD-views/WarehouseManager/picking/usePickList')

function setup() {
  const deps = {
    token: () => 't',
    getWarehouseId: () => 'hub-1',
    flashAction: vi.fn(),
    openScanner: vi.fn(),
    lastGlobalScan: ref(null),
    runWaveAction: vi.fn().mockResolvedValue(true),
  }
  return { deps, ...usePickList(deps) }
}

let router

beforeEach(() => {
  openSlipWithData.mockClear()
  vi.spyOn(console, 'error').mockImplementation(() => {})
  router = stubFetch([
    [
      'POST',
      '/inventory/pick-list/o1',
      { items: [{ sku: 'A', scan_code: 'SCAN-A', required_quantity: 2, location_path: 'Z1-A1' }] },
    ],
    [
      'GET',
      '/orders/o1/pick-progress',
      { items: [], is_complete: true, picked_items: 1, total_items: 1 },
    ],
    [
      'POST',
      '/orders/o1/pick-item',
      {
        id: 'p1',
        quantity_required: 2,
        quantity_picked: 2,
        is_complete: true,
        picker_name: 'Ravi',
      },
    ],
  ])
})

describe('pick list dialog', () => {
  it('opens a wave and keeps Proceed disabled until every item is picked', async () => {
    const p = setup()
    await p.openPickList({ id: 'QC-1', rawId: 'o1', status: 'PICKING' })

    expect(p.showPickListModal.value).toBe(true)
    expect(p.pickListItems.value[0]).toMatchObject({
      sku: 'A',
      quantity_picked: 0,
      is_complete: false,
    })
    expect(p.pickListActionDisabled.value).toBe(true)

    await p.toggleItemPicked(p.pickListItems.value[0])
    expect(router.last('POST').body).toEqual({
      sku: 'A',
      quantity_picked: 2,
      location: 'Z1-A1',
      notes: null,
    })
    expect(p.pickListItems.value[0]).toMatchObject({ is_complete: true, picker_name: 'Ravi' })
    expect(p.pickListActionDisabled.value).toBe(false)
    expect(p.deps.flashAction).toHaveBeenCalledWith('A marked picked')
  })

  it('confirms an item when the scanned code matches and rejects a wrong code', async () => {
    const p = setup()
    await p.openPickList({ id: 'QC-1', rawId: 'o1', status: 'PICKING' })
    const item = p.pickListItems.value[0]

    p.requestItemScan(item)
    expect(p.deps.openScanner).toHaveBeenCalledWith('scan')
    p.deps.lastGlobalScan.value = 'WRONG'
    await nextTick()
    await vi.waitFor(() =>
      expect(p.deps.flashAction).toHaveBeenCalledWith('Scanned code "WRONG" does not match SCAN-A'),
    )

    p.requestItemScan(item)
    p.deps.lastGlobalScan.value = 'scan-a'
    await vi.waitFor(() => expect(p.deps.flashAction).toHaveBeenCalledWith('A scan confirmed'))
  })

  it('asks to start picking before confirming items on a waiting wave', async () => {
    const p = setup()
    await p.openPickList({ id: 'QC-1', rawId: 'o1', status: 'AWAITING_PICK' })

    p.requestItemScan(p.pickListItems.value[0])
    expect(p.deps.flashAction).toHaveBeenCalledWith('Start picking before confirming items')
  })

  it('completes the wave through the wave action and closes the dialog', async () => {
    const p = setup()
    await p.openPickList({ id: 'QC-1', rawId: 'o1', status: 'PICKING' })

    await p.completePickList()

    expect(p.deps.runWaveAction).toHaveBeenCalledWith(expect.objectContaining({ id: 'QC-1' }))
    expect(p.showPickListModal.value).toBe(false)
  })

  it('prints the list with a location on every row', async () => {
    const p = setup()
    await p.openPickList({ id: 'QC-1', rawId: 'o1', status: 'PICKING' })

    await p.printPickList()

    const [kind, payload] = openSlipWithData.mock.calls[0]
    expect(kind).toBe('digitalPickList')
    expect(payload.items[0].location_path).toBe('Z1-A1')
  })
})
