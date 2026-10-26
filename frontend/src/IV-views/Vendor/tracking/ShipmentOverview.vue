<template>
    <!-- Row 1: Shipment Details + Driver side by side -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

        <!-- Shipment details -->
        <div class="glass-panel rounded-2xl p-5">
            <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">Shipment Details</h4>
            <div class="space-y-3">
                <div class="rounded-2xl border border-green-100 dark:border-green-500/20 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-500/10 dark:to-emerald-500/10 p-4 sm:p-5 overflow-hidden">
                    <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                            <div class="text-[10px] text-green-700 dark:text-green-400 uppercase font-bold tracking-[0.18em]">Shipment Amount</div>
                            <div class="mt-2 text-[clamp(1.75rem,4vw,2.6rem)] font-black leading-none text-green-600 dark:text-green-400">
                                ₹{{ formatCurrencyAmount(selected.amount) }}
                            </div>
                        </div>
                        <div class="w-11 h-11 rounded-2xl bg-white/80 dark:bg-white/10 border border-green-200/70 dark:border-green-400/20 flex items-center justify-center flex-shrink-0">
                            <span class="material-symbols-outlined text-[20px] text-green-600 dark:text-green-400">account_balance_wallet</span>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Weight</div>
                        <div class="text-lg font-bold text-gray-900 dark:text-white leading-tight">
                            {{ formatMetricValue(selected.weight) }}<span class="text-xs font-medium text-gray-400 ml-1">kg</span>
                        </div>
                    </div>
                    <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Pallets</div>
                        <div class="text-lg font-bold text-gray-900 dark:text-white leading-tight">{{ formatMetricValue(selected.pallets) }}</div>
                    </div>
                    <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Payment</div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white leading-snug break-words">{{ selected.paymentMode }}</div>
                    </div>
                    <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 flex items-start gap-3">
                        <span class="material-symbols-outlined text-blue-400 text-[20px] mt-0.5">category</span>
                        <div class="min-w-0">
                            <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Category</div>
                            <div class="text-sm font-semibold text-gray-900 dark:text-white leading-snug break-words">{{ selected.category }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Driver card -->
        <div v-if="selected.driver" class="glass-panel rounded-2xl p-5">
            <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">Driver</h4>

            <!-- Row 1: Avatar + Name/Vehicle/Status -->
            <div class="flex items-center gap-4 mb-4">
                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20 flex-shrink-0">
                    <span class="material-symbols-outlined text-white text-[28px]">person</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="font-bold text-gray-900 dark:text-white truncate">{{ selected.driver }}</div>
                    <div class="flex items-center gap-1.5 mt-0.5 text-xs text-gray-400">
                        <span class="material-symbols-outlined text-[13px]">directions_car</span>
                        <span>{{ selected.vehicle || '—' }}</span>
                    </div>
                    <div class="flex items-center gap-1 mt-1.5">
                        <span class="w-2 h-2 rounded-full" :class="selectedDriverStatus.dotClass"></span>
                        <span class="text-[10px] font-bold" :class="selectedDriverStatus.textClass">{{ selectedDriverStatus.label }}</span>
                    </div>
                </div>
            </div>

            <!-- Row 2: Phone + Call button -->
            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                <div>
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Phone</div>
                    <div class="text-sm font-bold text-gray-900 dark:text-white tracking-wide">
                        {{ selected.driverPhone || '—' }}
                    </div>
                </div>
                <button @click="showCallModal = true" :disabled="!canCallDriver"
                    class="w-10 h-10 rounded-xl text-white transition-colors flex items-center justify-center shadow-md"
                    :class="canCallDriver ? 'bg-green-500 hover:bg-green-600 shadow-green-500/20' : 'bg-gray-300 dark:bg-white/10 cursor-not-allowed shadow-none'"
                    title="Call Driver">
                    <span class="material-symbols-outlined text-[20px]">call</span>
                </button>
            </div>
        </div>
        <!-- No driver placeholder to keep grid balanced -->
        <div v-else class="glass-panel rounded-2xl p-5 flex items-center justify-center text-gray-400">
            <div class="text-center">
                <span class="material-symbols-outlined text-3xl text-gray-300 block mb-1">person_off</span>
                <div class="text-xs">No driver assigned yet</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { formatCurrencyAmount, formatMetricValue } from './trackingFormat'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { canCallDriver, selected, selectedDriverStatus, showCallModal } = inject(vendorTrackingPageKey)
</script>
