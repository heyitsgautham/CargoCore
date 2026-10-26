import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiUrl,
  clearAuthSession,
  getStoredAccessToken,
  getStoredUser,
  storeAuthSession,
} from '@/config/api'
import {
  ROLE_DASHBOARD_MAP,
  buildHubAccessState,
  resolveRoleHome,
} from './auth/roleRouting'
import { useAuthVerification } from './auth/verification'
import { useHubAccess } from './auth/hubAccess'

const MAX_LOGIN_ATTEMPTS = 5
const LOCKOUT_DURATION_MS = 5 * 60 * 1000

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
  const assignedHubAccess = ref(buildHubAccessState(user.value))

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

  const dashboardPath = computed(() => resolveRoleHome(user.value))
  const isAssignedHubArchived = computed(() => assignedHubAccess.value.isArchived)

  function syncWarehouseStateFromUser(userData = user.value) {
    assignedHubAccess.value = buildHubAccessState(userData)

    const warehouseId = userData?.warehouse_id ?? null
    if (!warehouseId) {
      currentWarehouse.value = null
      return
    }

    const existingWarehouse = currentWarehouse.value || {}
    const resolvedIsActive = typeof userData?.warehouse_is_active === 'boolean'
      ? userData.warehouse_is_active
      : existingWarehouse.is_active
    const resolvedStatus = userData?.warehouse_status
      || (typeof resolvedIsActive === 'boolean' ? (resolvedIsActive ? 'Active' : 'Archived') : existingWarehouse.status)

    currentWarehouse.value = {
      ...existingWarehouse,
      id: warehouseId,
      name: userData?.warehouse_name || existingWarehouse.name || 'Assigned Warehouse',
      address: userData?.warehouse_address || existingWarehouse.address || '',
      is_active: resolvedIsActive,
      status: resolvedStatus,
    }
  }

  function persistUserProfile(profile) {
    const mergedProfile = { ...(user.value || {}), ...(profile || {}) }
    user.value = mergedProfile
    storeAuthSession({ user: mergedProfile })
    syncWarehouseStateFromUser(mergedProfile)
    return mergedProfile
  }

  // ── Session sync ──────────────────────────────────────────────
  if (typeof window !== 'undefined') {
    const syncSession = () => {
      token.value = getStoredAccessToken()
      user.value = getStoredUser()
      isAuthenticated.value = !!token.value
      if (!token.value) {
        currentWarehouse.value = null
        assignedHubAccess.value = buildHubAccessState(null)
        return
      }
      syncWarehouseStateFromUser(user.value)
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
    syncWarehouseStateFromUser(userData)
    resetLoginAttempts()
  }

  function clearAuthState() {
    user.value = null
    token.value = null
    isAuthenticated.value = false
    currentWarehouse.value = null
    assignedHubAccess.value = buildHubAccessState(null)
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

      if (data.user.role === 'WAREHOUSE_MANAGER' && data.user.warehouse_is_active !== false) {
        await ensureWarehouseContext()
      }

      return { success: true, redirect: resolveRoleHome(data.user) }
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

      if (data.user.role === 'WAREHOUSE_MANAGER' && data.user.warehouse_is_active !== false) {
        await ensureWarehouseContext()
      }

      return { success: true, redirect: resolveRoleHome(data.user) }
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
  /**
   * Verify OTP — handles both OTP login and signup registration completion
   */
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
  /**
   * Password reset — step 1: send OTP to email
   */
  /**
   * Password reset — step 2: submit new password with OTP token
   */
  /**
   * Warehouse context — fetch and cache assigned warehouse for WAREHOUSE_MANAGER
   */
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
    if (role === user.value?.role) {
      return resolveRoleHome(user.value)
    }
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
    syncWarehouseStateFromUser(user.value)
  }

  const {
    sendOTP,
    verifyOTP,
    initTFASetup,
    confirmTFASetup,
    sendPasswordResetOTP,
    resetPassword,
  } = useAuthVerification({
    clearAuthState,
    error,
    loading,
    otpTarget,
    pendingFlow,
    pendingRegistrationData,
    setAuthState,
    successMessage,
    tfaBackupCodes,
    tfaQrUrl,
    tfaSecret,
    user,
  })

  const { ensureWarehouseContext, ensureHubOperationalAccess } = useHubAccess({
    assignedHubAccess,
    currentWarehouse,
    persistUserProfile,
    syncWarehouseStateFromUser,
    user,
  })

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
    assignedHubAccess,

    // ── Getters ────────────────────────────────────────────────
    isLockedOut,
    lockoutRemainingMs,
    userRole,
    userName,
    userEmail,
    userRoleLabel,
    dashboardPath,
    isAssignedHubArchived,

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
    ensureHubOperationalAccess,
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
