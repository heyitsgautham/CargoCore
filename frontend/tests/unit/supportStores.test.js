import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/utils/aiApi', () => ({
  fetchEscalationCenter: vi.fn(),
  resolveEscalationCenter: vi.fn(),
  fetchTickets: vi.fn(),
  createTicket: vi.fn(),
  updateTicket: vi.fn(),
  replyTicket: vi.fn(),
  deleteTicket: vi.fn(),
  fetchSupportRefundCases: vi.fn(),
  flagRefundCaseUrgent: vi.fn(),
  fetchCustomerHistory: vi.fn(),
  fetchContactSubmissions: vi.fn(),
  submitPublicContactForm: vi.fn(),
  updateContactSubmission: vi.fn(),
  replyContactSubmission: vi.fn(),
  deleteContactSubmission: vi.fn(),
}))

const api = await import('@/utils/aiApi')
const { useEscalationStore } = await import('@/stores/escalationStore')
const { useTicketStore } = await import('@/stores/ticketStore')
const { useRefundStore } = await import('@/stores/refundStore')
const { useContactStore } = await import('@/stores/contactStore')

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('escalation store', () => {
  it('loads escalations and splits them by status', async () => {
    api.fetchEscalationCenter.mockResolvedValue({
      escalations: [
        { id: 1, status: 'OPEN' },
        { id: 2, status: 'RESOLVED' },
        { id: 3, status: 'OPEN' },
      ],
      open_count: 2,
      resolved_count: 1,
    })
    const store = useEscalationStore()

    await store.load('OPEN')

    expect(api.fetchEscalationCenter).toHaveBeenCalledWith('OPEN')
    expect(store.openEscalations.map((e) => e.id)).toEqual([1, 3])
    expect(store.resolvedEscalations.map((e) => e.id)).toEqual([2])
    expect(store.loading).toBe(false)
  })

  it('records the error message and rethrows when loading fails', async () => {
    api.fetchEscalationCenter.mockRejectedValue(new Error('boom'))
    const store = useEscalationStore()

    await expect(store.load()).rejects.toThrow('boom')
    expect(store.error).toBe('boom')
    expect(store.loading).toBe(false)
  })

  it('marks a resolved escalation and moves the counters', async () => {
    api.fetchEscalationCenter.mockResolvedValue({
      escalations: [{ id: 'e1', status: 'OPEN' }],
      open_count: 1,
      resolved_count: 0,
    })
    api.resolveEscalationCenter.mockResolvedValue({})
    const store = useEscalationStore()
    await store.load()

    await store.resolve('e1')

    expect(store.escalations[0].status).toBe('RESOLVED')
    expect(store.escalations[0].resolved_at).toBeTruthy()
    expect(store.openCount).toBe(0)
    expect(store.resolvedCount).toBe(1)
  })

  it('leaves counters alone when the escalation is not in the list', async () => {
    api.resolveEscalationCenter.mockResolvedValue({})
    const store = useEscalationStore()

    await store.resolve('missing')

    expect(store.openCount).toBe(0)
    expect(store.resolvedCount).toBe(0)
  })
})

describe('ticket store', () => {
  const tickets = [
    { id: 't1', status: 'new', priority: 'urgent' },
    { id: 't2', status: 'in_progress', priority: 'low' },
    { id: 't3', status: 'resolved', priority: 'urgent' },
  ]

  it('loads once and computes the dashboard stats', async () => {
    api.fetchTickets.mockResolvedValue({ tickets, agents: [{ id: 'a1' }] })
    const store = useTicketStore()

    await store.load()
    await store.load()

    expect(api.fetchTickets).toHaveBeenCalledTimes(1)
    expect(store.stats).toEqual({ total: 3, new: 1, in_progress: 1, resolved: 1, urgent: 2 })
    expect(store.agents).toEqual([{ id: 'a1' }])
  })

  it('reloads when forced', async () => {
    api.fetchTickets.mockResolvedValue({ tickets: [] })
    const store = useTicketStore()

    await store.load()
    await store.load(true)

    expect(api.fetchTickets).toHaveBeenCalledTimes(2)
  })

  it('puts new tickets first and replaces updated ones in place', async () => {
    api.fetchTickets.mockResolvedValue({ tickets: [...tickets] })
    api.createTicket.mockResolvedValue({ id: 't4', status: 'new' })
    api.updateTicket.mockResolvedValue({ id: 't2', status: 'resolved' })
    api.replyTicket.mockResolvedValue({ id: 't9', status: 'in_progress' })
    const store = useTicketStore()
    await store.load()

    await store.create({ subject: 'x' })
    await store.update('t2', { status: 'resolved' })
    await store.reply('t9', 'hello')

    expect(store.tickets.map((t) => t.id)).toEqual(['t9', 't4', 't1', 't2', 't3'])
    expect(store.tickets.find((t) => t.id === 't2').status).toBe('resolved')
  })

  it('drops a ticket after the backend deletes it', async () => {
    api.fetchTickets.mockResolvedValue({ tickets: [...tickets] })
    api.deleteTicket.mockResolvedValue(null)
    const store = useTicketStore()
    await store.load()

    await store.remove('t1')

    expect(api.deleteTicket).toHaveBeenCalledWith('t1')
    expect(store.tickets.map((t) => t.id)).toEqual(['t2', 't3'])
  })
})

