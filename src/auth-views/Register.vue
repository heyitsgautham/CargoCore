<template>
    <div class="register-view animate-view">
        <!-- Header -->
        <div class="reg-header">
            <h2 class="reg-title">Create your account</h2>
            <p class="reg-subtitle">Join as a Vendor or Customer</p>
        </div>

        <!-- Step Dots -->
        <div class="step-dots" role="progressbar" :aria-valuenow="currentStep" aria-valuemin="1" aria-valuemax="3">
            <div v-for="s in 3" :key="s" class="dot-item"
                :class="{ 'dot-active': currentStep === s, 'dot-done': currentStep > s }">
                <span class="dot-circle">
                    <svg v-if="currentStep > s" viewBox="0 0 20 20" fill="currentColor" class="dot-check">
                        <path fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd" />
                    </svg>
                    <span v-else class="dot-num">{{ s }}</span>
                </span>
                <span class="dot-label">{{ ['Role', 'Details', 'Profile'][s - 1] }}</span>
            </div>
            <div class="dot-line">
                <div class="dot-line-fill" :style="{ width: ((currentStep - 1) / 2) * 100 + '%' }"></div>
            </div>
        </div>

        <form @submit.prevent="handleNext" novalidate>
            <!-- ─── STEP 1: Role ─────────────────────── -->
            <div v-if="currentStep === 1" class="step-content">
                <div class="role-grid">
                    <button type="button" class="role-card" :class="{ 'role-selected': form.role === 'customer' }"
                        @click="form.role = 'customer'">
                        <div class="role-icon customer-ic">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                            </svg>
                        </div>
                        <div>
                            <h4 class="role-name">Customer</h4>
                            <p class="role-desc">Ship packages with ease</p>
                        </div>
                        <div v-if="form.role === 'customer'" class="role-tick"><svg viewBox="0 0 20 20"
                                fill="currentColor">
                                <path fill-rule="evenodd"
                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                    clip-rule="evenodd" />
                            </svg></div>
                    </button>
                    <button type="button" class="role-card" :class="{ 'role-selected': form.role === 'vendor' }"
                        @click="form.role = 'vendor'">
                        <div class="role-icon vendor-ic">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                                <polyline points="9 22 9 12 15 12 15 22" />
                            </svg>
                        </div>
                        <div>
                            <h4 class="role-name">Vendor</h4>
                            <p class="role-desc">Manage bulk shipments</p>
                        </div>
                        <span class="role-badge">Approval</span>
                        <div v-if="form.role === 'vendor'" class="role-tick"><svg viewBox="0 0 20 20"
                                fill="currentColor">
                                <path fill-rule="evenodd"
                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                    clip-rule="evenodd" />
                            </svg></div>
                    </button>
                </div>
                <p v-if="errors.role" class="field-error" role="alert">{{ errors.role }}</p>
            </div>

            <!-- ─── STEP 2: Details ──────────────────── -->
            <div v-if="currentStep === 2" class="step-content">
                <div class="field-row">
                    <div class="field-group">
                        <label for="r-name" class="field-label">Full Name</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.fullName }">
                            <input id="r-name" v-model="form.fullName" type="text" placeholder="John Doe"
                                class="auth-input" autocomplete="name" />
                        </div>
                        <p v-if="errors.fullName" class="field-error">{{ errors.fullName }}</p>
                    </div>
                    <div class="field-group">
                        <label for="r-phone" class="field-label">Phone</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.phone }">
                            <input id="r-phone" v-model="form.phone" type="tel" placeholder="+91 98765 43210"
                                class="auth-input" autocomplete="tel" />
                        </div>
                        <p v-if="errors.phone" class="field-error">{{ errors.phone }}</p>
                    </div>
                </div>

                <div class="field-group">
                    <label for="r-email" class="field-label">Email</label>
                    <div class="input-wrap" :class="{ 'input-error': errors.email }">
                        <input id="r-email" v-model="form.email" type="email" placeholder="you@company.com"
                            class="auth-input" autocomplete="email" />
                    </div>
                    <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
                </div>

                <div class="field-row">
                    <div class="field-group">
                        <label for="r-pw" class="field-label">Password</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.password }">
                            <input id="r-pw" v-model="form.password" :type="showPw ? 'text' : 'password'"
                                placeholder="Min 8 chars" class="auth-input" autocomplete="new-password" />
                            <button type="button" class="toggle-pw" @click="showPw = !showPw" tabindex="-1">
                                <svg viewBox="0 0 20 20" fill="currentColor" class="eye-icon">
                                    <path v-if="!showPw" d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                    <path v-if="!showPw" fill-rule="evenodd"
                                        d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                                        clip-rule="evenodd" />
                                    <path v-if="showPw" fill-rule="evenodd"
                                        d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                                        clip-rule="evenodd" />
                                    <path v-if="showPw"
                                        d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                                </svg>
                            </button>
                        </div>
                        <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
                    </div>
                    <div class="field-group">
                        <label for="r-cpw" class="field-label">Confirm Password</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.confirmPassword }">
                            <input id="r-cpw" v-model="form.confirmPassword" type="password" placeholder="Re-enter"
                                class="auth-input" autocomplete="new-password" />
                        </div>
                        <p v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</p>
                    </div>
                </div>

                <!-- Strength -->
                <div v-if="form.password" class="password-strength">
                    <div class="strength-bar">
                        <div class="strength-fill" :style="{ width: strengthPercent + '%' }" :class="strengthClass">
                        </div>
                    </div>
                    <span class="strength-label" :class="strengthClass">{{ strengthLabel }}</span>
                </div>

                <label class="checkbox-label" for="r-terms">
                    <input id="r-terms" v-model="form.acceptTerms" type="checkbox" class="auth-checkbox" />
                    <span class="checkbox-custom"></span>
                    <span>I agree to <a href="#" class="terms-link">Terms</a> & <a href="#"
                            class="terms-link">Privacy</a></span>
                </label>
                <p v-if="errors.acceptTerms" class="field-error">{{ errors.acceptTerms }}</p>
            </div>

            <!-- ─── STEP 3: Role-Specific ────────────── -->
            <div v-if="currentStep === 3" class="step-content">
                <!-- Customer -->
                <div v-if="form.role === 'customer'">
                    <div class="field-group">
                        <label for="c-addr" class="field-label">Default Pickup Address</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.pickupAddress }">
                            <input id="c-addr" v-model="form.pickupAddress" type="text" placeholder="123 Main Street"
                                class="auth-input" />
                        </div>
                        <p v-if="errors.pickupAddress" class="field-error">{{ errors.pickupAddress }}</p>
                    </div>
                    <div class="field-row field-row-3">
                        <div class="field-group">
                            <label for="c-city" class="field-label">City</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.city }"><input id="c-city"
                                    v-model="form.city" type="text" placeholder="Mumbai" class="auth-input" /></div>
                            <p v-if="errors.city" class="field-error">{{ errors.city }}</p>
                        </div>
                        <div class="field-group">
                            <label for="c-state" class="field-label">State</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.state }"><input id="c-state"
                                    v-model="form.state" type="text" placeholder="Maharashtra" class="auth-input" />
                            </div>
                            <p v-if="errors.state" class="field-error">{{ errors.state }}</p>
                        </div>
                        <div class="field-group">
                            <label for="c-pin" class="field-label">Pincode</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.pincode }"><input id="c-pin"
                                    v-model="form.pincode" type="text" placeholder="400001" class="auth-input"
                                    maxlength="6" /></div>
                            <p v-if="errors.pincode" class="field-error">{{ errors.pincode }}</p>
                        </div>
                    </div>
                </div>

                <!-- Vendor -->
                <div v-if="form.role === 'vendor'">
                    <div class="field-row">
                        <div class="field-group">
                            <label for="v-co" class="field-label">Company Name</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.companyName }"><input id="v-co"
                                    v-model="form.companyName" type="text" placeholder="Acme Logistics"
                                    class="auth-input" /></div>
                            <p v-if="errors.companyName" class="field-error">{{ errors.companyName }}</p>
                        </div>
                        <div class="field-group">
                            <label for="v-gst" class="field-label">GST / Tax ID</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.gstTaxId }"><input id="v-gst"
                                    v-model="form.gstTaxId" type="text" placeholder="22AAAAA0000A1Z5"
                                    class="auth-input" /></div>
                            <p v-if="errors.gstTaxId" class="field-error">{{ errors.gstTaxId }}</p>
                        </div>
                    </div>

                    <div class="field-group">
                        <label for="v-addr" class="field-label">Business Address</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.businessAddress }"><input id="v-addr"
                                v-model="form.businessAddress" type="text" placeholder="Business address"
                                class="auth-input" /></div>
                        <p v-if="errors.businessAddress" class="field-error">{{ errors.businessAddress }}</p>
                    </div>

                    <div class="field-row">
                        <div class="field-group">
                            <label for="v-cp" class="field-label">Contact Person</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.contactPerson }"><input id="v-cp"
                                    v-model="form.contactPerson" type="text" placeholder="Full name"
                                    class="auth-input" /></div>
                            <p v-if="errors.contactPerson" class="field-error">{{ errors.contactPerson }}</p>
                        </div>
                        <div class="field-group">
                            <label for="v-bp" class="field-label">Business Phone</label>
                            <div class="input-wrap" :class="{ 'input-error': errors.businessPhone }"><input id="v-bp"
                                    v-model="form.businessPhone" type="tel" placeholder="+91 22 1234 5678"
                                    class="auth-input" /></div>
                            <p v-if="errors.businessPhone" class="field-error">{{ errors.businessPhone }}</p>
                        </div>
                    </div>

                    <div class="field-group">
                        <label for="v-be" class="field-label">Business Email</label>
                        <div class="input-wrap" :class="{ 'input-error': errors.businessEmail }"><input id="v-be"
                                v-model="form.businessEmail" type="email" placeholder="info@company.com"
                                class="auth-input" /></div>
                        <p v-if="errors.businessEmail" class="field-error">{{ errors.businessEmail }}</p>
                    </div>
                </div>
            </div>

            <!-- Success -->
            <div v-if="submitted" class="submit-success">
                <div class="success-icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="success-svg">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke-linecap="round" />
                        <polyline points="22 4 12 14.01 9 11.01" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                </div>
                <h3 v-if="form.role === 'vendor'" class="success-title">Submitted!</h3>
                <h3 v-else class="success-title">Account Created!</h3>
                <p v-if="form.role === 'vendor'" class="success-desc">Pending admin approval. We will email you once
                    approved.</p>
                <p v-else class="success-desc">You can now sign in with your credentials.</p>
            </div>

            <!-- Nav Buttons -->
            <div v-if="!submitted" class="step-nav">
                <button v-if="currentStep > 1" type="button" class="btn-back" @click="currentStep--">
                    <svg viewBox="0 0 20 20" fill="currentColor" class="nav-arrow">
                        <path fill-rule="evenodd"
                            d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                            clip-rule="evenodd" />
                    </svg>
                    Back
                </button>
                <div v-else></div>
                <button type="submit" class="btn-primary btn-next" :disabled="auth.loading">
                    <span v-if="auth.loading" class="btn-spinner"></span>
                    {{ currentStep === 3 ? (auth.loading ? 'Creating…' : 'Create Account') : 'Continue' }}
                    <svg v-if="currentStep < 3" viewBox="0 0 20 20" fill="currentColor" class="nav-arrow">
                        <path fill-rule="evenodd"
                            d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                            clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        </form>
    </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const router = useRouter()
