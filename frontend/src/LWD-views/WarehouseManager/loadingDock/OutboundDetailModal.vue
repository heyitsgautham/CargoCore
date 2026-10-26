<template>
    <div v-if="showTruckDetail && selectedOutbound"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showTruckDetail = false">
        <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg">Order Details</h3>
                <button @click="showTruckDetail = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-3">
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Tracking</div>
                        <div class="text-gray-900 dark:text-white font-bold font-mono">{{ selectedOutbound.tracking }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Type</div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.type }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Items</div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.items }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Status</div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOutbound.status }}</div>
                    </div>
                </div>
                <button @click="showTruckDetail = false"
                    class="w-full bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm transition-colors">Close</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const { selectedOutbound, showTruckDetail } = inject(loadingDockPageKey)
</script>
