import { describe, expect, it } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import * as api from '@/LWD-views/WarehouseManager/picking/pickingApi'

const HUB = 'hub-1'

describe('picking API calls', () => {
  it('loads orders with an optional search and returns null on failure', async () => {
    const router = stubFetch([['GET', '/api/v1/orders?', { items: [{ id: 'o1' }] }]])
    expect(await api.fetchOrders('t', ' QC 1 ')).toEqual([{ id: 'o1' }])
    expect(router.calls[0].url).toContain('&search=QC%201')
    expect(router.calls[0].headers.Authorization).toBe('Bearer t')

    stubFetch([])
    expect(await api.fetchOrders('t')).toBeNull()
  })

  it('falls back to the order items when no pick list can be generated', async () => {
    stubFetch([
      ['POST', '/inventory/pick-list/o1', { status: 400, body: { detail: 'no stock' } }],
      ['GET', '/api/v1/orders/o1', { items: [{ sku: 'SKU-1', name: 'Sofa', quantity: 2 }, {}] }],
    ])
    const items = await api.fetchPickListItems('t', 'o1')
    expect(items[0]).toMatchObject({
      sku: 'SKU-1',
      item_name: 'Sofa',
      required_quantity: 2,
      location_path: 'Location TBD',
    })
    expect(items[1]).toMatchObject({ sku: 'ITEM-2', scan_code: 'SCAN-2', required_quantity: 1 })

    stubFetch([['POST', '/inventory/pick-list/o2', { status: 400, body: { detail: 'no stock' } }]])
    await expect(api.fetchPickListItems('t', 'o2')).rejects.toThrow('no stock')
  })

  it('confirms a pick and reports the server error', async () => {
    const router = stubFetch([
      ['POST', '/operations/orders/o1/pick-item', { id: 'p1', is_complete: true }],
    ])
    expect(
      await api.confirmPickItem('t', HUB, 'o1', { sku: 'A', quantity_picked: 1 }),
    ).toMatchObject({ id: 'p1' })
    expect(router.calls[0].body).toEqual({ sku: 'A', quantity_picked: 1 })

    stubFetch([['POST', '/pick-item', { status: 409, body: { detail: 'Over pick' } }]])
    await expect(api.confirmPickItem('t', HUB, 'o1', {})).rejects.toThrow('Over pick')
  })

  it('reads prerequisites, treating a missing floor plan as unset and other errors as set', async () => {
    stubFetch([
      ['GET', '/api/v1/inventory?', { total: 12 }],
      ['GET', '/floor-plan', { status: 404, body: {} }],
    ])
    expect(await api.checkPrerequisites('t', HUB)).toEqual({
      inventoryCount: 12,
      floorPlanConfigured: false,
    })

    stubFetch([
      ['GET', '/api/v1/inventory?', { items: [{}, {}] }],
      ['GET', '/floor-plan', { status: 500, body: {} }],
    ])
    expect(await api.checkPrerequisites('t', HUB)).toEqual({
      inventoryCount: 2,
      floorPlanConfigured: true,
    })
  })

  it('creates a quality check once, or finds the existing one on a conflict', async () => {
    stubFetch([['POST', '/orders/o1/quality-check', { id: 'qc-1' }]])
    const check = { rawId: 'o1', checkId: null }
    expect(await api.ensureQualityCheckRecord('t', HUB, check)).toBe('qc-1')
    expect(await api.ensureQualityCheckRecord('t', HUB, check)).toBe('qc-1')

    stubFetch([
      ['POST', '/orders/o2/quality-check', { status: 409, body: {} }],
      ['GET', '/quality-checks?order_id=o2', { items: [{ id: 'qc-2' }] }],
    ])
    expect(await api.ensureQualityCheckRecord('t', HUB, { rawId: 'o2' })).toBe('qc-2')

    await expect(api.ensureQualityCheckRecord('t', null, { rawId: 'o3' })).rejects.toThrow(
      'Missing warehouse',
    )
  })

  it('saves check fields and marks the check verified when every box is ticked', async () => {
    const router = stubFetch([['PUT', '/quality-checks/qc-1', { id: 'qc-1', is_passed: false }]])
    const check = {
      checkId: 'qc-1',
      goodsCorrect: true,
      countCorrect: true,
      packagingOk: true,
      laborConfirmed: true,
      weightOk: true,
      labelAttached: true,
    }
    await api.persistQualityCheck('t', HUB, check)
    expect(router.calls[0].body).toMatchObject({ goods_correct: true, label_attached: true })
    expect(check).toMatchObject({ verified: true, isPassed: false })
  })

  it('maps packing stations and tells whether materials were issued', async () => {
    stubFetch([
      [
        'GET',
        '/packing-stations',
        { items: [{ id: 's1', station_number: 'P1', status: 'ACTIVE' }] },
      ],
      ['GET', '/api/v1/orders/o1/items', [{ quantity: 2 }]],
      [
        'GET',
        '/inventory/movements?reference_order_id=o1',
        { items: [{ movement_type: 'issue' }] },
      ],
      ['GET', '/api/v1/orders/o2/items', [{ quantity: 1 }]],
      ['GET', '/inventory/movements?reference_order_id=o2', { items: [] }],
    ])
    expect(await api.fetchPackingStations('t', HUB)).toEqual([
      expect.objectContaining({ id: 's1', name: 'P1', packer: 'Active', active: true }),
    ])
    expect(await api.packingMaterialsStatus('t', 'o1')).toBe('ok')
    expect(await api.packingMaterialsStatus('t', 'o2')).toBe('not-issued')
  })

  it('picks the transition endpoint for each wave status', () => {
    expect(api.waveTransition(HUB, { rawId: 'o1', status: 'AWAITING_PICK' }, 'l1')).toMatchObject({
      target: 'PICKING',
      body: JSON.stringify({ labourer_id: 'l1' }),
    })
    expect(api.waveTransition(HUB, { rawId: 'o1', status: 'PACKING' }).url).toContain(
      '/complete-packing',
    )
    expect(api.waveTransition(HUB, { rawId: 'o1', status: 'PACKED' })).toBeNull()
    expect(api.revertPickingUrl(HUB, 'o1')).toContain('/orders/o1/revert-picking')
  })
})
