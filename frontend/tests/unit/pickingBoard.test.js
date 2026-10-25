import { beforeEach, describe, expect, it } from 'vitest'
import {
  buildOrderAssignments,
  buildPickWaves,
  buildQualityChecks,
  canConfirmPick,
  classifyPickingOrders,
  filterWaves,
  groupWavesByStatus,
  mergePickListWithProgress,
  pipelineCounts,
  prerequisiteWarnings,
  toDispatcherNotice,
  wavesForTab,
} from '@/LWD-views/WarehouseManager/picking/pickingBoard'
import { patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'

const HUB = 'hub-1'

function order(id, overrides = {}) {
  return {
    id,
    tracking_code: `QC-${id}`,
    warehouse_id: HUB,
    status: 'CONFIRMED',
    warehouse_substatus: 'AWAITING_PICK',
    packing_amount: 250,
    labor_count: 0,
    items: [{ quantity: 2 }, { quantity: 1 }],
    total_amount: 4650,
    ...overrides,
  }
}

beforeEach(() => localStorage.clear())

describe('classifyPickingOrders', () => {
  it('puts each order of the hub at its warehouse stage', () => {
    const stages = classifyPickingOrders(
      [
        order('a'),
        order('b', { warehouse_substatus: 'PICKING' }),
        order('c', { warehouse_substatus: 'PICKED' }),
        order('d', { warehouse_substatus: 'PACKING' }),
        order('e', { warehouse_substatus: 'QC_PASSED' }),
        order('f', { warehouse_id: 'other-hub' }),
      ],
      HUB,
    )

    expect(stages.awaitingPick.map((o) => o.id)).toEqual(['a'])
    expect(stages.picking.map((o) => o.id)).toEqual(['b'])
    expect(stages.picked.map((o) => o.id)).toEqual(['c'])
    expect(stages.packing.map((o) => o.id)).toEqual(['d'])
    expect(stages.packed.map((o) => o.id)).toEqual(['e'])
  })

  it('keeps direct transport and cancelled orders out of the pick flow', () => {
    const stages = classifyPickingOrders(
      [
        order('direct', { packing_amount: 0 }),
        order('cancelled', { status: 'CANCELLED', warehouse_substatus: 'PICKING' }),
        order('dispatcher', {
          status: 'ASSIGNED',
          packing_amount: 0,
          assigned_driver_id: 'drv',
          assigned_vehicle_id: null,
        }),
      ],
      HUB,
    )

    expect(stages.awaitingPick).toEqual([])
    expect(stages.picking).toEqual([])
    expect(stages.dispatcherAssigned.map((o) => o.id)).toEqual(['dispatcher'])
  })

  it('reads a stage the manager already moved locally before the backend catches up', () => {
    patchWarehouseOrderUiState(HUB, 'a', { warehouse_substatus: 'PICKING' })

    const stages = classifyPickingOrders([order('a')], HUB)

    expect(stages.awaitingPick).toEqual([])
    expect(stages.picking[0]).toMatchObject({ id: 'a', warehouse_substatus: 'PICKING' })
  })
})

describe('pick waves', () => {
  const labourers = [
    { id: 'l1', name: 'Ravi', assigned_order_id: 'a' },
    { id: 'l2', email: 'meena@example.com', assigned_order_id: 'a' },
    { id: 'l3', name: 'Free' },
  ]

  it('builds one card per active order with its labourers and undo state', () => {
    const stages = classifyPickingOrders(
      [order('a', { labor_count: 2 }), order('b', { warehouse_substatus: 'PICKING' })],
      HUB,
    )
    const waves = buildPickWaves(stages, {
      labourers,
      orderAssignments: buildOrderAssignments(labourers),
      undoHistory: [{ orderId: 'b' }],
    })

    expect(waves).toHaveLength(2)
    expect(waves[0]).toMatchObject({
      id: 'QC-a',
      items: 3,
      status: 'AWAITING_PICK',
      laborRequired: 2,
      assignedPicker: 'meena@example.com',
      canUndo: false,
    })
    expect(waves[0].laborAssigned.map((l) => l.name)).toEqual(['Ravi', 'meena@example.com'])
    expect(waves[1]).toMatchObject({ id: 'QC-b', status: 'PICKING', canUndo: true })
  })

  it('puts waves short of labourers on hold and lists every tab in board order', () => {
    const grouped = groupWavesByStatus([
      { id: 'w1', status: 'AWAITING_PICK', laborRequired: 2, laborAssigned: [{}] },
      { id: 'w2', status: 'AWAITING_PICK', laborRequired: 1, laborAssigned: [{}] },
      { id: 'w3', status: 'PACKING', laborRequired: 0 },
      { id: 'w4', status: 'PICKING', laborRequired: 3, laborAssigned: [] },
    ])

    expect(grouped.ON_HOLD.map((w) => [w.id, w.status])).toEqual([['w1', 'ON_HOLD']])
    expect(grouped.AWAITING_PICK.map((w) => w.id)).toEqual(['w2'])
    expect(grouped.PICKING.map((w) => w.id)).toEqual(['w4'])
    expect(wavesForTab(grouped, 'ALL').map((w) => w.id)).toEqual(['w1', 'w2', 'w4', 'w3'])
    expect(wavesForTab(grouped, 'PACKING').map((w) => w.id)).toEqual(['w3'])
  })

  it('filters by search text, status and priority together', () => {
    const waves = [
      { id: 'QC-1', type: 'VENDOR', priority: 'EXPRESS', status: 'PICKING' },
      { id: 'QC-2', type: 'INDIVIDUAL', priority: 'STANDARD', status: 'PICKING' },
      { id: 'QC-3', type: 'INDIVIDUAL', priority: null, status: 'PACKING', assignedPicker: 'Ravi' },
    ]

    expect(filterWaves(waves, { search: ' ravi ' }).map((w) => w.id)).toEqual(['QC-3'])
    expect(filterWaves(waves, { statuses: ['PICKING'] }).map((w) => w.id)).toEqual(['QC-1', 'QC-2'])
    expect(filterWaves(waves, { priority: 'STANDARD' }).map((w) => w.id)).toEqual(['QC-2', 'QC-3'])
    expect(filterWaves(waves, { search: 'individual', statuses: ['PACKING'] })).toHaveLength(1)
  })
})

describe('pipeline and quality checks', () => {
  it('counts orders per pipeline step, with only packed-for orders as accepted', () => {
    const stages = classifyPickingOrders(
      [
        order('a'),
        order('b', { packing_amount: 0, status: 'CONFIRMED' }),
        order('c', { warehouse_substatus: 'PICKING' }),
        order('d', { warehouse_substatus: 'PICKED' }),
        order('e', { warehouse_substatus: 'PACKED' }),
        order('f', { warehouse_substatus: 'READY_FOR_DISPATCH' }),
      ],
      HUB,
    )

    expect(pipelineCounts(stages)).toEqual([1, 2, 0, 2, 1])
  })

  it('starts each packed order from its saved check and counts a pass as verified', () => {
    const packed = [order('e', { warehouse_substatus: 'PACKED' }), order('f')]
    const checks = buildQualityChecks(
      packed,
      [
        {
          id: 'qc-1',
          order_id: 'e',
          goods_correct: true,
          count_correct: true,
          packaging_verified: true,
          weight_verified: true,
          label_attached: true,
        },
      ],
      { e: { labourerId: 'l1' } },
    )

    expect(checks[0]).toMatchObject({
      orderId: 'QC-e',
      checkId: 'qc-1',
      laborConfirmed: true,
      verified: true,
      isPassed: false,
    })
    expect(checks[1]).toMatchObject({ checkId: null, verified: false, goodsCorrect: false })
  })
})

describe('pick list', () => {
  it('merges saved progress and treats later stages as fully picked', () => {
    const items = [
      { sku: 'A', required_quantity: 3 },
      { sku: 'B', quantity: 2 },
    ]

    const picking = mergePickListWithProgress(
      items,
      [{ sku: 'A', quantity_picked: 5, is_complete: true, picker_name: 'Ravi' }],
      'PICKING',
    )
    expect(picking[0]).toMatchObject({ quantity_picked: 3, is_complete: true, picker_name: 'Ravi' })
    expect(picking[1]).toMatchObject({
      quantity_required: 2,
      quantity_picked: 0,
      is_complete: false,
    })

    const packed = mergePickListWithProgress(items, [], 'PACKING')
    expect(packed.map((item) => [item.quantity_picked, item.is_complete])).toEqual([
      [3, true],
      [2, true],
    ])
  })

  it('confirms a row only while picking and while quantity remains', () => {
    const item = { quantity_required: 2, quantity_picked: 1 }

    expect(canConfirmPick({ status: 'PICKING' }, item)).toBe(true)
    expect(canConfirmPick({ status: 'PICKED' }, item)).toBe(false)
    expect(canConfirmPick({ status: 'PICKING' }, { ...item, syncing: true })).toBe(false)
    expect(canConfirmPick({ status: 'PICKING' }, { ...item, quantity_picked: 2 })).toBe(false)
  })
})

describe('prerequisites and notices', () => {
  it('warns about stock and floor plan only when house-shift orders are waiting', () => {
    expect(
      prerequisiteWarnings({
        hasHouseShiftOrders: false,
        inventoryCount: 0,
        floorPlanConfigured: false,
        labourerCount: 2,
      }),
    ).toEqual([])
    expect(
      prerequisiteWarnings({
        hasHouseShiftOrders: true,
        inventoryCount: 0,
        floorPlanConfigured: false,
        labourerCount: 0,
      }),
    ).toHaveLength(3)
  })

  it('describes a dispatcher-assigned order with a short id when it has no tracking code', () => {
    expect(
      toDispatcherNotice({ id: 'abcdef123456', assigned_driver_name: null, total_amount: 0 }),
    ).toEqual({
      id: 'ABCDEF12',
      rawId: 'abcdef123456',
      driverName: 'a driver',
      pickupAddr: '',
      value: 0,
    })
  })
})
