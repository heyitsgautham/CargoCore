<template>
    <!-- 4. Fuel Reimbursement -->
    <div class="glass-panel rounded-xl overflow-hidden border border-orange-100 dark:border-orange-500/20">
        <div
            class="p-4 bg-orange-50 dark:bg-orange-900/10 flex items-center justify-between border-b border-orange-100 dark:border-orange-500/20">
            <div class="flex items-center gap-2">
                <span
                    class="material-symbols-outlined text-orange-600 dark:text-orange-400">local_gas_station</span>
                <h3 class="font-bold text-orange-900 dark:text-orange-100">Fuel & Fleet Expenses</h3>
            </div>
        </div>
        <div class="p-5 space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div
                    class="bg-gray-50 dark:bg-black/20 p-3 rounded-lg border border-gray-200 dark:border-white/10">
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Current Fuel Rate
                        (₹/L)</label>
                    <input type="number" :disabled="!isEditMode" step="0.1"
                        v-model.number="rates.fuel.currentRate"
                        class="w-full bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded p-2 text-sm font-mono text-orange-600 dark:text-orange-400 font-bold outline-none">
                </div>
                <div
                    class="bg-gray-50 dark:bg-black/20 p-3 rounded-lg border border-gray-200 dark:border-white/10">
                    <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Max Claim Limit
                        (₹/KM)</label>
                    <input type="number" :disabled="!isEditMode" step="0.1"
                        v-model.number="rates.fuel.maxClaimPerKm"
                        class="w-full bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded p-2 text-sm font-mono outline-none">
                </div>
            </div>
            <div>
                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Expected Standard
                    Mileage (KM/L)</label>
                <input type="number" :disabled="!isEditMode" step="0.5"
                    v-model.number="rates.fuel.benchmarkMileage"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono outline-none">
                <p class="text-[10px] text-gray-500 mt-1">Deviations beyond 15% between odometer and fuel
                    receipts trigger immediate OCR/GPS fraud audit logs.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { isEditMode, rates } = inject(rateGovernancePageKey)
</script>
