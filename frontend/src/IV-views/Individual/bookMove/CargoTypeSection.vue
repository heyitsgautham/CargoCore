<template>
    <!-- Section 1: Cargo Type -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span
                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">1</span>
            Select Cargo Type
        </h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            <button v-for="type in cargoTypes" :key="type.name"
                class="p-3 sm:p-4 rounded-xl border transition-all flex flex-col items-center gap-2 group"
                :class="form.cargoType === type.name
                    ? 'bg-green-500/10 border-green-500 dark:bg-green-500/10 dark:border-green-500'
                    : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-green-500/50'"
                @click="form.cargoType = type.name">
                <span class="material-symbols-outlined text-2xl sm:text-3xl"
                    :class="form.cargoType === type.name ? 'text-green-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                    {{ type.icon }}
                </span>
                <span class="text-xs font-medium"
                    :class="form.cargoType === type.name ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                    {{ type.name }}
                </span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { cargoTypes, form } = inject(bookMovePageKey)
</script>
