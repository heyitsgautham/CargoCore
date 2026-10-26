<template>
    <!-- Payment -->
    <div class="glass-panel p-6 rounded-xl space-y-4">
        <h3
            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
            4. Payment Mode</h3>
        <div class="flex flex-wrap gap-3">
            <label v-for="mode in ['Invoice', 'COD', 'Full Payment']" :key="mode"
                class="flex items-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition-colors"
                :class="form.paymentMode === mode ? 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-green-400'">
                <input type="radio" :value="mode" v-model="form.paymentMode" class="sr-only">
                <span class="material-symbols-outlined text-[18px]">{{
                    mode === 'COD' ? 'payments' : mode === 'Invoice' ? 'receipt' : 'credit_card'
                    }}</span>
                <span class="text-sm font-medium">{{ mode }}</span>
            </label>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { form } = inject(createShipmentPageKey)
</script>
