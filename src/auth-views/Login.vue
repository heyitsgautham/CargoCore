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
const passwordStrength = computed(() => {
    const p = form.password; if (!p) return 0; let s = 0
    if (p.length >= 8) s++; if (p.length >= 12) s++
    if (/[a-z]/.test(p) && /[A-Z]/.test(p)) s++
    if (/\d/.test(p)) s++; if (/[^a-zA-Z0-9]/.test(p)) s++
    return s
})

const strengthPercent = computed(() => (passwordStrength.value / 5) * 100)
const strengthLabel = computed(() => ['', 'Very weak', 'Weak', 'Fair', 'Strong', 'Excellent'][passwordStrength.value])
const strengthClass = computed(() => ['', 'strength-1', 'strength-2', 'strength-3', 'strength-4', 'strength-5'][passwordStrength.value])

// Validation
function validateEmail() {
    errors.email = !form.email ? 'Email is required' : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) ? 'Invalid email' : ''
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

<style scoped>
.login-view {
    width: 100%;
}

.animate-view>* {
    animation: fade-in-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    opacity: 0;
    transform: translateY(10px);
}

.animate-view>*:nth-child(1) {
    animation-delay: 0.1s;
}

.animate-view>*:nth-child(2) {
    animation-delay: 0.2s;
}

.animate-view>*:nth-child(3) {
    animation-delay: 0.3s;
}

.animate-view>*:nth-child(4) {
    animation-delay: 0.4s;
}

.animate-view>*:nth-child(5) {
    animation-delay: 0.5s;
}

@keyframes fade-in-up {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.login-header {
    margin-bottom: 1.5rem;
}

.login-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #fff;
    margin-bottom: 0.15rem;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
}

.login-subtitle {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.95);
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
}

/* Lockout */
.lockout-banner {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem;
    margin-bottom: 1rem;
    background: transparent;
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 0.6rem;
}

.lockout-icon {
    width: 20px;
    height: 20px;
    color: #ef4444;
    flex-shrink: 0;
}

.lockout-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #ef4444;
}

.lockout-timer {
    font-size: 0.7rem;
    color: rgba(239, 68, 68, 0.7);
}

/* Fields */
.field-group {
    margin-bottom: 1rem;
}

.field-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 500;
    color: #fff;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.25);
    margin-bottom: 0.35rem;
}

.label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
}

.forgot-link {
    font-size: 0.7rem;
    color: #1CE783;
    text-decoration: none;
    text-shadow: 0 0 8px rgba(28, 231, 131, 0.3);
}

.forgot-link:hover {
    opacity: 0.8;
}

.input-wrap {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0 0.75rem;
    height: 42px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 0.6rem;
    transition: all 0.25s ease;
    box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
}

.input-wrap:focus-within {
    border-color: rgba(28, 231, 131, 0.65);
    background: transparent;
    box-shadow: 0 0 0 2px rgba(28, 231, 131, 0.08);
}

.input-error {
    border-color: rgba(239, 68, 68, 0.5) !important;
}

.input-icon {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    color: rgba(255, 255, 255, 0.6);
}

.auth-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: #fff;
    font-size: 0.85rem;
    font-family: inherit;
}

.auth-input::placeholder {
    color: rgba(255, 255, 255, 0.85);
}

.auth-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.toggle-password {
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    display: flex;
}

.eye-icon {
    width: 16px;
    height: 16px;
    color: rgba(255, 255, 255, 0.6);
    transition: color 0.2s;
}

.toggle-password:hover .eye-icon {
    color: rgba(255, 255, 255, 0.7);
}

.field-error {
    font-size: 0.7rem;
    color: #ef4444;
    margin-top: 0.25rem;
}

/* Password strength */
.password-strength {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    margin-top: -0.35rem;
}

.strength-bar {
    flex: 1;
    height: 3px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 3px;
    overflow: hidden;
}

.strength-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease, background 0.4s;
}

.strength-label {
    font-size: 0.65rem;
    font-weight: 500;
    white-space: nowrap;
}

.strength-1 {
    background: #ef4444;
    color: #ef4444;
}

.strength-2 {
    background: #f59e0b;
    color: #f59e0b;
}

.strength-3 {
    background: #eab308;
    color: #eab308;
}

.strength-4 {
    background: #22c55e;
    color: #22c55e;
}

.strength-5 {
    background: #1CE783;
    color: #1CE783;
}

/* Checkbox */
.remember-row {
    margin-bottom: 1.25rem;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: pointer;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.9);
    user-select: none;
}

.auth-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.checkbox-custom {
    width: 16px;
    height: 16px;
    border: 1.5px solid rgba(255, 255, 255, 0.6);
    border-radius: 4px;
    position: relative;
    transition: all 0.2s;
    flex-shrink: 0;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.15);
}

.auth-checkbox:checked+.checkbox-custom {
    background: #1CE783;
    border-color: #1CE783;
}

.auth-checkbox:checked+.checkbox-custom::after {
    content: '';
    position: absolute;
    left: 4px;
    top: 1px;
    width: 5px;
    height: 8px;
    border: solid #0a0e11;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
}

/* Buttons */
.btn-primary {
    width: 100%;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    background: linear-gradient(135deg, #1CE783, #15b86a);
    color: #0a0e11;
    font-weight: 600;
    font-size: 0.85rem;
    border: none;
    border-radius: 0.6rem;
    cursor: pointer;
    transition: all 0.25s ease;
    font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(28, 231, 131, 0.25);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(10, 14, 17, 0.3);
    border-top-color: #0a0e11;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Divider */
.auth-divider {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1rem 0;
}

.auth-divider::before,
.auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.15);
}

.auth-divider span {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.6);
}

/* Google + OTP Row */
.alt-login-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
}

.btn-google-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 40px;
    overflow: hidden;
    border-radius: 0.6rem;
}

.btn-google-wrap.btn-google-disabled {
    opacity: 0.5;
    pointer-events: none;
}

.btn-otp {
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.45);
    border-radius: 0.6rem;
    color: #fff;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
    box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
    transition: all 0.2s;
}

.btn-otp:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.35);
}

.btn-otp:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.otp-icon {
    width: 16px;
    height: 16px;
}

.attempts-note {
    text-align: center;
    margin-top: 0.75rem;
    font-size: 0.65rem;
    color: rgba(255, 182, 32, 0.5);
}

/* OTP section */
.back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.75rem;
    cursor: pointer;
    padding: 0;
    margin-bottom: 1rem;
    font-family: inherit;
}

.back-link:hover {
    color: #1CE783;
}

.back-arrow {
    width: 14px;
    height: 14px;
}

.otp-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.25rem;
}

.otp-desc {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 1.25rem;
}
</style>
