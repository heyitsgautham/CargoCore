<template>
    <!-- Read-Only Details Modal -->
    <Teleport to="body">
        <div v-if="showDetailsModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div class="bg-slate-950/98 rounded-3xl w-full max-w-md max-h-[90vh] shadow-2xl flex flex-col animate-scale-in border border-white/10 backdrop-blur-xl">
                <div class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/90 shrink-0 rounded-t-3xl">
                    <div>
                        <h3 class="text-lg font-bold text-white">Claim Details</h3>
                        <p class="text-xs text-gray-500 font-mono">{{ selectedRMA?.referenceCode || selectedRMA?.id }}</p>
                    </div>
                    <button @click="showDetailsModal = false" class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4 overflow-y-auto custom-scrollbar">
                    <!-- Flow badge -->
                    <div class="flex items-center gap-2">
                        <span v-if="selectedRMA?.flow_type === 'photo_review'"
                            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 border border-blue-500/30 text-blue-400">
                            <span class="material-symbols-outlined text-[11px]">photo_camera</span> Photo Review Only
                        </span>
                        <span v-else-if="selectedRMA?.flow_type === 'pickup_inspection'"
                            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-purple-500/20 border border-purple-500/30 text-purple-400">
                            <span class="material-symbols-outlined text-[11px]">local_shipping</span> Pickup Inspection Required
                        </span>
                        <span class="px-2 py-0.5 rounded-full text-xs font-bold uppercase border ml-auto" :class="getStatusClass(selectedRMA?.status)">
                            {{ selectedRMA?.status || 'Reported' }}
                        </span>
                    </div>

                    <div v-if="selectedRMA?.walletCredited" class="flex items-center gap-2 rounded-xl border border-green-500/20 bg-green-500/10 px-3 py-2 text-sm text-green-300">
                        <span class="material-symbols-outlined text-[18px]">wallet</span>
                        Refund issued to customer wallet.
                    </div>

                    <div v-if="selectedRMA?.transportChargeAmount > 0" class="rounded-xl border border-amber-500/20 bg-amber-500/10 px-3 py-3 text-sm text-amber-200">
                        <div class="text-[10px] uppercase tracking-wider font-bold text-amber-400 mb-2">Transport Charge Recovery</div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <div class="text-[10px] text-gray-500 mb-0.5">Applied Charge</div>
                                <div class="font-bold text-white">₹{{ selectedRMA.transportChargeAmount || 0 }}</div>
                            </div>
                            <div>
                                <div class="text-[10px] text-gray-500 mb-0.5">Status</div>
                                <div class="font-bold text-amber-300">{{ selectedRMA.transportChargeStatus || 'Pending' }}</div>
                            </div>
                            <div>
                                <div class="text-[10px] text-gray-500 mb-0.5">Collected From Wallet</div>
                                <div class="font-bold text-white">₹{{ selectedRMA.transportChargeWalletCollected || 0 }}</div>
                            </div>
                            <div>
                                <div class="text-[10px] text-gray-500 mb-0.5">Pending For Next Order</div>
                                <div class="font-bold text-white">₹{{ selectedRMA.transportChargePendingAmount || 0 }}</div>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p class="text-xs text-gray-500 mb-0.5">Claim ID</p>
                            <p class="font-mono font-bold text-white">{{ selectedRMA?.referenceCode || selectedRMA?.id }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-500 mb-0.5">Order ID</p>
                            <p class="font-mono font-bold text-white">{{ selectedRMA?.orderId || '—' }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-500 mb-0.5">Customer</p>
                            <p class="font-bold text-white">{{ selectedRMA?.customer }}</p>
                        </div>
                        <div>
                            <p class="text-xs text-gray-500 mb-0.5">Refund Amount</p>
                            <p class="font-bold text-green-400 font-mono">₹{{ selectedRMA?.refundAmount || 0 }}</p>
                        </div>
                    </div>

                    <div v-if="selectedRMA?.reason" class="bg-white/5 p-3 rounded-xl text-sm text-gray-300 italic border border-white/10">
                        "{{ selectedRMA.reason }}"
                    </div>

                    <div v-if="selectedRMA?.flow_type === 'pickup_inspection' && (selectedRMA?.wmActualCondition || selectedRMA?.wmGenuineness !== undefined || selectedRMA?.wmRecommendedSettlement || selectedRMA?.wmRemarks)"
                        class="rounded-xl border border-teal-500/20 bg-teal-500/10 p-4 space-y-3">
                        <div class="text-[10px] text-teal-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-[14px]">warehouse</span>
                            WM Inspection Summary
                        </div>
                        <div class="grid grid-cols-2 gap-3 text-sm">
                            <div v-if="selectedRMA?.wmActualCondition">
                                <div class="text-[10px] text-gray-500 mb-0.5">Actual Condition</div>
                                <div class="font-bold text-white">{{ selectedRMA.wmActualCondition }}</div>
                            </div>
                            <div v-if="selectedRMA?.wmGenuineness !== undefined">
                                <div class="text-[10px] text-gray-500 mb-0.5">Claim Valid</div>
                                <div class="font-bold" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                    {{ selectedRMA.wmGenuineness ? 'Genuine' : 'Not Genuine' }}
                                </div>
                            </div>
                            <div v-if="selectedRMA?.wmRecommendedSettlement">
                                <div class="text-[10px] text-gray-500 mb-0.5">Recommended Outcome</div>
                                <div class="font-bold text-yellow-400">{{ selectedRMA.wmRecommendedSettlement }}</div>
                            </div>
                            <div v-if="selectedRMA?.wmDisposition">
                                <div class="text-[10px] text-gray-500 mb-0.5">Warehouse Disposition</div>
                                <div class="font-bold text-cyan-400">{{ selectedRMA.wmDisposition }}</div>
                            </div>
                            <div v-if="selectedRMA?.wmGraderName">
                                <div class="text-[10px] text-gray-500 mb-0.5">Inspected By</div>
                                <div class="font-bold text-white">{{ selectedRMA.wmGraderName }}</div>
                            </div>
                            <div v-if="selectedRMA?.wmGradedAt">
                                <div class="text-[10px] text-gray-500 mb-0.5">Inspection Time</div>
                                <div class="text-xs text-gray-300">{{ formatDateTime(selectedRMA.wmGradedAt) }}</div>
                            </div>
                            <div v-if="selectedRMA?.wmRemarks" class="col-span-2">
                                <div class="text-[10px] text-gray-500 mb-0.5">WM Remarks</div>
                                <div class="text-xs text-gray-300 italic">"{{ selectedRMA.wmRemarks }}"</div>
                            </div>
                        </div>
                    </div>

                    <div v-if="selectedRMA?.notes" class="bg-white/5 p-3 rounded-xl text-sm text-gray-400 border border-white/10">
                        <p class="text-xs text-gray-500 mb-1">LM Notes</p>
                        {{ selectedRMA.notes }}
                    </div>

                    <!-- Refund action if approved/partially approved and not yet refunded -->
                    <div v-if="['Approved', 'Partially Approved'].includes(selectedRMA?.status) && selectedRMA?.refundAmount > 0 && !selectedRMA?.walletCredited"
                        class="pt-2 border-t border-white/10">
                        <button @click="handleIssueRefund"
                            :disabled="refundIssuing || refundIssued"
                            class="w-full py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2"
                            :class="refundIssued
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30 cursor-default'
                                : 'bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white'">
                            <span v-if="refundIssuing" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                            <span v-else class="material-symbols-outlined text-[18px]">{{ refundIssued ? 'check_circle' : 'account_balance_wallet' }}</span>
                            {{ refundIssued ? 'Refund Issued' : refundIssuing ? 'Issuing...' : `Issue ₹${selectedRMA.refundAmount} to Customer Wallet` }}
                        </button>
                        <p v-if="refundError" class="text-xs text-red-400 mt-1.5 text-center">{{ refundError }}</p>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    formatDateTime,
    getStatusClass,
    handleIssueRefund,
    refundError,
    refundIssued,
    refundIssuing,
    selectedRMA,
    showDetailsModal,
} = inject(reverseLogisticsPageKey)
</script>
