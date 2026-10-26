<template>
    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Issuance Log -->
        <div class="lg:col-span-2 glass-panel rounded-xl overflow-hidden">
            <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-100 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">inventory_2</span>
                    Material Issuance Log
                </h3>
                <div class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-0.5 flex">
                    <button
                        :class="logTab === 'issued' ? 'bg-primary rounded text-background-dark text-xs font-bold px-3 py-1' : 'px-3 py-1 text-gray-600 dark:text-gray-400 text-xs'"
                        @click="logTab = 'issued'">Issued</button>
                    <button
                        :class="logTab === 'reserved' ? 'bg-primary rounded text-background-dark text-xs font-bold px-3 py-1' : 'px-3 py-1 text-gray-600 dark:text-gray-400 text-xs'"
                        @click="logTab = 'reserved'">Reserved</button>
                </div>
            </div>
            <div class="overflow-auto max-h-[400px]">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase sticky top-0">
                        <tr>
                            <th class="p-4">Order ID</th>
                            <th class="p-4">Material</th>
                            <th class="p-4">Qty</th>
                            <th class="p-4">Issued To</th>
                            <th class="p-4">Time</th>
                            <th class="p-4">Status</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="log in filteredLog" :key="log.id" class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                            <td class="p-4 font-mono text-primary font-bold">{{ log.orderId }}</td>
                            <td class="p-4 text-gray-900 dark:text-white">{{ log.material }}</td>
                            <td class="p-4 text-gray-600 dark:text-gray-300">{{ log.qty }}</td>
                            <td class="p-4 text-gray-600 dark:text-gray-400">{{ log.issuedTo }}</td>
                            <td class="p-4 text-gray-500 text-xs font-mono">{{ log.time }}</td>
                            <td class="p-4">
                                <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="log.statusClass">{{ log.status }}</span>
                            </td>
                        </tr>
                        <tr v-if="filteredLog.length === 0">
                            <td colspan="6" class="p-8 text-center text-gray-500">No {{ logTab }} records found</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Returnable Assets -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-yellow-600 dark:text-yellow-400">assignment_return</span>
                    Returnable Assets
                </h3>
            </div>
            <div class="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                <div v-for="asset in returnableAssets" :key="asset.id"
                    class="p-3 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-lg hover:border-white/20 transition-colors">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ asset.name }}</div>
                            <div class="text-xs text-gray-500 font-mono">{{ asset.orderId }}</div>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold border" :class="asset.statusClass">{{ asset.status }}</span>
                    </div>
                    <div class="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                        <span>Issued: {{ asset.qty }} pcs</span>
                        <span>Returned: {{ asset.returned }} pcs</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                        <div class="bg-blue-500 h-full" :style="`width: ${asset.qty > 0 ? (asset.returned / asset.qty) * 100 : 0}%`"></div>
                    </div>
                    <div class="flex gap-2 mt-2">
                        <button @click="verifyReturn(asset)"
                            class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-1 rounded text-xs font-bold transition-colors"
                            :class="asset.status === 'Returned' ? 'opacity-50 cursor-not-allowed' : ''">
                            {{ asset.status === 'Returned' ? '✓ Verified' : 'Verify Return' }}
                        </button>
                        <button @click="flagAsset(asset)"
                            class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-1 px-3 rounded text-xs font-bold transition-colors"
                            :class="asset.flagged ? 'bg-red-500/40 border border-red-500/50' : ''">
                            {{ asset.flagged ? '🚩 Flagged' : 'Flag' }}
                        </button>
                    </div>
                </div>
                <div v-if="returnableAssets.length === 0" class="text-center text-gray-500 py-6 text-sm">
                    No returnable assets tracked yet
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { packingMaterialsPageKey } from './packingMaterialsPageContext'

const {
    filteredLog,
    flagAsset,
    logTab,
    returnableAssets,
    verifyReturn,
} = inject(packingMaterialsPageKey)
</script>
