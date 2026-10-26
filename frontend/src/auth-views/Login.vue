<template>
    <div class="login-view animate-view">
        <!-- Header -->
        <div class="login-header">
            <h2 class="login-title">Welcome back</h2>
            <p class="login-subtitle">Sign in to your Cargo-Core account</p>
        </div>

        <!-- Lockout Warning -->
        <div v-if="auth.isLockedOut" class="lockout-banner" role="alert">
            <svg class="lockout-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd"
                    d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                    clip-rule="evenodd" />
            </svg>
            <div>
                <p class="lockout-title">Account temporarily locked</p>
                <p class="lockout-timer">Try again in {{ lockoutDisplay }}</p>
            </div>
        </div>

        <!-- OTP Mode -->
        <div v-if="otpMode">
            <button class="back-link" @click="otpMode = false" aria-label="Back to password login">
                <svg viewBox="0 0 20 20" fill="currentColor" class="back-arrow">
                    <path fill-rule="evenodd"
                        d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                        clip-rule="evenodd" />
                </svg>
                Back to login
            </button>

            <h3 class="otp-title">Login with OTP</h3>
            <p class="otp-desc">Enter your email or phone to receive a one-time code.</p>

            <div class="field-group">
                <label for="otp-target" class="field-label">Email or Phone</label>
                <div class="input-wrap">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                    </svg>
                    <input id="otp-target" v-model="otpTarget" type="text" placeholder="you@company.com or +91..."
                        class="auth-input" :disabled="auth.isLockedOut" autocomplete="email"
                        @keyup.enter="handleSendOTP" />
                </div>
            </div>

            <button class="btn-primary" :disabled="!otpTarget || auth.loading || auth.isLockedOut"
                @click="handleSendOTP">
                <span v-if="auth.loading" class="btn-spinner"></span>
                {{ auth.loading ? 'Sending…' : 'Send OTP' }}
            </button>
        </div>

        <!-- Standard Login Form -->
        <form v-else @submit.prevent="handleLogin" novalidate>
            <!-- Email -->
            <div class="field-group">
                <label for="login-email" class="field-label">Email address</label>
                <div class="input-wrap" :class="{ 'input-error': errors.email }">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                    </svg>
                    <input id="login-email" v-model="form.email" type="email" placeholder="you@company.com"
                        class="auth-input" :disabled="auth.isLockedOut" autocomplete="email" aria-required="true"
                        @blur="validateEmail" />
                </div>
                <p v-if="errors.email" class="field-error" role="alert">{{ errors.email }}</p>
            </div>

            <!-- Password -->
            <div class="field-group">
                <div class="label-row">
                    <label for="login-password" class="field-label">Password</label>
                    <router-link to="/forgot-password" class="forgot-link">Forgot password?</router-link>
                </div>
                <div class="input-wrap" :class="{ 'input-error': errors.password }">
                    <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd"
                            d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                            clip-rule="evenodd" />
                    </svg>
                    <input id="login-password" v-model="form.password" :type="showPassword ? 'text' : 'password'"
                        placeholder="Enter your password" class="auth-input" :disabled="auth.isLockedOut"
                        autocomplete="current-password" />
                    <button type="button" class="toggle-password" @click="showPassword = !showPassword" tabindex="-1"
                        :aria-label="showPassword ? 'Hide password' : 'Show password'">
                        <svg v-if="!showPassword" viewBox="0 0 20 20" fill="currentColor" class="eye-icon">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                            <path fill-rule="evenodd"
                                d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                clip-rule="evenodd" />
                        </svg>
                        <svg v-else viewBox="0 0 20 20" fill="currentColor" class="eye-icon">
                            <path fill-rule="evenodd"
                                d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                                clip-rule="evenodd" />
                            <path
                                d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                        </svg>
                    </button>
                </div>
                <p v-if="errors.password" class="field-error" role="alert">{{ errors.password }}</p>
            </div>

            <!-- Strength meter -->
            <div v-if="form.password" class="password-strength">
                <div class="strength-bar">
                    <div class="strength-fill" :style="{ width: strengthPercent + '%' }" :class="strengthClass"></div>
                </div>
                <span class="strength-label" :class="strengthClass">{{ strengthLabel }}</span>
            </div>

            <!-- Remember me -->
            <div class="remember-row">
                <label class="checkbox-label" for="remember-me">
                    <input id="remember-me" v-model="form.rememberMe" type="checkbox" class="auth-checkbox" />
                    <span class="checkbox-custom"></span>
                    <span>Remember me</span>
                </label>
            </div>

            <!-- Login Button -->
            <button type="submit" class="btn-primary" :disabled="auth.loading || auth.isLockedOut">
                <span v-if="auth.loading" class="btn-spinner"></span>
                {{ auth.loading ? 'Signing in…' : 'Sign in' }}
            </button>

            <!-- Divider -->
            <div class="auth-divider"><span>or</span></div>

            <!-- Google + OTP row -->
            <div class="alt-login-row">
                <div class="btn-google-wrap" :class="{ 'btn-google-disabled': auth.loading || auth.isLockedOut }">
                    <GoogleLogin :callback="handleGoogleCredential" :button-config="{ type: 'standard', theme: 'filled_black', size: 'large', text: 'signin_with', shape: 'rectangular', logo_alignment: 'left', width: '160' }" />
                </div>
                <button type="button" class="btn-otp" @click="otpMode = true" :disabled="auth.isLockedOut">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="otp-icon">
                        <path
                            d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                    </svg>
                    OTP
                </button>
            </div>
        </form>

        <!-- Remaining attempts -->
        <p v-if="loginAttempts > 0 && loginAttempts < 5 && !auth.isLockedOut" class="attempts-note">
            {{ 5 - loginAttempts }} {{ (5 - loginAttempts) === 1 ? 'attempt' : 'attempts' }} remaining
        </p>
    </div>
