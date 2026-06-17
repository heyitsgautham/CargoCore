<template>
    <div class="tfa-view">
        <!-- Back -->
        <button class="back-link" @click="$router.back()" aria-label="Go back">
            <svg viewBox="0 0 20 20" fill="currentColor" class="back-arrow">
                <path fill-rule="evenodd"
                    d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                    clip-rule="evenodd" />
            </svg>
        </button>

        <!-- Step Indicator -->
        <div class="tfa-steps">
            <div v-for="s in 3" :key="s" class="tfa-step" :class="{ 'ts-active': step === s, 'ts-done': step > s }">
                <span class="ts-dot"></span>
            </div>
        </div>

        <!-- ─── Step 1: Intro ──────────────────────────────── -->
        <div v-if="step === 1" class="step-content">
            <div class="tfa-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="tfa-icon-svg">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </div>
            <h2 class="tfa-title">Enable Two-Factor Authentication</h2>
            <p class="tfa-desc">Add an extra layer of security to your account using Google Authenticator or any
                TOTP-compatible app.</p>

            <div class="tfa-benefits">
                <div class="benefit-item">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="benefit-icon">
                        <path fill-rule="evenodd"
                            d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clip-rule="evenodd" />
                    </svg>
                    <span>Protects against password theft</span>
                </div>
                <div class="benefit-item">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="benefit-icon">
                        <path fill-rule="evenodd"
                            d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clip-rule="evenodd" />
                    </svg>
                    <span>Required for high-security operations</span>
                </div>
                <div class="benefit-item">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="benefit-icon">
                        <path fill-rule="evenodd"
                            d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clip-rule="evenodd" />
                    </svg>
                    <span>Backup codes for account recovery</span>
                </div>
            </div>

            <button class="btn-primary" @click="handleInit" :disabled="auth.loading" aria-label="Set up TFA">
                <span v-if="auth.loading" class="btn-spinner"></span>
                {{ auth.loading ? 'Generating…' : 'Set Up Now' }}
            </button>

            <button class="btn-skip" @click="$router.push(auth.dashboardPath)" aria-label="Skip TFA setup">
                I'll do this later
            </button>
        </div>

        <!-- ─── Step 2: QR Code ────────────────────────────── -->
        <div v-if="step === 2" class="step-content">
            <h2 class="tfa-title">Scan QR Code</h2>
            <p class="tfa-desc">Open Google Authenticator (or any TOTP app) and scan this QR code.</p>

            <!-- QR Code -->
            <div class="qr-container">
                <div class="qr-wrapper">
                    <QRCodeVue :value="auth.tfaQrUrl" :size="180" :margin="2" level="M" render-as="svg"
                        foreground="#1CE783" background="transparent" />
                </div>
            </div>

            <!-- Manual Key -->
            <div class="manual-key">
                <p class="key-label">Or enter this key manually:</p>
                <div class="key-value-wrap">
                    <code class="key-value">{{ auth.tfaSecret }}</code>
                    <button class="key-copy" @click="copyKey" :aria-label="keyCopied ? 'Copied' : 'Copy key'">
                        <svg v-if="!keyCopied" viewBox="0 0 20 20" fill="currentColor" class="copy-icon">
                            <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                            <path
                                d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                        </svg>
                        <svg v-else viewBox="0 0 20 20" fill="currentColor" class="copy-icon copied">
                            <path fill-rule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Verify Code -->
            <p class="verify-label">Enter the 6-digit code from your app:</p>
            <div class="tfa-code-inputs">
                <input v-for="(_, i) in 6" :key="i" :ref="el => { if (el) codeRefs[i] = el }" v-model="codeDigits[i]"
                    type="text" inputmode="numeric" maxlength="1" class="otp-digit"
                    :class="{ 'digit-filled': codeDigits[i] }" @input="onCodeInput(i, $event)"
                    @keydown="onCodeKeydown(i, $event)" @paste="onCodePaste" @focus="$event.target.select()" />
            </div>

            <button class="btn-primary" :disabled="verifyCode.length !== 6 || auth.loading" @click="handleConfirm"
                aria-label="Confirm TFA setup">
                <span v-if="auth.loading" class="btn-spinner"></span>
                {{ auth.loading ? 'Verifying…' : 'Verify & Enable' }}
            </button>
        </div>

        <!-- ─── Step 3: Backup Codes ───────────────────────── -->
        <div v-if="step === 3" class="step-content">
            <div class="success-icon-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="success-svg">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke-linecap="round" />
                    <polyline points="22 4 12 14.01 9 11.01" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </div>

            <h2 class="tfa-title">TFA Enabled Successfully!</h2>
            <p class="tfa-desc">Save these backup recovery codes in a secure place. Each code can only be used once.</p>

            <div class="backup-codes-grid">
                <div v-for="(code, i) in auth.tfaBackupCodes" :key="i" class="backup-code">
                    <span class="code-index">{{ i + 1 }}.</span>
                    <code>{{ code }}</code>
                </div>
            </div>

            <div class="backup-actions">
                <button class="btn-outline" @click="copyAllCodes" aria-label="Copy all backup codes">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="action-icon">
                        <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                        <path
                            d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                    </svg>
                    {{ codesCopied ? 'Copied!' : 'Copy All' }}
                </button>
                <button class="btn-outline" @click="downloadCodes" aria-label="Download backup codes">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="action-icon">
                        <path fill-rule="evenodd"
                            d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                            clip-rule="evenodd" />
                    </svg>
                    Download
                </button>
            </div>

            <div class="warning-box">
                <svg viewBox="0 0 20 20" fill="currentColor" class="warning-icon">
                    <path fill-rule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clip-rule="evenodd" />
                </svg>
                <p>If you lose access to your authenticator app and don't have backup codes, you may be locked out of
                    your account.</p>
            </div>

            <button class="btn-primary" @click="$router.push(auth.dashboardPath)" aria-label="Go to dashboard">
                Go to Dashboard
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useAuthStore } from '../stores/authStore.js'
import QRCodeVue from 'qrcode.vue'

