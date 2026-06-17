<template>
    <div class="otp-view">
        <!-- Back -->
        <button class="back-link" @click="goBack" aria-label="Go back">
            <svg viewBox="0 0 20 20" fill="currentColor" class="back-arrow">
                <path fill-rule="evenodd"
                    d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                    clip-rule="evenodd" />
            </svg>
        </button>

        <!-- Icon -->
        <div class="otp-icon-wrap">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="otp-icon-svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0110 0v4" />
                <circle cx="12" cy="16" r="1" />
            </svg>
        </div>

        <!-- Header -->
        <h2 class="otp-title">{{ isTfa ? 'Two-Factor Authentication' : 'Enter verification code' }}</h2>
        <p class="otp-desc">
            {{ isTfa
                ? 'Enter the 6-digit code from your authenticator app.'
                : `We sent a code to ${maskedTarget}. Enter it below.`
            }}
        </p>

        <!-- OTP Inputs -->
        <div class="otp-inputs" role="group" aria-label="OTP code input">
            <input v-for="(_, i) in 6" :key="i" :ref="el => { if (el) inputRefs[i] = el }" v-model="digits[i]"
                type="text" inputmode="numeric" maxlength="1" class="otp-digit"
                :class="{ 'digit-filled': digits[i], 'digit-error': hasError }" :aria-label="`Digit ${i + 1}`"
                autocomplete="one-time-code" @input="onInput(i, $event)" @keydown="onKeydown(i, $event)"
                @paste="onPaste" @focus="$event.target.select()" />
        </div>

        <!-- Error -->
        <p v-if="hasError" class="otp-error" role="alert">
            <svg viewBox="0 0 20 20" fill="currentColor" class="error-icon">
                <path fill-rule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd" />
            </svg>
            {{ auth.error || 'Invalid code. Please try again.' }}
        </p>

        <!-- Verify Button -->
        <button class="btn-primary" :disabled="code.length !== 6 || auth.loading" @click="handleVerify"
            aria-label="Verify code">
            <span v-if="auth.loading" class="btn-spinner"></span>
            {{ auth.loading ? 'Verifying…' : 'Verify' }}
        </button>

        <!-- Resend (OTP only) -->
        <div v-if="!isTfa" class="resend-section">
            <p v-if="resendTimer > 0" class="resend-timer">
                Resend code in <span class="timer-count">{{ resendTimer }}s</span>
            </p>
            <button v-else class="resend-btn" @click="handleResend" :disabled="auth.loading" aria-label="Resend OTP">
                Didn't receive a code? <span class="resend-link">Resend</span>
            </button>
        </div>

        <!-- TFA: use backup code -->
        <div v-if="isTfa" class="backup-section">
            <button class="backup-link" @click="showBackupInput = !showBackupInput">
                Use a backup recovery code
            </button>
            <div v-if="showBackupInput" class="backup-input-wrap">
                <input v-model="backupCode" type="text" placeholder="XXXX-XXXX" class="auth-input backup-field"
                    maxlength="9" />
                <button class="btn-outline-sm" :disabled="!backupCode || auth.loading" @click="handleBackupVerify">
                    Verify
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isTfa = computed(() => route.query.mode === 'tfa')
const digits = reactive(['', '', '', '', '', ''])
const inputRefs = reactive([])
const hasError = ref(false)
const resendTimer = ref(30)
const showBackupInput = ref(false)
const backupCode = ref('')

let timerInterval = null

const code = computed(() => digits.join(''))

const maskedTarget = computed(() => {
    const t = auth.otpTarget
    if (!t) return '***'
    if (t.includes('@')) {
        const [local, domain] = t.split('@')
        return `${local[0]}***@${domain}`
    }
    return t.slice(0, 3) + '****' + t.slice(-2)
})

// ── Input Handlers ─────────────────────────
function onInput(index, event) {
    const val = event.target.value.replace(/\D/g, '')
    digits[index] = val ? val[0] : ''
    hasError.value = false

    if (val && index < 5) {
        inputRefs[index + 1]?.focus()
    }

    // Auto-submit when all 6 digits filled
    if (code.value.length === 6) {
        handleVerify()
    }
}

function onKeydown(index, event) {
    if (event.key === 'Backspace' && !digits[index] && index > 0) {
        digits[index - 1] = ''
        inputRefs[index - 1]?.focus()
    }
    if (event.key === 'ArrowLeft' && index > 0) inputRefs[index - 1]?.focus()
    if (event.key === 'ArrowRight' && index < 5) inputRefs[index + 1]?.focus()
}

