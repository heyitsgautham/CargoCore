import { describe, expect, it } from 'vitest'
import {
  getConditionClass,
  getDispositionBg,
  getDispositionColor,
  getDispositionIcon,
  getDispositionLabel,
} from '@/LWD-views/WarehouseManager/returnsWarehouse/returnLabels'

describe('warehouse return labels', () => {
  it('names and colours each disposition', () => {
    expect(getDispositionLabel('claims')).toBe('Sent to Claims')
    expect(getDispositionLabel('other')).toBe('other')
    expect([
      getDispositionBg('restock'),
      getDispositionColor('restock'),
      getDispositionIcon('restock'),
    ]).toEqual(['bg-green-500/20', 'text-green-500', 'check'])
    expect(getDispositionIcon('recycle')).toBe('recycling')
  })

  it('colours conditions from like new to beyond repair', () => {
    expect(getConditionClass('Like New')).toContain('green')
    expect(getConditionClass('Minor Wear')).toContain('yellow')
    expect(getConditionClass('Damaged')).toContain('orange')
    expect(getConditionClass('Destroyed')).toContain('red')
  })
})
