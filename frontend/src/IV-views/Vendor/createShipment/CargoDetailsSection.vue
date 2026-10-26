<template>
    <!-- Cargo Details -->
    <div class="glass-panel p-6 rounded-xl space-y-4">
        <h3
            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
            1. Cargo Details</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Goods Description
                    *</label>
                <input v-model="form.description" type="text" placeholder="e.g. Electronic components"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div v-if="form.category !== 'b2c'">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">HSN/SAC
                    Code</label>
                <input v-model="form.hsnCode" type="text" placeholder="e.g. 8471"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div v-if="form.category === 'palletized'">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pallet Count
                    *</label>
                <input v-model.number="form.palletCount" @input="recalculate" type="number" min="1"
                    placeholder="e.g. 12"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Total Weight (kg)
                    *</label>
                <input v-model.number="form.weight" @input="recalculate" type="number" min="1"
                    placeholder="e.g. 4500"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Estimated Volume
                    (m³)</label>
                <input v-model.number="form.volume" type="number" min="0" step="0.01"
                    placeholder="e.g. 12.5"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Declared Value
                    (₹)</label>
                <input v-model.number="form.declaredValue" type="number" placeholder="e.g. 50000"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Insurance
                    Required</label>
                <select v-model="form.insuranceRequired"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <option value="no" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">No</option>
                    <option value="yes" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Yes ({{ rates.insurancePct ?? 3 }}% of value)</option>
                </select>
            </div>
            <div class="sm:col-span-2">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Special
                    Handling</label>
                <div class="flex flex-wrap gap-3">
                    <label v-for="h in handlingOptions" :key="h"
                        class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors"
                        :class="form.handling.includes(h) ? 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400'">
                        <input type="checkbox" :value="h" v-model="form.handling" class="sr-only">
                        <span class="text-sm">{{ h }}</span>
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { form, handlingOptions, rates, recalculate } = inject(createShipmentPageKey)
</script>