const auth = useAuthStore()
const step = ref(1)
const keyCopied = ref(false)
const codesCopied = ref(false)

// Code input
const codeDigits = reactive(['', '', '', '', '', ''])
const codeRefs = reactive([])
const verifyCode = computed(() => codeDigits.join(''))

async function handleInit() {
    const result = await auth.initTFASetup()
    if (result.success) step.value = 2
}

async function handleConfirm() {
    if (verifyCode.value.length !== 6) return
    const result = await auth.confirmTFASetup(verifyCode.value)
    if (result.success) step.value = 3
}

function onCodeInput(i, event) {
    const val = event.target.value.replace(/\D/g, '')
    codeDigits[i] = val ? val[0] : ''
    if (val && i < 5) codeRefs[i + 1]?.focus()
}

function onCodeKeydown(i, event) {
    if (event.key === 'Backspace' && !codeDigits[i] && i > 0) {
        codeDigits[i - 1] = ''
        codeRefs[i - 1]?.focus()
    }
}

function onCodePaste(event) {
    event.preventDefault()
    const p = (event.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
    for (let i = 0; i < 6; i++) codeDigits[i] = p[i] || ''
}

async function copyKey() {
    try {
        await navigator.clipboard.writeText(auth.tfaSecret)
        keyCopied.value = true
        setTimeout(() => keyCopied.value = false, 2000)
    } catch { /* fallback */ }
}

async function copyAllCodes() {
    try {
        await navigator.clipboard.writeText(auth.tfaBackupCodes.join('\n'))
        codesCopied.value = true
        setTimeout(() => codesCopied.value = false, 2000)
    } catch { /* fallback */ }
}

function downloadCodes() {
    const content = `Cargo-Core Backup Recovery Codes\nGenerated: ${new Date().toISOString()}\n${'─'.repeat(40)}\n\n${auth.tfaBackupCodes.map((c, i) => `${i + 1}. ${c}`).join('\n')}\n\nKeep these codes in a safe place. Each code can only be used once.`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'cargo-core-recovery-codes.txt'
    a.click()
    URL.revokeObjectURL(url)
}
</script>

<style scoped>
.tfa-view {
    width: 100%;
}

.back-link {
    display: inline-flex;
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

/* ── Steps ─────────────────────────────────── */
.tfa-steps {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 2rem;
}

.tfa-step .ts-dot {
    display: block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    transition: all 0.3s;
}

.ts-active .ts-dot {
    background: #1CE783;
    box-shadow: 0 0 8px rgba(28, 231, 131, 0.3);
    width: 24px;
    border-radius: 4px;
}

.ts-done .ts-dot {
    background: rgba(28, 231, 131, 0.4);
}

.step-content {
    text-align: center;
    animation: fade-up 0.35s ease;
}

@keyframes fade-up {
    from {
        opacity: 0;
        transform: translateY(12px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── Intro ─────────────────────────────────── */
.tfa-icon-wrap {
    width: 72px;
    height: 72px;
    margin: 0 auto 1.5rem;
    border-radius: 50%;
    background: rgba(28, 231, 131, 0.08);
    border: 1px solid rgba(28, 231, 131, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
}

.tfa-icon-svg {
    width: 32px;
    height: 32px;
    color: #1CE783;
}

.tfa-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
}

.tfa-desc {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.6;
    margin-bottom: 1.5rem;
    max-width: 360px;
    margin-left: auto;
    margin-right: auto;
}

.tfa-benefits {
    text-align: left;
    max-width: 300px;
    margin: 0 auto 2rem;
}

.benefit-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.6rem;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.95);
}

.benefit-icon {
    width: 18px;
    height: 18px;
    color: #1CE783;
    flex-shrink: 0;
}

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

.btn-skip {
    display: block;
    width: 100%;
    margin-top: 0.75rem;
    padding: 0.6rem;
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    transition: color 0.2s;
}

.btn-skip:hover {
    color: rgba(255, 255, 255, 0.75);
}

/* ── QR Code ───────────────────────────────── */
.qr-container {
    display: flex;
    justify-content: center;
    margin-bottom: 1.5rem;
}

.qr-wrapper {
    padding: 1.25rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 1rem;
}

.manual-key {
    margin-bottom: 1.5rem;
}

.key-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 0.4rem;
}

.key-value-wrap {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.75rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 0.5rem;
}

.key-value {
    font-size: 0.85rem;
    color: #1CE783;
    letter-spacing: 0.15em;
    font-family: monospace;
}

.key-copy {
    background: none;
    border: none;
    padding: 0.2rem;
    cursor: pointer;
    display: flex;
}

.copy-icon {
    width: 16px;
    height: 16px;
    color: rgba(255, 255, 255, 0.5);
    transition: color 0.2s;
}

.copy-icon.copied {
    color: #1CE783;
}

.key-copy:hover .copy-icon {
    color: rgba(255, 255, 255, 0.8);
}

.verify-label {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 0.75rem;
}

.tfa-code-inputs {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.otp-digit {
    width: 44px;
    height: 52px;
    background: rgba(255, 255, 255, 0.04);
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    color: #fff;
    font-size: 1.35rem;
    font-weight: 700;
    font-family: 'Inter', monospace;
    text-align: center;
    outline: none;
    transition: all 0.2s;
}

.otp-digit:focus {
    border-color: rgba(28, 231, 131, 0.6);
    background: rgba(28, 231, 131, 0.05);
    box-shadow: 0 0 0 3px rgba(28, 231, 131, 0.1);
}

.digit-filled {
    border-color: rgba(28, 231, 131, 0.3);
}

/* ── Backup Codes ──────────────────────────── */
.success-icon-wrap {
    width: 64px;
    height: 64px;
    margin: 0 auto 1.25rem;
    background: rgba(28, 231, 131, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.success-svg {
    width: 32px;
    height: 32px;
    color: #1CE783;
}

.backup-codes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 1.25rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 0.75rem;
}

.backup-code {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.5rem;
}

.code-index {
    font-size: 0.65rem;
    color: rgba(255, 255, 255, 0.6);
    min-width: 16px;
}

.backup-code code {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.75);
    letter-spacing: 0.05em;
    font-family: monospace;
}

.backup-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
    margin-bottom: 1.25rem;
}

.btn-outline {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    color: rgba(255, 255, 255, 0.95);
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
}

.btn-outline:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
}

.action-icon {
    width: 16px;
    height: 16px;
}

.warning-box {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
    margin-bottom: 1.5rem;
    background: rgba(255, 176, 32, 0.06);
    border: 1px solid rgba(255, 176, 32, 0.15);
    border-radius: 0.75rem;
    text-align: left;
}

.warning-icon {
    width: 20px;
    height: 20px;
    color: #FFB020;
    flex-shrink: 0;
    margin-top: 0.1rem;
}

.warning-box p {
    font-size: 0.75rem;
    color: rgba(255, 176, 32, 0.8);
    line-height: 1.5;
}
</style>
