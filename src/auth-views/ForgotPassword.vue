<template>
    <div class="forgot-view">

        <!-- Step 1: Enter email -->
        <template v-if="step === 1">
            <div class="forgot-header">
                <div class="icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="2" y="7" width="20" height="14" rx="2" />
                        <path d="M16 3H8a2 2 0 00-2 2v2h12V5a2 2 0 00-2-2z" />
                        <path d="M12 13v4M10 15h4" stroke-linecap="round" />
                    </svg>
                </div>
                <h2 class="forgot-title">Forgot Password?</h2>
                <p class="forgot-subtitle">Enter your registered email and we'll send a reset link.</p>
            </div>

            <form @submit.prevent="sendReset" novalidate>
                <div class="field-group">
                    <label for="forgot-email" class="field-label">Email address</label>
                    <div class="input-wrap" :class="{ 'input-error': error }">
                        <svg class="input-icon" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                        </svg>
                        <input id="forgot-email" v-model="email" type="email" placeholder="you@company.com"
                            class="auth-input" autocomplete="email" :disabled="loading" @blur="validate" />
                    </div>
                    <p v-if="error" class="field-error">{{ error }}</p>
                </div>

                <button class="btn-primary" type="submit" :disabled="loading || !email">
                    <span v-if="loading" class="btn-spinner"></span>
                    {{ loading ? 'Sending…' : 'Send Reset Link' }}
                </button>
            </form>
        </template>

        <!-- Step 2: Email sent confirmation -->
        <template v-else>
            <div class="success-wrap">
                <div class="success-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#1CE783" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h2 class="forgot-title">Check your inbox</h2>
                <p class="forgot-subtitle">
                    We sent a password reset link to<br />
                    <span class="email-highlight">{{ email }}</span>
                </p>
                <p class="resend-text">
                    Didn't receive it?
                    <button class="resend-btn" :disabled="resendCooldown > 0" @click="resend">
                        {{ resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend email' }}
                    </button>
                </p>
            </div>
        </template>

        <!-- Back to login -->
        <router-link to="/login" class="back-row">
            <svg viewBox="0 0 20 20" fill="currentColor" class="back-arrow">
                <path fill-rule="evenodd"
                    d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                    clip-rule="evenodd" />
            </svg>
            Back to login
        </router-link>

    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/authStore.js'

const auth = useAuthStore()
const email = ref('')
const error = ref('')
const loading = ref(false)
const step = ref(1)
const resendCooldown = ref(0)

const validate = () => {
    if (!email.value) { error.value = 'Email is required'; return false }
    if (!/\S+@\S+\.\S+/.test(email.value)) { error.value = 'Enter a valid email address'; return false }
    error.value = ''
    return true
}

const startCooldown = () => {
    resendCooldown.value = 60
    const t = setInterval(() => {
        resendCooldown.value--
        if (resendCooldown.value <= 0) clearInterval(t)
    }, 1000)
}

const sendReset = async () => {
    if (!validate()) return
    loading.value = true
    auth.clearError()
    const result = await auth.sendPasswordResetOTP(email.value)
    loading.value = false
    if (result.success) {
        step.value = 2
        startCooldown()
    } else {
        error.value = auth.error || 'Failed to send reset link.'
    }
}

const resend = async () => {
    loading.value = true
    auth.clearError()
    const result = await auth.sendPasswordResetOTP(email.value)
    loading.value = false
    if (result.success) startCooldown()
    else error.value = auth.error || 'Failed to resend.'
}
</script>

<style scoped>
.forgot-view {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 0.5rem 0;
}

.forgot-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    text-align: center;
}

.icon-wrap {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(28, 231, 131, 0.08);
    border: 1.5px solid rgba(28, 231, 131, 0.4);
    box-shadow: 0 0 24px rgba(28, 231, 131, 0.15), inset 0 0 12px rgba(28, 231, 131, 0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.25rem;
}

.icon-wrap svg {
    width: 28px;
    height: 28px;
    color: #1CE783;
}

.forgot-title {
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(90deg, #fff 30%, #1CE783);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}

.forgot-subtitle {
    font-size: 0.875rem;
    color: rgb(255, 255, 255);
    line-height: 1.6;
    margin: 0;
}

/* Fields (inherits from AuthLayout's global auth styles) */
.field-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-bottom: 1.25rem;
}

.field-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: rgb(255, 255, 255);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.input-wrap {
    position: relative;
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 0.6rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrap:focus-within {
    border-color: rgba(28, 231, 129, 0.828);
    box-shadow: 0 0 0 3px rgba(28, 231, 131, 0.08);
}

.input-error {
    border-color: rgba(239, 68, 68, 0.5) !important;
}

.input-icon {
    width: 16px;
    height: 16px;
    color: rgba(28, 231, 129, 0.809);
    position: absolute;
    left: 0.85rem;
    flex-shrink: 0;
}

.auth-input {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    padding: 0.7rem 0.85rem 0.7rem 2.5rem;
    font-size: 0.875rem;
    color: #fff;
    font-family: inherit;
}

.auth-input::placeholder {
    color: rgba(255, 255, 255, 0.814);
}

.auth-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.field-error {
    font-size: 0.72rem;
    color: #f87171;
    margin: 0;
}

.btn-primary {
    width: 100%;
    padding: 0.75rem;
    border-radius: 0.6rem;
    background: linear-gradient(135deg, #1CE783 0%, #0ea86a 100%);
    border: none;
    color: #000;
    font-size: 0.875rem;
    font-weight: 700;
    font-family: inherit;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    letter-spacing: 0.01em;
    transition: filter 0.2s, transform 0.15s, box-shadow 0.2s;
    box-shadow: 0 4px 18px rgba(28, 231, 131, 0.3);
}

.btn-primary:hover:not(:disabled) {
    filter: brightness(1.08);
    box-shadow: 0 6px 24px rgba(28, 231, 131, 0.45);
    transform: translateY(-1px);
}

.btn-primary:active:not(:disabled) {
    transform: translateY(0);
}

.btn-primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    box-shadow: none;
}

.btn-spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(0, 0, 0, 0.2);
    border-top-color: #000;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Success state */
.success-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.85rem;
    text-align: center;
    padding: 1rem 0;
}

.success-icon {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: rgba(28, 231, 131, 0.1);
    border: 1.5px solid rgba(28, 231, 131, 0.45);
    box-shadow: 0 0 32px rgba(28, 231, 131, 0.2), inset 0 0 16px rgba(28, 231, 131, 0.06);
    display: flex;
    align-items: center;
    justify-content: center;
}

.success-icon svg {
    width: 30px;
    height: 30px;
}

.email-highlight {
    color: #1CE783;
    font-weight: 600;
}

.resend-text {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.45);
    margin: 0;
}

.resend-btn {
    background: none;
    border: none;
    color: #1CE783;
    font-size: 0.8rem;
    font-family: inherit;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
    padding: 0;
    transition: color 0.2s;
}

.resend-btn:hover:not(:disabled) {
    color: #4fffaa;
}

.resend-btn:disabled {
    cursor: not-allowed;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.3);
}

/* Back link */
.back-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: rgba(28, 231, 131, 0.65);
    text-decoration: none;
    justify-content: center;
    transition: color 0.2s;
}

.back-row:hover {
    color: #1CE783;
}

.back-arrow {
    width: 14px;
    height: 14px;
}
</style>
