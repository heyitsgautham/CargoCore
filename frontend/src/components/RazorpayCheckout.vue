<template>
  <!-- Backdrop -->
  <Teleport to="body">
    <Transition name="rzp-fade">
      <div v-if="modelValue"
        class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
        style="background: rgba(0,0,0,0.65); backdrop-filter: blur(4px);"
        @click.self="handleClose">

        <!-- Modal Card -->
        <Transition name="rzp-slide">
          <div v-if="modelValue"
            class="w-full max-w-md bg-white dark:bg-[#1a1a2e] rounded-2xl shadow-2xl overflow-hidden relative"
            style="max-height: 90vh; overflow-y: auto;">

            <!-- ── SUCCESS SCREEN ── -->
            <CheckoutSuccess v-if="phase === 'success'" />


            <!-- ── PROCESSING SCREEN ── -->
            <div v-else-if="phase === 'processing'" class="flex flex-col items-center justify-center py-20 px-8 text-center">
              <div class="relative w-20 h-20 mb-6">
                <svg class="w-20 h-20 animate-spin text-[#3395FF]" viewBox="0 0 50 50">
                  <circle class="opacity-20" cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4"/>
                  <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4"
                    stroke-dasharray="80" stroke-dashoffset="60" stroke-linecap="round"/>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                  <img src="https://razorpay.com/favicon.ico" alt="rzp" class="w-8 h-8 rounded" onerror="this.style.display='none'"/>
                </div>
              </div>
              <p class="text-gray-700 dark:text-gray-300 font-semibold text-lg">Processing payment…</p>
              <p class="text-gray-400 dark:text-gray-500 text-xs mt-2">Please do not refresh or close this window</p>
            </div>

            <!-- ── CHECKOUT FORM ── -->
            <template v-else>
              <!-- Header -->
              <div class="flex items-center justify-between px-5 py-4 bg-[#3395FF]">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 bg-white rounded-lg flex items-center justify-center font-black text-[#3395FF] text-lg">R</div>
                  <div>
                    <div class="text-white font-bold text-sm leading-tight">Razorpay Checkout</div>
                    <div class="text-blue-100 text-xs">Secure Payment</div>
                  </div>
                </div>
                <button @click="handleClose" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/20 text-white transition-colors">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>

              <!-- Amount summary -->
              <div class="px-5 pt-5 pb-4 border-b border-gray-100 dark:border-white/10">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-[#3395FF]/10 flex items-center justify-center flex-shrink-0">
                    <span class="text-[#3395FF] text-lg">₹</span>
                  </div>
                  <div>
                    <div class="text-2xl font-black text-gray-900 dark:text-white">₹{{ amount.toLocaleString() }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ description || 'Order Payment' }}</div>
                  </div>
                </div>
                <div v-if="email || name" class="mt-3 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                  </svg>
                  <span>{{ name || email }}</span>
                </div>
              </div>

              <!-- Method Tabs -->
              <div class="flex border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                <button v-for="tab in tabs" :key="tab.key"
                  @click="activeTab = tab.key"
                  class="flex-1 text-xs font-semibold py-3 px-1 text-center transition-colors border-b-2"
                  :class="activeTab === tab.key
                    ? 'border-[#3395FF] text-[#3395FF] bg-white dark:bg-[#1a1a2e]'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'">
                  {{ tab.label }}
                </button>
              </div>

              <!-- Tab Content -->
              <CheckoutMethods />

              <!-- Pay Button -->
              <div class="px-5 pb-5 space-y-3">
                <button @click="initiatePayment"
                  :disabled="!canPay"
                  class="w-full py-3.5 rounded-xl font-bold text-white text-sm transition-all flex items-center justify-center gap-2"
                  :class="canPay
                    ? 'bg-[#3395FF] hover:bg-blue-600 shadow-lg shadow-blue-500/30'
                    : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                  </svg>
                  {{ activeTab === 'cargowallet' ? 'Pay ₹' + amount.toLocaleString() + ' from Wallet' : 'Pay ₹' + amount.toLocaleString() + ' Securely' }}
                </button>
                <div class="flex items-center justify-center gap-2 text-[10px] text-gray-400">
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                  </svg>
                  <span>256-bit SSL · PCI-DSS Compliant · Powered by Razorpay</span>
                </div>
              </div>

            </template>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import CheckoutSuccess from './razorpayCheckout/CheckoutSuccess.vue'
import CheckoutMethods from './razorpayCheckout/CheckoutMethods.vue'
import { razorpayCheckoutKey } from './razorpayCheckout/razorpayCheckoutContext'
import { ref, computed, watch, provide, toRef } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  amount: { type: Number, required: true },
  orderId: { type: String, default: '' },
  description: { type: String, default: '' },
  name: { type: String, default: '' },
  email: { type: String, default: '' },
  walletBalance: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const phase = ref('form') // 'form' | 'processing' | 'success'
const activeTab = ref('upi')
const generatedPayId = ref('')

// ── Coin rain data ──
const coins = ref([])
const confetti = ref([])
const sparkles = ref([])

const CONFETTI_COLORS = ['#FFD700','#3395FF','#22c55e','#f97316','#a855f7','#ec4899','#06b6d4']

function spawnParticles() {
  // coins
  coins.value = Array.from({ length: 14 }, (_, i) => ({
    id: i,
    x: 5 + Math.random() * 90,
    delay: Math.random() * 0.8,
    dur: 1.4 + Math.random() * 0.8,
    size: 22 + Math.random() * 18,
  }))
  // confetti strips
  confetti.value = Array.from({ length: 28 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    w: 4 + Math.random() * 6,
    h: 10 + Math.random() * 10,
    color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    delay: Math.random() * 1.0,
    dur: 1.6 + Math.random() * 0.8,
    rot: Math.random() * 360,
  }))
  // sparkle bursts outward from center
  const angles = Array.from({ length: 12 }, (_, i) => (i / 12) * 2 * Math.PI)
  sparkles.value = angles.map((a, i) => ({
    id: i,
    tx: Math.round(Math.cos(a) * (60 + Math.random() * 40)),
    ty: Math.round(Math.sin(a) * (60 + Math.random() * 40)),
    color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
    delay: 0.1 + Math.random() * 0.2,
  }))
}