const auth = useAuthStore()
const currentStep = ref(1)
const submitted = ref(false)
const showPw = ref(false)

const form = reactive({
    role: '', fullName: '', email: '', phone: '', password: '', confirmPassword: '', acceptTerms: false,
    pickupAddress: '', city: '', state: '', pincode: '',
    companyName: '', businessAddress: '', gstTaxId: '', contactPerson: '', businessPhone: '', businessEmail: ''
})

const errors = reactive({})

// Password strength
const passwordStrength = computed(() => { const p = form.password; if (!p) return 0; let s = 0; if (p.length >= 8) s++; if (p.length >= 12) s++; if (/[a-z]/.test(p) && /[A-Z]/.test(p)) s++; if (/\d/.test(p)) s++; if (/[^a-zA-Z0-9]/.test(p)) s++; return s })
const strengthPercent = computed(() => (passwordStrength.value / 5) * 100)
const strengthLabel = computed(() => ['', 'Very weak', 'Weak', 'Fair', 'Strong', 'Excellent'][passwordStrength.value])
const strengthClass = computed(() => ['', 'strength-1', 'strength-2', 'strength-3', 'strength-4', 'strength-5'][passwordStrength.value])

function clearErrors() { Object.keys(errors).forEach(k => errors[k] = '') }

