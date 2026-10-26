<template>
    <!-- Claims List -->
    <div class="flex flex-col gap-5">

        <!-- Grouped view when showing All and no search -->
        <template v-if="activeStatus === 'All' && !searchQuery">

            <!-- Group: Action Required -->
            <div v-if="actionRequiredList.length > 0" class="flex flex-col gap-2">
                <div class="flex items-center gap-2 px-1">
                    <span class="relative flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                    </span>
                    <span class="text-[11px] font-bold uppercase tracking-widest text-orange-500">Action Required</span>
                    <span class="bg-orange-500/20 text-orange-500 text-[10px] font-bold px-1.5 py-0.5 rounded-full">{{ actionRequiredList.length }}</span>
                    <div class="flex-1 h-px bg-orange-500/20"></div>
                </div>
                <div v-for="rma in actionRequiredList" :key="rma.id">
                    <div class="glass-panel rounded-xl border-l-4 border-orange-500 border border-orange-500/20 hover:border-orange-500/40 transition-all cursor-pointer group"
                        @click="openDetails(rma)">
                        <div class="flex items-center gap-4 p-4">
                            <!-- Claim ID + Order -->
                            <div class="w-40 shrink-0">
                                <div class="font-mono font-bold text-primary text-sm">{{ rma.referenceCode || rma.id }}</div>
                                <div class="text-[10px] text-gray-500 font-mono mt-0.5">{{ rma.orderId ? rma.orderId.slice(0, 8) + '...' : '—' }}</div>
                                <div class="flex flex-wrap gap-1 mt-1.5">
                                    <span v-if="rma.isUrgent" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                                        <span class="material-symbols-outlined text-[10px]">priority_high</span> Urgent
                                    </span>
                                    <span v-if="rma.images?.length > 0"
                                        @click.stop="openImageGallery(rma)"
                                        class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 cursor-pointer">
                                        <span class="material-symbols-outlined text-[10px]">photo_library</span> {{ rma.images.length }}
                                    </span>
                                </div>
                            </div>
                            <!-- Customer + Reason -->
                            <div class="flex-1 min-w-0">
                                <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ rma.customer }}</div>
                                <div class="text-xs text-gray-500 italic mt-0.5 truncate">"{{ rma.reason }}"</div>
                                <div v-if="(rma.wmGenuineness !== undefined && rma.wmGenuineness !== null) || rma.wmRecommendedSettlement"
                                    class="mt-1.5 flex items-center gap-1.5 text-[10px] text-teal-400 font-semibold">
                                    <span class="material-symbols-outlined text-[12px]">verified</span>
                                    WM: {{ rma.wmGenuineness ? 'Genuine' : 'Suspicious' }}
                                    <span v-if="rma.wmRecommendedSettlement" class="text-gray-500">·</span>
                                    <span v-if="rma.wmRecommendedSettlement">{{ rma.wmRecommendedSettlement }}</span>
                                </div>
                            </div>
                            <!-- Flow + Status -->
                            <div class="w-52 shrink-0 flex flex-col gap-1.5">
                                <span v-if="rma.flow_type === 'photo_review'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-blue-500/10 border-blue-500/20 text-blue-400 w-fit">
                                    <span class="material-symbols-outlined text-[10px]">photo_camera</span> Photo Review
                                </span>
                                <span v-else-if="rma.flow_type === 'pickup_inspection'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-purple-500/10 border-purple-500/20 text-purple-400 w-fit">
                                    <span class="material-symbols-outlined text-[10px]">local_shipping</span> Pickup Inspection
                                </span>
                                <div class="flex items-center gap-1.5">
                                    <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border w-fit" :class="getStatusClass(rma.status)">
                                        {{ rma.status || 'Reported' }}
                                    </span>
                                </div>
                                <div class="text-[10px] font-medium" :class="getStatusHintClass(rma.status)">{{ getStatusHint(rma.status, rma.flow_type) }}</div>
                            </div>
                            <!-- Action -->
                            <div class="w-40 shrink-0 flex justify-end">
                                <button v-if="rma.flow_type === 'photo_review' && rma.status === 'Claims Reviewed'"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-4 rounded-lg text-xs shadow transition-all flex items-center gap-1.5 w-full justify-center">
                                    <span class="material-symbols-outlined text-[14px]">rate_review</span> Decide Now
                                </button>
                                <button v-else-if="rma.flow_type === 'photo_review' && (!rma.status || rma.status === 'Reported')"
                                    @click.stop="forwardToWM(rma)"
                                    class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg text-xs shadow transition-all flex items-center gap-1.5 w-full justify-center">
                                    <span class="material-symbols-outlined text-[14px]">forward_to_inbox</span> Forward to WM
                                </button>
                                <button v-else-if="rma.flow_type === 'pickup_inspection' && rma.status === 'Physically Inspected'"
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-4 rounded-lg text-xs shadow transition-all flex items-center gap-1.5 w-full justify-center">
                                    <span class="material-symbols-outlined text-[14px]">rate_review</span> Final Decision
                                </button>
                                <button v-else
                                    @click.stop="openLMDecisionModal(rma)"
                                    class="bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-4 rounded-lg text-xs shadow transition-all flex items-center gap-1.5 w-full justify-center">
                                    <span class="material-symbols-outlined text-[14px]">local_shipping</span> Review Pickup
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Group: In Progress -->
            <div v-if="inProgressList.length > 0" class="flex flex-col gap-2">
                <div class="flex items-center gap-2 px-1">
                    <span class="w-2 h-2 rounded-full bg-blue-400"></span>
                    <span class="text-[11px] font-bold uppercase tracking-widest text-blue-400">In Progress</span>
                    <span class="bg-blue-500/20 text-blue-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">{{ inProgressList.length }}</span>
                    <div class="flex-1 h-px bg-blue-500/20"></div>
                </div>
                <div v-for="rma in inProgressList" :key="rma.id">
                    <div class="glass-panel rounded-xl border-l-4 border-blue-500/60 border border-blue-500/10 hover:border-blue-500/30 transition-all cursor-pointer opacity-80 hover:opacity-100"
                        @click="openDetails(rma)">
                        <div class="flex items-center gap-4 p-4">
                            <div class="w-40 shrink-0">
                                <div class="font-mono font-bold text-primary text-sm">{{ rma.referenceCode || rma.id }}</div>
                                <div class="text-[10px] text-gray-500 font-mono mt-0.5">{{ rma.orderId ? rma.orderId.slice(0, 8) + '...' : '—' }}</div>
                                <span v-if="rma.images?.length > 0"
                                    @click.stop="openImageGallery(rma)"
                                    class="mt-1.5 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 cursor-pointer">
                                    <span class="material-symbols-outlined text-[10px]">photo_library</span> {{ rma.images.length }}
                                </span>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ rma.customer }}</div>
                                <div class="text-xs text-gray-500 italic mt-0.5 truncate">"{{ rma.reason }}"</div>
                            </div>
                            <div class="w-52 shrink-0 flex flex-col gap-1.5">
                                <span v-if="rma.flow_type === 'photo_review'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-blue-500/10 border-blue-500/20 text-blue-400 w-fit">
                                    <span class="material-symbols-outlined text-[10px]">photo_camera</span> Photo Review
                                </span>
                                <span v-else-if="rma.flow_type === 'pickup_inspection'"
                                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-purple-500/10 border-purple-500/20 text-purple-400 w-fit">
                                    <span class="material-symbols-outlined text-[10px]">local_shipping</span> Pickup Inspection
                                </span>
                                <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border w-fit" :class="getStatusClass(rma.status)">
                                    {{ rma.status || 'Reported' }}
                                </span>
                                <div class="text-[10px] font-medium" :class="getStatusHintClass(rma.status)">{{ getStatusHint(rma.status, rma.flow_type) }}</div>
                            </div>
                            <div class="w-40 shrink-0 flex justify-end">
                                <span v-if="rma.flow_type === 'photo_review' && rma.status === 'Under Review'"
                                    class="text-blue-400 text-[11px] font-bold flex items-center gap-1 italic">
                                    <span class="material-symbols-outlined text-[16px] animate-spin" style="animation-duration:3s">hourglass_empty</span> WM Reviewing
                                </span>
                                <span v-else class="text-purple-400 text-[11px] font-bold flex items-center gap-1 italic">
                                    <span class="material-symbols-outlined text-[16px]">local_shipping</span> In Transit
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Group: Resolved (collapsible) -->
            <div v-if="resolvedList.length > 0" class="flex flex-col gap-2">
                <button class="flex items-center gap-2 px-1 text-left w-full group" @click="showResolved = !showResolved">
                    <span class="w-2 h-2 rounded-full bg-gray-400"></span>
                    <span class="text-[11px] font-bold uppercase tracking-widest text-gray-400">Resolved</span>
                    <span class="bg-gray-500/20 text-gray-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">{{ resolvedList.length }}</span>
                    <div class="flex-1 h-px bg-gray-500/20"></div>
                    <span class="material-symbols-outlined text-gray-400 text-[16px] transition-transform" :class="showResolved ? 'rotate-180' : ''">expand_more</span>
                </button>
                <template v-if="showResolved">
                    <div v-for="rma in resolvedList" :key="rma.id">
                        <div class="glass-panel rounded-xl border-l-4 border-gray-400/30 border border-gray-200/30 dark:border-white/5 hover:border-gray-400/50 transition-all cursor-pointer opacity-60 hover:opacity-90"
                            @click="openDetailsReadOnly(rma)">
                            <div class="flex items-center gap-4 p-4">
                                <div class="w-40 shrink-0">
                                    <div class="font-mono font-bold text-gray-500 text-sm">{{ rma.referenceCode || rma.id }}</div>
                                    <div class="text-[10px] text-gray-500 font-mono mt-0.5">{{ rma.orderId ? rma.orderId.slice(0, 8) + '...' : '—' }}</div>
                                    <span v-if="rma.walletCredited" class="mt-1.5 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-green-500/10 text-green-400 border border-green-500/20">
                                        <span class="material-symbols-outlined text-[10px]">wallet</span> Refunded
                                    </span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="font-semibold text-gray-600 dark:text-gray-300 text-sm">{{ rma.customer }}</div>
                                    <div class="text-xs text-gray-500 italic mt-0.5 truncate">"{{ rma.reason }}"</div>
                                </div>
                                <div class="w-52 shrink-0 flex flex-col gap-1.5">
                                    <span v-if="rma.flow_type === 'photo_review'"
                                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-gray-500/10 border-gray-500/20 text-gray-400 w-fit">
                                        <span class="material-symbols-outlined text-[10px]">photo_camera</span> Photo Review
                                    </span>
                                    <span v-else-if="rma.flow_type === 'pickup_inspection'"
                                        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-gray-500/10 border-gray-500/20 text-gray-400 w-fit">
                                        <span class="material-symbols-outlined text-[10px]">local_shipping</span> Pickup Inspection
                                    </span>
                                    <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border w-fit" :class="getStatusClass(rma.status)">
                                        {{ rma.status }}
                                    </span>
                                </div>
                                <div class="w-40 shrink-0 flex justify-end">
                                    <span class="text-gray-400 text-[11px] font-medium flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[16px]">check_circle</span> Closed
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>

            <!-- Empty state -->
            <div v-if="actionRequiredList.length === 0 && inProgressList.length === 0 && resolvedList.length === 0"
                class="glass-panel rounded-xl p-12 flex flex-col items-center gap-3 text-gray-500 opacity-50">
                <span class="material-symbols-outlined text-5xl">inbox</span>
                <p class="text-sm">No return claims found.</p>
            </div>
        </template>

        <!-- Flat filtered list (specific status tab or search active) -->
        <template v-else>
            <div v-if="filteredList.length === 0"
                class="glass-panel rounded-xl p-12 flex flex-col items-center gap-3 text-gray-500 opacity-50">
                <span class="material-symbols-outlined text-5xl">search_off</span>
                <p class="text-sm">No claims match your filter.</p>
            </div>
            <div v-for="rma in filteredList" :key="rma.id">
                <div class="glass-panel rounded-xl border-l-4 transition-all cursor-pointer hover:shadow-md"
                    :class="[
                        getRowAccentClass(rma),
                        'border border-gray-200 dark:border-white/5 hover:border-gray-300 dark:hover:border-white/10'
                    ]"
                    @click="openDetails(rma)">
                    <div class="flex items-center gap-4 p-4">
                        <div class="w-40 shrink-0">
                            <div class="font-mono font-bold text-primary text-sm">{{ rma.referenceCode || rma.id }}</div>
                            <div class="text-[10px] text-gray-500 font-mono mt-0.5">{{ rma.orderId ? rma.orderId.slice(0, 8) + '...' : '—' }}</div>
                            <div class="flex flex-wrap gap-1 mt-1.5">
                                <span v-if="rma.isUrgent" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                                    <span class="material-symbols-outlined text-[10px]">priority_high</span> Urgent
                                </span>
                                <span v-if="rma.walletCredited" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-green-500/10 text-green-400 border border-green-500/20">
                                    <span class="material-symbols-outlined text-[10px]">wallet</span> Refunded
                                </span>
                                <span v-if="rma.images?.length > 0"
                                    @click.stop="openImageGallery(rma)"
                                    class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 cursor-pointer">
                                    <span class="material-symbols-outlined text-[10px]">photo_library</span> {{ rma.images.length }}
                                </span>
                            </div>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="font-semibold text-gray-900 dark:text-white text-sm">{{ rma.customer }}</div>
                            <div class="text-xs text-gray-500 italic mt-0.5 truncate">"{{ rma.reason }}"</div>
                            <div v-if="(rma.wmGenuineness !== undefined && rma.wmGenuineness !== null) || rma.wmRecommendedSettlement"
                                class="mt-1.5 flex items-center gap-1.5 text-[10px] text-teal-400 font-semibold">
                                <span class="material-symbols-outlined text-[12px]">verified</span>
                                WM: {{ rma.wmGenuineness ? 'Genuine' : 'Suspicious' }}
                                <span v-if="rma.wmRecommendedSettlement" class="text-gray-500">·</span>
                                <span v-if="rma.wmRecommendedSettlement">{{ rma.wmRecommendedSettlement }}</span>
                            </div>
                        </div>
                        <div class="w-52 shrink-0 flex flex-col gap-1.5">
                            <span v-if="rma.flow_type === 'photo_review'"
                                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-blue-500/10 border-blue-500/20 text-blue-400 w-fit">
                                <span class="material-symbols-outlined text-[10px]">photo_camera</span> Photo Review
                            </span>
                            <span v-else-if="rma.flow_type === 'pickup_inspection'"
                                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border bg-purple-500/10 border-purple-500/20 text-purple-400 w-fit">
                                <span class="material-symbols-outlined text-[10px]">local_shipping</span> Pickup Inspection
                            </span>
                            <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border w-fit" :class="getStatusClass(rma.status)">
                                {{ rma.status || 'Reported' }}
                            </span>
                            <div class="text-[10px] font-medium" :class="getStatusHintClass(rma.status)">{{ getStatusHint(rma.status, rma.flow_type) }}</div>
                        </div>
                        <div class="w-40 shrink-0 flex justify-end">
                            <button v-if="rma.flow_type === 'photo_review' && rma.status === 'Claims Reviewed'"
                                @click.stop="openLMDecisionModal(rma)"
                                class="bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition-all flex items-center gap-1 w-full justify-center">
                                <span class="material-symbols-outlined text-[14px]">rate_review</span> Decide Now
                            </button>
                            <button v-else-if="rma.flow_type === 'photo_review' && (!rma.status || rma.status === 'Reported')"
                                @click.stop="forwardToWM(rma)"
                                class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition-all flex items-center gap-1 w-full justify-center">
                                <span class="material-symbols-outlined text-[14px]">forward_to_inbox</span> Forward to WM
                            </button>
                            <span v-else-if="rma.flow_type === 'photo_review' && rma.status === 'Under Review'"
                                class="text-blue-400 text-[11px] font-bold flex items-center gap-1 italic">
                                <span class="material-symbols-outlined text-[16px] animate-spin" style="animation-duration:3s">hourglass_empty</span> WM Reviewing
                            </span>
                            <button v-else-if="rma.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested'].includes(rma.status || 'Reported')"
                                @click.stop="openLMDecisionModal(rma)"
                                class="bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition-all flex items-center gap-1 w-full justify-center">
                                <span class="material-symbols-outlined text-[14px]">local_shipping</span> Review Pickup
                            </button>
                            <button v-else-if="rma.flow_type === 'pickup_inspection' && rma.status === 'Physically Inspected'"
                                @click.stop="openLMDecisionModal(rma)"
                                class="bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-3 rounded-lg text-xs shadow transition-all flex items-center gap-1 w-full justify-center">
                                <span class="material-symbols-outlined text-[14px]">rate_review</span> Final Decision
                            </button>
                            <span v-else-if="['Pickup Approved', 'Pickup Scheduled', 'Collected', 'At Warehouse'].includes(rma.status)"
                                class="text-purple-400 text-[11px] font-bold flex items-center gap-1 italic">
                                <span class="material-symbols-outlined text-[16px]">local_shipping</span> In Transit
                            </span>
                            <button v-else-if="['Refunded', 'Closed'].includes(rma.status)"
                                @click.stop="openDetailsReadOnly(rma)"
                                class="text-green-400 hover:text-green-300 text-[11px] font-medium flex items-center gap-1 transition-colors">
                                <span class="material-symbols-outlined text-[16px]">check_circle</span> Closed
                            </button>
                            <button v-else
                                @click.stop="openDetailsReadOnly(rma)"
                                class="text-gray-400 hover:text-gray-200 text-[11px] font-medium flex items-center gap-1 transition-colors">
                                <span class="material-symbols-outlined text-[16px]">visibility</span> Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    actionRequiredList,
    activeStatus,
    filteredList,
    forwardToWM,
    getRowAccentClass,
    getStatusClass,
    getStatusHint,
    getStatusHintClass,
    inProgressList,
    openDetails,
    openDetailsReadOnly,
    openImageGallery,
    openLMDecisionModal,
    resolvedList,
    searchQuery,
    showResolved,
} = inject(reverseLogisticsPageKey)
</script>
