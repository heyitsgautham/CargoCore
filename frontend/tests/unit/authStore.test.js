import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

const loginReply = (user) => ({ access_token: 'access-1', refresh_token: 'refresh-1', user })

async function freshStore() {
  vi.resetModules()
  const { useAuthStore } = await import('@/stores/authStore')
  return useAuthStore()
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  setActivePinia(createPinia())
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('password login', () => {
  it('stores the session and sends each role to its dashboard', async () => {
    const router = stubFetch([
      [
        'POST',
        '/auth/login',
        loginReply({ id: 'u1', name: 'Dina Dispatcher', email: 'd@x.com', role: 'DISPATCHER' }),
      ],
    ])
    const store = await freshStore()

    const result = await store.login('d@x.com', 'StrongPass123', true)

    expect(result).toEqual({ success: true, redirect: '/dispatcher/dashboard' })
    expect(router.calls[0].body).toEqual({ email: 'd@x.com', password: 'StrongPass123' })
    expect(store.isAuthenticated).toBe(true)
    expect(store.userRoleLabel).toBeTruthy()
    expect(localStorage.getItem('auth_token')).toBe('access-1')
    expect(localStorage.getItem('remember_email')).toBe('d@x.com')
  })

  it('counts failed attempts and locks the account after five', async () => {
    stubFetch([
      ['POST', '/auth/login', { status: 401, body: { detail: 'Invalid email or password' } }],
    ])
    const store = await freshStore()

    for (let attempt = 1; attempt <= 4; attempt += 1) {
      const result = await store.login('a@x.com', 'wrong')
      expect(result.attemptsLeft).toBe(5 - attempt)
    }
    await store.login('a@x.com', 'wrong')

    expect(store.isLockedOut).toBe(true)
    expect(store.lockoutRemainingMs).toBeGreaterThan(0)
    expect((await store.login('a@x.com', 'right')).locked).toBe(true)
    expect(Number(localStorage.getItem('lockout_until'))).toBeGreaterThan(Date.now())
  })

  it('reports other server errors without counting an attempt', async () => {
    stubFetch([
      ['POST', '/auth/login', { status: 403, body: { detail: 'Account awaiting approval' } }],
    ])
    const store = await freshStore()

    const result = await store.login('v@x.com', 'pw')

    expect(result).toEqual({ success: false, status: 403 })
    expect(store.error).toBe('Account awaiting approval')
    expect(store.loginAttempts).toBe(0)
  })

  it('loads the hub for a warehouse manager', async () => {
    stubFetch([
      [
        'POST',
        '/auth/login',
        loginReply({ id: 'u2', name: 'Wendy', role: 'WAREHOUSE_MANAGER', warehouse_id: 'wh-1' }),
      ],
      [
        'GET',
        '/auth/me',
        { id: 'u2', name: 'Wendy', role: 'WAREHOUSE_MANAGER', warehouse_id: 'wh-1' },
      ],
      [
        'GET',
        '/api/v1/warehouses',
        { items: [{ id: 'wh-1', name: 'North Hub', is_active: true }] },
      ],
    ])
    const store = await freshStore()

    const result = await store.login('w@x.com', 'pw')

    expect(result.redirect).toBe('/warehouse/dashboard')
    expect(store.currentWarehouse?.name).toBe('North Hub')
  })
})

describe('signup and OTP flows', () => {
  it('rejects self-registration for staff roles', async () => {
    stubFetch([])
    const store = await freshStore()

    expect((await store.register({ role: 'dispatcher' })).success).toBe(false)
    expect(store.error).toMatch(/Customer and Vendor/)
  })

  it('registers a customer after the email OTP is verified', async () => {
    const router = stubFetch([
      ['POST', '/auth/send-otp', {}],
      ['POST', '/auth/verify-otp', {}],
      ['POST', '/auth/register', loginReply({ id: 'u3', name: 'Asha', role: 'INDIVIDUAL' })],
    ])
    const store = await freshStore()

    const started = await store.register({
      role: 'customer',
      name: 'Asha',
      email: 'asha@x.com',
      password: 'StrongPass123',
      phone: '9000000000',
    })
    expect(started.success).toBe(true)
    expect(store.pendingFlow).toBe('signup')

    const verified = await store.verifyOTP('123456')

    expect(verified).toEqual({ success: true, redirect: '/individual/dashboard' })
    expect(router.calls.map((c) => new URL(c.url).pathname)).toEqual([
      '/api/v1/auth/send-otp',
      '/api/v1/auth/verify-otp',
      '/api/v1/auth/register',
    ])
    expect(store.pendingFlow).toBe('')
  })

  it('sends a vendor back to login while approval is pending', async () => {
    stubFetch([
      ['POST', '/auth/send-otp', {}],
      ['POST', '/auth/verify-otp', {}],
      ['POST', '/auth/register', { pending_approval: true, message: 'Awaiting review' }],
    ])
    const store = await freshStore()

    await store.register({
      role: 'vendor',
      name: 'Acme',
      email: 'acme@x.com',
      password: 'StrongPass123',
      companyName: 'Acme',
    })
    const verified = await store.verifyOTP('123456')

    expect(verified).toEqual({ success: true, redirect: '/login' })
    expect(store.isAuthenticated).toBe(false)
    expect(store.successMessage).toBe('Awaiting review')
  })

  it('logs in with an emailed code', async () => {
    stubFetch([
      ['POST', '/auth/send-login-otp', {}],
      ['POST', '/auth/verify-login-otp', loginReply({ id: 'u4', name: 'Vik', role: 'VENDOR' })],
    ])
    const store = await freshStore()

    expect((await store.sendOTP('vik@x.com')).success).toBe(true)
    expect(store.otpTarget).toBe('vik@x.com')
    expect(await store.verifyOTP('999999')).toEqual({
      success: true,
      redirect: '/vendor/dashboard',
    })
  })

  it('surfaces a wrong code', async () => {
    stubFetch([
      ['POST', '/auth/verify-login-otp', { status: 400, body: { detail: 'Code expired' } }],
    ])
    const store = await freshStore()

    expect((await store.verifyOTP('000000')).success).toBe(false)
    expect(store.error).toBe('Code expired')
  })

  it('requests and completes a password reset', async () => {
    const router = stubFetch([
      ['POST', '/auth/forgot-password', {}],
      ['POST', '/auth/reset-password', {}],
    ])
    const store = await freshStore()

    expect((await store.sendPasswordResetOTP('a@x.com')).success).toBe(true)
    expect((await store.resetPassword('a@x.com', '123456', 'NewPass123')).success).toBe(true)
    expect(router.last('POST').body).toEqual({
      email: 'a@x.com',
      token: '123456',
      new_password: 'NewPass123',
    })
  })
})

describe('session housekeeping', () => {
  it('logs out, clears storage and returns the driver vehicle', async () => {
    const router = stubFetch([
      ['POST', '/auth/login', loginReply({ id: 'u5', name: 'Ravi', role: 'DRIVER' })],
      ['POST', '/return-vehicle', {}],
      ['POST', '/auth/logout', {}],
    ])
    const store = await freshStore()
    await store.login('ravi@x.com', '1234')

    const route = store.logout()

    expect(route).toBe('/login')
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(router.calls.some((c) => c.url.includes('/return-vehicle'))).toBe(true)
  })

  it('reads a session written by another tab', async () => {
    stubFetch([])
    const store = await freshStore()
    localStorage.setItem('auth_token', 'from-other-tab')
    localStorage.setItem(
      'auth_user',
      JSON.stringify({ id: 'u6', name: 'Lata', role: 'LOGISTIC_MANAGER' }),
    )

    store.syncSessionFromStorage()

    expect(store.isAuthenticated).toBe(true)
    expect(store.userName).toBe('Lata')
    expect(store.getDashboardRoute()).toBe('/logistic/dashboard')
  })

  it('clears errors on request', async () => {
    stubFetch([['POST', '/auth/login', { status: 500, body: {} }]])
    const store = await freshStore()
    await store.login('a@x.com', 'pw')

    store.clearErrors()

    expect(store.error).toBe('')
  })
})