function validateStep1() { clearErrors(); if (!form.role) errors.role = 'Select a role'; return !errors.role }

function validateStep2() {
    clearErrors()
    if (!form.fullName.trim()) errors.fullName = 'Required'
    if (!form.email) errors.email = 'Required'; else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Invalid email'
    if (!form.phone.trim()) errors.phone = 'Required'
    if (!form.password) errors.password = 'Required'; else if (form.password.length < 8) errors.password = 'Min 8 chars'; else if (!/[A-Z]/.test(form.password)) errors.password = 'Need uppercase'; else if (!/[a-z]/.test(form.password)) errors.password = 'Need lowercase'; else if (!/\d/.test(form.password)) errors.password = 'Need a number'
    if (!form.confirmPassword) errors.confirmPassword = 'Required'; else if (form.confirmPassword !== form.password) errors.confirmPassword = 'Mismatch'
    if (!form.acceptTerms) errors.acceptTerms = 'Must accept'
    return !Object.values(errors).some(Boolean)
}

function validateStep3() {
    clearErrors()
    if (form.role === 'customer') {
        if (!form.pickupAddress.trim()) errors.pickupAddress = 'Required'; if (!form.city.trim()) errors.city = 'Required'
        if (!form.state.trim()) errors.state = 'Required'; if (!form.pincode.trim()) errors.pincode = 'Required'; else if (!/^\d{6}$/.test(form.pincode)) errors.pincode = 'Invalid'
    } else {
        if (!form.companyName.trim()) errors.companyName = 'Required'; if (!form.businessAddress.trim()) errors.businessAddress = 'Required'
        if (!form.gstTaxId.trim()) errors.gstTaxId = 'Required'; if (!form.contactPerson.trim()) errors.contactPerson = 'Required'
        if (!form.businessPhone.trim()) errors.businessPhone = 'Required'
        if (!form.businessEmail) errors.businessEmail = 'Required'; else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.businessEmail)) errors.businessEmail = 'Invalid email'
    }
    return !Object.values(errors).some(Boolean)
}

