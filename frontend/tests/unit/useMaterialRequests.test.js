import { reactive, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useMaterialRequests } from '@/LWD-views/WarehouseManager/inventory/useMaterialRequests'

function setup() {
  const deps = {
    API_BASE: 'http://api',
    addForm: reactive({ sku: '', name: '', category: '', stock: 5, weight: 1, zone: 'B' }),
    customCategories: ref([]),
    persistCustomCategories: vi.fn(),
    showAddModal: ref(false),
    toastMsg: ref(''),
  }
  return { deps, ...useMaterialRequests(deps) }
}

let router

beforeEach(() => {
  localStorage.setItem('auth_token', 'tok')
  router = stubFetch([
    [
      'GET',
      '/inventory/material-requests',
      {
        items: [
          { id: 1, material_name: 'Foam Sheet', status: 'APPROVED' },
          { id: 2, material_name: 'Pallet Wrap', status: 'PENDING' },
          { id: 3, material_name: 'Ice Packs', status: 'REJECTED' },
        ],
      },
    ],
    ['POST', '/inventory/material-requests', { id: 4 }],
  ])
})

describe('material requests', () => {
  it('splits requests by status', async () => {
    const r = setup()
    await r.fetchMyMaterialRequests()
    expect(r.approvedMaterials.value.map((m) => m.id)).toEqual([1])
    expect(r.pendingMaterials.value.map((m) => m.id)).toEqual([2])
    expect(r.rejectedMaterials.value.map((m) => m.id)).toEqual([3])
  })

  it('submits a request and resets the form', async () => {
    const r = setup()
    Object.assign(r.materialRequestForm, {
      name: 'Bubble Wrap XL',
      unit: 'roll',
      reason: 'Fragile orders',
    })
    r.showRequestMaterialModal.value = true

    await r.submitMaterialRequest()

    expect(router.last('POST').body).toEqual({
      material_name: 'Bubble Wrap XL',
      unit: 'roll',
      suggested_rate: null,
      reason: 'Fragile orders',
    })
    expect(r.materialRequestForm.name).toBe('')
    expect(r.showRequestMaterialModal.value).toBe(false)
    expect(r.deps.toastMsg.value).toBe('Material request submitted!')
  })

  it('pre-fills the add stock form from an approved request', () => {
    const r = setup()
    r.addApprovedMaterial({ material_name: 'Foam Sheet Large' })

    expect(r.deps.addForm).toMatchObject({
      sku: 'FOAM-SHEET',
      name: 'Foam Sheet Large',
      category: 'Packing Materials',
      stock: 0,
      zone: 'A',
    })
    expect(r.deps.customCategories.value).toEqual(['Packing Materials'])
    expect(r.deps.persistCustomCategories).toHaveBeenCalledOnce()
    expect(r.deps.showAddModal.value).toBe(true)
  })
})
