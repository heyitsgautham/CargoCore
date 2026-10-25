<template>
    <!-- 5. ASSETS & INVENTORY (Specific Items) -->
    <div v-if="activeTab === 'assets'" class="space-y-6 animate-fade-in">

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Specific Counts for User Requests -->
            <div
                class="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-500/20">
                <h4 class="text-xs uppercase font-bold text-blue-800 dark:text-blue-300">Total Boxes</h4>
                <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{ getInventoryCount(['Box',
                    'Packaging']) }}</p>
            </div>
            <div
                class="p-4 bg-orange-50 dark:bg-orange-900/10 rounded-xl border border-orange-100 dark:border-orange-500/20">
                <h4 class="text-xs uppercase font-bold text-orange-800 dark:text-orange-300">Crates & Cargo</h4>
                <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{
                    getInventoryCount(['Crates', 'Cargo']) }}</p>
            </div>
            <div
                class="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-500/20">
                <h4 class="text-xs uppercase font-bold text-purple-800 dark:text-purple-300">Tape & Tools</h4>
                <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{ getInventoryCount(['Tape',
                    'Consumables']) }}</p>
            </div>
            <div
                class="p-4 bg-teal-50 dark:bg-teal-900/10 rounded-xl border border-teal-100 dark:border-teal-500/20">
                <h4 class="text-xs uppercase font-bold text-teal-800 dark:text-teal-300">Utensils</h4>
                <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{
                    getInventoryCount(['Utensils']) }}</p>
            </div>
        </div>

        <!-- Returnable Equipment Audit -->
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden mt-6 mb-6">
            <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-indigo-50 dark:bg-indigo-900/10">
                <h3 class="font-bold text-indigo-900 dark:text-indigo-300">Returnable Equipment Audit
                    (Crates/Blankets)</h3>
            </div>
            <table class="w-full text-left text-xs">
                <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-4">Customer Order</th>
                        <th class="p-4 text-center">Equipment Issued</th>
                        <th class="p-4 text-center">Returned</th>
                        <th class="p-4 text-center text-red-500">Missing/Damaged</th>
                        <th class="p-4 text-right">Penalty Cost</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="eq in store.equipmentLedger" :key="eq.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-4 font-bold text-gray-900 dark:text-white">{{ eq.referenceCode || 'Unknown' }}</td>
                        <td class="p-4 text-center font-mono">{{ eq.issuedCount }} {{ eq.itemType }}</td>
                        <td class="p-4 text-center font-mono">{{ eq.returnedCount }}</td>
                        <td class="p-4 text-center font-bold" :class="(eq.issuedCount - eq.returnedCount) > 0 ? 'text-red-500' : 'text-gray-300'">
                            {{ Math.max(0, eq.issuedCount - eq.returnedCount) }}
                        </td>
                        <td class="p-4 text-right font-mono font-bold" :class="(eq.issuedCount - eq.returnedCount) > 0 ? 'text-red-600' : 'text-green-600'">
                            {{ (eq.issuedCount - eq.returnedCount) > 0 ? `-$${((eq.issuedCount - eq.returnedCount) * 20).toFixed(2)}` : '$0.00' }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- MAIN INVENTORY TABLE -->
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 overflow-hidden flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white">Detailed Inventory Levels</h3>
                    <button @click="openRestockModal"
                        class="bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 rounded-lg text-xs font-bold transition-colors flex items-center gap-1 relative">
                        <span class="material-symbols-outlined text-[14px]">pending_actions</span> Pending Restocks
                        <span v-if="escalatedRestockCount > 0"
                            class="ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-orange-500 text-white animate-pulse">\u26a1 {{ escalatedRestockCount }} Urgent</span>
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto custom-scrollbar">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="text-gray-400 border-b border-gray-100 dark:border-white/5">
                                <th class="pb-2">Item Name</th>
                                <th class="pb-2">Category</th>
                                <th class="pb-2 text-right">Capacity</th>
                                <th class="pb-2 text-right">Stock Left</th>
                                <th class="pb-2 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="item in store.filteredInventory" :key="item.id">
                                <td class="py-2 font-medium">{{ item.name }}</td>
                                <td class="py-2 text-gray-500">{{ item.category }}</td>
                                <td class="py-2 text-right font-mono">{{ Math.floor(item.quantity * 1.5) }} {{
                                    item.unit }}</td>
                                <td class="py-2 text-right font-mono font-bold">{{ item.quantity }} {{ item.unit
                                    }}</td>
                                <td class="py-2 text-right">
                                    <span class="px-2 py-0.5 rounded text-[10px]"
                                        :class="item.status === 'Good' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">{{
                                        item.status }}</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Damage Claims -->
            <div
                class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 overflow-hidden flex flex-col">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Damage & Claims Queue</h3>
                <div class="flex-1 overflow-y-auto custom-scrollbar space-y-3">
                    <div v-for="(claim, index) in damageClaims" :key="index" @click="openClaimModal(claim)"
                        class="p-3 border border-red-100 dark:border-red-500/20 bg-red-50 dark:bg-red-500/5 rounded-xl flex gap-3 cursor-pointer hover:bg-red-100 dark:hover:bg-red-500/10 transition-colors">
                        <div
                            class="w-12 h-12 bg-gray-300 rounded-lg shrink-0 flex items-center justify-center font-bold text-gray-500 bg-gray-200 overflow-hidden">
                            <img v-if="claim.image" :src="claim.image" class="w-full h-full object-cover">
                            <span v-else>IMG</span>
                        </div>
                        <div class="flex-1">
                            <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ claim.title }}</h4>
                            <p class="text-xs text-gray-500">Reported by {{ claim.reporter }} • {{ claim.time }}
                            </p>
                            <div class="mt-2 text-red-500 text-xs font-bold"
                                :class="{ 'text-green-500': claim.status === 'Resolved' }">{{ claim.status }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    damageClaims,
    escalatedRestockCount,
    getInventoryCount,
    openClaimModal,
    openRestockModal,
    store,
} = inject(reportsPageKey)
</script>

<style scoped src="./Reports.css"></style>
