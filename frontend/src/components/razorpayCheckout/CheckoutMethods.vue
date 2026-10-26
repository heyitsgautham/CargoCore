<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { razorpayCheckoutKey } from './razorpayCheckoutContext'

const {
    activeTab,
    allBanks,
    card,
    cargoWalletSufficient,
    formatCardNumber,
    formatExpiry,
    popularBanks,
    props,
    selectedBank,
    selectedWallet,
    upiError,
    upiId,
    wallets,
} = inject(razorpayCheckoutKey)
</script>
