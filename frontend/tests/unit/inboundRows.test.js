import { describe, expect, it } from 'vitest'
import {
  formatIssueStatus,
  getInboundDisplayStatus,
  getInboundStatusClass,
  inboundStatsFrom,
  isAsnInPickingFlow,
  issueStatusClass,
  toDockSlot,
  toInboundRow,
} from '@/LWD-views/WarehouseManager/inbound/inboundRows'

describe('inbound rows', () => {
  it('maps an inbound API shipment to a board row', () => {
    const row = toInboundRow(
      {
        order_id: 'abcdef12-0000',
        supplier_name: 'Mehta Home Retail',
        expected_qty: 12,
        status: 'InTransit',
        has_damage: 1,
        damage_count: 2,
        can_move_to_picking: false,
        total_amount: '4650',
        auto_debit_enabled: 1,
      },
      'hub-1',
    )
    expect(row).toMatchObject({
      id: 'ASN-ABCDEF',
      rawId: 'abcdef12-0000',
      warehouseId: 'hub-1',
      supplier: 'Mehta Home Retail',
      expected: 12,
      received: 0,
      eta: 'TBD',
      displayStatus: 'InTransit',
      damaged: true,
      damageCount: 2,
      canMoveToPicking: false,
      totalAmount: 4650,
      autoDebitEnabled: true,
    })
    expect(toInboundRow({ order_id: 'x', tracking_code: 'QC-1' }, 'h').status).toBe('Scheduled')
  })

  it('labels warehouse stages and keeps rows already in picking off the board', () => {
    expect(getInboundDisplayStatus('Arrived', 'awaiting_pick')).toBe('Ready for Picking')
    expect(getInboundDisplayStatus('Arrived', 'ON_HOLD')).toBe('Vendor Take-Back')
    expect(getInboundDisplayStatus('Arrived', null)).toBe('Arrived')
    expect(getInboundStatusClass('Unknown', null)).toContain('text-gray-500')
    expect(isAsnInPickingFlow({ warehouseSubstatus: 'packed' })).toBe(true)
    expect(isAsnInPickingFlow({ warehouseSubstatus: 'ON_HOLD' })).toBe(false)
  })

  it('names support ticket states and reads the stats block', () => {
    expect(formatIssueStatus('IN_PROGRESS')).toBe('Support Working')
    expect(formatIssueStatus(null)).toBe('Support Open')
    expect(issueStatusClass('weird')).toContain('text-blue-600')
    expect(inboundStatsFrom({ arrived_today: 3 })).toEqual({
      arrivedToday: 3,
      inTransit: 0,
      mismatchesFound: 0,
      damageReports: 0,
    })
    expect(toDockSlot({ status: 'Active' }).statusClass).toBe('bg-blue-500/20 text-blue-500')
  })
})
