import { reactive, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useCreateServiceMove } from '@/LWD-views/Dispatcher/serviceMoves/useCreateServiceMove'

function setup(overrides = {}) {
  const deps = {
    authHeaders: () => ({ Authorization: 'Bearer t' }),
    buildServiceMoveMeta: () => 'SERVICE_MOVE_META::{}',
    buildServiceTimeBlock: () => '09:00 start · 4h block',
    closeNewMoveModal: vi.fn(),
    fetchServiceMoves: vi.fn(),
    formError: ref(''),
    formSuccess: ref(''),
    loading: ref(false),
    newMove: reactive({
      title: 'Office move',
      type: 'Office Shift',
      pickup: 'MG Road',
      pickupLat: 12.97,
      pickupLng: 77.59,
      delivery: 'Indiranagar',
      deliveryLat: 12.97,
      deliveryLng: 77.64,
      scheduledDate: '2026-10-27',
      scheduledTime: '09:00',
      driverId: 'd1',
      vehicleId: '',
      ...overrides,
    }),
    resetNewMoveForm: vi.fn(),
    selectedVehicleOption: ref({ code: 'TRK-1' }),
    toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
  }
  return { deps, ...useCreateServiceMove(deps) }
}

let router

beforeEach(() => {
  router = stubFetch([
    ['POST', /\/api\/v1\/orders$/, { id: 'o1' }],
    ['POST', '/orders/o1/assign', { ok: true }],
  ])
})

describe('creating a service move', () => {
  it('posts the order with its meta and time block, then assigns the driver', async () => {
    const { deps, createServiceMove } = setup()

    await createServiceMove()

    expect(router.calls[0].body).toMatchObject({
      order_type: 'SERVICE_MOVE',
      cargo_type: 'Office Shift',
      pickup_addr: 'MG Road',
      delivery_addr: 'Indiranagar',
      vehicle_type: 'TRK-1',
      scheduled_at: '2026-10-27T09:00:00',
      service_time_block: '09:00 start · 4h block',
    })
    expect(router.calls[1].body).toEqual({ driver_id: 'd1', vehicle_id: null })
    expect(deps.toast.success).toHaveBeenCalled()
    expect(deps.resetNewMoveForm).toHaveBeenCalled()
    expect(deps.loading.value).toBe(false)
  })

  it('does nothing until title, pickup and delivery are set', async () => {
    const { createServiceMove } = setup({ delivery: '' })
    await createServiceMove()
    expect(router.calls).toHaveLength(0)
  })

  it('warns when the move is created but the assignment fails', async () => {
    router = stubFetch([
      ['POST', /\/api\/v1\/orders$/, { id: 'o1' }],
      ['POST', '/orders/o1/assign', { status: 409, body: { detail: 'Driver busy' } }],
    ])
    const { deps, createServiceMove } = setup()

    await createServiceMove()

    expect(deps.toast.warning).toHaveBeenCalledWith('Driver busy')
    expect(deps.closeNewMoveModal).toHaveBeenCalled()
  })

  it('shows the API error when the order is refused', async () => {
    router = stubFetch([
      ['POST', /\/api\/v1\/orders$/, { status: 422, body: { detail: 'Bad pickup' } }],
    ])
    const { deps, createServiceMove } = setup({ driverId: '' })

    await createServiceMove()

    expect(deps.formError.value).toBe('Bad pickup')
    expect(deps.toast.error).toHaveBeenCalledWith('Bad pickup')
    expect(deps.loading.value).toBe(false)
  })
})