async function handleNext() {
    if (currentStep.value === 1 && validateStep1()) currentStep.value = 2
    else if (currentStep.value === 2 && validateStep2()) currentStep.value = 3
    else if (currentStep.value === 3 && validateStep3()) {
        auth.clearError()
        const result = await auth.register({ ...form })
        if (result.success) {
            router.push('/verify-otp?mode=registration')
        }
    }
}

function resetForm() {
    currentStep.value = 1
    submitted.value = false
    showPw.value = false
    Object.assign(form, {
        role: '', fullName: '', email: '', phone: '', password: '', confirmPassword: '', acceptTerms: false,
        pickupAddress: '', city: '', state: '', pincode: '',
        companyName: '', businessAddress: '', gstTaxId: '', contactPerson: '', businessPhone: '', businessEmail: ''
    })
    clearErrors()
}

defineExpose({ resetForm })
</script>

<style scoped>
.register-view {
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

@keyframes fade-in-up {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.reg-header {
    margin-bottom: 1.25rem;
}

.reg-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #fff;
    margin-bottom: 0.15rem;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
}

.reg-subtitle {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.95);
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
}

/* Step dots */
.step-dots {
    display: flex;
    justify-content: space-between;
    position: relative;
    margin-bottom: 1.5rem;
    padding: 0 1rem;
}

.dot-line {
    position: absolute;
    top: 11px;
    left: 50px;
    right: 50px;
    height: 2px;
    background: rgba(255, 255, 255, 0.15);
    z-index: 0;
}

.dot-line-fill {
    height: 100%;
    background: #1CE783;
    border-radius: 2px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.dot-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    position: relative;
    z-index: 1;
}

.dot-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    font-weight: 600;
    background: transparent;
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    transition: all 0.3s;
}

.dot-active .dot-circle {
    background: transparent;
    border-color: #1CE783;
    color: #1CE783;
    box-shadow: 0 0 8px rgba(28, 231, 131, 0.2);
}

.dot-done .dot-circle {
    background: #1CE783;
    border-color: #1CE783;
    color: #0a0e11;
}

.dot-check {
    width: 14px;
    height: 14px;
}

.dot-num {
    font-size: 0.6rem;
}

.dot-label {
    font-size: 0.55rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255, 255, 255, 0.7);
}

.dot-active .dot-label {
    color: #1CE783;
}

/* Step content animation */
.step-content {
    animation: step-in 0.3s ease;
}

@keyframes step-in {
    from {
        opacity: 0;
        transform: translateX(12px);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Role cards */
.role-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
}

.role-card {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.9rem 0.75rem;
    background: transparent;
    border: 1.5px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.05);
    border-radius: 0.75rem;
    cursor: pointer;
    transition: all 0.25s;
    text-align: left;
    font-family: inherit;
    color: #fff;
}

.role-card:hover {
    border-color: rgba(255, 255, 255, 0.6);
    box-shadow: 0 0 12px rgba(255, 255, 255, 0.15);
    background: transparent;
}

.role-selected {
    border-color: rgba(28, 231, 131, 0.8) !important;
    box-shadow: 0 0 15px rgba(28, 231, 131, 0.25) !important;
    background: transparent !important;
}

