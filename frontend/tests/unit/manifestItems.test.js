import { describe, expect, it } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import {
  buildLogFromOrderItems,
  fetchTripPackingItems,
  formatStatus,
  freshLog,
  isPackingItem,
  resolveDisplay,
} from '@/LWD-views/Dispatcher/manifestCenter/manifestItems'

describe('manifest packing items', () => {
  it('recognises packing items by SKU prefix or name', () => {
    expect(isPackingItem('PKG-TAPE', null)).toBe(true)
    expect(isPackingItem('INV-9', 'Bubble Wrap Roll')).toBe(true)
    expect(isPackingItem('INV-9', 'Sofa')).toBe(false)
    expect(isPackingItem(null, null)).toBe(false)
  })

  it('builds an asset log with sent quantities and nothing returned yet', () => {
    expect(buildLogFromOrderItems([{ sku: 'INV-1', name: 'Tape', quantity: 2 }])).toEqual([
      { name: 'Tape', icon: 'inventory_2', sku: 'INV-1', sentOut: 2, returned: 0 },
    ])
    expect(resolveDisplay(null, null).name).toBe('Item')
    expect(Array.isArray(freshLog())).toBe(true)
    expect(typeof formatStatus('IN_TRANSIT')).toBe('string')
  })

  it('loads only the packing items of a trip and sends the token', async () => {
    const router = stubFetch([
      [
        'GET',
        '/orders/o1/items',
        [
          { sku: 'PKG-CARTON', name: 'Carton', quantity: 4 },
          { sku: 'SOFA', name: 'Three-seat sofa', quantity: 1 },
        ],
      ],
    ])

    const items = await fetchTripPackingItems('o1', 'tok')

    expect(items.map((i) => i.sku)).toEqual(['PKG-CARTON'])
    expect(router.calls[0].headers).toEqual({ Authorization: 'Bearer tok' })
    expect(await fetchTripPackingItems('missing', null)).toEqual([])
  })
})
