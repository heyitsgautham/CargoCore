<template>
  <div class="auth-layout dark text-gray-100 bg-gray-950">
    <!-- Fullscreen Spline 3D Background -->
    <div class="spline-bg" aria-hidden="true">
      <SplineScene scene="https://prod.spline.design/bdC6PhfGQosiy2rT/scene.splinecode" />
    </div>

    <!-- ── Top Navbar ──────────────────────────── -->
    <header class="auth-navbar">
      <div class="auth-brand">
        <img src="@/assets/cargo-core-logo.png" alt="Cargo-Core Logo" class="brand-logo" />
        <div>
          <span class="brand-name">Cargo-Core</span>
          <span class="brand-tagline">Moving What Matters</span>
        </div>
      </div>
      <nav class="auth-nav">
        <router-link to="/" class="nav-link">Home</router-link>
        <router-link to="/about" class="nav-link">About</router-link>
        <router-link to="/article" class="nav-link">Article</router-link>
      </nav>
    </header>

    <!-- ══ Split-Panel Auth Card ══════════════ -->
    <div class="auth-container" :class="{ 'auth-container--single': !showTabs }">
      <div class="auth-glass-card" :class="{ 'card--single': !showTabs, 'has-interacted': hasInteracted }">

        <!-- Two-panel mode (Login / Register) -->
        <template v-if="showTabs">
          <!-- Form panels (both always visible, promo covers one) -->
          <div class="panels-wrapper">

            <!-- Left form slot: Login -->
            <div class="form-panel form-panel--login"
              :class="{ 'is-active-form': hasInteracted && activeTab === 'login' }">
              <div class="auth-scroll-area" v-if="hasInteracted && activeTab === 'login'">
                <LoginView />
              </div>
            </div>

            <!-- Right form slot: Register -->
            <div class="form-panel form-panel--register"
              :class="{ 'is-active-form': hasInteracted && activeTab === 'register' }">
              <div class="auth-scroll-area" v-if="hasInteracted && activeTab === 'register'">
                <RegisterView ref="registerRef" />
              </div>
            </div>
          </div>

          <!-- 3D Folding Promos Overlay -->
          <div class="promos-container">
            <!-- Left Promo (Sign In) -->
            <div class="promo-panel promo-left" :class="{ 'is-folded': hasInteracted && activeTab === 'login' }">
              <div class="promo-inner">
                <div class="promo-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" />
                    <polyline points="10 17 15 12 10 7" />
                    <line x1="15" y1="12" x2="3" y2="12" />
                  </svg>
                </div>
                <h3 class="promo-title">Welcome Back</h3>
                <p class="promo-desc">Already have an account? Sign in to manage your shipments.</p>
                <button class="promo-btn" @click="handlePromoClick('login')">Sign In</button>
              </div>
            </div>

            <!-- Right Promo (Create Account) -->
            <div class="promo-panel promo-right" :class="{ 'is-folded': hasInteracted && activeTab === 'register' }">
              <div class="promo-inner">
                <div class="promo-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <line x1="19" y1="8" x2="19" y2="14" />
                    <line x1="22" y1="11" x2="16" y2="11" />
                  </svg>
                </div>
                <h3 class="promo-title">New Here?</h3>
                <p class="promo-desc">Create an account and start shipping with Cargo-Core today.</p>
                <button class="promo-btn" @click="handlePromoClick('register')">Create Account</button>
              </div>
            </div>
          </div>
        </template>

        <!-- Single-panel mode (VerifyOTP / SetupTFA) -->
        <template v-else>
          <div class="auth-scroll-area auth-scroll-area--single">
            <component :is="currentView" :key="routePath" />
          </div>
        </template>

      </div>
    </div>

    <!-- ── Bottom Footer Bar ──────────────────── -->
    <footer class="auth-footer">
      <p class="footer-copy">&copy; 2026 Cargo-Core Technologies Pvt. Ltd.</p>
    </footer>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast.show" :class="['auth-toast', `toast-${toast.type}`]" role="alert">
        <span class="toast-icon">{{ toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ' }}</span>
        <span>{{ toast.message }}</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineAsyncComponent, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import SplineScene from '../LWDDVI-components/SplineScene.vue'

import LoginView from '../auth-views/Login.vue'
import RegisterView from '../auth-views/Register.vue'

const VerifyOTPView = defineAsyncComponent(() => import('../auth-views/VerifyOTP.vue'))
const SetupTFAView = defineAsyncComponent(() => import('../auth-views/SetupTFA.vue'))
const ForgotPasswordView = defineAsyncComponent(() => import('../auth-views/ForgotPassword.vue'))

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeTab = ref('login')
const slideDirection = ref('slide-left')
const registerRef = ref(null)
const hasInteracted = ref(false)

const routePath = computed(() => route.path)
const showTabs = computed(() => ['/login', '/register'].includes(routePath.value) && routePath.value !== '/forgot-password')
const isRegister = computed(() => activeTab.value === 'register')

const currentView = computed(() => {
  switch (routePath.value) {
    case '/register': return RegisterView
    case '/verify-otp': return VerifyOTPView
    case '/setup-tfa': return SetupTFAView
    case '/forgot-password': return ForgotPasswordView
    default: return LoginView
  }
})

watch(routePath, (path) => {
  if (path === '/register') activeTab.value = 'register'
  else if (path === '/login') activeTab.value = 'login'
}, { immediate: true })

function switchTab(tab) {
  if (tab === activeTab.value) return
  // Reset register form when switching away from it
  if (activeTab.value === 'register' && registerRef.value?.resetForm) {
    registerRef.value.resetForm()
  }
  slideDirection.value = tab === 'register' ? 'slide-left' : 'slide-right'
  activeTab.value = tab
  router.push(tab === 'register' ? '/register' : '/login')
}

function handlePromoClick(tab) {
  hasInteracted.value = true
  switchTab(tab)
}

const toast = ref({ show: false, message: '', type: 'info', timer: null })

function showToast(message, type = 'info', duration = 4000) {
  clearTimeout(toast.value.timer)
  toast.value = { show: true, message, type, timer: setTimeout(() => { toast.value.show = false }, duration) }
}

watch(() => auth.error, (msg) => { if (msg) showToast(msg, 'error') })
watch(() => auth.successMessage, (msg) => { if (msg) showToast(msg, 'success') })

// Force HTML body to black + no scroll while auth layout is active
let originalBodyBg = ''
let originalBodyOverflow = ''
let originalHtmlOverflow = ''
onMounted(() => {
  originalBodyBg = document.body.style.backgroundColor
  originalBodyOverflow = document.body.style.overflow
  originalHtmlOverflow = document.documentElement.style.overflow
  document.body.style.backgroundColor = '#000'
  document.body.style.overflow = 'hidden'
  document.documentElement.style.overflow = 'hidden'
})

onUnmounted(() => {
  document.body.style.backgroundColor = originalBodyBg
  document.body.style.overflow = originalBodyOverflow
  document.documentElement.style.overflow = originalHtmlOverflow
})
</script>

<style scoped>
.auth-layout {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
  background-color: #000;
  color: #fff;
}

/* ── Fullscreen Spline Background ───────────── */
.spline-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  width: 100vw;
  height: 100vh;
}

/* ── Top Navbar ─────────────────────────────── */
.auth-navbar {
  position: fixed;
  top: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  height: 64px;
  width: calc(100% - 3rem);
  max-width: 1200px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  background: rgba(77, 77, 79, 0.007);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 100px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2), 0 0 16px rgba(255, 255, 255, 0.15);
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-logo {
  height: 32px;
  width: auto;
  object-fit: contain;
}

.brand-name {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
  line-height: 1.2;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

.brand-tagline {
  display: block;
  font-size: 0.55rem;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.auth-nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.nav-link {
  padding: 0.4rem 0.9rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
  text-decoration: none;
  border-radius: 999px;
  border: 1px solid transparent;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.nav-link:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.06);
}

/* ══════════════════════════════════════════════
   SPLIT-PANEL AUTH CARD
   ══════════════════════════════════════════════ */

.auth-container {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 1000px;
  padding: 0 1.5rem;
  margin-top: 80px;
  margin-bottom: 48px;
}

.auth-container--single {
  max-width: 520px;
}

.auth-glass-card {
  position: relative;
  width: 100%;
  height: 520px;
  border: 1px solid transparent;
  border-radius: 1.25rem;
  overflow: hidden;
  background: transparent;
  box-shadow: none;
  transition: border-color 0.8s ease, box-shadow 0.8s ease;
}

.auth-glass-card.has-interacted {
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.01);
}

.card--single {
  height: auto;
  max-height: calc(100vh - 160px);
}

/* ── Form Panels (side by side, stationary) ─── */
.panels-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
}

