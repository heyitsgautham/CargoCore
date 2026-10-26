import { describe, expect, it } from 'vitest'
import {
  decisionTitle,
  filterClaims,
  getRowAccentClass,
  getStatusHint,
  isInProgress,
  isResolved,
  needsManagerAction,
  returnStats,
} from '@/LWD-views/LogisticManager/reverseLogistics/returnClaims'

const claims = [
  {
    id: 'RMA-1',
    orderId: 'QC-1',
    customer: 'Asha',
    status: 'Approved',
    flow_type: 'photo_review',
    refundAmount: 500,
  },
  { id: 'RMA-2', orderId: 'QC-2', customer: 'Ravi', status: null, flow_type: 'photo_review' },
  {
    id: 'RMA-3',
    orderId: 'QC-3',
    customer: 'Meena',
    status: 'At Warehouse',
    flow_type: 'pickup_inspection',
  },
  {
    id: 'RMA-4',
    orderId: 'QC-4',
    customer: 'Imran',
    status: 'Pickup Requested',
    flow_type: 'pickup_inspection',
  },
  {
    id: 'RMA-5',
    orderId: 'QC-5',
    customer: 'Lata',
    status: 'Refunded',
    flow_type: 'pickup_inspection',
    refundAmount: 250,
  },
]

describe('returns board', () => {
  it('counts new, per-flow, awaiting-manager claims and refunded value', () => {
    expect(returnStats(claims)).toEqual({
      reported: 1,
      photoReview: 2,
      pickupInspection: 3,
      awaitingLM: 1,
      refundValue: 750,
    })
  })

  it('orders claims by workflow stage and treats a missing status as Reported', () => {
    expect(filterClaims(claims, 'All', '').map((c) => c.id)).toEqual([
      'RMA-2',
      'RMA-4',
      'RMA-3',
      'RMA-1',
      'RMA-5',
    ])
    expect(filterClaims(claims, 'Reported', '').map((c) => c.id)).toEqual(['RMA-2'])
    expect(filterClaims(claims, 'All', 'meena').map((c) => c.id)).toEqual(['RMA-3'])
  })

  it('sorts each claim into action required, in progress or resolved', () => {
    expect(claims.filter(needsManagerAction).map((c) => c.id)).toEqual(['RMA-2', 'RMA-4'])
    expect(claims.filter(isInProgress).map((c) => c.id)).toEqual(['RMA-3'])
    expect(claims.filter(isResolved).map((c) => c.id)).toEqual(['RMA-1', 'RMA-5'])
    expect(getRowAccentClass(claims[3])).toBe('border-l-orange-500')
    expect(getRowAccentClass(claims[0])).toBe('border-l-gray-400/30')
    expect(getRowAccentClass(claims[2])).toBe('border-l-blue-500/60')
  })

  it('titles the decision dialog by flow and stage', () => {
    expect(decisionTitle(null)).toBe('Review Claim')
    expect(decisionTitle(claims[1])).toBe('Damage Review Decision')
    expect(decisionTitle(claims[3])).toBe('Pickup Approval Decision')
    expect(decisionTitle({ flow_type: 'pickup_inspection', status: 'Physically Inspected' })).toBe(
      'Final Inspection Decision',
    )
    expect(getStatusHint('Reported', 'photo_review')).toBe('Awaiting LM — forward to WM')
  })
})
