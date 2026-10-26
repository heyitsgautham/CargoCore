import { reactive, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useInboundIssues } from '@/LWD-views/WarehouseManager/inbound/useInboundIssues'

function setup() {
  const deps = {
    asns: ref([{ id: 'ASN-1', rawId: 'o1', warehouseId: 'hub-1' }]),
    authHeaders: () => ({ Authorization: 'Bearer t' }),
    authStore: { currentUser: { warehouse_id: 'hub-1' } },
    damageForm: reactive({ asnId: 'ASN-1', count: 0, description: '', hasPhoto: false }),
    damagePhoto: ref(null),
    fetchInboundShipments: vi.fn(),
    isCameraOpen: ref(false),
    mismatchForm: reactive({
      asnId: 'ASN-1',
      type: 'Quantity difference',
      details: '2 boxes short',
    }),
    showDamageModal: ref(true),
    showMismatchModal: ref(true),
    showToast: vi.fn(),
  }
  return { deps, ...useInboundIssues(deps) }
}

beforeEach(() => vi.spyOn(console, 'error').mockImplementation(() => {}))

describe('inbound issues', () => {
  it('flags a mismatch on the selected ASN and reloads the board', async () => {
    const router = stubFetch([['POST', '/operations/orders/o1/report-mismatch', {}]])
    const r = setup()

    await r.submitMismatch()

    expect(router.calls[0].url).toContain('/warehouses/hub-1/')
    expect(router.calls[0].body).toEqual({
      mismatch_type: 'Quantity difference',
      details: '2 boxes short',
    })
    expect(r.deps.showMismatchModal.value).toBe(false)
    expect(r.deps.showToast).toHaveBeenCalledWith('Mismatch flagged for ASN-1')
    expect(r.deps.fetchInboundShipments).toHaveBeenCalled()
  })

  it('asks for a count and a description before reporting damage', async () => {
    const router = stubFetch([['POST', '/report-damage', {}]])
    const r = setup()

    await r.submitDamage()
    expect(r.deps.showToast).toHaveBeenLastCalledWith('Enter damaged item count')
    r.deps.damageForm.count = 2
    await r.submitDamage()
    expect(r.deps.showToast).toHaveBeenLastCalledWith('Enter damage description')
    expect(router.calls).toHaveLength(0)
  })

  it('reports damage with the captured photo and resets the form', async () => {
    const router = stubFetch([['POST', '/operations/orders/o1/report-damage', {}]])
    const r = setup()
    r.openDamageCamera()
    expect(r.deps.isCameraOpen.value).toBe(true)
    r.handlePhotoCapture({ preview: 'data:image/jpeg;base64,AAA' })
    r.deps.damageForm.count = 2
    r.deps.damageForm.description = '  Torn wrap  '

    await r.submitDamage()

    expect(router.calls[0].body).toEqual({
      damaged_count: 2,
      description: 'Torn wrap',
      photo_url: 'data:image/jpeg;base64,AAA',
    })
    expect(r.deps.damageForm).toMatchObject({ count: 0, description: '', hasPhoto: false })
    expect(r.deps.damagePhoto.value).toBeNull()
  })

  it('shows the server error and keeps the dialog open', async () => {
    stubFetch([['POST', '/report-mismatch', { status: 409, body: { detail: 'Already reported' } }]])
    const r = setup()

    await r.submitMismatch()

    expect(r.deps.showToast).toHaveBeenCalledWith('Already reported')
    expect(r.deps.showMismatchModal.value).toBe(true)
  })

  it('refuses an unknown ASN', async () => {
    const r = setup()
    r.deps.mismatchForm.asnId = 'ASN-404'
    await r.submitMismatch()
    expect(r.deps.showToast).toHaveBeenCalledWith('Select a valid ASN first')
  })
})