describe('refund store', () => {
  it('counts urgent cases and chargeback risks', async () => {
    api.fetchSupportRefundCases.mockResolvedValue({
      cases: [
        { id: 1, status: 'Rejected', sentiment: 'Negative', is_urgent: true },
        { id: 2, status: 'Rejected', sentiment: 'Neutral', is_urgent: false },
        { id: 3, status: 'Approved', sentiment: 'Negative', is_urgent: true },
      ],
      stats: { total_refunded_value: 1200 },
    })
    const store = useRefundStore()

    await store.load()

    expect(store.chargebackRiskCount).toBe(1)
    expect(store.urgentCount).toBe(2)
    expect(store.stats.total_refunded_value).toBe(1200)
  })

  it('replaces a case after flagging it urgent and passes null for a blank reason', async () => {
    api.fetchSupportRefundCases.mockResolvedValue({ cases: [{ id: 5, is_urgent: false }] })
    api.flagRefundCaseUrgent.mockResolvedValue({ id: 5, is_urgent: true })
    const store = useRefundStore()
    await store.load()

    await store.flagUrgent(5, true, '')

    expect(api.flagRefundCaseUrgent).toHaveBeenCalledWith(5, true, null)
    expect(store.cases[0].is_urgent).toBe(true)
  })

  it('caches customer history and returns null on failure', async () => {
    api.fetchCustomerHistory.mockResolvedValueOnce({ orders: 4 })
    const store = useRefundStore()

    expect(await store.loadCustomerHistory('u1')).toEqual({ orders: 4 })
    expect(await store.loadCustomerHistory('u1')).toEqual({ orders: 4 })
    expect(api.fetchCustomerHistory).toHaveBeenCalledTimes(1)

    api.fetchCustomerHistory.mockRejectedValueOnce(new Error('404'))
    expect(await store.loadCustomerHistory('u2')).toBeNull()
    expect(await store.loadCustomerHistory(null)).toBeNull()
  })

  it('refresh forces a reload', async () => {
    api.fetchSupportRefundCases.mockResolvedValue({ cases: [] })
    const store = useRefundStore()
    await store.load()
    await store.refresh()
    expect(api.fetchSupportRefundCases).toHaveBeenCalledTimes(2)
  })
})

describe('contact store', () => {
  it('fills defaults for a public contact form and returns the reference code', async () => {
    api.submitPublicContactForm.mockResolvedValue({ id: 'c1', reference_code: 'CC-1001' })
    const store = useContactStore()

    const code = await store.submit({ name: 'Priya', message: 'Need a quote' })

    expect(code).toBe('CC-1001')
    expect(api.submitPublicContactForm).toHaveBeenCalledWith({
      name: 'Priya',
      email: '',
      phone: '',
      category: 'general',
      subject: 'General Inquiry',
      priority: 'medium',
      message: 'Need a quote',
    })
    expect(store.submissions[0].id).toBe('c1')
    expect(store.initialized).toBe(true)
  })

  it('computes stats and clears resolved submissions one by one', async () => {
    api.fetchContactSubmissions.mockResolvedValue({
      submissions: [
        { id: 1, status: 'new', priority: 'urgent' },
        { id: 2, status: 'resolved' },
        { id: 3, status: 'resolved' },
        { id: 4, status: 'in_progress' },
      ],
    })
    api.deleteContactSubmission.mockResolvedValue(null)
    const store = useContactStore()
    await store.load()

    expect(store.stats).toEqual({ total: 4, new: 1, inProgress: 1, resolved: 2, urgent: 1 })

    await store.clearResolved()

    expect(api.deleteContactSubmission.mock.calls.map((call) => call[0])).toEqual([2, 3])
    expect(store.submissions.map((s) => s.id)).toEqual([1, 4])
  })

  it('updates in place, inserts unknown rows first, and removes deleted ones', async () => {
    api.fetchContactSubmissions.mockResolvedValue({ submissions: [{ id: 1, status: 'new' }] })
    api.updateContactSubmission.mockResolvedValue({ id: 1, status: 'in_progress' })
    api.replyContactSubmission.mockResolvedValue({ id: 2, status: 'resolved' })
    api.deleteContactSubmission.mockResolvedValue(null)
    const store = useContactStore()
    await store.load()

    await store.update(1, { status: 'in_progress' })
    await store.reply(2, 'Thanks')
    expect(store.submissions.map((s) => `${s.id}:${s.status}`)).toEqual([
      '2:resolved',
      '1:in_progress',
    ])

    await store.remove(2)
    expect(store.submissions.map((s) => s.id)).toEqual([1])
  })

  it('stores the error message when loading fails', async () => {
    api.fetchContactSubmissions.mockRejectedValue(new Error(''))
    const store = useContactStore()
    await expect(store.load()).rejects.toThrow()
    expect(store.error).toBe('Failed to load contact submissions')
  })
})
