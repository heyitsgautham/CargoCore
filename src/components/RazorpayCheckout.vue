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
            <div v-if="phase === 'success'" class="flex flex-col items-center justify-center py-10 px-8 text-center relative overflow-hidden" style="min-height: 420px;">

              <!-- Confetti / Coin Rain Canvas -->
              <div class="absolute inset-0 pointer-events-none overflow-hidden">
                <!-- Gold coins -->
                <div v-for="c in coins" :key="'c'+c.id"
                  class="absolute coin-fall"
                  :style="{ left: c.x + '%', animationDelay: c.delay + 's', animationDuration: c.dur + 's', top: '-40px' }">
                  <div class="coin-spin" :style="{ width: c.size + 'px', height: c.size + 'px' }">
                    <svg viewBox="0 0 40 40" :width="c.size" :height="c.size">
                      <circle cx="20" cy="20" r="18" fill="#FFD700" stroke="#FFA500" stroke-width="2"/>
                      <circle cx="20" cy="20" r="14" fill="#FFEC3D" stroke="#FFB300" stroke-width="1"/>
                      <text x="20" y="25" text-anchor="middle" font-size="13" font-weight="bold" fill="#B8860B">₹</text>
                    </svg>
                  </div>
                </div>

                <!-- Confetti strips -->
                <div v-for="p in confetti" :key="'p'+p.id"
                  class="absolute confetti-fall rounded-sm"
                  :style="{
                    left: p.x + '%',
                    width: p.w + 'px',
                    height: p.h + 'px',
                    background: p.color,
                    animationDelay: p.delay + 's',
                    animationDuration: p.dur + 's',
                    top: '-20px',
                    transform: 'rotate(' + p.rot + 'deg)'
                  }">
                </div>

                <!-- Sparkle bursts from center -->
                <div class="absolute inset-0 flex items-center justify-center">
                  <div v-for="s in sparkles" :key="'s'+s.id"
                    class="absolute sparkle-burst"
                    :style="{ '--tx': s.tx + 'px', '--ty': s.ty + 'px', animationDelay: s.delay + 's' }">
                    <svg width="12" height="12" viewBox="0 0 12 12">
                      <polygon points="6,0 7.5,4.5 12,6 7.5,7.5 6,12 4.5,7.5 0,6 4.5,4.5" :fill="s.color"/>
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Main success icon -->
              <div class="relative z-10 w-28 h-28 rounded-full flex items-center justify-center mb-4 success-ring" style="background: radial-gradient(circle, #22c55e33 0%, #16a34a22 100%); border: 3px solid #22c55e;">
                <div class="w-20 h-20 rounded-full bg-green-500 flex items-center justify-center animate-pop shadow-xl shadow-green-500/40">
                  <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" class="checkmark-path"/>
                  </svg>
                </div>
              </div>

              <h3 class="relative z-10 text-2xl font-black text-gray-900 dark:text-white mb-1 animate-slideup">Payment Successful! 🎉</h3>
              <p class="relative z-10 text-green-600 dark:text-green-400 font-bold text-lg mb-1 animate-slideup" style="animation-delay:0.1s">₹{{ amount.toLocaleString() }}</p>
              <p class="relative z-10 text-xs text-gray-400 dark:text-gray-500 font-mono mb-5 animate-slideup" style="animation-delay:0.15s">{{ generatedPayId }}</p>

              <div class="relative z-10 w-full px-3 py-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700/50 rounded-xl text-xs text-left space-y-1.5 animate-slideup" style="animation-delay:0.2s">
                <div class="flex justify-between"><span class="text-gray-500">Method</span><span class="font-bold text-gray-900 dark:text-white">{{ selectedMethodLabel }}</span></div>
                <div class="flex justify-between" v-if="orderId"><span class="text-gray-500">Order ID</span><span class="font-mono font-bold text-gray-900 dark:text-white">{{ orderId }}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">Status</span><span class="font-bold text-green-600 dark:text-green-400">✓ Authorized</span></div>
              </div>

              <button @click="emitSuccess"
                class="relative z-10 mt-5 w-full py-3 bg-[#3395FF] hover:bg-blue-600 text-white font-bold rounded-xl transition-colors text-sm animate-slideup shadow-lg shadow-blue-500/30"
                style="animation-delay:0.25s">
                Done
              </button>
            </div>


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
              <div class="px-5 py-5 space-y-4 min-h-[220px]">

                <!-- UPI -->
                <div v-if="activeTab === 'upi'" class="space-y-4">
                  <div>
                    <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Enter UPI ID</label>
                    <input v-model="upiId" type="text" placeholder="yourname@upi"
                      class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 focus:border-[#3395FF] outline-none transition-all"
                      :class="upiError ? 'border-red-400' : ''"/>
                    <p v-if="upiError" class="text-red-500 text-xs mt-1">{{ upiError }}</p>
                  </div>
                  <div class="grid grid-cols-4 gap-2">
                    <button v-for="app in ['GPay', 'PhonePe', 'Paytm', 'BHIM']" :key="app"
                      @click="upiId = app.toLowerCase() + '@upi'"
                      class="flex flex-col items-center gap-1 py-2 px-1 rounded-lg border border-gray-200 dark:border-white/10 hover:border-[#3395FF] hover:bg-[#3395FF]/5 transition-all text-[10px] font-medium text-gray-600 dark:text-gray-400">
                      <div class="w-7 h-7 rounded-full flex items-center justify-center text-base"
                        :style="{ background: { GPay: '#4285f4', PhonePe: '#5f259f', Paytm: '#00b9f1', BHIM: '#00a046' }[app] }">
                        {{ app[0] }}
                      </div>
                      {{ app }}
                    </button>
                  </div>
                </div>

                <!-- Card -->
                <div v-if="activeTab === 'card'" class="space-y-3">
                  <div>
                    <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Card Number</label>
                    <input v-model="card.number" type="text" placeholder="0000 0000 0000 0000" maxlength="19"
                      @input="formatCardNumber"
                      class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 focus:border-[#3395FF] outline-none font-mono transition-all"/>
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Expiry (MM/YY)</label>
                      <input v-model="card.expiry" type="text" placeholder="MM/YY" maxlength="5"
                        @input="formatExpiry"
                        class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 focus:border-[#3395FF] outline-none font-mono transition-all"/>
                    </div>
                    <div>
                      <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">CVV</label>
                      <input v-model="card.cvv" type="password" placeholder="•••" maxlength="4"
                        class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 focus:border-[#3395FF] outline-none font-mono transition-all"/>
                    </div>
                  </div>
                  <div>
                    <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Name on Card</label>
                    <input v-model="card.name" type="text" placeholder="As on your card"
                      class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 focus:border-[#3395FF] outline-none transition-all"/>
                  </div>
                  <div class="flex gap-2">
                    <img v-for="brand in ['VISA', 'MC', 'AMEX', 'RuPay']" :key="brand"
                      class="h-6 px-2 py-1 bg-white dark:bg-white/10 rounded border border-gray-200 dark:border-white/10 text-[9px] font-black text-gray-700 dark:text-gray-300 flex items-center"
                      :alt="brand" :src="`https://placehold.co/48x24/f8fafc/475569?text=${brand}&font=raleway`"/>
                  </div>
                </div>

                <!-- Net Banking -->
                <div v-if="activeTab === 'netbanking'" class="space-y-3">
                  <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400">Select Bank</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button v-for="bank in popularBanks" :key="bank.name"
                      @click="selectedBank = bank.name"
                      class="flex items-center gap-2 p-3 rounded-xl border text-left text-sm font-medium transition-all"
                      :class="selectedBank === bank.name
                        ? 'border-[#3395FF] bg-[#3395FF]/5 text-[#3395FF]'
                        : 'border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-300 hover:border-gray-300'">
                      <div class="w-7 h-7 rounded flex items-center justify-center text-white text-xs font-black flex-shrink-0"
                        :style="{ background: bank.color }">{{ bank.name[0] }}</div>
                      <span class="text-xs truncate">{{ bank.name }}</span>
                    </button>
                  </div>
                  <select v-model="selectedBank"
                    class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-[#3395FF]/40 outline-none">
                    <option value="" class="bg-white dark:bg-gray-800">-- Other Banks --</option>
                    <option v-for="b in allBanks" :key="b" :value="b" class="bg-white dark:bg-gray-800">{{ b }}</option>
                  </select>
                </div>

                <!-- Wallet -->
                <div v-if="activeTab === 'wallet'" class="space-y-3">
                  <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400">Choose Wallet</label>
                  <div class="grid grid-cols-2 gap-3">
                    <button v-for="w in wallets" :key="w.name"
                      @click="selectedWallet = w.name"
                      class="flex items-center gap-3 p-3 rounded-xl border transition-all"
                      :class="selectedWallet === w.name
                        ? 'border-[#3395FF] bg-[#3395FF]/5'
                        : 'border-gray-200 dark:border-white/10 hover:border-gray-300'">
                      <div class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-lg font-black flex-shrink-0"
                        :style="{ background: w.color }">{{ w.name[0] }}</div>
                      <div>
                        <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ w.name }}</div>
                        <div class="text-[10px] text-gray-400">{{ w.sub }}</div>
                      </div>
                    </button>
                  </div>
                </div>

                <!-- Cargo Core Wallet -->
                <div v-if="activeTab === 'cargowallet'" class="space-y-4">
                  <!-- Balance card -->
                  <div class="rounded-2xl border-2 p-4 flex items-center gap-4 transition-all"
                    :class="cargoWalletSufficient
                      ? 'border-green-400 dark:border-green-500/60 bg-green-50 dark:bg-green-900/10'
                      : 'border-red-300 dark:border-red-500/40 bg-red-50 dark:bg-red-900/10'">
                    <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                      :class="cargoWalletSufficient ? 'bg-green-100 dark:bg-green-800/30' : 'bg-red-100 dark:bg-red-800/30'">
                      <svg class="w-6 h-6" :class="cargoWalletSufficient ? 'text-green-600 dark:text-green-400' : 'text-red-500'" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                      </svg>
                    </div>
                    <div class="flex-1">
                      <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Cargo Core Wallet</div>
                      <div class="text-2xl font-black mt-0.5" :class="cargoWalletSufficient ? 'text-green-700 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                        ₹{{ props.walletBalance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </div>
                      <div class="text-[10px] mt-0.5" :class="cargoWalletSufficient ? 'text-green-600 dark:text-green-500' : 'text-red-500'">
                        {{ cargoWalletSufficient ? 'Available balance' : 'Insufficient balance' }}
                      </div>
                    </div>
                    <svg v-if="cargoWalletSufficient" class="w-6 h-6 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <svg v-else class="w-6 h-6 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                  </div>

                  <!-- Payment breakdown -->
                  <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-3 space-y-2 text-xs border border-gray-200 dark:border-white/10">
                    <div class="flex justify-between">
                      <span class="text-gray-500">Amount to pay</span>
                      <span class="font-bold text-gray-900 dark:text-white">₹{{ props.amount.toLocaleString() }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span class="text-gray-500">Wallet balance</span>
                      <span class="font-bold" :class="cargoWalletSufficient ? 'text-green-600 dark:text-green-400' : 'text-red-500'">
                        ₹{{ props.walletBalance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </span>
                    </div>
                    <div class="border-t border-gray-200 dark:border-white/10 pt-2 flex justify-between">
                      <span class="font-semibold" :class="cargoWalletSufficient ? 'text-gray-600 dark:text-gray-400' : 'text-red-600 dark:text-red-400'">
                        {{ cargoWalletSufficient ? 'Balance after payment' : 'Shortfall' }}
                      </span>
                      <span class="font-black" :class="cargoWalletSufficient ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'">
                        {{ cargoWalletSufficient
                          ? '₹' + (props.walletBalance - props.amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                          : '₹' + (props.amount - props.walletBalance).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' needed'
                        }}
                      </span>
                    </div>
                  </div>

                  <!-- Insufficient notice -->
                  <div v-if="!cargoWalletSufficient"
                    class="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-500/20 text-xs text-amber-700 dark:text-amber-400">
                    <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>Top up your Cargo Core Wallet in the <strong>Wallet</strong> section, then come back to pay.</span>
                  </div>
                </div>

              </div>

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
import { ref, computed, watch } from 'vue'

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
</script>

<style scoped>
.rzp-fade-enter-active, .rzp-fade-leave-active { transition: opacity 0.25s ease; }
.rzp-fade-enter-from, .rzp-fade-leave-to { opacity: 0; }

.rzp-slide-enter-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.rzp-slide-leave-active { transition: all 0.2s ease-in; }
.rzp-slide-enter-from { opacity: 0; transform: scale(0.92) translateY(20px); }
.rzp-slide-leave-to { opacity: 0; transform: scale(0.95) translateY(10px); }

/* ── coin rain ── */
@keyframes coinFall {
  0%   { transform: translateY(-40px) rotate(0deg); opacity: 1; }
  80%  { opacity: 1; }
  100% { transform: translateY(480px) rotate(720deg); opacity: 0; }
}
.coin-fall { animation: coinFall linear both; }

@keyframes coinSpin {
  from { transform: rotateY(0deg); }
  to   { transform: rotateY(360deg); }
}
.coin-spin { animation: coinSpin 0.6s linear infinite; display: inline-block; }

/* ── confetti ── */
@keyframes confettiFall {
  0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
  100% { transform: translateY(500px) rotate(540deg); opacity: 0; }
}
.confetti-fall { animation: confettiFall linear both; }

/* ── sparkle burst ── */
@keyframes sparkleBurst {
  0%   { transform: translate(0,0) scale(1); opacity: 1; }
  60%  { transform: translate(var(--tx), var(--ty)) scale(1.2); opacity: 1; }
  100% { transform: translate(calc(var(--tx)*1.4), calc(var(--ty)*1.4)) scale(0); opacity: 0; }
}
.sparkle-burst { animation: sparkleBurst 0.7s ease-out both; }

/* ── checkmark draw ── */
@keyframes drawCheck {
  from { stroke-dashoffset: 30; }
  to   { stroke-dashoffset: 0; }
}
.checkmark-path {
  stroke-dasharray: 30;
  stroke-dashoffset: 30;
  animation: drawCheck 0.4s ease 0.3s both;
}

/* ── success ring pulse ── */
@keyframes ringPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); }
  50%       { box-shadow: 0 0 0 12px rgba(34,197,94,0); }
}
.success-ring { animation: ringPulse 1.5s ease-in-out infinite; }

/* ── pop ── */
@keyframes pop {
  0%   { transform: scale(0); opacity: 0; }
  60%  { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}
.animate-pop { animation: pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both; }

/* ── slide up ── */
@keyframes slideUp {
  from { transform: translateY(16px); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
.animate-slideup { animation: slideUp 0.4s ease both; }
</style>
