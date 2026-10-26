import { beforeEach, describe, expect, it } from 'vitest'
import {
  getEmoji,
  inventoryIdTokenFromSku,
  keywordsForSku,
  mergeIssuanceLogs,
  normalizeIssuanceLog,
  normalizeSku,
  readCachedIssuanceLogs,
  writeCachedIssuanceLogs,
} from '@/LWD-views/WarehouseManager/packingMaterials/materialRecords'

beforeEach(() => localStorage.clear())

describe('packing material records', () => {
  it('labels issue, reservation and automatic packing movements', () => {
    const issued = normalizeIssuanceLog({
      id: 1,
      movement_type: 'ISSUE',
      reference_order_tracking: 'QC-1',
      item_name: 'Bubble Wrap',
      quantity: '3',
      performed_by_name: 'Ravi',
      created_at: '2026-10-26T10:00:00Z',
    })
    expect(issued).toMatchObject({
      orderId: 'QC-1',
      qty: 3,
      issuedTo: 'Ravi',
      status: 'Issued',
      type: 'issued',
    })

    expect(normalizeIssuanceLog({ movement_type: 'RESERVED' })).toMatchObject({
      status: 'Reserved',
      type: 'reserved',
      orderId: 'N/A',
    })
    expect(normalizeIssuanceLog({ movement_type: 'PACK' })).toMatchObject({
      status: 'Auto-Packed',
      issuedTo: 'System (Packing)',
      type: 'issued',
    })
  })

  it('merges log groups without duplicates and caches them per hub', () => {
    const first = normalizeIssuanceLog({ id: 'a', created_at: '2026-10-25T10:00:00Z' })
    const second = normalizeIssuanceLog({ id: 'b', created_at: '2026-10-26T10:00:00Z' })
    const merged = mergeIssuanceLogs([first], [first, second])

    expect(merged.map((log) => log.id).sort()).toEqual(['a', 'b'])

    writeCachedIssuanceLogs('hub-1', merged)
    expect(
      readCachedIssuanceLogs('hub-1')
        .map((log) => log.id)
        .sort(),
    ).toEqual(['a', 'b'])
    expect(readCachedIssuanceLogs('hub-2')).toEqual([])
  })

  it('matches order SKUs to stock by id token and keywords', () => {
    expect(normalizeSku(' pkg-tape ')).toBe('PKG-TAPE')
    expect(inventoryIdTokenFromSku('PKG-INV-001')).toBe('INV-001')
    expect(keywordsForSku('PKG-BUBBLE-WRAP')).toEqual(expect.arrayContaining(['bubble', 'wrap']))
    expect(keywordsForSku('PKG-FOAM-SHEET')).toContain('foam sheet')
    expect(typeof getEmoji('Packing Tape', 'Consumables')).toBe('string')
  })
})
