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

<style scoped src="./styles/AuthLayout.css"></style>
