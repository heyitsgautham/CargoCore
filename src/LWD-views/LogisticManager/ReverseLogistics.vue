<template>
    <div class="min-h-[calc(100vh-8rem)] flex flex-col gap-4 pb-6 lg:gap-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">undo</span>
            Reverse Logistics & Returns
        </h2>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-orange-500/30 transition-colors">
                <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <span class="material-symbols-outlined text-6xl text-orange-500">pending_actions</span>
                </div>
                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Reported (New)</div>
                <div class="flex items-end gap-2 z-10 mt-1">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ reportedCount }}</div>
                    <span v-if="reportedCount > 0" class="text-xs font-bold text-orange-500 bg-orange-50 dark:bg-orange-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">
                        Requires Action
                    </span>
                </div>
            </div>

            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-blue-500/30 transition-colors">
                <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <span class="material-symbols-outlined text-6xl text-blue-500">photo_camera</span>
                </div>
                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Photo Review</div>
                <div class="flex items-end gap-2 z-10 mt-1">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ photoReviewCount }}</div>
                    <span class="text-xs font-bold text-blue-500 bg-blue-50 dark:bg-blue-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Flow 1</span>
                </div>
            </div>

            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-purple-500/30 transition-colors">
                <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <span class="material-symbols-outlined text-6xl text-purple-500">local_shipping</span>
                </div>
                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Pickup Inspection</div>
                <div class="flex items-end gap-2 z-10 mt-1">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ pickupInspectionCount }}</div>
                    <span class="text-xs font-bold text-purple-500 bg-purple-50 dark:bg-purple-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Flow 2</span>
                </div>
            </div>

            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-teal-500/30 transition-colors">
                <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <span class="material-symbols-outlined text-6xl text-teal-500">rate_review</span>
                </div>
                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Awaiting LM Decision</div>
                <div class="flex items-end gap-2 z-10 mt-1">
                    <div class="text-3xl font-bold text-gray-900 dark:text-white">{{ awaitingLMCount }}</div>
                    <span v-if="awaitingLMCount > 0" class="text-xs font-bold text-teal-500 bg-teal-50 dark:bg-teal-500/10 px-1.5 py-0.5 rounded flex items-center mb-1">Act Now</span>
                </div>
            </div>

            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex flex-col justify-between relative overflow-hidden group hover:border-green-500/30 transition-colors">
                <div class="absolute right-0 top-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <span class="material-symbols-outlined text-6xl text-green-500">currency_exchange</span>
                </div>
                <div class="text-xs text-gray-500 uppercase font-bold tracking-wider z-10">Total Refund Value</div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">₹{{ refundValue.toLocaleString() }}</div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="glass-panel min-h-[32rem] rounded-xl overflow-hidden flex flex-col border border-gray-200 dark:border-white/5 relative">
            <!-- Filter Bar -->
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5 flex-wrap gap-3">
                <div class="flex gap-1 bg-white dark:bg-black/20 p-1 rounded-lg border border-gray-200 dark:border-white/10 flex-wrap">
                    <button v-for="tab in tabs" :key="tab.id"
                        @click="activeStatus = tab.id"
                        class="px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1.5"
                        :class="activeStatus === tab.id ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'">
                        <span v-if="tab.dot" class="w-1.5 h-1.5 rounded-full" :class="tab.dot"></span>
                        {{ tab.label }}
                    </button>
                </div>
                <div class="relative">
                    <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input v-model="searchQuery" type="text" placeholder="Search Claim ID, Order ID..."
                        class="pl-9 pr-4 py-1.5 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 text-gray-700 dark:text-gray-200 w-64">
                </div>
            </div>

            <div class="overflow-x-auto overflow-y-visible custom-scrollbar bg-white dark:bg-gray-900">
                <table class="min-w-[1100px] w-full text-left text-sm border-separate border-spacing-0">
                    <thead class="bg-gray-50 dark:bg-card-dark sticky top-0 z-10 shadow-sm">
                        <tr class="text-gray-500 dark:text-gray-400 uppercase tracking-wider text-[10px]">
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Claim ID</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Order & Customer</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Flow Type</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Reason</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Photos</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10">Status</th>
                            <th class="py-3 px-4 font-medium border-b dark:border-white/10 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="rma in filteredList" :key="rma.id"
                            class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                            @click="openDetails(rma)">
                            <td class="py-3 px-4 font-mono text-primary font-bold text-xs">{{ rma.referenceCode || rma.id }}</td>
                            <td class="py-3 px-4">
                                <div class="font-medium text-gray-900 dark:text-white text-sm">{{ rma.customer }}</div>
                                <div class="text-xs text-gray-500 font-mono">{{ rma.orderId ? rma.orderId.slice(0, 8) + '...' : '—' }}</div>
                                <div v-if="rma.walletCredited" class="mt-1 inline-flex items-center gap-1 rounded-full border border-green-200 bg-green-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-green-700 dark:border-green-500/20 dark:bg-green-500/10 dark:text-green-400">
                                    <span class="material-symbols-outlined text-[12px]">wallet</span>
                                    Refunded
                                </div>
                                <div v-if="rma.isUrgent" class="mt-1 inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-400" :title="rma.urgentReason || 'Flagged urgent by support'">
                                    <span class="material-symbols-outlined text-[12px]">priority_high</span>
                                    Urgent
                                </div>
                            </td>
                            <td class="py-3 px-4">
                                <span v-if="rma.flow_type === 'photo_review'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:border-blue-500/20 dark:text-blue-400">
                                    <span class="material-symbols-outlined text-[12px]">photo_camera</span>
                                    Photo Review Only
                                </span>
                                <span v-else-if="rma.flow_type === 'pickup_inspection'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-500/10 dark:border-purple-500/20 dark:text-purple-400">
                                    <span class="material-symbols-outlined text-[12px]">local_shipping</span>
                                    Pickup Inspection Required
                                </span>
                                <span v-else class="text-gray-400 text-xs italic">—</span>
                            </td>
                            <td class="py-3 px-4 text-gray-600 dark:text-gray-300 text-xs max-w-[240px]">
                                <div class="truncate">{{ rma.reason }}</div>
                                <div v-if="rma.flow_type === 'pickup_inspection' && (rma.wmGenuineness !== undefined || rma.wmRecommendedSettlement || rma.wmRemarks)"
                                    class="mt-1 text-[10px] font-semibold text-teal-600 dark:text-teal-400">
                                    WM:
                                    {{ rma.wmGenuineness === undefined ? 'Inspection recorded' : (rma.wmGenuineness ? 'Genuine' : 'Not Genuine') }}
                                    <span v-if="rma.wmRecommendedSettlement">• {{ rma.wmRecommendedSettlement }}</span>
                                </div>
                            </td>
                            <td class="py-3 px-4">
                                <button v-if="rma.images && rma.images.length > 0"
                                    @click.stop="openImageGallery(rma)"
                                    class="text-blue-500 hover:text-blue-700 bg-blue-50 dark:bg-blue-500/10 p-1.5 rounded-lg transition-colors flex items-center justify-center relative"
                                    :title="rma.images.length + ' image(s)'">
                                    <span class="material-symbols-outlined text-[18px]">photo_library</span>
                                    <span class="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] w-3.5 h-3.5 flex items-center justify-center rounded-full font-bold">{{ rma.images.length }}</span>
                                </button>
                                <span v-else class="text-gray-400 opacity-50 flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[14px]">hide_image</span>
                                </span>
                            </td>
                            <td class="py-3 px-4">
                                <div class="flex flex-col items-start gap-1">
                                    <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border"
                                        :class="getStatusClass(rma.status)">
                                        {{ rma.status || 'Reported' }}
                                    </span>
                                    <span class="text-[10px] font-medium" :class="getStatusHintClass(rma.status)">
                                        {{ getStatusHint(rma.status, rma.flow_type) }}
                                    </span>
                                </div>
                            </td>
                            <td class="py-3 px-4 text-right">
                                <!-- Photo Review: Claims Reviewed → LM must decide -->
                                <button v-if="rma.flow_type === 'photo_review' && rma.status === 'Claims Reviewed'"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-teal-600 hover:bg-teal-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs shadow-sm transition-all flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">rate_review</span> Decide
                                </button>
                                <!-- Photo Review: Reported → LM forwards to WM for damage review -->
                                <button v-else-if="rma.flow_type === 'photo_review' && (!rma.status || rma.status === 'Reported')"
                                    @click.stop="forwardToWM(rma)"
                                    class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs shadow-sm transition-all flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">forward_to_inbox</span> Forward to WM
                                </button>
                                <!-- Photo Review: Under Review → WM is reviewing, LM waits -->
                                <span v-else-if="rma.flow_type === 'photo_review' && rma.status === 'Under Review'"
                                    class="text-blue-400 text-[10px] font-bold flex items-center gap-1 ml-auto italic">
                                    <span class="material-symbols-outlined text-[14px]">hourglass_empty</span> WM Reviewing
                                </span>
                                <!-- Pickup Inspection: Pickup Requested → LM approves or rejects pickup -->
                                <button v-else-if="rma.flow_type === 'pickup_inspection' && rma.status === 'Pickup Requested'"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-orange-600 hover:bg-orange-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs shadow-sm transition-all flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">local_shipping</span> Review Pickup
                                </button>
                                <!-- Pickup Inspection: Reported → same as Pickup Requested, LM reviews -->
                                <button v-else-if="rma.flow_type === 'pickup_inspection' && (!rma.status || rma.status === 'Reported')"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-orange-600 hover:bg-orange-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs shadow-sm transition-all flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">local_shipping</span> Review Pickup
                                </button>
                                <!-- Pickup Inspection: Physically Inspected → LM final decision -->
                                <button v-else-if="rma.flow_type === 'pickup_inspection' && rma.status === 'Physically Inspected'"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-teal-600 hover:bg-teal-700 text-white font-bold py-1.5 px-3 rounded-lg text-xs shadow-sm transition-all flex items-center gap-1 ml-auto">
                                    <span class="material-symbols-outlined text-[14px]">rate_review</span> Final Decision
                                </button>
                                <!-- In transit / at warehouse: waiting -->
                                <span v-else-if="['Pickup Approved', 'Pickup Scheduled', 'Collected', 'At Warehouse'].includes(rma.status)"
                                    class="text-purple-400 text-[10px] font-bold flex items-center gap-1 ml-auto italic">
                                    <span class="material-symbols-outlined text-[14px]">local_shipping</span> In Transit
                                </span>
                                <!-- Refunded / Closed -->
                                <button v-else-if="['Refunded', 'Closed'].includes(rma.status)"
                                    @click.stop="openDetailsReadOnly(rma)"
                                    class="text-green-400 hover:text-green-300 text-xs font-medium flex items-center gap-1 ml-auto transition-colors">
                                    <span class="material-symbols-outlined text-[16px]">check_circle</span> Closed
                                </button>
                                <!-- Fallback: view details -->
                                <button v-else
                                    @click.stop="openDetailsReadOnly(rma)"
                                    class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xs font-medium flex items-center gap-1 ml-auto transition-colors">
                                    <span class="material-symbols-outlined text-[16px]">visibility</span> Details
                                </button>
                            </td>
                        </tr>
                        <tr v-if="filteredList.length === 0">
                            <td colspan="7" class="py-12 text-center text-gray-500">
                                <div class="flex flex-col items-center gap-2 opacity-50">
                                    <span class="material-symbols-outlined text-4xl">inbox</span>
                                    <p class="text-sm">No claims found.</p>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- LM Decision Modal (Adaptive) -->
        <Teleport to="body">
            <div v-if="showDecisionModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div class="bg-slate-950/98 rounded-3xl w-full max-w-lg max-h-[90vh] shadow-2xl flex flex-col animate-scale-in border border-white/10 backdrop-blur-xl">
                    <!-- Header -->
                    <div class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/90 shrink-0 rounded-t-3xl">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <span v-if="selectedRMA?.flow_type === 'photo_review'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 border border-blue-500/30 text-blue-400">
                                    <span class="material-symbols-outlined text-[11px]">photo_camera</span>
                                    Photo Review Only
                                </span>
                                <span v-else-if="selectedRMA?.flow_type === 'pickup_inspection'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-purple-500/20 border border-purple-500/30 text-purple-400">
                                    <span class="material-symbols-outlined text-[11px]">local_shipping</span>
                                    Pickup Inspection Required
                                </span>
                            </div>
                            <h3 class="text-lg font-bold text-white">{{ decisionModalTitle }}</h3>
                            <p class="text-xs text-gray-500 font-mono">{{ selectedRMA?.referenceCode || selectedRMA?.id }} • {{ selectedRMA?.customer }}</p>
                        </div>
                        <button @click="showDecisionModal = false" class="text-gray-400 hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-6 space-y-5 overflow-y-auto custom-scrollbar">
                        <!-- Customer claim summary -->
                        <div class="flex items-start gap-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                            <span class="material-symbols-outlined text-blue-400 text-[20px] mt-0.5">person</span>
                            <div>
                                <div class="font-bold text-white text-sm">{{ selectedRMA?.customer }}</div>
                                <div class="text-xs text-gray-400 mt-0.5">{{ selectedRMA?.reason }}</div>
                            </div>
                            <button v-if="selectedRMA?.images?.length > 0"
                                @click="openImageGallery(selectedRMA)"
                                class="ml-auto text-blue-400 hover:text-blue-300 flex items-center gap-1 text-xs font-bold shrink-0">
                                <span class="material-symbols-outlined text-[16px]">photo_library</span>
                                {{ selectedRMA.images.length }} Photos
                            </button>
                        </div>

                        <!-- SECTION: Photo Review → Claims Reviewed by WM -->
                        <template v-if="selectedRMA?.flow_type === 'photo_review' && selectedRMA?.status === 'Claims Reviewed'">
                            <div class="rounded-xl border border-teal-500/20 bg-teal-500/10 p-4 space-y-3">
                                <div class="text-[10px] text-teal-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-[14px]">verified</span>
                                    Damage Review by Warehouse Team
                                </div>
                                <div class="grid grid-cols-2 gap-3">
                                    <div v-if="selectedRMA?.wmDamageSeverity">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Damage Severity</div>
                                        <div class="text-sm font-bold text-white">{{ selectedRMA.wmDamageSeverity }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmGenuineness !== undefined">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Claim Genuineness</div>
                                        <div class="text-sm font-bold" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                            {{ selectedRMA.wmGenuineness ? 'Looks Genuine' : 'Looks Suspicious' }}
                                        </div>
                                    </div>
                                    <div v-if="selectedRMA?.wmRecommendedSettlement" class="col-span-2">
                                        <div class="text-[10px] text-gray-500 mb-0.5">WM Recommended Settlement</div>
                                        <div class="text-sm font-bold text-yellow-400">{{ selectedRMA.wmRecommendedSettlement }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmRemarks" class="col-span-2">
                                        <div class="text-[10px] text-gray-500 mb-0.5">WM Remarks</div>
                                        <div class="text-xs text-gray-300 italic">"{{ selectedRMA.wmRemarks }}"</div>
                                    </div>
                                </div>
                            </div>

                            <!-- LM Decision -->
                            <div class="space-y-3">
                                <label class="block text-xs font-bold text-gray-300 uppercase">Your Decision</label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button v-for="opt in photoReviewDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="py-2.5 px-3 rounded-xl text-xs font-bold border transition-all text-left"
                                        :class="decisionForm.action === opt.value
                                            ? opt.activeClass
                                            : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'">
                                        {{ opt.label }}
                                    </button>
                                </div>

                                <!-- Refund amount if full/partial -->
                                <div v-if="['Full Refund', 'Partial Refund'].includes(decisionForm.action)" class="bg-slate-900/70 p-3 rounded-xl border border-white/10 space-y-2">
                                    <div class="flex justify-between items-center">
                                        <label class="text-xs font-bold text-gray-300 uppercase">Refund Amount (₹)</label>
                                        <span class="text-xs font-mono text-gray-500">Max: ₹{{ selectedRMA?.originalPrice || 0 }}</span>
                                    </div>
                                    <input v-model.number="decisionForm.amount" type="number"
                                        class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-1 focus:ring-primary font-mono"
                                        :placeholder="'₹' + (selectedRMA?.originalPrice || 0)">
                                    <div class="flex gap-1">
                                        <button v-for="pct in [25, 50, 75, 100]" :key="pct"
                                            @click="decisionForm.amount = Math.round((selectedRMA?.originalPrice || 0) * (pct/100))"
                                            class="flex-1 py-1 bg-slate-800 text-[10px] font-bold rounded border border-white/10 hover:bg-slate-700 transition-colors text-gray-200">
                                            {{ pct }}%
                                        </button>
                                    </div>
                                    <div class="text-xs text-gray-500">Refund goes to customer wallet or chosen refund method.</div>
                                </div>

                                <div>
                                    <label class="block text-xs font-bold text-gray-300 uppercase mb-1">Notes / Reason</label>
                                    <textarea v-model="decisionForm.notes" rows="2"
                                        placeholder="Add notes for this decision..."
                                        class="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-primary/50"></textarea>
                                </div>
                            </div>
                        </template>

                        <!-- SECTION: Pickup Inspection → LM approves/rejects pickup -->
                        <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested'].includes(selectedRMA?.status || 'Reported')">
                            <div class="rounded-xl border border-orange-500/20 bg-orange-500/10 p-3 text-xs text-orange-300 flex items-start gap-2">
                                <span class="material-symbols-outlined text-[16px] mt-0.5">warning</span>
                                <span>Customer has requested physical pickup for inspection. Review their claim and photos before approving.</span>
                            </div>

                            <div class="space-y-3">
                                <label class="block text-xs font-bold text-gray-300 uppercase">Pickup Decision</label>
                                <div class="grid grid-cols-1 gap-2">
                                    <button v-for="opt in pickupDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="py-2.5 px-3 rounded-xl text-xs font-bold border transition-all text-left"
                                        :class="decisionForm.action === opt.value
                                            ? opt.activeClass
                                            : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'">
                                        <div>{{ opt.label }}</div>
                                        <div class="text-[10px] font-normal opacity-70 mt-0.5">{{ opt.desc }}</div>
                                    </button>
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-gray-300 uppercase mb-1">Notes</label>
                                    <textarea v-model="decisionForm.notes" rows="2"
                                        placeholder="Add reason or instructions..."
                                        class="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-primary/50"></textarea>
                                </div>
                            </div>
                        </template>

                        <!-- SECTION: Pickup Inspection → Physically Inspected → LM final decision -->
                        <template v-else-if="selectedRMA?.flow_type === 'pickup_inspection' && selectedRMA?.status === 'Physically Inspected'">
                            <div class="rounded-xl border border-teal-500/20 bg-teal-500/10 p-4 space-y-3">
                                <div class="text-[10px] text-teal-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-[14px]">warehouse</span>
                                    Physical Inspection Report
                                </div>
                                <div class="grid grid-cols-2 gap-3">
                                    <div v-if="selectedRMA?.wmActualCondition">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Actual Condition</div>
                                        <div class="text-sm font-bold text-white">{{ selectedRMA.wmActualCondition }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmGenuineness !== undefined">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Claim Valid</div>
                                        <div class="text-sm font-bold" :class="selectedRMA.wmGenuineness ? 'text-green-400' : 'text-red-400'">
                                            {{ selectedRMA.wmGenuineness ? 'Genuine' : 'Not Genuine' }}
                                        </div>
                                    </div>
                                    <div v-if="selectedRMA?.wmRecommendedSettlement" class="col-span-2">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Recommended Outcome</div>
                                        <div class="text-sm font-bold text-yellow-400">{{ selectedRMA.wmRecommendedSettlement }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmDisposition">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Warehouse Disposition</div>
                                        <div class="text-sm font-bold text-cyan-400">{{ selectedRMA.wmDisposition }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmGraderName">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Inspected By</div>
                                        <div class="text-sm font-bold text-white">{{ selectedRMA.wmGraderName }}</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmRemarks" class="col-span-2">
                                        <div class="text-[10px] text-gray-500 mb-0.5">WM Remarks</div>
                                        <div class="text-xs text-gray-300 italic">"{{ selectedRMA.wmRemarks }}"</div>
                                    </div>
                                    <div v-if="selectedRMA?.wmGradedAt" class="col-span-2">
                                        <div class="text-[10px] text-gray-500 mb-0.5">Inspection Time</div>
                                        <div class="text-xs text-gray-300">{{ formatDateTime(selectedRMA.wmGradedAt) }}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Charge logic note -->
                            <div class="rounded-xl border border-yellow-500/20 bg-yellow-500/10 p-3 text-xs text-yellow-300 space-y-1">
                                <div class="font-bold uppercase tracking-wide text-[10px]">Charge Policy Reminder</div>
                                <div>If claim is <strong>genuine</strong>: waive pickup charge.</div>
                                <div>If claim is <strong>partially valid</strong>: deduct reasonable transport charge.</div>
                                <div>If claim is <strong>rejected</strong>: pickup or transport charge may apply.</div>
                            </div>

                            <!-- LM Final Decision -->
                            <div class="space-y-3">
                                <label class="block text-xs font-bold text-gray-300 uppercase">Final Decision</label>
                                <div class="grid grid-cols-1 gap-2">
                                    <button v-for="opt in finalDecisions" :key="opt.value"
                                        @click="decisionForm.action = opt.value"
                                        class="py-2.5 px-3 rounded-xl text-xs font-bold border transition-all text-left"
                                        :class="decisionForm.action === opt.value
                                            ? opt.activeClass
                                            : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'">
                                        {{ opt.label }}
                                    </button>
                                </div>

                                <div v-if="['Full Refund', 'Partial Refund'].includes(decisionForm.action)" class="bg-slate-900/70 p-3 rounded-xl border border-white/10 space-y-2">
                                    <div class="flex justify-between items-center">
                                        <label class="text-xs font-bold text-gray-300 uppercase">Refund Amount (₹)</label>
                                        <span class="text-xs font-mono text-gray-500">Max: ₹{{ selectedRMA?.originalPrice || 0 }}</span>
                                    </div>
                                    <input v-model.number="decisionForm.amount" type="number"
                                        class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-1 focus:ring-primary font-mono">
                                    <div class="flex gap-1">
                                        <button v-for="pct in [25, 50, 75, 100]" :key="pct"
                                            @click="decisionForm.amount = Math.round((selectedRMA?.originalPrice || 0) * (pct/100))"
                                            class="flex-1 py-1 bg-slate-800 text-[10px] font-bold rounded border border-white/10 hover:bg-slate-700 transition-colors text-gray-200">
                                            {{ pct }}%
                                        </button>
                                    </div>
                                </div>

                                <!-- Apply transport charge if rejecting -->
                                <div v-if="decisionForm.action === 'Reject Claim'" class="flex items-center gap-2 bg-slate-800 border border-white/10 rounded-xl px-3 py-2">
                                    <input type="checkbox" id="applyCharge" v-model="decisionForm.applyTransportCharge" class="rounded">
                                    <label for="applyCharge" class="text-xs text-gray-300 cursor-pointer">Apply pickup/transport charge to customer</label>
                                </div>

                                <div>
                                    <label class="block text-xs font-bold text-gray-300 uppercase mb-1">Notes</label>
                                    <textarea v-model="decisionForm.notes" rows="2"
                                        placeholder="Add notes for this decision..."
                                        class="w-full bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-400 outline-none focus:ring-2 focus:ring-primary/50"></textarea>
                                </div>
                            </div>
                        </template>
                    </div>

                    <!-- Footer Buttons -->
                    <div class="p-4 bg-slate-900/90 flex justify-end gap-2 border-t border-white/10 shrink-0 rounded-b-3xl">
                        <button @click="showDecisionModal = false"
                            class="px-4 py-2 text-gray-400 hover:bg-white/10 rounded-xl text-sm font-bold transition-colors">
                            Cancel
                        </button>
                        <button @click="submitDecision"
                            :disabled="!decisionForm.action || submitting"
                            class="px-6 py-2 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-bold rounded-xl shadow-sm transition-all flex items-center gap-2">
                            <span v-if="submitting" class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                            <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
                            {{ submitting ? 'Processing...' : 'Confirm Decision' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

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

        <!-- Image Gallery Modal -->
        <Teleport to="body">
            <div v-if="showImageModal" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[60] flex items-center justify-center p-4 animate-fade-in" @click.self="showImageModal = false">
                <div class="w-full max-w-4xl h-[80vh] flex flex-col relative">
                    <div class="absolute top-0 left-0 w-full p-4 flex justify-between items-start z-10 pointer-events-none">
                        <div class="pointer-events-auto">
                            <span class="bg-white/10 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-mono border border-white/20">
                                {{ selectedRMA?.referenceCode || selectedRMA?.id }}
                            </span>
                        </div>
                        <button @click="showImageModal = false" class="pointer-events-auto text-white/50 hover:text-white bg-black/50 hover:bg-black/80 rounded-full p-2 transition-all">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="flex-1 flex items-center justify-center relative overflow-hidden rounded-xl bg-black border border-white/10">
                        <img v-if="selectedImages.length > 0"
                             :src="selectedImages[activeImageIndex]"
                             class="max-h-full max-w-full object-contain transition-opacity duration-300"
                             :key="activeImageIndex"
                             alt="Claim proof">
                        <div v-else class="text-white/40 flex flex-col items-center gap-3 px-6 text-center">
                            <span class="material-symbols-outlined text-6xl">broken_image</span>
                            <template v-if="legacyFileNames.length > 0">
                                <p class="text-sm font-medium text-white/60">Image preview unavailable</p>
                                <p class="text-xs text-white/30 max-w-xs">This report was submitted before image upload was supported. The customer attached {{ legacyFileNames.length }} file(s) but only the filename(s) were saved.</p>
                                <div class="mt-1 space-y-1">
                                    <div v-for="name in legacyFileNames" :key="name" class="text-[11px] font-mono bg-white/10 px-3 py-1 rounded-full text-white/50">{{ name }}</div>
                                </div>
                                <p class="text-[11px] text-amber-400/70 mt-2">Ask the customer to resubmit with the new report form to view images.</p>
                            </template>
                            <template v-else>
                                <p class="text-sm">No images attached to this report.</p>
                            </template>
                        </div>
                        <button v-if="selectedImages.length > 1"
                                @click="activeImageIndex = (activeImageIndex - 1 + selectedImages.length) % selectedImages.length"
                                class="absolute left-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white text-white hover:text-black rounded-full p-4 hover:shadow-lg transition-all backdrop-blur-md">
                            <span class="material-symbols-outlined text-2xl">chevron_left</span>
                        </button>
                        <button v-if="selectedImages.length > 1"
                                @click="activeImageIndex = (activeImageIndex + 1) % selectedImages.length"
                                class="absolute right-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white text-white hover:text-black rounded-full p-4 hover:shadow-lg transition-all backdrop-blur-md">
                            <span class="material-symbols-outlined text-2xl">chevron_right</span>
                        </button>
                    </div>
                    <div v-if="selectedImages.length > 0" class="h-24 mt-4 flex gap-2 justify-center overflow-x-auto py-2">
                        <button v-for="(img, idx) in selectedImages" :key="idx"
                            @click="activeImageIndex = idx"
                            class="relative h-full aspect-video rounded-lg overflow-hidden border-2 transition-all"
                            :class="activeImageIndex === idx ? 'border-primary shadow-lg ring-2 ring-primary/30 scale-105' : 'border-transparent opacity-60 hover:opacity-100'">
                            <img :src="img" class="w-full h-full object-cover">
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'

const store = useLogisticStore()
const { filteredReturns } = storeToRefs(store)
let refreshTimer = null

async function refreshReturnsView() {
    await store.refresh()
}

function handleVisibilityRefresh() {
    if (document.visibilityState === 'visible') refreshReturnsView()
}

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(() => {
        if (document.visibilityState === 'visible') refreshReturnsView()
    }, 15000)
}

function stopAutoRefresh() {
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}

onMounted(() => {
    refreshReturnsView()
    startAutoRefresh()
    window.addEventListener('focus', refreshReturnsView)
    document.addEventListener('visibilitychange', handleVisibilityRefresh)
})

onUnmounted(() => {
    stopAutoRefresh()
    window.removeEventListener('focus', refreshReturnsView)
    document.removeEventListener('visibilitychange', handleVisibilityRefresh)
})

// View state
const searchQuery = ref('')
const activeStatus = ref('All')
const showDecisionModal = ref(false)
const showDetailsModal = ref(false)
const showImageModal = ref(false)
const selectedRMA = ref(null)
const selectedImages = ref([])
const legacyFileNames = ref([])
const activeImageIndex = ref(0)
const submitting = ref(false)

// Refund state
const refundIssuing = ref(false)
const refundIssued = ref(false)
const refundError = ref('')
const issuedRefundIds = new Set()

// Decision form
const decisionForm = ref({
    action: '',
    amount: 0,
    notes: '',
    applyTransportCharge: false
})

// Tabs
const tabs = [
    { id: 'All', label: 'All' },
    { id: 'Reported', label: 'Reported', dot: 'bg-yellow-500' },
    { id: 'Under Review', label: 'Under Review', dot: 'bg-blue-500' },
    { id: 'Claims Reviewed', label: 'Claims Reviewed', dot: 'bg-teal-500' },
    { id: 'Pickup Requested', label: 'Pickup Requested', dot: 'bg-orange-500' },
    { id: 'Pickup Approved', label: 'Pickup Approved', dot: 'bg-blue-500' },
    { id: 'Pickup Scheduled', label: 'Pickup Scheduled', dot: 'bg-blue-400' },
    { id: 'At Warehouse', label: 'At Warehouse', dot: 'bg-purple-500' },
    { id: 'Physically Inspected', label: 'Physically Inspected', dot: 'bg-teal-500' },
    { id: 'Approved', label: 'Approved', dot: 'bg-green-500' },
    { id: 'Rejected', label: 'Rejected', dot: 'bg-red-500' },
    { id: 'Refunded', label: 'Refunded', dot: 'bg-green-400' },
    { id: 'Closed', label: 'Closed', dot: 'bg-gray-400' },
]

// Decision options
const photoReviewDecisions = [
    { value: 'Full Refund', label: 'Full Refund', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Partial Refund', label: 'Partial Refund', activeClass: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300' },
    { value: 'Reject Claim', label: 'Reject Claim', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
    { value: 'Need More Evidence', label: 'Keep Pending / Need More Evidence', activeClass: 'bg-blue-500/20 border-blue-500/40 text-blue-300' },
]

const pickupDecisions = [
    { value: 'Approve Pickup', label: 'Approve Pickup', desc: 'Forward to dispatcher to assign driver and vehicle.', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Reject Pickup Request', label: 'Reject Pickup Request', desc: 'Decline the pickup — notify customer with reason.', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
    { value: 'Ask for More Evidence', label: 'Ask for More Evidence', desc: 'Request additional photos or information before deciding.', activeClass: 'bg-blue-500/20 border-blue-500/40 text-blue-300' },
]

const finalDecisions = [
    { value: 'Full Refund', label: 'Full Refund — Claim valid, waive charges', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Partial Refund', label: 'Partial Refund — Deduct reasonable transport/handling charge', activeClass: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300' },
    { value: 'Reject Claim', label: 'Reject Claim — Pickup/transport charge may apply', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
]

// Stats
const reportedCount = computed(() =>
    filteredReturns.value.filter(r => !r.status || r.status === 'Reported').length
)

const photoReviewCount = computed(() =>
    filteredReturns.value.filter(r => r.flow_type === 'photo_review').length
)

const pickupInspectionCount = computed(() =>
    filteredReturns.value.filter(r => r.flow_type === 'pickup_inspection').length
)

const awaitingLMCount = computed(() =>
    filteredReturns.value.filter(r =>
        r.status === 'Claims Reviewed' ||
        r.status === 'Physically Inspected' ||
        (r.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested'].includes(r.status || 'Reported'))
    ).length
)

const refundValue = computed(() =>
    filteredReturns.value
        .filter(r => ['Approved', 'Partially Approved', 'Refunded'].includes(r.status))
        .reduce((sum, r) => sum + (r.refundAmount || 0), 0)
)

// Filtered list
const statusOrder = [
    'Reported', 'Under Review', 'Claims Reviewed',
    'Pickup Requested', 'Pickup Approved', 'Pickup Rejected', 'Pickup Scheduled',
    'Collected', 'At Warehouse', 'Physically Inspected',
    'Approved', 'Partially Approved', 'Rejected', 'Refunded', 'Closed'
]

const filteredList = computed(() => {
    let list = filteredReturns.value

    if (activeStatus.value !== 'All') {
        if (activeStatus.value === 'Reported') {
            list = list.filter(r => !r.status || r.status === 'Reported')
        } else {
            list = list.filter(r => r.status === activeStatus.value)
        }
    }

    list = [...list].sort((a, b) => {
        const ai = statusOrder.indexOf(a.status || 'Reported')
        const bi = statusOrder.indexOf(b.status || 'Reported')
        return ai - bi
    })

    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(r =>
            String(r.id || '').toLowerCase().includes(q) ||
            String(r.orderId || '').toLowerCase().includes(q) ||
            String(r.customer || '').toLowerCase().includes(q)
        )
    }

    return list
})

// Decision modal title
const decisionModalTitle = computed(() => {
    if (!selectedRMA.value) return 'Review Claim'
    if (selectedRMA.value.flow_type === 'photo_review') return 'Damage Review Decision'
    if (['Reported', 'Pickup Requested'].includes(selectedRMA.value.status || 'Reported')) return 'Pickup Approval Decision'
    return 'Final Inspection Decision'
})

// Status helpers
const getStatusClass = (status) => {
    switch (status) {
        case 'Reported': return 'bg-yellow-50 border-yellow-200 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20'
        case 'Under Review': return 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
        case 'Claims Reviewed': return 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
        case 'Pickup Requested': return 'bg-orange-50 border-orange-200 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/20'
        case 'Pickup Approved': return 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
        case 'Pickup Rejected': return 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
        case 'Pickup Scheduled': return 'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/20'
        case 'Collected': return 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400 dark:border-indigo-500/20'
        case 'At Warehouse': return 'bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20'
        case 'Physically Inspected': return 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
        case 'Approved': return 'bg-green-50 border-green-200 text-green-700 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20'
        case 'Partially Approved': return 'bg-lime-50 border-lime-200 text-lime-700 dark:bg-lime-500/10 dark:text-lime-400 dark:border-lime-500/20'
        case 'Rejected': return 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
        case 'Refunded': return 'bg-green-50 border-green-300 text-green-700 dark:bg-green-500/10 dark:text-green-300 dark:border-green-500/30'
        case 'Closed': return 'bg-gray-50 border-gray-200 text-gray-600 dark:bg-gray-500/10 dark:text-gray-400 dark:border-gray-500/20'
        default: return 'bg-yellow-50 border-yellow-200 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20'
    }
}

const getStatusHint = (status, flowType) => {
    switch (status) {
        case 'Reported': return flowType === 'photo_review' ? 'Forwarded to WM for review' : 'Awaiting LM pickup decision'
        case 'Under Review': return 'WM is reviewing claim'
        case 'Claims Reviewed': return 'LM decision needed'
        case 'Pickup Requested': return 'LM to approve/reject'
        case 'Pickup Approved': return 'Awaiting dispatcher'
        case 'Pickup Rejected': return 'Pickup declined'
        case 'Pickup Scheduled': return 'Driver en route'
        case 'Collected': return 'Parcel picked up'
        case 'At Warehouse': return 'Awaiting WM inspection'
        case 'Physically Inspected': return 'LM final decision needed'
        case 'Approved': return 'Refund approved'
        case 'Partially Approved': return 'Partial refund approved'
        case 'Rejected': return 'Claim rejected'
        case 'Refunded': return 'Refund issued'
        case 'Closed': return 'Case closed'
        default: return 'Awaiting review'
    }
}

const getStatusHintClass = (status) => {
    switch (status) {
        case 'Claims Reviewed':
        case 'Physically Inspected': return 'text-teal-600 dark:text-teal-400'
        case 'Pickup Requested': return 'text-orange-600 dark:text-orange-400'
        case 'Pickup Approved':
        case 'Pickup Scheduled': return 'text-blue-600 dark:text-blue-400'
        case 'Pickup Rejected':
        case 'Rejected': return 'text-red-600 dark:text-red-400'
        case 'At Warehouse':
        case 'Collected': return 'text-purple-600 dark:text-purple-400'
        case 'Approved': return 'text-green-600 dark:text-green-400'
        case 'Partially Approved': return 'text-lime-600 dark:text-lime-400'
        case 'Refunded': return 'text-green-500 dark:text-green-300'
        case 'Closed': return 'text-gray-400'
        default: return 'text-yellow-600 dark:text-yellow-400'
    }
}

const formatDateTime = (value) => {
    if (!value) return '—'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return parsed.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

// Actions
const openImageGallery = (rma) => {
    selectedRMA.value = rma
    const allImages = rma.images || []
    selectedImages.value = allImages.filter(img => img && (img.startsWith('http') || img.startsWith('/') || img.startsWith('data:')))
    legacyFileNames.value = allImages.filter(img => img && !img.startsWith('http') && !img.startsWith('/') && !img.startsWith('data:'))
    activeImageIndex.value = 0
    showImageModal.value = true
}

const forwardToWM = async (rma) => {
    await store.updateReturnStatus(rma.id, 'Under Review', { notes: 'Forwarded to WM for damage review' })
}

const openLMDecisionModal = (rma) => {
    selectedRMA.value = rma
    decisionForm.value = { action: '', amount: rma.originalPrice || 0, notes: '', applyTransportCharge: false }
    showDecisionModal.value = true
}

const openDetails = (rma) => {
    selectedRMA.value = rma
    const needsDecision =
        (rma.flow_type === 'photo_review' && rma.status === 'Claims Reviewed') ||
        (rma.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested', 'Physically Inspected'].includes(rma.status || 'Reported'))
    if (needsDecision) {
        openLMDecisionModal(rma)
    } else {
        openDetailsReadOnly(rma)
    }
}

const openDetailsReadOnly = (rma) => {
    selectedRMA.value = rma
    refundIssued.value = Boolean(rma.walletCredited || issuedRefundIds.has(rma.id))
    refundIssuing.value = false
    refundError.value = ''
    showDetailsModal.value = true
}

const submitDecision = async () => {
    if (!selectedRMA.value || !decisionForm.value.action || submitting.value) return
    submitting.value = true

    try {
        const rma = selectedRMA.value
        const action = decisionForm.value.action

        // Map action to new status
        let newStatus
        if (action === 'Full Refund') newStatus = 'Approved'
        else if (action === 'Partial Refund') newStatus = 'Partially Approved'
        else if (action === 'Reject Claim') newStatus = 'Rejected'
        else if (action === 'Need More Evidence') newStatus = 'Under Review'
        else if (action === 'Approve Pickup') newStatus = 'Pickup Approved'
        else if (action === 'Reject Pickup Request') newStatus = 'Pickup Rejected'
        else if (action === 'Ask for More Evidence') newStatus = 'Under Review'
        else newStatus = action

        await store.updateReturnStatus(rma.id, newStatus, {
            refundAmount: ['Full Refund', 'Partial Refund'].includes(action) ? decisionForm.value.amount : 0,
            notes: decisionForm.value.notes,
            applyTransportCharge: decisionForm.value.applyTransportCharge || false,
        })

        // Add refund transaction if applicable
        if (['Full Refund', 'Partial Refund'].includes(action) && decisionForm.value.amount > 0) {
            await store.addTransaction({
                id: Date.now(),
                date: new Date().toISOString().split('T')[0],
                desc: `Refund for ${rma.id}`,
                amount: -decisionForm.value.amount,
                type: 'Expense',
                status: 'Completed',
                hubId: store.activeWarehouse
            })
        }

        // Auto-schedule driver pickup when LM approves pickup
        if (action === 'Approve Pickup') {
            try {
                await store.scheduleReturnPickup(rma.id)
            } catch (e) {
                console.warn('Could not auto-schedule pickup:', e?.message)
            }
        }

        showDecisionModal.value = false
    } finally {
        submitting.value = false
    }
}

const handleIssueRefund = async () => {
    if (!selectedRMA.value || refundIssuing.value || refundIssued.value) return
    refundIssuing.value = true
    refundError.value = ''
    try {
        const result = await store.issueReturnRefund(selectedRMA.value.id)
        issuedRefundIds.add(selectedRMA.value.id)
        refundIssued.value = true
        selectedRMA.value = { ...selectedRMA.value, status: 'Refunded', walletCredited: true }
        if (result && !result.credited) {
            refundError.value = 'Note: refund was already issued previously.'
        }
    } catch (e) {
        refundError.value = e?.message || 'Failed to issue refund. Please try again.'
    } finally {
        refundIssuing.value = false
    }
}
</script>