.role-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.role-icon svg {
    width: 20px;
    height: 20px;
}

.customer-ic {
    background: transparent;
    color: #44a8e9;
}

.vendor-ic {
    background: transparent;
    color: #a844e9;
}

.role-name {
    font-size: 0.85rem;
    font-weight: 600;
}

.role-desc {
    font-size: 0.65rem;
    color: rgba(255, 255, 255, 0.8);
}

.role-badge {
    position: absolute;
    top: 0.4rem;
    right: 0.4rem;
    padding: 0.1rem 0.35rem;
    font-size: 0.5rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    background: rgba(255, 176, 32, 0.12);
    color: #FFB020;
    border-radius: 3px;
}

.role-tick {
    position: absolute;
    bottom: 0.4rem;
    right: 0.4rem;
    width: 18px;
    height: 18px;
    background: #1CE783;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pop-in 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.role-tick svg {
    width: 12px;
    height: 12px;
    color: #0a0e11;
}

@keyframes pop-in {
    from {
        transform: scale(0);
    }

    to {
        transform: scale(1);
    }
}

/* Field system */
.field-group {
    margin-bottom: 0.75rem;
}

.field-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 500;
    color: #fff;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.25);
    margin-bottom: 0.25rem;
}

.field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
}

.field-row-3 {
    grid-template-columns: 1fr 1fr 1fr;
}

.input-wrap {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0 0.65rem;
    height: 38px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
    border-radius: 0.55rem;
    transition: all 0.25s;
}

.input-wrap:focus-within {
    border-color: rgba(28, 231, 131, 0.65);
    background: transparent;
    box-shadow: 0 0 0 2px rgba(28, 231, 131, 0.08);
}

.input-error {
    border-color: rgba(239, 68, 68, 0.5) !important;
}

.auth-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: #fff;
    font-size: 0.8rem;
    font-family: inherit;
    min-width: 0;
}

.auth-input::placeholder {
    color: rgba(255, 255, 255, 0.85);
}

.field-error {
    font-size: 0.6rem;
    color: #ef4444;
    margin-top: 0.15rem;
}

.toggle-pw {
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    display: flex;
}

.eye-icon {
    width: 14px;
    height: 14px;
    color: rgba(255, 255, 255, 0.25);
}

/* Strength */
.password-strength {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    margin-top: -0.25rem;
}

.strength-bar {
    flex: 1;
    height: 2px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    overflow: hidden;
}

.strength-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease, background 0.4s;
}

.strength-label {
    font-size: 0.6rem;
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
.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    cursor: pointer;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.9);
    user-select: none;
    margin-top: 0.25rem;
}

.auth-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.checkbox-custom {
    width: 15px;
    height: 15px;
    border: 1.5px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    position: relative;
    transition: all 0.2s;
    flex-shrink: 0;
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
    width: 4px;
    height: 8px;
    border: solid #0a0e11;
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
}

.terms-link {
    color: #1CE783;
    text-decoration: none;
}

/* Nav */
.step-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1.25rem;
    gap: 0.75rem;
}

.btn-back {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 0.55rem;
    color: rgba(255, 255, 255, 0.95);
    font-size: 0.8rem;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
}

.btn-back:hover {
    background: transparent;
    border-color: rgba(255, 255, 255, 0.2);
    color: #fff;
}

.nav-arrow {
    width: 14px;
    height: 14px;
}

.btn-primary {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.55rem 1.25rem;
    background: linear-gradient(135deg, #1CE783, #15b86a);
    color: #0a0e11;
    font-weight: 600;
    font-size: 0.8rem;
    border: none;
    border-radius: 0.55rem;
    cursor: pointer;
    transition: all 0.25s;
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

.btn-next {
    margin-left: auto;
}

.btn-spinner {
    width: 14px;
    height: 14px;
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

/* Success */
.submit-success {
    text-align: center;
    padding: 1.5rem 0;
    animation: step-in 0.4s ease;
}

.success-icon-wrap {
    width: 52px;
    height: 52px;
    margin: 0 auto 1rem;
    background: rgba(28, 231, 131, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.success-svg {
    width: 26px;
    height: 26px;
    color: #1CE783;
}

.success-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.35rem;
}

.success-desc {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.45);
    line-height: 1.5;
}

@media (max-width: 480px) {
    .role-grid {
        grid-template-columns: 1fr;
    }

    .field-row {
        grid-template-columns: 1fr;
    }

    .field-row-3 {
        grid-template-columns: 1fr;
    }
}
</style>
