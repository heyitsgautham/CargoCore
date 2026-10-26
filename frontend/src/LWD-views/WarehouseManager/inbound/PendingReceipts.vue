<template>
    <!-- Pending Receipt with Mismatch & Damage -->
    <div class="xl:col-span-3 glass-panel rounded-xl overflow-hidden">
        <div
            class="p-4 border-b border-gray-100 dark:border-white/5 font-bold text-gray-900 dark:text-white flex flex-wrap gap-2 justify-between items-center">
            <span>ASN Verification & Receiving</span>
            <div class="flex gap-2">
                <button @click="showMismatchModal = true"
                    class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">flag</span> Flag Mismatch
                </button>
                <button @click="showDamageModal = true"
                    class="bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-600 dark:text-yellow-400 px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">broken_image</span> Report Damage
                </button>
            </div>
        </div>
        <div class="overflow-x-auto">
        <table class="w-full text-left text-sm min-w-[700px]">
            <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase text-[11px]">
                <tr>
                    <th class="px-4 py-3">ASN ID</th>
                    <th class="px-4 py-3">Supplier</th>
                    <th class="px-4 py-3">Exp / Rcvd</th>
                    <th class="px-4 py-3">ETA</th>
                    <th class="px-4 py-3">Status</th>
                    <th class="px-4 py-3">Issues</th>
                    <th class="px-4 py-3">Action</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                <tr v-for="asn in asns" :key="asn.id"
                    class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                    <td class="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-300">{{ asn.id }}</td>
                    <td class="px-4 py-3 text-gray-900 dark:text-white text-xs">{{ asn.supplier }}</td>
                    <td class="px-4 py-3 text-xs">
                        <span class="text-gray-600 dark:text-gray-400">{{ asn.expected }}</span>
                        <span class="text-gray-400 mx-1">/</span>
                        <span :class="asn.received !== asn.expected && asn.received > 0 ? 'text-red-500 font-bold' : 'text-gray-500'">
                            {{ asn.received || '--' }}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-xs text-gray-600 dark:text-gray-300 whitespace-nowrap">{{ asn.eta }}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="asn.statusClass">
                            {{ asn.displayStatus }}
                        </span>
                    </td>
                    <td class="px-4 py-3">
                        <div class="flex gap-1 flex-wrap">
                            <span v-if="asn.mismatch"
                                class="px-1.5 py-0.5 bg-red-500/20 text-red-600 dark:text-red-400 text-[9px] font-bold rounded border border-red-500/20">MISMATCH</span>
                            <span v-if="asn.damaged"
                                class="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 text-[9px] font-bold rounded border border-yellow-500/20">DAMAGED</span>
                            <span v-if="!asn.mismatch && !asn.damaged" class="text-gray-500 text-xs">—</span>
                        </div>
                        <div v-if="asn.issueResolutionLabel" class="mt-1 text-[10px] text-gray-500 dark:text-gray-400">
                            {{ asn.issueResolutionLabel }}
                        </div>
                        <div v-if="asn.issueStatus || asn.issueTicketReference" class="mt-1 flex gap-1 flex-wrap items-center">
                            <span v-if="asn.issueStatus" class="px-1.5 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wider"
                                :class="issueStatusClass(asn.issueStatus)">
                                {{ formatIssueStatus(asn.issueStatus) }}
                            </span>
                            <span v-if="asn.issueTicketReference" class="text-[10px] text-gray-400">
                                {{ asn.issueTicketReference }}
                            </span>
                        </div>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <button @click="openInboundEstimator(asn.id)"
                            class="bg-violet-500/15 hover:bg-violet-500/25 text-violet-600 dark:text-violet-300 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                            AI Plan
                        </button>
                        <button v-if="showTakeBackAction(asn)" @click="generateTakeBack(asn)"
                            class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                            Generate Vendor Take-Back
                        </button>
                        <button v-if="asn.status === 'InTransit'" @click="markArrived(asn)"
                            class="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-600 dark:text-indigo-300 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                            Mark Arrived
                        </button>
                        <button v-else-if="canStartInboundProcessing(asn)" @click="startReceiving(asn)"
                            class="bg-primary/20 hover:bg-primary/30 text-primary px-3 py-1.5 rounded text-xs font-bold transition-colors">
                            Start Receiving
                        </button>
                        <button v-else-if="canCompleteInboundProcessing(asn)" @click="completeReceiving(asn, { navigateToPicking: true })"
                            class="bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap">
                            Complete & Move to Picking
                        </button>
                        <span v-else-if="asn.warehouseSubstatus === 'ON_HOLD'" class="text-red-500 text-xs font-bold">Vendor take-back generated</span>
                        <span v-else-if="showIssueHoldState(asn)" class="text-amber-500 text-xs font-bold">{{ asn.issueBlockingReason || 'Awaiting support/vendor decision' }}</span>
                        <span v-else-if="asn.status === 'Completed'" class="text-green-500 text-xs font-bold">Ready for next step</span>
                        <span v-else class="text-gray-500 text-xs">Awaiting arrival</span>
                    </td>
                </tr>
                <tr v-if="asns.length === 0">
                    <td colspan="7" class="p-8 text-center text-gray-500 text-sm">
                        No vendor inbound shipments are scheduled for this warehouse.
                    </td>
                </tr>
            </tbody>
        </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const {
    asns,
    canCompleteInboundProcessing,
    canStartInboundProcessing,
    completeReceiving,
    formatIssueStatus,
    generateTakeBack,
    issueStatusClass,
    markArrived,
    openInboundEstimator,
    showDamageModal,
    showIssueHoldState,
    showMismatchModal,
    showTakeBackAction,
    startReceiving,
} = inject(inboundPageKey)
</script>
