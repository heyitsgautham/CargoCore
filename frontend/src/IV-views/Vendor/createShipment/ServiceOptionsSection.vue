<template>
    <!-- Service Options -->
    <div class="glass-panel p-6 rounded-xl space-y-4">
        <h3
            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
            3. Service Options</h3>
        <div class="flex flex-col sm:flex-row gap-4">
            <label
                class="flex-1 flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors"
                :class="form.packingRequired ? 'border-blue-500 bg-blue-500/5' : 'border-gray-200 dark:border-white/10 hover:border-blue-400'">
                <input type="checkbox" v-model="form.packingRequired" @change="recalculate"
                    class="sr-only">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                    :class="form.packingRequired ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-400'">
                    <span class="material-symbols-outlined text-[20px]">inventory</span>
                </div>
                <div>
                    <div class="font-medium text-sm text-gray-900 dark:text-white">Packing Service</div>
                    <div class="text-xs text-gray-500">+₹{{ (rates.customerPackingFee ?? 200).toLocaleString() }} flat fee</div>
                </div>
            </label>
            <label
                class="flex-1 flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors"
                :class="form.laborRequired ? 'border-purple-500 bg-purple-500/5' : 'border-gray-200 dark:border-white/10 hover:border-purple-400'">
                <input type="checkbox" v-model="form.laborRequired" @change="recalculate"
                    class="sr-only">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                    :class="form.laborRequired ? 'bg-purple-500 text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-400'">
                    <span class="material-symbols-outlined text-[20px]">groups</span>
                </div>
                <div>
                    <div class="font-medium text-sm text-gray-900 dark:text-white">Labor Helpers</div>
                    <div class="text-xs text-gray-500">+₹{{ (rates.customerLaborRate ?? 250).toLocaleString() }} per helper</div>
                </div>
            </label>
        </div>
        <div v-if="form.laborRequired" class="flex items-center gap-3">
            <label class="text-xs text-gray-500 dark:text-gray-400">Number of helpers:</label>
            <div class="flex items-center gap-2">
                <button @click="form.laborCount = Math.max(1, form.laborCount - 1); recalculate()"
                    class="w-7 h-7 rounded-full bg-gray-100 dark:bg-white/10 hover:bg-blue-500/20 text-gray-700 dark:text-white flex items-center justify-center font-bold transition-colors">-</button>
                <span class="w-8 text-center font-bold text-gray-900 dark:text-white">{{ form.laborCount
                    }}</span>
                <button @click="form.laborCount = Math.min(8, form.laborCount + 1); recalculate()"
                    class="w-7 h-7 rounded-full bg-gray-100 dark:bg-white/10 hover:bg-blue-500/20 text-gray-700 dark:text-white flex items-center justify-center font-bold transition-colors">+</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { form, rates, recalculate } = inject(createShipmentPageKey)
</script>
