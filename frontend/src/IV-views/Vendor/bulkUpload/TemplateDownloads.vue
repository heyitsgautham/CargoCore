<template>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button @click="downloadTemplate('commercial')"
            class="glass-panel p-5 rounded-xl flex items-center gap-4 hover:ring-1 hover:ring-blue-500/30 transition-all text-left group">
            <div class="p-2.5 bg-blue-500/20 rounded-lg text-blue-500">
                <span class="material-symbols-outlined">business</span>
            </div>
            <div class="flex-1">
                <div
                    class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-blue-500 transition-colors">
                    Commercial (B2B)</div>
                <div class="text-[10px] text-gray-500">Standard B2B shipments</div>
            </div>
            <span
                class="material-symbols-outlined text-gray-400 group-hover:text-blue-500 transition-colors">download</span>
        </button>
        <button @click="downloadTemplate('palletized')"
            class="glass-panel p-5 rounded-xl flex items-center gap-4 hover:ring-1 hover:ring-green-500/30 transition-all text-left group">
            <div class="p-2.5 bg-green-500/20 rounded-lg text-green-500">
                <span class="material-symbols-outlined">inventory_2</span>
            </div>
            <div class="flex-1">
                <div
                    class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-green-500 transition-colors">
                    Palletized</div>
                <div class="text-[10px] text-gray-500">Pallet-based cargo</div>
            </div>
            <span
                class="material-symbols-outlined text-gray-400 group-hover:text-green-500 transition-colors">download</span>
        </button>
        <button @click="downloadTemplate('b2c')"
            class="glass-panel p-5 rounded-xl flex items-center gap-4 hover:ring-1 hover:ring-orange-500/30 transition-all text-left group">
            <div class="p-2.5 bg-orange-500/20 rounded-lg text-orange-500">
                <span class="material-symbols-outlined">person</span>
            </div>
            <div class="flex-1">
                <div
                    class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-orange-500 transition-colors">
                    B2C Shipment</div>
                <div class="text-[10px] text-gray-500">Direct to customer</div>
            </div>
            <span
                class="material-symbols-outlined text-gray-400 group-hover:text-orange-500 transition-colors">download</span>
        </button>
        <router-link to="/vendor/api-docs"
            class="glass-panel p-5 rounded-xl flex items-center gap-4 hover:ring-1 hover:ring-purple-500/30 transition-all group">
            <div class="p-2.5 bg-purple-500/20 rounded-lg text-purple-500">
                <span class="material-symbols-outlined">code</span>
            </div>
            <div class="flex-1">
                <div
                    class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-purple-500 transition-colors">
                    API Documentation</div>
                <div class="text-[10px] text-gray-500">Integrate with your ERP</div>
            </div>
            <span
                class="material-symbols-outlined text-gray-400 group-hover:text-purple-500 transition-colors">open_in_new</span>
        </router-link>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bulkUploadPageKey } from './bulkUploadPageContext'

const { downloadTemplate } = inject(bulkUploadPageKey)
</script>
