import { ref } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useDamageReview } from '@/LWD-views/WarehouseManager/returnsWarehouse/useDamageReview'
import { useReturnGrading } from '@/LWD-views/WarehouseManager/returnsWarehouse/useReturnGrading'

const authStore = { authToken: 'tok' }

beforeEach(() => {
  vi.useFakeTimers()
  vi.spyOn(console, 'error').mockImplementation(() => {})
})
afterEach(() => vi.useRealTimers())

describe('damage review (flow 1)', () => {
  function setup() {
    const deps = { authStore, submittingReview: ref(false), toastMsg: ref('') }
    return { deps, ...useDamageReview(deps) }
  }

  it('loads the review queue and sends the assessment for a claim', async () => {
    const router = stubFetch([
      ['GET', '/damage-reports?status=Under%20Review', { items: [{ id: 'd1' }, { id: 'd2' }] }],
      ['POST', '/damage-reports/d1/review', {}],
    ])
    const r = setup()
    await r.fetchDamageReviewQueue()
    expect(r.damageReviewQueue.value.map((c) => c.id)).toEqual(['d1', 'd2'])

    r.selectDamageReport({ id: 'd1' })
    Object.assign(r.damageReviewForm.value, {
      severity: 'Major',
      genuineness: true,
      recommendedSettlement: 'Full Refund',
      remarks: 'Glass shattered',
    })
    await r.submitDamageReview()

    expect(router.last('POST').body).toEqual({
      damage_severity: 'Major',
      is_genuine: true,
      recommended_settlement: 'Full Refund',
      remarks: 'Glass shattered',
      new_status: 'Claims Reviewed',
    })
    expect(r.damageReviewQueue.value.map((c) => c.id)).toEqual(['d2'])
    expect(r.selectedDamageReport.value).toBeNull()
    expect(r.deps.toastMsg.value).toBe('Damage review submitted to Logistics Manager.')
  })

  it('keeps the claim selected when the review is refused', async () => {
    stubFetch([['POST', '/damage-reports/d1/review', { status: 500, body: {} }]])
    const r = setup()
    r.damageReviewQueue.value = [{ id: 'd1' }]
    r.selectDamageReport({ id: 'd1' })

    await r.submitDamageReview()

    expect(r.deps.toastMsg.value).toBe('Failed to submit damage review.')
    expect(r.damageReviewQueue.value).toHaveLength(1)
    expect(r.deps.submittingReview.value).toBe(false)
  })
})

describe('return grading (flow 2)', () => {
  function setup(overrides = {}) {
    const deps = {
      authStore,
      capturedPhoto: ref(null),
      completedItems: ref([]),
      conditionNotes: ref('Box dented'),
      disposition: ref('restock'),
      inboundReturns: ref([{ id: 'abcdef-1', tracking_code: 'QC-9' }]),
      inspectionGenuineness: ref(true),
      inspectionRecommendedOutcome: ref('Partial Refund'),
      inspectionRemarks: ref(''),
      itemCondition: ref('Minor Wear'),
      mapGradingToCompleted: (g) => ({ id: g.id, done: true }),
      pendingGradings: ref([]),
      rmaId: ref('RMA-QC-9'),
      selectedGradingId: ref(null),
      selectedOrderForReturn: ref({ id: 'abcdef-1' }),
      submitting: ref(false),
      toastMsg: ref(''),
      warehouseId: ref('hub-1'),
      ...overrides,
    }
    return { deps, ...useReturnGrading(deps) }
  }

  it('creates and completes a grading, then clears the form', async () => {
    const router = stubFetch([
      ['POST', /\/operations\/returns$/, { id: 'g1' }],
      ['POST', '/operations/returns/g1/complete', { id: 'g1' }],
    ])
    const r = setup()

    await r.submitReturn()

    expect(router.calls[0].body).toMatchObject({
      rma_code: 'RMA-QC-9',
      order_id: 'abcdef-1',
      item_condition: 'Minor Wear',
      disposition: 'restock',
      is_genuine: true,
      recommended_outcome: 'Partial Refund',
      inspection_remarks: null,
    })
    expect(r.deps.completedItems.value).toEqual([{ id: 'g1', done: true }])
    expect(r.deps.inboundReturns.value).toEqual([])
    expect(r.deps.toastMsg.value).toBe('Return RMA-QC-9 — Restocked')
    expect(r.deps.rmaId.value).toBe('')
  })

  it('updates an existing grading before completing it', async () => {
    const router = stubFetch([
      ['PUT', '/operations/returns/g7', {}],
      ['POST', '/operations/returns/g7/complete', { id: 'g7' }],
    ])
    const r = setup({ selectedGradingId: ref('g7'), pendingGradings: ref([{ id: 'g7' }]) })

    await r.submitReturn()

    expect(router.calls.map((c) => c.method)).toEqual(['PUT', 'POST'])
    expect(r.deps.pendingGradings.value).toEqual([])
  })

  it('refuses to grade without a warehouse', async () => {
    const router = stubFetch([])
    const r = setup({ warehouseId: ref(null) })

    await r.submitReturn()

    expect(router.calls).toHaveLength(0)
    expect(r.deps.toastMsg.value).toBe('No warehouse selected')
  })
})
