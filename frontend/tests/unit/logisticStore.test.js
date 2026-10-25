import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useLogisticStore } from '@/stores/logisticStore'
import { stubFetch } from '../helpers/fetchRouter'

const bootstrap = {
  dashboard_stats: { orders_today: 4 },
  hubs: [{ id: 'wh-1', name: 'North Hub', status: 'Active' }],
  drivers: [{ id: 'd1', hub_id: 'wh-1', name: 'Ravi', status: 'Active', efficiency: 90 }],
  vehicles: [
    {
      id: 'v1',
      hub_id: 'wh-1',
      code: 'KA01',
      type: 'Tempo',
      status: 'Active',
      driver: 'Ravi',
      mileage: 1,
    },
  ],
  users: [
    {
      id: 'u1',
      email: 'wm@example.com',
      name: 'Wendy',
      role: 'WAREHOUSE_MANAGER',
      is_active: true,
      hub_id: 'wh-1',
    },
    {
      id: 'u2',
      email: 'vendor@example.com',
      name: 'Vendor Co',
      role: 'VENDOR',
      is_active: true,
      approval_status: 'PENDING',
    },
  ],
  returns: [
    {
      id: 'r1',
      hub_id: 'wh-1',
      status: 'Pending',
      reason: 'Scratch',
      condition: 'Reported',
      customer: 'Asha',
    },
  ],
  zones: [{ id: 'z1', hub_id: 'wh-1', name: 'Zone A', type: 'Radius', radius: 3 }],
  chats: [{ id: 't1', hub_id: 'wh-1', name: 'North crew' }],
  notifications: [{ id: 'n1', title: 'Hello', message: 'World', read: false }],
  tasks: [{ id: 'k1', text: 'Renew insurance', status: 'To Do' }],
  transactions: [{ id: 'x1', description: 'Diesel', amount: 100, type: 'expense' }],
  finance_summary: { balance: 5000 },
  reports: [
    {
      id: 'report-1',
      hub_id: 'wh-1',
      title: 'North Hub Performance Report',
      date: '1d ago',
      icon: 'analytics',
      color: 'blue',
    },
    {
      id: 'report-2',
      hub_id: 'wh-2',
      title: 'South Hub Performance Report',
      date: '2d ago',
      icon: 'analytics',
      color: 'green',
    },
  ],
}

let router

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('auth_token', 'tok')
  setActivePinia(createPinia())
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  router = stubFetch([
    ['GET', '/logistics/bootstrap', bootstrap],
    ['GET', '/finance/summary', { balance: 5000, revenue: 9000 }],
    [
      'GET',
      '/logistics/tasks',
      [{ id: 'k1', text: 'Renew insurance', status: 'To Do', target_time: '2026-11-01T10:00:00Z' }],
    ],
    ['POST', '/logistics/tasks', { id: 'k2', text: 'Call insurer', status: 'To Do' }],
    ['PUT', '/logistics/tasks/k2', { id: 'k2', text: 'Call insurer', status: 'Done' }],
    ['DELETE', '/logistics/tasks/', {}],
    ['GET', '/logistics/chats', [{ id: 't1', name: 'North crew', last_message: 'Hi' }]],
    ['POST', /\/logistics\/chats$/, { id: 't2', name: 'Manager · Ravi', messages: [] }],
    [
      'POST',
      '/logistics/chats/t1/messages',
      {
        id: 't1',
        name: 'North crew',
        last_message: 'On my way',
        messages: [{ text: 'On my way' }],
      },
    ],
    ['PUT', '/logistics/chats/t1', { id: 't1', name: 'North crew', muted: true }],
    ['DELETE', '/logistics/chats/t1', {}],
    [
      'GET',
      /\/logistics\/notifications$/,
      [{ id: 'n1', title: 'Hello', message: 'World', read: false }],
    ],
    ['PUT', '/logistics/notifications/n1', {}],
    ['POST', '/mark-all-read', {}],
    ['DELETE', /\/logistics\/notifications$/, {}],
    ['POST', '/notifications/broadcast', { message: 'sent' }],
    [
      'GET',
      /\/logistics\/alerts$/,
      [{ id: 'a1', title: 'Jam', description: 'Delay', severity: 'high' }],
    ],
    ['POST', /\/logistics\/alerts$/, { id: 'a2' }],
    ['POST', '/alerts/a1/resolve', {}],
    ['POST', '/logistics/zones', { id: 'z2', name: 'Zone B', warehouse_id: 'wh-1' }],
    ['PUT', '/logistics/zones/z1', {}],
    ['DELETE', '/logistics/zones/z1', {}],
    ['POST', /\/api\/v1\/users$/, { id: 'u3', username: 'drv.ravi' }],
    [
      'PUT',
      '/api/v1/users/',
      (body, url) => ({
        id: url.split('/').at(-1),
        email: 'vendor@example.com',
        name: 'Vendor Co',
        role: 'VENDOR',
        is_active: true,
        approval_status: body.approval_status || 'APPROVED',
      }),
    ],
    ['DELETE', '/api/v1/users/', {}],
    ['POST', '/logistics/transactions', { id: 'x2', desc: 'Tyres', amount: -900, type: 'expense' }],
    ['POST', '/ai/chat', { message: 'All hubs are on track.', session_id: 's1' }],
    ['POST', /\/api\/v1\/warehouses$/, { id: 'wh-2' }],
    ['PUT', '/api/v1/warehouses/', {}],
    ['DELETE', '/api/v1/warehouses/', {}],
    ['PUT', '/logistics/vehicles/v1', {}],
    ['PUT', '/logistics/drivers/d1', {}],
    ['POST', /\/logistics\/vehicles$/, { id: 'v2' }],
  ])
})

