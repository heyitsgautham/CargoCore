<template>
    <div>
        <div class="glass-panel p-4 sm:p-6 rounded-xl flex flex-col sticky top-[5.5rem] z-10">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined"
                    :class="moveType === 'house-shift' ? 'text-green-500' : 'text-blue-500'">receipt_long</span>
                {{ moveType === 'house-shift' ? 'Estimated Cost' : 'Package Cost' }}
            </h3>
            <div
                class="mb-4 rounded-lg border px-4 py-3"
                :class="moveType === 'house-shift'
                    ? 'border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/5'
                    : 'border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/5'">
                <div
                    class="text-[11px] uppercase tracking-wider font-bold"
                    :class="moveType === 'house-shift' ? 'text-green-700 dark:text-green-300' : 'text-blue-700 dark:text-blue-300'">
                    {{ routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'This Order Will Go To' }}
                </div>
                <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                    {{ routingPreview?.warehouse_name || 'Resolving best available hub...' }}
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                    {{ routingPreview?.message || 'We will choose the best available operational hub if you do not select one.' }}
                </div>
            </div>

            <!-- House Shift Pricing -->
            <template v-if="moveType === 'house-shift'">
                <!-- Distance badge -->
                <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20">
                    <span class="material-symbols-outlined text-green-500 text-sm">route</span>
                    <span class="text-xs font-bold text-green-700 dark:text-green-400">{{ distanceKm }} km</span>
                    <span class="text-xs text-gray-500">(road estimate)</span>
                </div>
                <div v-else class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
                    <span class="material-symbols-outlined text-amber-500 text-sm">info</span>
                    <span class="text-xs text-amber-700 dark:text-amber-400">Select pickup &amp; destination to get exact pricing</span>
                </div>
                <div class="space-y-3 mb-4">
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Base Fare</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ quote.base.toLocaleString()
                            }}</span></div>
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Vehicle ({{ selectedVehicle?.name
                            }})</span><span class="text-gray-900 dark:text-white font-mono">₹{{
                            quote.vehicle.toLocaleString() }}</span></div>
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Labor ({{ form.laborCount }} ×
                            ₹{{ (rates.individualLaborRate ?? 800).toLocaleString() }})</span><span class="text-gray-900 dark:text-white font-mono">₹{{
                            quote.labor.toLocaleString() }}</span></div>
                    <div v-if="form.packingRequired" class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Packing Service</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ quote.packing.toLocaleString()
                            }}</span></div>
                    <div v-if="materialsCostTotal > 0" class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Materials</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{
                            materialsCostTotal.toLocaleString() }}</span></div>
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Platform Fee</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ quote.platformFee.toLocaleString() }}</span></div>
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">GST (18%)</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ quote.taxes.toLocaleString() }}</span></div>
                    <div v-if="carryForwardCharge > 0" class="flex justify-between text-sm">
                        <span class="text-amber-600 dark:text-amber-300">Previous rejected-claim transport charge</span>
                        <span class="text-amber-600 dark:text-amber-300 font-mono">₹{{ carryForwardCharge.toLocaleString() }}</span>
                    </div>
                </div>
                <div class="border-t border-gray-200 dark:border-white/10 pt-4 mb-2">
                    <div class="flex justify-between items-end">
                        <span class="text-lg font-bold text-gray-900 dark:text-white">Total</span>
                        <span class="text-3xl font-bold text-green-600 dark:text-primary">₹{{
                            bookingTotal.toLocaleString() }}</span>
                    </div>
                    <div class="text-xs text-gray-500 text-right mt-1">*Dedicated truck — no batching</div>
                </div>
                <div
                    class="text-xs bg-purple-50 dark:bg-purple-500/5 border border-purple-200 dark:border-purple-500/20 rounded-lg p-2 mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-500 text-sm">timer</span>
                    <span class="text-purple-700 dark:text-purple-300">Service time block: {{ serviceTimeBlock
                        }}</span>
                </div>
            </template>

            <!-- Small Package Pricing -->
            <template v-else>
                <!-- Distance badge -->
                <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20">
                    <span class="material-symbols-outlined text-blue-500 text-sm">route</span>
                    <span class="text-xs font-bold text-blue-700 dark:text-blue-400">{{ distanceKm }} km</span>
                    <span class="text-xs text-gray-500">(road estimate)</span>
                </div>
                <div v-else class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
                    <span class="material-symbols-outlined text-amber-500 text-sm">info</span>
                    <span class="text-xs text-amber-700 dark:text-amber-400">Select pickup &amp; destination for delivery fee</span>
                </div>
                <div class="space-y-3 mb-4">
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Base (by weight)</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ pkgBase.toLocaleString()
                            }}</span></div>
                    <div class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Delivery Fee{{ distanceKm ? ' (' + distanceKm + ' km × ₹' + (rates.smallPackagePerKmRate ?? 12) + ')' : '' }}</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ pkgDeliveryFee.toLocaleString() }}</span></div>
                    <div v-if="pkgMinimumAdjustment > 0" class="flex justify-between text-sm"><span
                            class="text-gray-500 dark:text-gray-400">Minimum Charge Adjustment</span><span
                            class="text-gray-900 dark:text-white font-mono">₹{{ pkgMinimumAdjustment.toLocaleString() }}</span></div>
                    <div v-if="carryForwardCharge > 0" class="flex justify-between text-sm">
                        <span class="text-amber-600 dark:text-amber-300">Previous rejected-claim transport charge</span>
                        <span class="text-amber-600 dark:text-amber-300 font-mono">₹{{ carryForwardCharge.toLocaleString() }}</span>
                    </div>
                </div>
                <div class="border-t border-gray-200 dark:border-white/10 pt-4 mb-4">
                    <div class="flex justify-between items-end">
                        <span class="text-lg font-bold text-gray-900 dark:text-white">Total</span>
                        <span class="text-3xl font-bold text-blue-600 dark:text-blue-400">₹{{
                            bookingTotal.toLocaleString() }}</span>
                    </div>
                    <div class="text-xs text-gray-500 text-right mt-1">Auto-pickup scheduled</div>
                </div>
            </template>

            <!-- Dummy Payment text removed -->

            <div
                v-if="warehouseBookingBlocked"
                class="mb-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
                {{ warehouseBookingMessage }}
            </div>

            <button @click="handleBookingClick"
                :disabled="warehouseBookingBlocked"
                class="w-full py-3 font-bold rounded-xl transition-colors text-lg mb-2 shadow-sm"
                :class="warehouseBookingBlocked
                    ? 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed shadow-none'
                    : (moveType === 'house-shift' ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white')">
                {{ warehouseBookingBlocked ? 'Booking Unavailable' : (moveType === 'house-shift' ? 'Confirm Booking' : 'Schedule Pickup') }}
            </button>
            <button @click="saveQuote"
                class="w-full py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors mb-2">
                Save as Quote
            </button>
            <button @click="resetForm"
                class="w-full py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 font-bold rounded-xl transition-colors text-sm flex items-center justify-center gap-1.5">
                <span class="material-symbols-outlined text-sm">cancel</span> Cancel / Reset
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const {
    bookingTotal,
    carryForwardCharge,
    distanceKm,
    form,
    handleBookingClick,
    materialsCostTotal,
    moveType,
    pkgBase,
    pkgDeliveryFee,
    pkgMinimumAdjustment,
    quote,
    rates,
    resetForm,
    routingPreview,
    saveQuote,
    selectedVehicle,
    serviceTimeBlock,
    warehouseBookingBlocked,
    warehouseBookingMessage,
} = inject(bookMovePageKey)
</script>
