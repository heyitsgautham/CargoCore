<template>
    <div class="glass-panel p-4 sm:p-6 rounded-xl border-l-4 border-blue-500">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-blue-500">package_2</span>
            Small Package Details
        </h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">Send books, documents, small boxes, or
            parcels. Auto-scheduled pickup with estimated delivery.</p>

        <div class="mb-5">
            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Package Type</label>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <button v-for="type in pkgTypes" :key="type.name"
                    class="p-2.5 rounded-xl border transition-all flex flex-col items-center gap-1.5 group"
                    :class="pkg.packageType === type.name
                        ? 'bg-blue-500/10 border-blue-500 dark:bg-blue-500/10 dark:border-blue-500'
                        : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-blue-500/50'"
                    @click="pkg.packageType = type.name">
                    <span class="material-symbols-outlined text-xl sm:text-2xl"
                        :class="pkg.packageType === type.name ? 'text-blue-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                        {{ type.icon }}
                    </span>
                    <span class="text-[11px] font-medium"
                        :class="pkg.packageType === type.name ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'">
                        {{ type.name }}
                    </span>
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Package
                    Description</label>
                <input v-model="pkg.description" type="text" placeholder="e.g., 3 books, 1 envelope"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 outline-none" />
            </div>
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Approx.
                    Weight (kg)</label>
                <input v-model.number="pkg.weight" type="number" min="0.1" step="0.1" placeholder="2.5"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 outline-none" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { pkg, pkgTypes } = inject(bookMovePageKey)
</script>
