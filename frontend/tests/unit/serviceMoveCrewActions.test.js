import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'
import { useMoveCrewActions } from '@/LWD-views/Dispatcher/serviceMoves/useMoveCrewActions'

function setup({ contacts = [], moves = [] } = {}) {
  const store = {
    dispatcherContacts: contacts,
    createChatForContact: vi.fn().mockResolvedValue({ id: 77 }),
    sendDispatchMessage: vi
      .fn()
      .mockResolvedValue({ messages: [{ id: 1, from: 'dispatch', text: 'On my way' }] }),
  }
  const deps = {
    authHeaders: () => ({ Authorization: 'Bearer t' }),
    completedToday: ref(0),
    crewChatMove: ref(null),
    crewMessages: ref([]),
    crewMsg: ref(''),
    crewThreadId: ref(null),
    moveMenu: ref('m1'),
    serviceMoves: ref(moves),
    showCrewChat: ref(false),
    showTrackingModal: ref(false),
    store,
    trackedDriver: ref(null),
    trackingLoading: ref(false),
    trackingMove: ref(null),
  }
  return { deps, ...useMoveCrewActions(deps) }
}

const move = () => ({ id: 'm1', orderId: 'o1', crew: [{ name: 'David', driverId: 'd1' }] })

describe('service move crew actions', () => {
  it('loads the driver position for tracking and toggles it off on a second click', async () => {
    stubFetch([['GET', '/tracking/orders/o1/driver', { latitude: 12.9, longitude: 77.6 }]])
    const m = move()
    const a = setup()

    await a.trackMove(m)
    expect(a.deps.trackedDriver.value).toEqual({ latitude: 12.9, longitude: 77.6 })
    expect(a.deps.showTrackingModal.value).toBe(true)

    await a.trackMove(m)
    expect(a.deps.showTrackingModal.value).toBe(false)
    expect(m.tracking).toBe(false)
  })

  it('opens the existing crew thread and sends through it', async () => {
    const a = setup({
      contacts: [
        {
          id: 'd1',
          name: 'David',
          threadId: 5,
          messages: [{ id: 9, sender: 'driver', text: 'Hi' }],
        },
      ],
    })

    await a.contactCrew(move())
    expect(a.deps.crewThreadId.value).toBe('5')
    expect(a.deps.crewMessages.value).toEqual([{ id: 9, from: 'driver', text: 'Hi' }])

    a.deps.crewMsg.value = ' On my way '
    await a.sendCrewMsg()
    expect(a.deps.store.sendDispatchMessage).toHaveBeenCalledWith('5', 'On my way')
    expect(a.deps.crewMessages.value).toEqual([{ id: 1, from: 'dispatch', text: 'On my way' }])
  })

  it('creates a thread for a contact without one, and keeps messages locally without a contact', async () => {
    const withContact = setup({ contacts: [{ id: 'd1', name: 'David', phone: '99' }] })
    await withContact.contactCrew(move())
    expect(withContact.deps.store.createChatForContact).toHaveBeenCalledWith('David', '99')
    expect(withContact.deps.crewThreadId.value).toBe('77')

    const noContact = setup()
    await noContact.contactCrew(move())
    noContact.deps.crewMsg.value = 'Hello'
    await noContact.sendCrewMsg()
    expect(noContact.deps.crewMessages.value.map((m) => m.text)).toEqual(['Hello'])
  })

  it('completes a move through the transition endpoint and removes it from the board', async () => {
    const router = stubFetch([['POST', '/orders/o1/transition', {}]])
    const m = move()
    const a = setup({ moves: [m] })

    await a.completeMove(m)

    expect(router.calls[0].body).toEqual({ next_status: 'DELIVERED' })
    expect(a.deps.completedToday.value).toBe(1)
    expect(a.deps.serviceMoves.value).toEqual([])
    expect(a.deps.moveMenu.value).toBeNull()
  })

  it('keeps a move on the board when cancelling fails', async () => {
    stubFetch([['POST', '/orders/o1/cancel', { status: 400, body: {} }]])
    const m = move()
    const a = setup({ moves: [m] })

    await a.cancelMove(m)

    expect(a.deps.serviceMoves.value).toEqual([m])
  })
})