.form-panel {
  width: 50%;
  height: 100%;
  flex-shrink: 0;
  background: transparent;
  backdrop-filter: blur(8px);
  opacity: 0;
  pointer-events: none;
  filter: blur(8px);
  transition: opacity 0.8s cubic-bezier(0.19, 1, 0.22, 1),
    transform 0.8s cubic-bezier(0.19, 1, 0.22, 1),
    filter 0.8s cubic-bezier(0.19, 1, 0.22, 1);
  transform: translateY(30px) scale(0.98);
}

.form-panel.is-active-form {
  opacity: 1;
  pointer-events: auto;
  filter: blur(0px);
  transform: translateY(0) scale(1);
}

/* ── 3D Folding Promos ──────────────────── */
.promos-container {
  position: absolute;
  inset: 0;
  display: flex;
  pointer-events: none;
  perspective: 1500px;
  z-index: 5;
}

.promo-panel {
  width: 50%;
  height: 100%;
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  backdrop-filter: blur(0px);
  transition: transform 1.2s cubic-bezier(0.19, 1, 0.22, 1),
    opacity 1s cubic-bezier(0.19, 1, 0.22, 1),
    filter 1s ease;
  transform-style: preserve-3d;
}

.promo-left {
  transform-origin: left center;
}

.promo-left.is-folded {
  transform: translateZ(200px) rotateY(-110deg) scale(0.9);
  opacity: 0;
  filter: blur(10px);
  pointer-events: none;
}

