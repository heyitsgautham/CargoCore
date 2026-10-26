<template>
    <!-- Category Selection -->
    <div class="glass-panel p-6 rounded-xl">
        <h3 class="text-base font-bold text-gray-900 dark:text-white mb-4">Shipment Category *</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label v-for="cat in categories" :key="cat.value"
                :class="form.category === cat.value ? 'border-blue-500 bg-blue-500/10' : 'border-gray-200 dark:border-white/10 hover:border-blue-400'"
                class="flex flex-col items-center p-4 rounded-xl border cursor-pointer transition-all">
                <input type="radio" :value="cat.value" v-model="form.category" class="sr-only">
                <span class="material-symbols-outlined text-3xl mb-2"
                    :class="form.category === cat.value ? 'text-blue-500' : 'text-gray-400 dark:text-gray-500'">{{
                        cat.icon }}</span>
                <span class="text-sm font-medium"
                    :class="form.category === cat.value ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'">{{
                        cat.label }}</span>
                <span class="text-xs text-gray-500 mt-1">{{ cat.desc }}</span>
            </label>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { categories, form } = inject(createShipmentPageKey)
</script>
