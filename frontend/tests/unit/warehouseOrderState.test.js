import { beforeEach, describe, expect, it } from 'vitest'
import {
  getEffectiveWarehouseSubstatus,
  getWarehouseOrderUiState,
  isWarehouseOrderAccepted,
  patchWarehouseOrderUiState,
  readWarehouseOrderState,
  writeWarehouseOrderState,
} from '@/utils/warehouseOrderState'

beforeEach(() => {
  localStorage.clear()
})

describe('warehouse order UI state', () => {
  it('stores state per warehouse under its own key', () => {
    writeWarehouseOrderState('wh-1', { 'order-1': { accepted: true } })

    expect(localStorage.getItem('warehouse-order-state:wh-1')).toBe('{"order-1":{"accepted":true}}')
    expect(readWarehouseOrderState('wh-2')).toEqual({})
  })

  it('uses an "unassigned" bucket when no warehouse id is given', () => {
    writeWarehouseOrderState(null, { o: { accepted: true } })
    expect(localStorage.getItem('warehouse-order-state:unassigned')).not.toBeNull()
  })

  it('returns an empty object when stored JSON is corrupt', () => {
    localStorage.setItem('warehouse-order-state:wh-1', '{not json')
    expect(readWarehouseOrderState('wh-1')).toEqual({})
  })

  it('merges patches into the existing order entry', () => {
    patchWarehouseOrderUiState('wh-1', 'order-1', { accepted: true })
    const merged = patchWarehouseOrderUiState('wh-1', 'order-1', { warehouse_substatus: 'PICKING' })

    expect(merged).toEqual({ accepted: true, warehouse_substatus: 'PICKING' })
    expect(getWarehouseOrderUiState('wh-1', 'order-1')).toEqual(merged)
    expect(getWarehouseOrderUiState('wh-1', 'missing')).toEqual({})
  })
})

describe('getEffectiveWarehouseSubstatus', () => {
  it('prefers the locally patched substatus over the order field', () => {
    const order = { id: 'order-1', warehouse_substatus: 'AWAITING_PICK' }
    expect(getEffectiveWarehouseSubstatus(order, 'wh-1')).toBe('AWAITING_PICK')

    patchWarehouseOrderUiState('wh-1', 'order-1', { warehouse_substatus: 'PACKED' })
    expect(getEffectiveWarehouseSubstatus(order, 'wh-1')).toBe('PACKED')
  })

  it('returns null when neither source has a substatus', () => {
    expect(getEffectiveWarehouseSubstatus({ id: 'x' }, 'wh-1')).toBeNull()
    expect(getEffectiveWarehouseSubstatus(undefined, 'wh-1')).toBeNull()
  })
})

describe('isWarehouseOrderAccepted', () => {
  it('reflects the accepted flag of the stored entry', () => {
    const order = { id: 'order-9' }
    expect(isWarehouseOrderAccepted(order, 'wh-1')).toBe(false)
    patchWarehouseOrderUiState('wh-1', 'order-9', { accepted: 1 })
    expect(isWarehouseOrderAccepted(order, 'wh-1')).toBe(true)
  })
})
