import { describe, expect, it } from 'vitest'
import {
  buildAssignmentMeta,
  buildDisplayStatus,
  formatOrderDisplayId,
  getInitials,
  mapStatusClass,
} from '@/LWD-views/WarehouseManager/labor/labourerStatus'

describe('labourer status on the labour board', () => {
  it('derives the board status from activity and assignment', () => {
    expect(buildDisplayStatus({ is_active: false })).toBe('Off Duty')
    expect(buildDisplayStatus({ is_active: true, status: 'OFF_DUTY' })).toBe('Off Duty')
    expect(buildDisplayStatus({ is_active: true })).toBe('In Warehouse')
    expect(
      buildDisplayStatus({
        is_active: true,
        assigned_order_id: 'o1',
        assigned_order_substatus: 'PICKING',
      }),
    ).toBe('Warehouse Order')
    expect(
      buildDisplayStatus({ is_active: true, assigned_order_id: 'o1', status: 'ON_FIELD' }),
    ).toBe('With Driver')
    expect(buildDisplayStatus({ is_active: true, assigned_order_id: 'o1' })).toBe('Service Move')
  })

  it('describes the current assignment', () => {
    expect(buildAssignmentMeta({ current_task: 'Sorting' })).toEqual({
      task: 'Sorting',
      assignmentHint: '',
      orderScope: '',
    })
    expect(
      buildAssignmentMeta({ assigned_order_id: 'o1', assigned_order_substatus: 'PACKING' }),
    ).toMatchObject({
      assignmentHint: 'Warehouse pick/pack assignment',
      orderScope: 'WM order',
    })
    expect(buildAssignmentMeta({ assigned_order_id: 'o1' }).task).toBe('Driver Move Assigned')
  })

  it('formats initials, order ids and status badges', () => {
    expect(getInitials('Ravi Kumar')).toBe('RK')
    expect(formatOrderDisplayId('o1', 'QC-DEMO103')).toBe('QC-DEMO103')
    expect(typeof formatOrderDisplayId('abcdef12-3456', null)).toBe('string')
    expect(mapStatusClass('Off Duty')).not.toBe(mapStatusClass('In Warehouse'))
  })
})
