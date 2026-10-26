<template>
    <Teleport to="body">
        <BaseModal :isOpen="showPoD" @close="showPoD = false">
            <template #title>Proof of Delivery — {{ podOrder?.id }}</template>
            <div class="space-y-4">
                <div v-if="podLoading" class="py-10 text-center text-sm text-gray-400">
                    <span class="material-symbols-outlined text-[32px] block mb-2 animate-spin">progress_activity</span>
                    Loading proof of delivery...
                </div>

                <div v-else-if="podError" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {{ podError }}
                </div>

                <template v-else-if="podOrder">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Recipient</div>
                            <div class="text-sm font-bold text-white">{{ podOrder.pod?.signedBy || podOrder.customerName || 'Receiver' }}</div>
                            <div v-if="podOrder.customerPhone" class="text-[11px] text-gray-400 mt-1">{{ podOrder.customerPhone }}</div>
                        </div>
                        <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Delivered At</div>
                            <div class="text-sm font-bold text-white">{{ podOrder.pod?.time || 'Not recorded' }}</div>
                        </div>
                        <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Signature</div>
                            <div class="text-sm font-bold" :class="podOrder.pod?.signatureCaptured ? 'text-emerald-400' : 'text-gray-300'">
                                {{ podOrder.pod?.signatureCaptured ? 'Captured' : 'Not captured' }}
                            </div>
                        </div>
                        <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Photo Proof</div>
                            <div class="text-sm font-bold" :class="podPhotoCount > 0 ? 'text-emerald-400' : 'text-gray-300'">
                                {{ podPhotoCount > 0 ? `${podPhotoCount} photo${podPhotoCount === 1 ? '' : 's'} attached` : 'No photos attached' }}
                            </div>
                        </div>
                    </div>

                    <div class="rounded-xl bg-white/5 border border-white/10 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Delivery Address</div>
                        <div class="text-sm text-white">{{ podOrder.pod?.location || podOrder.deliveryAddr || 'Not available' }}</div>
                    </div>

                    <div v-if="podOrder.pod?.notes" class="rounded-xl bg-white/5 border border-white/10 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">POD Notes</div>
                        <div class="text-sm text-gray-200 whitespace-pre-line">{{ podOrder.pod.notes }}</div>
                    </div>

                    <div v-if="podOrder.pod?.signature" class="rounded-xl bg-white/5 border border-white/10 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Signature Preview</div>
                        <div class="h-28 rounded-lg bg-white overflow-hidden flex items-center justify-center">
                            <img :src="podOrder.pod.signature" alt="POD signature" class="h-full w-full object-contain" />
                        </div>
                    </div>

                    <div class="rounded-xl bg-white/5 border border-white/10 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-3">Photo Proof</div>
                        <div v-if="podPhotos.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div v-for="(photo, index) in podPhotos" :key="`${podOrder.id}-${index}`" class="overflow-hidden rounded-lg border border-white/10 bg-black/20">
                                <img :src="photo" :alt="`POD photo ${index + 1}`" class="h-40 w-full object-cover" />
                            </div>
                        </div>
                        <div v-else class="text-sm text-gray-400">No POD photos were uploaded for this order.</div>
                    </div>
                </template>
            </div>
            <template #footer>
                <button
                    v-if="podOrder && !podLoading"
                    @click="openSlipWithData('proofOfDelivery', podOrder, authStore.currentUser)"
                    class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5"
                >
                    <span class="material-symbols-outlined text-[15px]">verified</span>
                    Open POD Slip
                </button>
                <button @click="showPoD = false" class="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-bold hover:bg-white/15 transition-colors">Close</button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const {
    authStore,
    openSlipWithData,
    podError,
    podLoading,
    podOrder,
    podPhotoCount,
    podPhotos,
    showPoD,
} = inject(orderStatusPageKey)
</script>
