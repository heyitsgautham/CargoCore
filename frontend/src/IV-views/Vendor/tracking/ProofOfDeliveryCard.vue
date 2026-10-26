<template>
    <!-- PoD (if delivered) -->
    <div v-if="selected.pod && selected.pod.confirmed" class="glass-panel rounded-2xl p-5">
        <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
            <span class="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
                <span class="material-symbols-outlined text-green-500 text-[16px]">verified</span>
            </span>
            Proof of Delivery
        </h4>
        <div class="grid grid-cols-1 gap-4">
            <div class="space-y-2">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Timestamp</div>
                    <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.timestamp }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Location</div>
                    <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.location }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Received By</div>
                    <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.signedBy || 'Receiver' }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Recipient Signature</div>
                    <div v-if="selected.pod.signature && !podSignatureBroken" class="mt-2 h-20 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-slate-950/60 overflow-hidden flex items-center justify-center">
                        <img :src="selected.pod.signature" alt="Recipient signature" class="max-h-full max-w-full object-contain" @error="podSignatureBroken = true">
                    </div>
                    <div v-else class="text-xs text-gray-400">No signature was uploaded for this delivery.</div>
                </div>
                <div v-if="selected.pod.notes" class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Notes</div>
                    <div class="text-xs font-medium text-gray-900 dark:text-white whitespace-pre-line">{{ selected.pod.notes }}</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Delivery Rating</div>
                            <div v-if="selected.customerRating" class="flex items-center gap-1.5">
                                <span v-for="n in 5" :key="`pod-rating-${n}`" class="text-base"
                                    :class="n <= selected.customerRating ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
                                <span class="text-xs font-semibold text-gray-700 dark:text-gray-200 ml-1">{{ Number(selected.customerRating).toFixed(1) }}/5.0</span>
                            </div>
                            <div v-else class="text-xs text-gray-400">No delivery rating has been submitted yet.</div>
                        </div>
                        <button v-if="!selected.customerRating" @click="openVendorRatingModal(selected)"
                            class="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 text-[11px] font-bold transition-colors">
                            Rate Delivery
                        </button>
                    </div>
                    <div v-if="selected.customerFeedback" class="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-line">
                        {{ selected.customerFeedback }}
                    </div>
                </div>
                <div class="flex gap-2">
                    <button @click="openSlipWithData('proofOfDelivery', selected, currentUser())"
                        class="flex-1 flex items-center justify-center gap-1.5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-xs font-bold transition-colors">
                        <span class="material-symbols-outlined text-[14px]">verified</span> Download PoD
                    </button>
                    <button @click="openSlipWithData('finalTaxInvoice', selected, currentUser())"
                        class="flex-1 flex items-center justify-center gap-1.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors">
                        <span class="material-symbols-outlined text-[14px]">request_quote</span> Tax Invoice
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    currentUser,
    openSlipWithData,
    openVendorRatingModal,
    podSignatureBroken,
    selected,
} = inject(vendorTrackingPageKey)
</script>