.promo-right {
  transform-origin: right center;
}

.promo-right.is-folded {
  transform: translateZ(200px) rotateY(110deg) scale(0.9);
  opacity: 0;
  filter: blur(10px);
  pointer-events: none;
}

.promo-content {
  text-align: center;
  padding: 2rem;
  max-width: 300px;
}

.promo-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.promo-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(28, 231, 131, 0.1);
  border: 1px solid rgba(28, 231, 131, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}

.promo-icon svg {
  width: 28px;
  height: 28px;
  color: #1CE783;
}

.promo-title {
  font-size: 1.65rem;
  font-weight: 800;
  color: #fff;
  text-shadow: 0 0 20px rgba(28, 231, 131, 0.4), 0 0 10px rgba(255, 255, 255, 0.3);
}

.promo-desc {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
  line-height: 1.6;
}

.promo-btn {
  margin-top: 0.5rem;
  padding: 0.65rem 2rem;
  border: 1.5px solid rgba(28, 231, 131, 0.5);
  border-radius: 999px;
  background: transparent;
  color: #1CE783;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s ease;
  letter-spacing: 0.02em;
}

.promo-btn:hover {
  background: rgba(28, 231, 131, 0.12);
  border-color: #1CE783;
  box-shadow: 0 0 20px rgba(28, 231, 131, 0.2);
}

/* ── Scrollable Content ─────────────────────── */
.auth-scroll-area {
  padding: 2rem 2rem;
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
}

.auth-scroll-area::-webkit-scrollbar {
  display: none;
}

.auth-scroll-area--single {
  max-height: calc(100vh - 200px);
}

/* ── Bottom Footer Bar ──────────────────────── */
.auth-footer {
  position: fixed;
  bottom: 0.31rem;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  padding: 0.2rem;
  background: transparent;
  z-index: 20;
}

.footer-copy {
  margin-bottom: 0.3rem;
  font-size: 0.7rem;
}

/* ── Toast ──────────────────────────────────── */
.auth-toast {
  position: fixed;
  bottom: 70px;
  right: 1.5rem;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.1rem;
  border-radius: 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2), 0 0 15px rgba(255, 255, 255, 0.1);
}

.toast-icon {
  font-size: 0.9rem;
}

.toast-success {
  color: #1CE783;
  border-color: rgba(28, 231, 131, 0.25);
}

.toast-error {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.25);
}

.toast-info {
  color: #44a8e9;
  border-color: rgba(68, 168, 233, 0.25);
}

.toast-enter-active {
  animation: toast-in 0.35s cubic-bezier(0.215, 0.61, 0.355, 1);
}

.toast-leave-active {
  animation: toast-in 0.25s cubic-bezier(0.55, 0.085, 0.68, 0.53) reverse;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(-12px) scale(0.95);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ── Responsive ─────────────────────────────── */
@media (max-width: 768px) {
  .auth-navbar {
    padding: 0 1rem;
  }

  .auth-container {
    max-width: 100%;
    padding: 0 1rem;
  }

  /* On mobile: hide promo, show form full-width with slide */
  .promos-container {
    display: none;
  }

  .panels-wrapper {
    width: 100%;
  }

  .form-panel {
    width: 100%;
    display: none;
    opacity: 1 !important;
    transform: none !important;
    pointer-events: auto !important;
  }

  .form-panel.is-active-form {
    display: block;
  }

  .auth-glass-card {
    height: auto;
    max-height: calc(100vh - 160px);
  }

  .auth-scroll-area {
    padding: 1.25rem;
    height: auto;
    max-height: calc(100vh - 200px);
  }

  .brand-tagline {
    display: none;
  }

  .nav-link {
    padding: 0.35rem 0.6rem;
    font-size: 0.75rem;
  }
}
</style>
