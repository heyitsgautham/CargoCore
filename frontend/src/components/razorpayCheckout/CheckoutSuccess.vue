<template>
    <div class="flex flex-col items-center justify-center py-10 px-8 text-center relative overflow-hidden" style="min-height: 420px;">

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
</template>

<script setup>
import { inject } from 'vue'
import { razorpayCheckoutKey } from './razorpayCheckoutContext'

const {
    amount,
    coins,
    confetti,
    emitSuccess,
    generatedPayId,
    orderId,
    selectedMethodLabel,
    sparkles,
} = inject(razorpayCheckoutKey)
</script>

<style scoped src="./RazorpayCheckout.css"></style>
