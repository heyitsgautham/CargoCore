import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiUrl,
  clearAuthSession,
  getStoredAccessToken,
  getStoredUser,
  storeAuthSession,
  authenticatedJsonRequest,
} from '@/config/api'

const MAX_LOGIN_ATTEMPTS = 5
const LOCKOUT_DURATION_MS = 5 * 60 * 1000

const ROLE_DASHBOARD_MAP = {
  INDIVIDUAL: '/individual/dashboard',
  VENDOR: '/vendor/dashboard',
  LOGISTIC_MANAGER: '/logistic/dashboard',
  WAREHOUSE_MANAGER: '/warehouse/dashboard',
  DISPATCHER: '/dispatcher/dashboard',
  DRIVER: '/driver/dashboard',
  AI_AGENT: '/ai/dashboard',
  AI_SUPPORT: '/ai/dashboard',
  CUSTOMER_SUPPORT: '/ai/dashboard',
  // lowercase variants used in some legacy code
  ai_agent: '/ai/dashboard',
  ai_support: '/ai/dashboard',
  customer_support: '/ai/dashboard',
  logistics_manager: '/logistic/dashboard',
  warehouse_manager: '/warehouse/dashboard',
  dispatcher: '/dispatcher/dashboard',
  vendor: '/vendor/dashboard',
  customer: '/individual/dashboard',
  manager: '/logistic/dashboard',
  warehouse: '/warehouse/dashboard',
  driver: '/driver/dashboard',
}

