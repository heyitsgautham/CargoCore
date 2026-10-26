<template>
    <!-- 1. Customer Charges (Revenue Side) -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div
            class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-black/20 flex items-center gap-3">
            <div
                class="w-8 h-8 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 flex items-center justify-center">
                <span class="material-symbols-outlined text-[20px]">account_balance_wallet</span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white text-lg">Customer Charges <span
                    class="text-xs font-normal text-gray-500 ml-2">(Revenue Basis)</span></h3>
        </div>

        <div class="p-6 space-y-8">
            <!-- A. Base Transport -->
            <div>
                <h4
                    class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                    A. Commercial / Vendor Transport Base</h4>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Base Fee
                            (₹)</label>
                        <input type="number" :disabled="!isEditMode" v-model.number="rates.baseBookingFee"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Rate / KM
                            (₹)</label>
                        <input type="number" :disabled="!isEditMode" v-model.number="rates.perKmRate"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Minimum
                            (₹)</label>
                        <input type="number" :disabled="!isEditMode" v-model.number="rates.minimumCharge"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Express Mul
                            (x)</label>
                        <input type="number" :disabled="!isEditMode" step="0.1"
                            v-model.number="rates.expressMultiplier"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                    </div>
                </div>
            </div>

            <!-- B. Labor & Packing -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4
                        class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                        B. Customer Add-ons</h4>
                    <div class="space-y-3">
                        <div
                            class="bg-blue-50/50 dark:bg-blue-900/10 p-3 rounded-xl border border-blue-100 dark:border-blue-800/20">
                            <label
                                class="block text-xs font-bold text-blue-700 dark:text-blue-400 uppercase mb-2">Labor / Helper (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.customerLaborRate"
                                class="w-full bg-white dark:bg-black/40 border border-blue-200 dark:border-blue-800/30 rounded-lg p-2.5 text-sm font-mono font-bold text-blue-900 dark:text-blue-100 focus:ring-2 focus:ring-blue-500/20 outline-none">
                            <p class="text-[10px] text-blue-600 dark:text-blue-400 mt-1 opacity-80">Per helper per shipment.</p>
                        </div>
                        <div
                            class="bg-purple-50/50 dark:bg-purple-900/10 p-3 rounded-xl border border-purple-100 dark:border-purple-800/20">
                            <label
                                class="block text-xs font-bold text-purple-700 dark:text-purple-400 uppercase mb-2">Packing Service Fee (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.customerPackingFee"
                                class="w-full bg-white dark:bg-black/40 border border-purple-200 dark:border-purple-800/30 rounded-lg p-2.5 text-sm font-mono font-bold text-purple-900 dark:text-purple-100 focus:ring-2 focus:ring-purple-500/20 outline-none">
                            <p class="text-[10px] text-purple-600 dark:text-purple-400 mt-1 opacity-80">Flat fee for packing service add-on.</p>
                        </div>
                        <div
                            class="bg-amber-50/50 dark:bg-amber-900/10 p-3 rounded-xl border border-amber-100 dark:border-amber-800/20">
                            <label
                                class="block text-xs font-bold text-amber-700 dark:text-amber-400 uppercase mb-2">Insurance Rate (%)</label>
                            <input type="number" :disabled="!isEditMode" step="0.1"
                                v-model.number="rates.insurancePct"
                                class="w-full bg-white dark:bg-black/40 border border-amber-200 dark:border-amber-800/30 rounded-lg p-2.5 text-sm font-mono font-bold text-amber-900 dark:text-amber-100 focus:ring-2 focus:ring-amber-500/20 outline-none">
                            <p class="text-[10px] text-amber-600 dark:text-amber-400 mt-1 opacity-80">% of declared value charged as insurance.</p>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="flex items-center justify-between mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                        <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300">
                            C. Packing Materials</h4>
                        <button v-if="isEditMode" @click="showAddMaterialModal = true"
                            class="flex items-center gap-1 text-xs text-primary hover:text-primary/80 font-medium">
                            <span class="material-symbols-outlined text-[16px]">add_circle</span>
                            Add Material
                        </button>
                    </div>
                    <div class="space-y-3">
                        <div v-for="(material, index) in materialsArray" :key="material.id"
                            class="flex items-center gap-3 group">
                            <span class="text-sm text-gray-600 dark:text-gray-400 w-28 truncate" :title="material.name">{{ material.name }}</span>
                            <span class="text-sm font-mono text-gray-400">₹</span>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="materialsArray[index].rate"
                                class="flex-1 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            <span class="text-xs text-gray-400 w-12">/ {{ material.unit }}</span>
                            <button v-if="isEditMode && !['box', 'bubbleWrap', 'crate'].includes(material.id)"
                                @click="removeMaterial(index)"
                                class="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-600 transition-opacity">
                                <span class="material-symbols-outlined text-[18px]">delete</span>
                            </button>
                        </div>
                        <p v-if="materialsArray.length === 0" class="text-xs text-gray-400 italic">No materials configured</p>
                    </div>
                </div>
            </div>

            <div>
                <h4
                    class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                    D. Individual / Parcel Pricing</h4>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">House Shift Booking Fee (₹)</label>
                                <input type="number" :disabled="!isEditMode" v-model.number="rates.individualBookingFee"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">House Shift Helper (₹)</label>
                                <input type="number" :disabled="!isEditMode" v-model.number="rates.individualLaborRate"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Packing %</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.individualPackingPct"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Small Parcel ₹ / KG</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.smallPackagePerKgRate"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Small Parcel ₹ / KM</label>
                            <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.smallPackagePerKmRate"
                                class="w-full lg:w-1/2 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                        </div>
                    </div>
                    <div>
                        <h5 class="text-xs font-bold text-gray-500 uppercase mb-3">House Shift Distance Rates (₹ / KM)</h5>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs text-gray-500 mb-1">Mini Truck</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.individualDistanceRates.miniTruck"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 mb-1">Tempo</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.individualDistanceRates.tempo"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 mb-1">LCV</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.individualDistanceRates.lcv"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 mb-1">HCV</label>
                                <input type="number" :disabled="!isEditMode" step="0.1" v-model.number="rates.individualDistanceRates.hcv"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono focus:ring-2 focus:ring-primary/20 outline-none">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const {
    isEditMode,
    materialsArray,
    rates,
    removeMaterial,
    showAddMaterialModal,
} = inject(rateGovernancePageKey)
</script>
