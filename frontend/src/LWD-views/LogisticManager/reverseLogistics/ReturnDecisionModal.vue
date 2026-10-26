<template>
    <!-- LM Decision Modal — 2-panel layout -->
    <Teleport to="body">
        <div v-if="showDecisionModal"
            class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showDecisionModal = false">
            <div class="bg-slate-950 rounded-2xl w-full max-w-4xl max-h-[92vh] shadow-2xl flex flex-col border border-white/10 overflow-hidden">

                <!-- Header -->
                <div class="px-6 py-4 border-b border-white/10 bg-slate-900/80 flex items-center justify-between shrink-0">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                            :class="selectedRMA?.flow_type === 'photo_review' ? 'bg-blue-500/20' : 'bg-purple-500/20'">
                            <span class="material-symbols-outlined text-[18px]"
                                :class="selectedRMA?.flow_type === 'photo_review' ? 'text-blue-400' : 'text-purple-400'">
                                {{ selectedRMA?.flow_type === 'photo_review' ? 'photo_camera' : 'local_shipping' }}
                            </span>
                        </div>
                        <div>
                            <div class="text-white font-bold text-sm">{{ decisionModalTitle }}</div>
                            <div class="text-gray-500 text-[11px] font-mono">{{ selectedRMA?.referenceCode || selectedRMA?.id }} · {{ selectedRMA?.customer }}</div>
                        </div>
                        <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border ml-2" :class="getStatusClass(selectedRMA?.status)">
                            {{ selectedRMA?.status || 'Reported' }}
                        </span>
                    </div>
                    <button @click="showDecisionModal = false" class="text-gray-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- 2-column body -->
                <div class="flex flex-1 min-h-0 divide-x divide-white/10">

                    <!-- ═══ LEFT PANEL: Claim Info + WM Review ═══ -->
                    <div class="w-[45%] shrink-0 flex flex-col overflow-y-auto custom-scrollbar bg-slate-900/40">

                        <!-- Customer claim info -->
                        <div class="p-5 border-b border-white/5">
                            <div class="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-3">Customer Claim</div>
                            <div class="flex items-start gap-3">
                                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-white/10 flex items-center justify-center shrink-0">
                                    <span class="text-white font-bold text-xs">{{ (selectedRMA?.customer || '?')[0].toUpperCase() }}</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="font-semibold text-white text-sm">{{ selectedRMA?.customer }}</div>
                                    <div class="text-xs text-gray-400 mt-0.5 italic">"{{ selectedRMA?.reason }}"</div>
                                    <div class="flex items-center gap-2 mt-2">
                                        <span class="text-[10px] text-gray-600 font-mono">₹{{ selectedRMA?.originalPrice || 0 }} value</span>
                                        <button v-if="selectedRMA?.images?.length > 0"
                                            @click="openImageGallery(selectedRMA)"
                                            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors">
                                            <span class="material-symbols-outlined text-[12px]">photo_library</span>
                                            {{ selectedRMA.images.length }} Photos
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- WM Review — Photo flow -->
                        <template v-if="selectedRMA?.flow_type === 'photo_review' && selectedRMA?.status === 'Claims Reviewed'">
                            <div class="p-5 flex-1">
                                <div class="flex items-center gap-2 mb-4">
                                    <div class="w-6 h-6 rounded-md bg-teal-500/20 flex items-center justify-center">
                                        <span class="material-symbols-outlined text-teal-400 text-[14px]">verified</span>
                                    </div>
                                    <span class="text-[11px] font-bold text-teal-400 uppercase tracking-wider">Warehouse Manager Review</span>
                                </div>

                                <div v-if="!selectedRMA?.wmDamageSeverity && selectedRMA?.wmGenuineness === undefined && !selectedRMA?.wmRecommendedSettlement"
                                    class="text-center py-6 text-gray-500 text-xs italic opacity-60">
                                    No WM review data available.
                                </div>

                                <div v-else class="space-y-3">
                                    <!-- Damage Severity -->
                                    <div v-if="selectedRMA?.wmDamageSeverity" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Damage Severity</div>
                                        <div class="text-sm font-bold text-white flex items-center gap-2">
                                            <span class="material-symbols-outlined text-orange-400 text-[16px]">warning</span>
                                            {{ selectedRMA.wmDamageSeverity }}
                                        </div>
                                    </div>

                                    <!-- Genuineness -->
                                    <div v-if="selectedRMA?.wmGenuineness !== undefined && selectedRMA?.wmGenuineness !== null" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Claim Assessment</div>
                                        <div class="flex items-center gap-2">
                                            <div class="w-6 h-6 rounded-full flex items-center justify-center"
                                                :class="selectedRMA.wmGenuineness ? 'bg-green-500/20' : 'bg-red-500/20'">
                                                <span class="material-symbols-outlined text-[14px]"
                                                    :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                                    {{ selectedRMA.wmGenuineness ? 'check_circle' : 'cancel' }}
                                                </span>
                                            </div>
                                            <span class="font-bold text-sm" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                                {{ selectedRMA.wmGenuineness ? 'Looks Genuine' : 'Looks Suspicious' }}
                                            </span>
                                        </div>
                                    </div>

                                    <!-- WM Recommendation -->
                                    <div v-if="selectedRMA?.wmRecommendedSettlement" class="bg-yellow-500/10 rounded-xl p-3 border border-yellow-500/20">
                                        <div class="text-[10px] text-yellow-500/70 uppercase tracking-wider mb-1">WM Recommends</div>
                                        <div class="font-bold text-yellow-400 text-sm flex items-center gap-1.5">
                                            <span class="material-symbols-outlined text-[16px]">recommend</span>
                                            {{ selectedRMA.wmRecommendedSettlement }}
                                        </div>
                                    </div>

                                    <!-- WM Remarks -->
                                    <div v-if="selectedRMA?.wmRemarks" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">WM Remarks</div>
                                        <div class="text-xs text-gray-300 italic leading-relaxed">"{{ selectedRMA.wmRemarks }}"</div>
                                    </div>
                                </div>
                            </div>
                        </template>

                        <!-- WM Review — Pickup Physically Inspected -->
                        <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection' && selectedRMA?.status === 'Physically Inspected'">
                            <div class="p-5 flex-1 space-y-3">
                                <div class="flex items-center gap-2 mb-1">
                                    <div class="w-6 h-6 rounded-md bg-teal-500/20 flex items-center justify-center">
                                        <span class="material-symbols-outlined text-teal-400 text-[14px]">warehouse</span>
                                    </div>
                                    <span class="text-[11px] font-bold text-teal-400 uppercase tracking-wider">Physical Inspection Report</span>
                                </div>

                                <div v-if="selectedRMA?.wmActualCondition" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                    <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Actual Condition</div>
                                    <div class="font-bold text-white text-sm">{{ selectedRMA.wmActualCondition }}</div>
                                </div>

                                <div v-if="selectedRMA?.wmGenuineness !== undefined && selectedRMA?.wmGenuineness !== null" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                    <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Claim Valid?</div>
                                    <div class="flex items-center gap-2">
                                        <span class="material-symbols-outlined text-[16px]" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                            {{ selectedRMA.wmGenuineness ? 'check_circle' : 'cancel' }}
                                        </span>
                                        <span class="font-bold text-sm" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                            {{ selectedRMA.wmGenuineness ? 'Genuine' : 'Not Genuine' }}
                                        </span>
                                    </div>
                                </div>

                                <div v-if="selectedRMA?.wmRecommendedSettlement" class="bg-yellow-500/10 rounded-xl p-3 border border-yellow-500/20">
                                    <div class="text-[10px] text-yellow-500/70 uppercase tracking-wider mb-1">WM Recommends</div>
                                    <div class="font-bold text-yellow-400 text-sm flex items-center gap-1.5">
                                        <span class="material-symbols-outlined text-[16px]">recommend</span>
                                        {{ selectedRMA.wmRecommendedSettlement }}
                                    </div>
                                </div>

                                <div v-if="selectedRMA?.wmDisposition" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                    <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Warehouse Disposition</div>
                                    <div class="font-bold text-cyan-400 text-sm">{{ selectedRMA.wmDisposition }}</div>
                                </div>

                                <div v-if="selectedRMA?.wmGraderName" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                    <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Inspected By</div>
                                    <div class="font-bold text-white text-sm">{{ selectedRMA.wmGraderName }}</div>
                                    <div v-if="selectedRMA?.wmGradedAt" class="text-[10px] text-gray-500 mt-0.5">{{ formatDateTime(selectedRMA.wmGradedAt) }}</div>
                                </div>

                                <div v-if="selectedRMA?.wmRemarks" class="bg-slate-800/60 rounded-xl p-3 border border-white/5">
                                    <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">WM Remarks</div>
                                    <div class="text-xs text-gray-300 italic leading-relaxed">"{{ selectedRMA.wmRemarks }}"</div>
                                </div>

                                <!-- Charge policy reminder -->
                                <div class="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-300/80 space-y-1">
                                    <div class="font-bold text-amber-400 text-[10px] uppercase tracking-wider flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[12px]">info</span> Charge Policy
                                    </div>
                                    <div>Genuine claim → waive pickup charge</div>
                                    <div>Partial → deduct transport charge</div>
                                    <div>Rejected → charge may apply</div>
                                </div>
                            </div>
                        </template>

                        <!-- Pickup Inspection — initial review (no WM data yet) -->
                        <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection'">
                            <div class="p-5 flex-1">
                                <div class="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 text-xs text-orange-300 flex items-start gap-2">
                                    <span class="material-symbols-outlined text-[18px] mt-0.5 shrink-0">warning</span>
                                    <div>
                                        <div class="font-bold mb-1">Physical Pickup Requested</div>
                                        Customer has requested a physical inspection. Review their photos and claim before deciding.
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>

                    <!-- ═══ RIGHT PANEL: LM Decision ═══ -->
                    <div class="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
                        <div class="p-5 flex-1 space-y-4">
                            <div class="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1">Your Decision</div>

                            <!-- Photo Review decisions -->
                            <template v-if="selectedRMA?.flow_type === 'photo_review' && selectedRMA?.status === 'Claims Reviewed'">
                                <div class="grid grid-cols-2 gap-2">
                                    <button v-for="opt in photoReviewDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="relative p-3.5 rounded-xl border transition-all text-left group"
                                        :class="decisionForm.action === opt.value ? opt.activeClass : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/8 hover:border-white/20'">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="material-symbols-outlined text-[18px]">
                                                {{ opt.value === 'Full Refund' ? 'payments' : opt.value === 'Partial Refund' ? 'money_off' : opt.value === 'Reject Claim' ? 'block' : 'pending_actions' }}
                                            </span>
                                            <span class="font-bold text-sm">{{ opt.value }}</span>
                                        </div>
                                        <div class="text-[10px] opacity-60 leading-relaxed">
                                            {{ opt.value === 'Full Refund' ? 'Issue full refund to customer wallet' : opt.value === 'Partial Refund' ? 'Issue partial refund with deduction' : opt.value === 'Reject Claim' ? 'Deny claim, no refund issued' : 'Request more photos or info' }}
                                        </div>
                                        <div v-if="decisionForm.action === opt.value"
                                            class="absolute top-2 right-2 w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                                            <span class="material-symbols-outlined text-[12px]">check</span>
                                        </div>
                                    </button>
                                </div>
                            </template>

                            <!-- Pickup inspection — initial -->
                            <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested'].includes(selectedRMA?.status || 'Reported')">
                                <div class="space-y-2">
                                    <button v-for="opt in pickupDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="relative w-full p-3.5 rounded-xl border transition-all text-left"
                                        :class="decisionForm.action === opt.value ? opt.activeClass : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/8 hover:border-white/20'">
                                        <div class="flex items-center gap-2 mb-0.5">
                                            <span class="material-symbols-outlined text-[18px]">
                                                {{ opt.value === 'Approve Pickup' ? 'local_shipping' : opt.value === 'Reject Pickup Request' ? 'cancel' : 'help' }}
                                            </span>
                                            <span class="font-bold text-sm">{{ opt.label }}</span>
                                            <div v-if="decisionForm.action === opt.value"
                                                class="ml-auto w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                                                <span class="material-symbols-outlined text-[12px]">check</span>
                                            </div>
                                        </div>
                                        <div class="text-[11px] opacity-60 ml-7">{{ opt.desc }}</div>
                                    </button>
                                </div>
                            </template>

                            <!-- Pickup inspection — final decision after physical inspection -->
                            <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection' && selectedRMA?.status === 'Physically Inspected'">
                                <div class="space-y-2">
                                    <button v-for="opt in finalDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="relative w-full p-3.5 rounded-xl border transition-all text-left"
                                        :class="decisionForm.action === opt.value ? opt.activeClass : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/8 hover:border-white/20'">
                                        <div class="flex items-center gap-2 mb-0.5">
                                            <span class="material-symbols-outlined text-[18px]">
                                                {{ opt.value === 'Full Refund' ? 'payments' : opt.value === 'Partial Refund' ? 'money_off' : 'block' }}
                                            </span>
                                            <span class="font-bold text-sm">{{ opt.value }}</span>
                                            <div v-if="decisionForm.action === opt.value"
                                                class="ml-auto w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                                                <span class="material-symbols-outlined text-[12px]">check</span>
                                            </div>
                                        </div>
                                        <div class="text-[10px] opacity-60 ml-7 leading-relaxed">{{ opt.label.split('—')[1]?.trim() }}</div>
                                    </button>
                                </div>
                            </template>

                            <!-- Refund amount panel (shown when refund selected) -->
                            <div v-if="['Full Refund', 'Partial Refund'].includes(decisionForm.action)"
                                class="bg-green-500/5 border border-green-500/20 rounded-xl p-4 space-y-3">
                                <div class="flex items-center justify-between">
                                    <div class="text-[11px] font-bold text-green-400 uppercase tracking-wider flex items-center gap-1.5">
                                        <span class="material-symbols-outlined text-[14px]">payments</span>
                                        Refund Amount
                                    </div>
                                    <span class="text-[11px] font-mono text-gray-500">Max ₹{{ selectedRMA?.originalPrice || 0 }}</span>
                                </div>
                                <div class="relative">
                                    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-sm">₹</span>
                                    <input v-model.number="decisionForm.amount" type="number"
                                        class="w-full bg-slate-800 border border-white/10 rounded-lg pl-7 pr-3 py-2.5 text-sm text-white outline-none focus:ring-1 focus:ring-green-500/50 font-mono"
                                        :placeholder="String(selectedRMA?.originalPrice || 0)">
                                </div>
                                <div class="grid grid-cols-4 gap-1.5">
                                    <button v-for="pct in [25, 50, 75, 100]" :key="pct"
                                        @click="decisionForm.amount = Math.round((selectedRMA?.originalPrice || 0) * (pct/100))"
                                        class="py-1.5 text-[11px] font-bold rounded-lg border transition-colors"
                                        :class="decisionForm.amount === Math.round((selectedRMA?.originalPrice || 0) * (pct/100))
                                            ? 'bg-green-500/20 border-green-500/40 text-green-400'
                                            : 'bg-slate-800 border-white/10 text-gray-300 hover:bg-slate-700'">
                                        {{ pct }}%
                                    </button>
                                </div>
                                <div class="text-[10px] text-gray-500 flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[12px]">info</span>
                                    Refund goes directly to customer wallet
                                </div>
                            </div>

                            <!-- Transport charge checkbox — only for pickup_inspection (a driver was dispatched) -->
                            <div v-if="decisionForm.action === 'Reject Claim' && selectedRMA?.flow_type === 'pickup_inspection'"
                                class="flex items-start gap-3 bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-3">
                                <input type="checkbox" id="applyCharge" v-model="decisionForm.applyTransportCharge"
                                    class="mt-0.5 rounded accent-red-500">
                                <label for="applyCharge" class="text-xs text-gray-300 cursor-pointer leading-relaxed">
                                    <span class="font-semibold text-red-400">Apply transport/pickup charge</span>
                                    <span class="block text-gray-500 mt-0.5">Customer will be billed for the pickup cost</span>
                                </label>
                            </div>

                            <!-- Notes -->
                            <div>
                                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">Notes / Reason</label>
                                <textarea v-model="decisionForm.notes" rows="3"
                                    placeholder="Add decision notes, reason, or instructions for the customer..."
                                    class="w-full bg-slate-800/80 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-primary/40 resize-none"></textarea>
                            </div>
                        </div>

                        <!-- Right panel footer — action buttons -->
                        <div class="px-5 py-4 border-t border-white/10 bg-slate-900/60 flex items-center gap-3 shrink-0">
                            <button @click="showDecisionModal = false"
                                class="px-4 py-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl text-sm font-bold transition-colors">
                                Cancel
                            </button>
                            <button @click="submitDecision"
                                :disabled="!decisionForm.action || submitting"
                                class="flex-1 py-2.5 font-bold rounded-xl shadow transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
                                :class="decisionForm.action === 'Reject Claim' || decisionForm.action === 'Reject Pickup Request'
                                    ? 'bg-red-600 hover:bg-red-500 text-white'
                                    : decisionForm.action === 'Full Refund' || decisionForm.action === 'Approve Pickup' || decisionForm.action === 'Partial Refund'
                                    ? 'bg-green-600 hover:bg-green-500 text-white'
                                    : 'bg-primary hover:bg-primary/90 text-white'">
                                <span v-if="submitting" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                                <span v-else class="material-symbols-outlined text-[18px]">
                                    {{ decisionForm.action === 'Reject Claim' || decisionForm.action === 'Reject Pickup Request' ? 'block' : 'check_circle' }}
                                </span>
                                {{ submitting ? 'Processing...' : decisionForm.action ? 'Confirm — ' + decisionForm.action : 'Select a decision above' }}
                            </button>
                        </div>
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
    decisionForm,
    decisionModalTitle,
    finalDecisions,
    formatDateTime,
    getStatusClass,
    openImageGallery,
    photoReviewDecisions,
    pickupDecisions,
    selectedRMA,
    showDecisionModal,
    submitDecision,
    submitting,
} = inject(reverseLogisticsPageKey)
</script>