watch(phase, (val) => { if (val === 'success') spawnParticles() })

const tabs = [
  { key: 'upi', label: 'UPI' },
  { key: 'card', label: 'Card' },
  { key: 'netbanking', label: 'Net Banking' },
  { key: 'wallet', label: 'Wallet' },
  { key: 'cargowallet', label: 'Cargo Core' },
]

// UPI
const upiId = ref('')
const upiError = ref('')

// Card
const card = ref({ number: '', expiry: '', cvv: '', name: '' })

function formatCardNumber() {
  let v = card.value.number.replace(/\D/g, '').substring(0, 16)
  card.value.number = v.replace(/(.{4})/g, '$1 ').trim()
}
function formatExpiry() {
  let v = card.value.expiry.replace(/\D/g, '').substring(0, 4)
  if (v.length >= 2) v = v.substring(0, 2) + '/' + v.substring(2)
  card.value.expiry = v
}

// Net Banking
const selectedBank = ref('')
const popularBanks = [
  { name: 'SBI', color: '#003f88' },
  { name: 'HDFC', color: '#0052b4' },
  { name: 'ICICI', color: '#e04040' },
  { name: 'Axis', color: '#800080' },
]
const allBanks = ['Kotak Mahindra', 'Yes Bank', 'Punjab National', 'Bank of Baroda', 'Canara Bank', 'Union Bank', 'IDFC First', 'IndusInd']

// Wallet
const selectedWallet = ref('')
const wallets = [
  { name: 'Paytm', color: '#00b9f1', sub: 'India\'s #1 Wallet' },
  { name: 'PhonePe', color: '#5f259f', sub: 'UPI Payments' },
  { name: 'Amazon Pay', color: '#ff9900', sub: 'Amazon Pay Wallet' },
  { name: 'Mobikwik', color: '#e92b2b', sub: 'Superwallet' },
]

const cargoWalletSufficient = computed(() => props.walletBalance >= props.amount)

const selectedMethodLabel = computed(() => {
  if (activeTab.value === 'upi') return upiId.value || 'UPI'
  if (activeTab.value === 'card') return `Card ending ${card.value.number.slice(-4) || '****'}`
  if (activeTab.value === 'netbanking') return selectedBank.value || 'Net Banking'
  if (activeTab.value === 'wallet') return selectedWallet.value || 'Wallet'
  if (activeTab.value === 'cargowallet') return 'Cargo Core Wallet'
  return 'Online'
})

const canPay = computed(() => {
  if (activeTab.value === 'upi') return upiId.value.trim().length > 3
  if (activeTab.value === 'card') return card.value.number.length >= 18 && card.value.expiry.length === 5 && card.value.cvv.length >= 3
  if (activeTab.value === 'netbanking') return !!selectedBank.value
  if (activeTab.value === 'wallet') return !!selectedWallet.value
  if (activeTab.value === 'cargowallet') return cargoWalletSufficient.value
  return false
})

function generatePayId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = 'pay_'
  for (let i = 0; i < 14; i++) result += chars.charAt(Math.floor(Math.random() * chars.length))
  return result
}

function initiatePayment() {
  if (!canPay.value) return
  if (activeTab.value === 'upi' && !upiId.value.includes('@')) {
    upiError.value = 'Enter a valid UPI ID (e.g. name@upi)'
    return
  }
  upiError.value = ''
  phase.value = 'processing'
  generatedPayId.value = generatePayId()
  setTimeout(() => {
    phase.value = 'success'
  }, 2000)
}

function emitSuccess() {
  emit('success', {
    payment_id: generatedPayId.value,
    method: selectedMethodLabel.value,
    amount: props.amount,
  })
  handleClose()
}

function handleClose() {
  if (phase.value === 'processing') return // don't allow close during processing
  phase.value = 'form'
  upiId.value = ''
  card.value = { number: '', expiry: '', cvv: '', name: '' }
  selectedBank.value = ''
  selectedWallet.value = ''
  emit('update:modelValue', false)
  emit('close')
}

provide(razorpayCheckoutKey, {
    activeTab,
    allBanks,
    amount: toRef(props, 'amount'),
    card,
    cargoWalletSufficient,
    coins,
    confetti,
    emitSuccess,
    formatCardNumber,
    formatExpiry,
    generatedPayId,
    orderId: toRef(props, 'orderId'),
    popularBanks,
    props,
    selectedBank,
    selectedMethodLabel,
    selectedWallet,
    sparkles,
    upiError,
    upiId,
    wallets,
})
</script>

<style scoped src="./razorpayCheckout/RazorpayCheckout.css"></style>
