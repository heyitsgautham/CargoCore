import { beforeEach, describe, expect, it } from 'vitest'
import {
  asArray,
  asStringId,
  asWarehouseId,
  deriveReturnFlowType,
  financeScopeFor,
  mapReturnRecord,
  normalizeDriverLoginId,
  normalizeDriverPin,
  normalizeReturnStatus,
  purgeLegacyCredentialCache,
  roleApiValue,
  roleLabel,
} from '@/stores/logistic/mappers'

describe('id and scope helpers', () => {
  it('asArray passes arrays through and turns anything else into []', () => {
    expect(asArray([1])).toEqual([1])
    expect(asArray(null)).toEqual([])
    expect(asArray({ length: 1 })).toEqual([])
  })

  it('asStringId stringifies ids and uses the fallback for null', () => {
    expect(asStringId(42)).toBe('42')
    expect(asStringId(null)).toBe('all')
    expect(asStringId(undefined, '')).toBe('')
  })

  it('asWarehouseId treats "all" in any case as no warehouse', () => {
    expect(asWarehouseId('wh-1')).toBe('wh-1')
    expect(asWarehouseId('ALL')).toBeNull()
    expect(asWarehouseId(null)).toBeNull()
  })

  it('financeScopeFor collapses empty and "all" to "all"', () => {
    expect(financeScopeFor('wh-1')).toBe('wh-1')
    expect(financeScopeFor('all')).toBe('all')
    expect(financeScopeFor(undefined)).toBe('all')
  })
})

describe('return records', () => {
  it('renames the legacy "Inspected" status', () => {
    expect(normalizeReturnStatus('Inspected')).toBe('Physically Inspected')
    expect(normalizeReturnStatus('Collected')).toBe('Collected')
  })

  it('derives the flow type from status or warehouse grading fields', () => {
    expect(deriveReturnFlowType({ flow_type: 'custom' })).toBe('custom')
    expect(deriveReturnFlowType({ status: 'Under Review' })).toBe('photo_review')
    expect(deriveReturnFlowType({ status: 'Inspected' })).toBe('pickup_inspection')
    expect(deriveReturnFlowType({ status: 'Pending', wm_graded_at: '2026-04-01' })).toBe(
      'pickup_inspection',
    )
    expect(deriveReturnFlowType({ status: 'Pending' })).toBeNull()
  })

  it('maps a pickup inspection record and coerces money fields to numbers', () => {
    const record = mapReturnRecord({
      id: 9,
      hub_id: 'hub-2',
      order_id: 77,
      status: 'At Warehouse',
      condition: 'Dented',
      transport_charge_amount: '150.5',
      wm_is_genuine: false,
    })

    expect(record).toMatchObject({
      id: '9',
      hubId: 'hub-2',
      orderId: '77',
      flow_type: 'pickup_inspection',
      wmActualCondition: 'Dented',
      wmDamageSeverity: null,
      wmGenuineness: false,
      transportChargeAmount: 150.5,
      transportChargePendingAmount: 0,
      images: [],
      walletCredited: false,
      isUrgent: false,
    })
  })

  it('puts the condition in damage severity for photo reviews', () => {
    const record = mapReturnRecord({ id: 1, status: 'Under Review', condition: 'Severe' })

    expect(record.flow_type).toBe('photo_review')
    expect(record.wmDamageSeverity).toBe('Severe')
    expect(record.wmActualCondition).toBeNull()
    expect(record.wmGenuineness).toBeUndefined()
    expect(record.hubId).toBeNull()
    expect(record.orderId).toBe('')
  })
})

describe('roles', () => {
  it('labels backend role names for display', () => {
    expect(roleLabel('LOGISTIC_MANAGER')).toBe('Logistic Manager')
    expect(roleLabel('AI_SUPPORT')).toBe('Customer Support')
    expect(roleLabel('LABOURER')).toBe('LABOURER')
    expect(roleLabel('')).toBe('User')
  })

  it('turns display role names into API role values', () => {
    expect(roleApiValue('Warehouse Manager')).toBe('WAREHOUSE_MANAGER')
    expect(roleApiValue('customer-support')).toBe('AI_AGENT')
    expect(roleApiValue(undefined)).toBe('DRIVER')
  })
})

describe('driver credentials', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('uses the given login id or falls back to the email prefix', () => {
    expect(normalizeDriverLoginId('  drv01 ')).toBe('drv01')
    expect(normalizeDriverLoginId('', 'ravi.k@cargo.test')).toBe('ravi.k')
    expect(normalizeDriverLoginId(null)).toBe('')
  })

  it('keeps a four digit PIN and replaces anything else with 1234', () => {
    expect(normalizeDriverPin(' 0420 ')).toBe('0420')
    expect(normalizeDriverPin('12345')).toBe('1234')
    expect(normalizeDriverPin('abcd')).toBe('1234')
  })

  it('deletes the plain-text credential store an older build left behind', () => {
    localStorage.setItem(
      'logistic_manager_created_credentials',
      '{"a@x.com":{"password":"secret"}}',
    )
    localStorage.setItem('theme', 'dark')

    purgeLegacyCredentialCache()

    expect(localStorage.getItem('logistic_manager_created_credentials')).toBeNull()
    expect(localStorage.getItem('theme')).toBe('dark')
  })
})
