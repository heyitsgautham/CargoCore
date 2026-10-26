<template>
    <!-- Pending Material Requests Section -->
    <div v-if="pendingMaterialRequests.length > 0" class="glass-panel rounded-xl overflow-hidden mt-6">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-orange-50/50 dark:bg-orange-900/20 flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-orange-100 dark:bg-orange-900/30 text-orange-600 flex items-center justify-center">
                <span class="material-symbols-outlined text-[20px]">pending_actions</span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white text-lg">Pending Material Requests
                <span class="text-xs font-normal text-orange-600 ml-2">({{ pendingMaterialRequests.length }} awaiting approval)</span>
            </h3>
        </div>
        <div class="p-4 space-y-3">
            <div v-for="req in pendingMaterialRequests" :key="req.id"
                class="flex items-center justify-between bg-white dark:bg-black/20 border border-gray-100 dark:border-white/10 rounded-lg p-3">
                <div class="flex-1">
                    <div class="flex items-center gap-2">
                        <span class="font-medium text-gray-900 dark:text-white">{{ req.material_name }}</span>
                        <span class="text-xs bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded">{{ req.unit }}</span>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">
                        Requested by {{ req.requested_by_name || 'Warehouse Manager' }}
                        <span v-if="req.suggested_rate"> • Suggested: ₹{{ req.suggested_rate }}</span>
                    </p>
                    <p v-if="req.reason" class="text-xs text-gray-400 mt-1 italic">"{{ req.reason }}"</p>
                </div>
                <div class="flex items-center gap-2">
                    <input type="number" v-model.number="approvalRates[req.id]" placeholder="Rate"
                        class="w-20 bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm font-mono">
                    <button @click="approveMaterialRequest(req)" :disabled="!approvalRates[req.id]"
                        class="bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">check</span>
                        Approve
                    </button>
                    <button @click="rejectMaterialRequest(req)"
                        class="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">close</span>
                        Reject
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { approvalRates, approveMaterialRequest, pendingMaterialRequests, rejectMaterialRequest } = inject(rateGovernancePageKey)
</script>
