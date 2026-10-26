<template>
    <!-- Sample Data Tables -->
    <div class="glass-panel p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Sample Data Preview</h3>
        <div class="space-y-4">
            <div v-for="cat in categories" :key="cat.value"
                class="border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden">
                <div @click="toggleSample(cat.value)"
                    class="flex items-center justify-between p-4 bg-gray-50 dark:bg-white/5 cursor-pointer hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-blue-500 text-xl">{{ cat.icon }}</span>
                        <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ cat.label }} Templates (5
                            rows)</h4>
                    </div>
                    <span class="material-symbols-outlined text-gray-500 transition-transform duration-300"
                        :class="expandedSample === cat.value ? 'rotate-180' : ''">expand_more</span>
                </div>

                <div v-show="expandedSample === cat.value"
                    class="border-t border-gray-200 dark:border-white/10">
                    <div class="overflow-x-auto">
                        <table class="w-full text-xs border-collapse">
                            <thead class="bg-gray-50 dark:bg-white/5">
                                <tr>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        Order ID</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        Description</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        Pallets</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        Weight (kg)</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        From</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        To</th>
                                    <th
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                        Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="i in 5" :key="i" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                        {{ cat.value.toUpperCase().substring(0, 3) }}_{{
                                            String(i).padStart(3, '0') }}</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                        Sample {{ cat.label }} cargo {{ i }}</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                        {{ 5 + i }}</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                        {{ (200 + i * 50).toLocaleString() }}</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                        Mumbai Hub</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                        Delhi</td>
                                    <td
                                        class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                        {{ new Date(2026, 2, 1 + i).toLocaleDateString('en-GB', {
                                            day:
                                                '2-digit', month: 'short'
                                        }) }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { categories, expandedSample, toggleSample } = inject(createShipmentPageKey)
</script>