</template>

<script setup>
import { emailError, passwordStrength as scorePassword } from '@/utils/validators'
import { reactive, ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { GoogleLogin } from 'vue3-google-login'
import { useAuthStore } from '../stores/authStore.js'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
    email: localStorage.getItem('remember_email') || '',
    password: '',
    rememberMe: !!localStorage.getItem('remember_email')
})

const errors = reactive({ email: '', password: '' })
const showPassword = ref(false)
const otpMode = ref(false)
const otpTarget = ref('')
const loginAttempts = computed(() => auth.loginAttempts)

// Lockout timer
const lockoutDisplay = ref('')
let lockoutInterval = null

function updateLockoutTimer() {
    const ms = auth.lockoutRemainingMs
    if (ms <= 0) { lockoutDisplay.value = ''; clearInterval(lockoutInterval); return }
    const mins = Math.floor(ms / 60000)
    const secs = Math.floor((ms % 60000) / 1000)
    lockoutDisplay.value = `${mins}:${String(secs).padStart(2, '0')}`
}

onMounted(() => { lockoutInterval = setInterval(updateLockoutTimer, 1000); updateLockoutTimer(); auth.clearError() })
onUnmounted(() => clearInterval(lockoutInterval))

// Password strength
const passwordStrength = computed(() => scorePassword(form.password))

const strengthPercent = computed(() => (passwordStrength.value / 5) * 100)
const strengthLabel = computed(() => ['', 'Very weak', 'Weak', 'Fair', 'Strong', 'Excellent'][passwordStrength.value])
const strengthClass = computed(() => ['', 'strength-1', 'strength-2', 'strength-3', 'strength-4', 'strength-5'][passwordStrength.value])

// Validation
function validateEmail() {
    errors.email = emailError(form.email, { required: 'Email is required' })
}

function validateForm() {
    validateEmail()
    errors.password = !form.password ? 'Password is required' : ''
    return !errors.email && !errors.password
}

// Handlers
async function handleLogin() {
    if (!validateForm()) return
    auth.clearError()
    const result = await auth.login(form.email, form.password, form.rememberMe)
    if (result.success && result.tfaRequired) router.push('/verify-otp?mode=tfa')
    else if (result.success && result.redirect) router.push(result.redirect)
}

async function handleGoogleCredential(response) {
    auth.clearError()
    const result = await auth.loginWithGoogle(response.credential)
    if (result.success && result.needsProfile) router.push('/register?google=true')
    else if (result.success && result.tfaRequired) router.push('/verify-otp?mode=tfa')
    else if (result.success && result.redirect) router.push(result.redirect)
}

async function handleSendOTP() {
    if (!otpTarget.value) return
    auth.clearError()
    const result = await auth.sendOTP(otpTarget.value)
    if (result.success) router.push('/verify-otp?mode=otp')
}
</script>

<style scoped src="./styles/Login.css"></style>
