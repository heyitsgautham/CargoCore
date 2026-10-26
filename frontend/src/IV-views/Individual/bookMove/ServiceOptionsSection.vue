<template>
    <!-- Section 4: Service Customization -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span
                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">4</span>
            Customize Service
        </h3>
        <div class="mb-6">
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Packing
                Service</label>
            <div class="flex flex-col sm:flex-row gap-3">
                <label
                    class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 flex-1 transition-all"
                    :class="!form.packingRequired ? 'border-green-500 bg-green-500/5' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5'">
                    <input type="radio" :value="false" v-model="form.packingRequired"
                        class="accent-green-500" />
                    <div><span class="text-sm text-gray-900 dark:text-white font-medium">I will pack
                            myself</span>
                        <p class="text-xs text-gray-500">No packing charges</p>
                    </div>
                </label>
                <label
                    class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 flex-1 transition-all"
                    :class="form.packingRequired ? 'border-green-500 bg-green-500/5' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5'">
                    <input type="radio" :value="true" v-model="form.packingRequired"
                        class="accent-green-500" />
                    <div><span class="text-sm text-gray-900 dark:text-white font-medium">We pack for
                            you</span>
                        <p class="text-xs text-gray-500">Professional packing team</p>
                    </div>
                </label>
            </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label
                    class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Additional
                    Labor (Helpers)</label>
                <div class="flex items-center gap-4">
                    <button @click="form.laborCount > 0 ? form.laborCount-- : null"
                        class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white flex items-center justify-center text-xl font-bold transition-colors">−</button>
                    <span class="text-2xl font-bold text-gray-900 dark:text-white w-8 text-center">{{
                        form.laborCount }}</span>
                    <button @click="form.laborCount++"
                        class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white flex items-center justify-center text-xl font-bold transition-colors">+</button>
                </div>
                <p class="text-xs text-gray-500 mt-2">₹{{ (rates.individualLaborRate ?? 800).toLocaleString() }}/helper per move</p>
            </div>
            <div v-if="form.packingRequired">
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Packing
                    Materials</label>
                <div class="space-y-2 max-h-44 overflow-y-auto no-scrollbar">
                    <div v-if="packingCatalogLoading" class="text-xs text-gray-400 py-2 text-center">Loading materials...</div>
                    <div v-for="mat in packingCatalog" :key="mat.key"
                        class="flex justify-between items-center text-sm p-2 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                        <div class="flex items-center gap-2"><span
                                class="material-symbols-outlined text-sm text-gray-400">{{ mat.icon
                                }}</span><span
                                class="text-gray-700 dark:text-gray-300 text-xs sm:text-sm">{{ mat.name
                                }}</span>
                            <span v-if="mat.stock !== null" class="text-[10px] font-mono" :class="mat.stock <= 5 ? 'text-red-400' : 'text-gray-500'">({{ mat.stock }} in stock)</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs text-gray-400">₹{{ mat.price }}/{{ mat.unit }}</span>
                            <input type="number" :value="form.materials[mat.key] || 0"
                                @input="form.materials[mat.key] = parseInt($event.target.value) || 0"
                                min="0" :max="mat.stock ?? 9999"
                                class="w-14 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1 text-right text-gray-900 dark:text-white text-sm" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">
                    Approx. Cargo Weight (kg)
                </label>
                <input
                    v-model.number="form.cargoWeightKg"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="e.g. 650"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all"
                />
                <p class="text-[11px] text-gray-500 mt-1">Recommended for dispatch planning and vehicle fit.</p>
            </div>
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">
                    Approx. Cargo Volume (m³)
                </label>
                <input
                    v-model.number="form.cargoVolumeM3"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="e.g. 8.5"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all"
                />
                <p class="text-[11px] text-gray-500 mt-1">AI room scan can prefill this when available.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { form, packingCatalog, packingCatalogLoading, rates } = inject(bookMovePageKey)
</script>