export const useAuthStore = defineStore('auth', () => {
  // ── Core auth state ──────────────────────────────────────────
  const user = ref(getStoredUser())
  const token = ref(getStoredAccessToken())
  const isAuthenticated = ref(!!token.value)

  // ── Login lockout state ───────────────────────────────────────
  const loginAttempts = ref(parseInt(localStorage.getItem('login_attempts') || '0', 10))
  const lockoutUntil = ref(parseInt(localStorage.getItem('lockout_until') || '0', 10))

  // ── OTP / registration flow ───────────────────────────────────
  const otpTarget = ref('')
  const pendingFlow = ref('')          // 'signup' | 'forgot' | ''
  const pendingRegistrationData = ref(null)

  // ── TFA setup state (mock until backend supports it) ─────────
  const tfaSecret = ref('')
  const tfaQrUrl = ref('')
  const tfaBackupCodes = ref([])

  // ── UI state ─────────────────────────────────────────────────
  const loading = ref(false)
  const error = ref('')
  const successMessage = ref('')

  // ── Warehouse context (warehouse manager only) ────────────────
  const currentWarehouse = ref(null)

  // ── Getters ──────────────────────────────────────────────────
  const isLockedOut = computed(() => {
    if (lockoutUntil.value === 0) return false
    if (Date.now() < lockoutUntil.value) return true
    clearLockout()
    return false
  })

  const lockoutRemainingMs = computed(() => {
    if (!isLockedOut.value) return 0
    return Math.max(0, lockoutUntil.value - Date.now())
  })

  const userRole = computed(() => user.value?.role ?? '')
  const userName = computed(() => user.value?.name ?? '')
  const userEmail = computed(() => user.value?.email ?? '')

  const userRoleLabel = computed(() => {
    const role = user.value?.role ?? ''
    if (role === 'INDIVIDUAL') return 'Customer'
    if (role === 'VENDOR') return 'Vendor'
    if (role === 'LOGISTIC_MANAGER' || role === 'manager') return 'Logistics Manager'
    if (role === 'WAREHOUSE_MANAGER' || role === 'warehouse') return 'Warehouse Manager'
    if (role === 'DISPATCHER' || role === 'dispatcher') return 'Dispatcher'
    if (role === 'DRIVER' || role === 'driver') return 'Driver'
    if (role === 'AI_AGENT' || role === 'ai_agent' || role === 'AI_SUPPORT' || role === 'ai_support' || role === 'CUSTOMER_SUPPORT' || role === 'customer_support') return 'Customer Support'
    return role
  })

  const dashboardPath = computed(() => ROLE_DASHBOARD_MAP[userRole.value] || '/login')

  // ── Session sync ──────────────────────────────────────────────
  if (typeof window !== 'undefined') {
    const syncSession = () => {
      token.value = getStoredAccessToken()
      user.value = getStoredUser()
      isAuthenticated.value = !!token.value
      if (!token.value) currentWarehouse.value = null
    }
    window.addEventListener('auth:session-changed', syncSession)
    window.addEventListener('storage', syncSession)
  }

  // ── Internal helpers ──────────────────────────────────────────
  function setAuthState(userData, accessToken, refreshToken) {
    user.value = userData
    token.value = accessToken
    isAuthenticated.value = true
    storeAuthSession({ accessToken, refreshToken, user: userData })
    resetLoginAttempts()
  }

  function clearAuthState() {
    user.value = null
    token.value = null
    isAuthenticated.value = false
    currentWarehouse.value = null
    clearAuthSession()
  }

  function incrementAttempts() {
    loginAttempts.value++
    localStorage.setItem('login_attempts', String(loginAttempts.value))
    if (loginAttempts.value >= MAX_LOGIN_ATTEMPTS) {
      const until = Date.now() + LOCKOUT_DURATION_MS
      lockoutUntil.value = until
      localStorage.setItem('lockout_until', String(until))
    }
  }

  function resetLoginAttempts() {
    loginAttempts.value = 0
    lockoutUntil.value = 0
    localStorage.removeItem('login_attempts')
    localStorage.removeItem('lockout_until')
  }

  function clearLockout() {
    lockoutUntil.value = 0
    loginAttempts.value = 0
    localStorage.removeItem('lockout_until')
    localStorage.removeItem('login_attempts')
  }

  // ── Actions ───────────────────────────────────────────────────

  /**
   * Email + password login (used by new Login.vue)
   */
  async function login(email, password, rememberMe = false) {
    if (isLockedOut.value) {
      error.value = 'Account temporarily locked. Please try again later.'
      return { success: false, locked: true }
    }

    loading.value = true
    error.value = ''

    try {
      const response = await fetch(apiUrl('api/v1/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Invalid credentials. Please try again.'
        if (response.status === 401) {
          incrementAttempts()
          return { success: false, attemptsLeft: MAX_LOGIN_ATTEMPTS - loginAttempts.value }
        }
        return { success: false, status: response.status }
      }

      const data = await response.json()
      setAuthState(data.user, data.access_token, data.refresh_token)

      if (rememberMe) {
        localStorage.setItem('remember_email', email)
      } else {
        localStorage.removeItem('remember_email')
      }

      if (data.user.role === 'WAREHOUSE_MANAGER') {
        await ensureWarehouseContext()
      }

      return { success: true, redirect: ROLE_DASHBOARD_MAP[data.user.role] || '/individual/dashboard' }
    } catch {
      incrementAttempts()
      error.value = 'Unable to connect to the server. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Google OAuth login — credential comes from vue3-google-login <GoogleLogin> callback
   */
  async function loginWithGoogle(credential) {
    if (!credential) {
      error.value = 'Google sign-in failed. No credential received.'
      return { success: false }
    }

    loading.value = true
    error.value = ''

    try {
      const response = await fetch(apiUrl('api/v1/auth/google-login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential, role: 'INDIVIDUAL' }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        if (response.status === 404) {
          return { success: true, needsProfile: true }
        }
        error.value = errData.detail || 'Google login failed.'
        return { success: false }
      }

      const data = await response.json()
      setAuthState(data.user, data.access_token, data.refresh_token)

      if (data.user.role === 'WAREHOUSE_MANAGER') {
        await ensureWarehouseContext()
      }

      return { success: true, redirect: ROLE_DASHBOARD_MAP[data.user.role] || '/individual/dashboard' }
    } catch {
      error.value = 'Google login failed. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Send OTP to email — used by OTP login flow
   */
  async function sendOTP(target) {
    loading.value = true
    error.value = ''

    try {
      const response = await fetch(apiUrl('api/v1/auth/send-otp'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: target }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Failed to send OTP.'
        return { success: false }
      }

      otpTarget.value = target
      successMessage.value = `OTP sent to ${target}`
      return { success: true }
    } catch {
      error.value = 'Unable to send OTP. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Verify OTP — handles both OTP login and signup registration completion
   */
  async function verifyOTP(code, _isTfa = false) {
    loading.value = true
    error.value = ''

    try {
      // Signup flow: verify OTP then POST /auth/register to complete registration
      if (pendingFlow.value === 'signup' && pendingRegistrationData.value) {
        const verifyResp = await fetch(apiUrl('api/v1/auth/verify-otp'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: otpTarget.value || pendingRegistrationData.value.email,
            otp: code,
          }),
        })

        if (!verifyResp.ok) {
          const errData = await verifyResp.json().catch(() => ({}))
          error.value = errData.detail || 'Invalid OTP. Please try again.'
          return { success: false }
        }

        const registerResp = await fetch(apiUrl('api/v1/auth/register'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(pendingRegistrationData.value),
        })

        if (!registerResp.ok) {
          const errData = await registerResp.json().catch(() => ({}))
          let msg = errData.detail || 'Registration failed.'
          if (Array.isArray(msg)) msg = msg[0]?.msg || 'Registration failed.'
          error.value = typeof msg === 'string' ? msg : 'Registration failed.'
          return { success: false }
        }

        const data = await registerResp.json()
        const registrationData = pendingRegistrationData.value
        pendingFlow.value = ''
        pendingRegistrationData.value = null
        otpTarget.value = ''

        if (data.pending_approval) {
          clearAuthState()
          successMessage.value = data.message || 'Vendor registration submitted. A Logistics Manager will review it before you can sign in.'
          return { success: true, redirect: '/login' }
        }

        const registeredUser = data.user || {
          ...registrationData,
          name: registrationData?.name,
        }
        setAuthState(registeredUser, data.access_token, data.refresh_token)

        return { success: true, redirect: ROLE_DASHBOARD_MAP[registeredUser.role] || '/individual/dashboard' }
      }

      // OTP login flow: just verify OTP and get token
      const response = await fetch(apiUrl('api/v1/auth/verify-otp'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: otpTarget.value, otp: code }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Invalid code. Please try again.'
        return { success: false }
      }

      const data = await response.json()
      setAuthState(data.user, data.access_token, data.refresh_token)
      return { success: true, redirect: ROLE_DASHBOARD_MAP[data.user?.role] || '/individual/dashboard' }
    } catch {
      error.value = 'Verification failed. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Register — sends OTP to email, stores form data for completion after OTP verify
   */
  async function register(formData) {
    if (!['customer', 'vendor'].includes(formData.role)) {
      error.value = 'Self-registration is only available for Customer and Vendor accounts.'
      return { success: false }
    }

    loading.value = true
    error.value = ''

    try {
      const role = formData.role === 'vendor' ? 'VENDOR' : 'INDIVIDUAL'

      const payload = {
        name: formData.fullName,
        email: formData.email,
        phone: formData.phone || null,
        password: formData.password,
        role,
        address: formData.role === 'customer'
          ? [formData.pickupAddress, formData.city, formData.state, formData.pincode]
              .filter(Boolean).join(', ')
          : formData.businessAddress || null,
        company_name: role === 'VENDOR' ? formData.companyName || null : null,
        tax_id: role === 'VENDOR' ? formData.gstTaxId || null : null,
        contact_person: role === 'VENDOR' ? formData.contactPerson || null : null,
        business_email: role === 'VENDOR' ? formData.businessEmail || null : null,
        business_phone: role === 'VENDOR' ? formData.businessPhone || null : null,
      }

      const response = await fetch(apiUrl('api/v1/auth/send-otp'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: payload.email }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        let msg = errData.detail || 'Failed to send verification email.'
        if (Array.isArray(msg)) msg = msg[0]?.msg || 'Failed.'
        error.value = typeof msg === 'string' ? msg : 'Registration failed.'
        return { success: false }
      }

      const data = await response.json()
      if (typeof window !== 'undefined' && data.debug_otp) {
        sessionStorage.setItem('signup_debug_otp', data.debug_otp)
      }

      otpTarget.value = payload.email
      pendingFlow.value = 'signup'
      pendingRegistrationData.value = payload
      successMessage.value = `Verification email sent to ${payload.email}`

      return { success: true }
    } catch {
      error.value = 'Unable to connect. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * TFA Setup — mock until backend implements TOTP
   */
  async function initTFASetup() {
    loading.value = true
    error.value = ''
    try {
      await new Promise(r => setTimeout(r, 600))
      tfaSecret.value = 'JBSWY3DPEHPK3PXP'
      tfaQrUrl.value = `otpauth://totp/CargoCore:${user.value?.email || 'user@example.com'}?secret=JBSWY3DPEHPK3PXP&issuer=CargoCore`
      tfaBackupCodes.value = [
        'A1B2-C3D4', 'E5F6-G7H8', 'I9J0-K1L2',
        'M3N4-O5P6', 'Q7R8-S9T0', 'U1V2-W3X4',
        'Y5Z6-A7B8', 'C9D0-E1F2',
      ]
      return { success: true }
    } catch {
      error.value = 'Failed to initialize TFA setup.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  async function confirmTFASetup(code) {
    loading.value = true
    error.value = ''
    try {
      await new Promise(r => setTimeout(r, 500))
      if (!/^\d{6}$/.test(code)) {
        error.value = 'Please enter a valid 6-digit code.'
        return { success: false }
      }
      if (user.value) {
        const updated = { ...user.value, tfaEnabled: true }
        user.value = updated
        storeAuthSession({ user: updated })
      }
      successMessage.value = 'Two-factor authentication enabled!'
      return { success: true }
    } catch {
      error.value = 'Verification failed. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Password reset — step 1: send OTP to email
   */
  async function sendPasswordResetOTP(email) {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(apiUrl('api/v1/auth/forgot-password'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Failed to send reset link.'
        return { success: false }
      }
      otpTarget.value = email
      return { success: true, message: 'Reset link sent to ' + email }
    } catch {
      error.value = 'Unable to connect. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Password reset — step 2: submit new password with OTP token
   */
  async function resetPassword(emailAddr, otp, newPassword) {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(apiUrl('api/v1/auth/reset-password'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailAddr, token: otp, new_password: newPassword }),
      })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Reset failed.'
        return { success: false }
      }
      return { success: true, message: 'Password reset successful!' }
    } catch {
      error.value = 'Unable to connect. Please try again.'
      return { success: false }
    } finally {
      loading.value = false
    }
  }

  /**
   * Google login — backward-compat for existing role-based pages that pass credential directly
   */
  async function googleLogin(credential, role = 'INDIVIDUAL') {
    loading.value = true
    error.value = ''
    try {
      const response = await fetch(apiUrl('api/v1/auth/google-login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential, role }),
      })
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        error.value = errData.detail || 'Google login failed.'
        return { success: false, message: error.value, status: response.status }
      }
      const data = await response.json()
      setAuthState(data.user, data.access_token, data.refresh_token)
      if (data.user.role === 'WAREHOUSE_MANAGER') await ensureWarehouseContext()
      return {
        success: true,
        message: `Welcome back, ${data.user.name}!`,
        status: response.status,
        redirect: ROLE_DASHBOARD_MAP[data.user.role] || '/individual/dashboard',
      }
    } catch {
      error.value = 'Unable to connect.'
      return { success: false, message: error.value, status: 0 }
    } finally {
      loading.value = false
    }
  }

  /**
   * Warehouse context — fetch and cache assigned warehouse for WAREHOUSE_MANAGER
   */
  async function ensureWarehouseContext() {
    if (!getStoredAccessToken() || !user.value) return null
    if (user.value?.role !== 'WAREHOUSE_MANAGER') { currentWarehouse.value = null; return null }

    try {
      const refreshedProfile = await authenticatedJsonRequest('api/v1/auth/me')
      const profile = { ...user.value, ...refreshedProfile }
      user.value = profile
      storeAuthSession({ user: profile })

      const data = await authenticatedJsonRequest('api/v1/warehouses?page=1&page_size=100')
      const warehouses = data.items || []
      const linked = warehouses.find(w =>
        w.id === profile.warehouse_id || w.manager_id === profile.id
      ) || (warehouses.length === 1 ? warehouses[0] : null)

      currentWarehouse.value = linked
      if (linked && profile.warehouse_id !== linked.id) {
        user.value = { ...user.value, warehouse_id: linked.id }
        storeAuthSession({ user: user.value })
      }
      return linked
    } catch {
      return null
    }
  }

  function logout() {
    // If the current user is a driver, notify the backend to end their shift and
    // return their vehicle. Capture the token NOW before clearAuthState() wipes it.
    // Requests are fire-and-forget so callers don't need to await this function.
    const role = user.value?.role
    const currentToken = token.value
    if ((role === 'DRIVER' || role === 'driver') && currentToken) {
      const headers = { 'Authorization': `Bearer ${currentToken}`, 'Content-Type': 'application/json' }
      const base = apiUrl('/api/v1/logistics')
      fetch(`${base}/drivers/me/shift/end`, { method: 'POST', headers }).catch(() => {})
      fetch(`${base}/drivers/me/return-vehicle`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ odometer_km: null, fuel_level_pct: null, notes: null }),
      }).catch(() => {})
    }
    clearAuthState()
    pendingFlow.value = ''
    pendingRegistrationData.value = null
    otpTarget.value = ''
    return '/login'
  }

  function getDashboardRoute(role = user.value?.role) {
    return ROLE_DASHBOARD_MAP[role] || '/login'
  }

  function getLoginRoute(_role = user.value?.role) {
    // Always use the new unified login
    return '/login'
  }

  function clearError() {
    error.value = ''
    successMessage.value = ''
  }

  // Backward-compat aliases for any existing code
  function clearErrors() { clearError() }
  function syncSessionFromStorage() {
    token.value = getStoredAccessToken()
    user.value = getStoredUser()
    isAuthenticated.value = !!token.value
  }

  return {
    // ── State ──────────────────────────────────────────────────
    user,
    token,
    isAuthenticated,
    loginAttempts,
    lockoutUntil,
    otpTarget,
    pendingFlow,
    pendingRegistrationData,
    tfaSecret,
    tfaQrUrl,
    tfaBackupCodes,
    loading,
    error,
    successMessage,
    currentWarehouse,

    // ── Getters ────────────────────────────────────────────────
    isLockedOut,
    lockoutRemainingMs,
    userRole,
    userName,
    userEmail,
    userRoleLabel,
    dashboardPath,

    // ── New auth actions (used by new auth-views) ───────────────
    login,
    loginWithGoogle,
    sendOTP,
    verifyOTP,
    register,
    initTFASetup,
    confirmTFASetup,
    clearError,

    // ── Password reset ─────────────────────────────────────────
    sendPasswordResetOTP,
    resetPassword,

    // ── Backward-compat (used by existing role dashboards) ─────
    googleLogin,
    ensureWarehouseContext,
    logout,
    getDashboardRoute,
    getLoginRoute,
    clearErrors,
    syncSessionFromStorage,

    // Aliases for older code that references these names
    currentUser: user,
    isLoading: loading,
    authToken: token,
    loginError: error,
    pendingEmail: otpTarget,
    pendingRole: ref(''),
  }
})