async function loadedStore() {
  const store = useLogisticStore()
  await store.initialize()
  return store
}

describe('logistic store bootstrap', () => {
  it('loads the report history and filters it by the selected hub', async () => {
    const store = await loadedStore()

    expect(store.reports.map((r) => r.title)).toEqual([
      'North Hub Performance Report',
      'South Hub Performance Report',
    ])
    store.activeWarehouse = 'wh-2'
    expect(store.filteredReports.map((r) => r.id)).toEqual(['report-2'])
  })

  it('hydrates every dashboard list from one bootstrap call', async () => {
    const store = await loadedStore()

    expect(store.initialized).toBe(true)
    expect(store.hubs[0].name).toBe('North Hub')
    expect(store.users.map((u) => u.role)).toEqual(['Warehouse Manager', 'Vendor'])
    expect(store.returns[0].flow_type).toBeNull()
    expect(store.tasks[0].text).toBe('Renew insurance')
    expect(store.unreadNotificationsCount).toBe(1)
    expect(router.calls.filter((c) => c.url.includes('/bootstrap'))).toHaveLength(1)
  })

  it('records the error when bootstrap fails', async () => {
    stubFetch([['GET', '/logistics/bootstrap', { status: 500, body: { detail: 'Database down' } }]])
    const store = useLogisticStore()

    await expect(store.initialize()).rejects.toThrow('Database down')

    expect(store.error).toContain('Database down')
    expect(store.isLoading).toBe(false)
  })

  it('switches hub and filters lists by the active hub', async () => {
    const store = await loadedStore()

    store.setWarehouse('wh-1')

    expect(store.activeWarehouse).toBe('wh-1')
    expect(store.filteredDrivers.map((d) => d.name)).toEqual(['Ravi'])
  })
})

