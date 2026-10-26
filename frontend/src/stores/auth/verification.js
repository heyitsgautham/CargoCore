// One-time codes, two-factor setup and password reset for the auth store.
import { apiUrl, storeAuthSession } from '@/config/api'
import { ROLE_DASHBOARD_MAP } from './roleRouting'

export function useAuthVerification({
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
}) {
  async function sendOTP(target) {
    loading.value = true
    error.value = ''

    try {
      const endpoint = pendingFlow.value === 'signup' ? 'api/v1/auth/send-otp' : 'api/v1/auth/send-login-otp'
      const response = await fetch(apiUrl(endpoint), {
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

      // OTP login flow: verify OTP and get JWT tokens
      const response = await fetch(apiUrl('api/v1/auth/verify-login-otp'), {
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

  return {
    sendOTP,
    verifyOTP,
    initTFASetup,
    confirmTFASetup,
    sendPasswordResetOTP,
    resetPassword,
   }
}