function onPaste(event) {
    event.preventDefault()
    const pasted = (event.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    for (let i = 0; i < 6; i++) {
        digits[i] = pasted[i] || ''
    }
    const nextEmpty = pasted.length < 6 ? pasted.length : 5
    inputRefs[nextEmpty]?.focus()

    if (pasted.length === 6) {
        handleVerify()
    }
}

// ── Actions ────────────────────────────────
async function handleVerify() {
    if (code.value.length !== 6) return
    auth.clearError()
    hasError.value = false

    const result = await auth.verifyOTP(code.value, isTfa.value)
    if (result.success) {
        router.push(result.redirect || '/login')
    } else {
        hasError.value = true
        // Clear and refocus
        for (let i = 0; i < 6; i++) digits[i] = ''
        inputRefs[0]?.focus()
    }
}

async function handleResend() {
    auth.clearError()
    hasError.value = false
    await auth.sendOTP(auth.otpTarget)
    resendTimer.value = 30
    startTimer()
}

async function handleBackupVerify() {
    if (!backupCode.value) return
    auth.clearError()
    const result = await auth.verifyOTP(backupCode.value, true)
    if (result.success) {
        router.push(result.redirect || '/login')
    } else {
        hasError.value = true
    }
}

function goBack() {
    router.back()
}

// ── Timer ──────────────────────────────────
function startTimer() {
    clearInterval(timerInterval)
    timerInterval = setInterval(() => {
        if (resendTimer.value > 0) resendTimer.value--
        else clearInterval(timerInterval)
    }, 1000)
}

onMounted(() => {
    if (!isTfa.value) startTimer()
    inputRefs[0]?.focus()
})

onUnmounted(() => clearInterval(timerInterval))
</script>

<style scoped>
.otp-view {
    width: 100%;
    text-align: center;
}

.back-link {
    display: inline-flex;
    align-items: center;
    background: none;
    border: none;
    padding: 0.25rem;
    color: rgba(255, 255, 255, 0.65);
    cursor: pointer;
    position: absolute;
    top: 0;
    left: 0;
    transition: color 0.2s;
}

.back-link:hover {
    color: #1CE783;
}

.back-arrow {
    width: 20px;
    height: 20px;
}

.otp-icon-wrap {
    width: 64px;
    height: 64px;
    margin: 1rem auto 1.25rem;
    border-radius: 50%;
    background: rgba(28, 231, 131, 0.08);
    border: 1px solid rgba(28, 231, 131, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
}

.otp-icon-svg {
    width: 28px;
    height: 28px;
    color: #1CE783;
}

.otp-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
}

.otp-desc {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 2rem;
    line-height: 1.5;
}

/* ── OTP Digit Inputs ──────────────────────── */
.otp-inputs {
    display: flex;
    justify-content: center;
    gap: 0.6rem;
    margin-bottom: 1.5rem;
}

.otp-digit {
    width: 48px;
    height: 56px;
    background: rgba(255, 255, 255, 0.04);
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    color: #fff;
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'Inter', monospace;
    text-align: center;
    outline: none;
    transition: all 0.2s ease;
    caret-color: #1CE783;
}

.otp-digit:focus {
    border-color: rgba(28, 231, 131, 0.6);
    background: rgba(28, 231, 131, 0.05);
    box-shadow: 0 0 0 3px rgba(28, 231, 131, 0.1);
}

.digit-filled {
    border-color: rgba(28, 231, 131, 0.3);
    background: rgba(28, 231, 131, 0.03);
}

.digit-error {
    border-color: rgba(239, 68, 68, 0.5) !important;
    animation: shake 0.4s ease;
}

@keyframes shake {

    0%,
    100% {
        transform: translateX(0);
    }

    25% {
        transform: translateX(-4px);
    }

    75% {
        transform: translateX(4px);
    }
}

/* ── Error ─────────────────────────────────── */
.otp-error {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    color: #ef4444;
    margin-bottom: 1.25rem;
}

.error-icon {
    width: 16px;
    height: 16px;
}

/* ── Button ────────────────────────────────── */
.btn-primary {
    width: 100%;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, #1CE783, #15b86a);
    color: #0a0e11;
    font-weight: 600;
    font-size: 0.9rem;
    border: none;
    border-radius: 0.75rem;
    cursor: pointer;
    transition: all 0.25s ease;
    font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(28, 231, 131, 0.25);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-spinner {
    width: 18px;
    height: 18px;
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

/* ── Resend ────────────────────────────────── */
.resend-section {
    margin-top: 1.5rem;
}

.resend-timer {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.8);
}

.timer-count {
    color: #1CE783;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

.resend-btn {
    background: none;
    border: none;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    font-family: inherit;
    padding: 0.25rem;
}

.resend-link {
    color: #1CE783;
    font-weight: 500;
}

.resend-btn:hover .resend-link {
    text-decoration: underline;
}

/* ── Backup Code ───────────────────────────── */
.backup-section {
    margin-top: 2rem;
}

.backup-link {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    text-decoration: underline;
    text-underline-offset: 2px;
}

.backup-link:hover {
    color: rgba(255, 255, 255, 0.8);
}

.backup-input-wrap {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
    justify-content: center;
}

.backup-field {
    width: 140px;
    text-align: center;
    padding: 0.5rem 0.75rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    color: #fff;
    font-size: 0.9rem;
    font-family: monospace;
    outline: none;
}

.backup-field:focus {
    border-color: rgba(28, 231, 131, 0.5);
}

.btn-outline-sm {
    padding: 0.5rem 1rem;
    background: rgba(28, 231, 131, 0.1);
    border: 1px solid rgba(28, 231, 131, 0.35);
    border-radius: 0.5rem;
    color: #1CE783;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
}

.btn-outline-sm:hover:not(:disabled) {
    background: rgba(28, 231, 131, 0.15);
}

.btn-outline-sm:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