describe('logistic store slices', () => {
  it('works through tasks', async () => {
    const store = await loadedStore()

    await store.fetchTasks()
    expect(store.tasks[0].targetTime).toBe(new Date('2026-11-01T10:00:00Z').getTime())
    await store.createTask({ text: 'Call insurer' })
    expect(store.tasks.map((t) => t.id)).toContain('k2')
    await store.patchTask('k2', { status: 'Done' })
    expect(store.tasks.find((t) => t.id === 'k2').status).toBe('Done')
    await store.clearDoneTasks()
    expect(store.tasks.find((t) => t.id === 'k2')).toBeUndefined()
    await store.deleteTask('k1')
    expect(store.tasks).toHaveLength(0)
  })

  it('works through chats', async () => {
    const store = await loadedStore()

    await store.fetchWmChats()
    expect(store.chats[0].lastMessage).toBe('Hi')
    await store.sendChatMessage('t1', 'On my way')
    await store.muteChatThread('t1', true)
    expect(store.getManagerDriverThreadName({ name: 'Ravi' })).toContain('Ravi')
    await store.createChatThread('Manager · Ravi')
    expect(store.chats.some((c) => c.id === 't2')).toBe(true)
    await store.deleteChatThread('t1')
    expect(store.chats.some((c) => c.id === 't1')).toBe(false)
  })

  it('works through notifications and broadcasts', async () => {
    const store = await loadedStore()

    await store.fetchNotifications()
    await store.markNotificationRead('n1')
    expect(store.unreadNotificationsCount).toBe(0)
    await store.markAllNotificationsRead()
    await store.sendBroadcast({ audience: 'drivers', message: 'Rain' })
    expect(router.last('POST').body).toEqual({ audience: 'drivers', message: 'Rain' })
    await store.clearNotifications()
    expect(store.notifications).toHaveLength(0)
  })

  it('works through alerts and zones', async () => {
    const store = await loadedStore()

    await store.fetchAlerts()
    expect(store.alerts[0].title).toBe('Jam')
    await store.addAlert({ title: 'Flood', description: 'Ring road' })
    await store.resolveAlert('a1')
    await store.createZone({ hubId: 'wh-1', name: 'Zone B', type: 'Radius', radius: 2 })
    await store.updateZone('z1', { name: 'Zone A1' })
    await store.deleteZone('z1')
    expect(router.calls.some((c) => c.method === 'DELETE' && c.url.includes('/zones/z1'))).toBe(
      true,
    )
  })

  it('creates staff and approves vendors', async () => {
    const store = await loadedStore()

    await store.addUser({
      name: 'Ravi',
      email: 'ravi@example.com',
      role: 'Driver',
      password: '12',
      hubId: 'wh-1',
    })
    const created = router.calls.find((c) => c.method === 'POST' && c.url.endsWith('/api/v1/users'))
    expect(created.body).toMatchObject({
      role: 'DRIVER',
      username: 'ravi',
      password: '1234',
      warehouse_id: 'wh-1',
    })

    await store.approveVendor('u2', 'Documents verified')
    expect(store.users.find((u) => u.id === 'u2').approvalStatus).toBe('APPROVED')
    await store.rejectVendor('u2', 'Missing GST')
    await store.deleteUser('wm@example.com')
    expect(router.calls.some((c) => c.method === 'DELETE' && c.url.endsWith('/users/u1'))).toBe(
      true,
    )
  })

  it('records finance entries and asks the AI assistant', async () => {
    const store = await loadedStore()

    store.financeSummary = { total_expenses: 100, capital_invested: 1000 }
    await store.addTransaction({ desc: 'Tyres', amount: 900, type: 'expense' })
    expect(router.last('POST').body).toMatchObject({
      description: 'Tyres',
      transaction_type: 'expense',
      amount: 900,
    })
    expect(store.transactions[0].desc).toBe('Tyres')
    expect(store.financeSummary).toMatchObject({ total_expenses: 1000, capital_invested: 100 })

    await store.fetchFinanceSummary()
    expect(store.financeSummary.revenue).toBe(9000)

    await store.askAi('How are the hubs doing?')
    expect(store.aiMessages.at(-1).text).toContain('on track')
  })

  it('manages hubs and the fleet', async () => {
    const store = await loadedStore()

    await store.addHub({ name: 'South Hub', address: '1 South Road' })
    await store.updateHub({ id: 'wh-1', name: 'North Hub', address: '2 North Road' })
    await store.archiveHub('wh-1')
    await store.restoreHub('wh-1')
    await store.updateVehicleStatus('v1', 'Maintenance')
    await store.updateDriverStatus('d1', 'On Break')

    const methods = router.calls.filter((c) => c.url.includes('/warehouses')).map((c) => c.method)
    expect(methods).toEqual(['POST', 'PUT', 'PUT', 'PUT'])
  })
})

describe('credentials of new accounts', () => {
  const secretValues = ['StaffPass2026', '4321']

  function storedText() {
    return Object.keys(localStorage)
      .filter((key) => !['auth_token', 'auth_refresh_token', 'auth_user'].includes(key))
      .map((key) => `${key}=${localStorage.getItem(key)}`)
      .join('\n')
  }

  it('keeps a new password or PIN in memory and never writes one to localStorage', async () => {
    const store = await loadedStore()

    await store.addUser({
      name: 'Sita',
      email: 'sita@example.com',
      role: 'Warehouse Manager',
      username: 'sita',
      password: 'StaffPass2026',
      hubId: 'wh-1',
    })
    expect(store.lastCreatedCredentials).toEqual({
      email: 'sita@example.com',
      username: 'drv.ravi',
      password: 'StaffPass2026',
    })
    await store.addUser({
      name: 'Ravi',
      email: 'ravi@example.com',
      role: 'Driver',
      password: '4321',
      hubId: 'wh-1',
    })
    expect(store.lastCreatedCredentials.password).toBe('4321')

    const stored = storedText()
    for (const secret of secretValues) expect(stored).not.toContain(secret)
    expect(stored).not.toMatch(/password|pin|credential/i)
    expect(store.users.every((user) => user.password === '')).toBe(true)

    store.clearCreatedCredentials()
    expect(store.lastCreatedCredentials).toBeNull()
  })

  it('refuses to create office staff without a password of 8 or more characters', async () => {
    const store = await loadedStore()

    for (const password of [undefined, '', 'short']) {
      await expect(
        store.addUser({
          name: 'Sita',
          email: 'sita@example.com',
          role: 'Warehouse Manager',
          username: 'sita',
          password,
          hubId: 'wh-1',
        }),
      ).rejects.toThrow('at least 8 characters')
    }
    expect(router.calls.some((c) => c.method === 'POST' && c.url.endsWith('/api/v1/users'))).toBe(
      false,
    )
  })

  it('clears credentials an older build saved', async () => {
    localStorage.setItem(
      'logistic_manager_created_credentials',
      '{"wm@example.com":{"password":"Old1234"}}',
    )

    useLogisticStore()

    expect(localStorage.getItem('logistic_manager_created_credentials')).toBeNull()
  })
})
