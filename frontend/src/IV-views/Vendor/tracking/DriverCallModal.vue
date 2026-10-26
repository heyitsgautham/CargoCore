<template>
    <!-- Driver Call Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showCallModal" @close="showCallModal = false">
            <template #title>Contact Driver</template>
            <div class="flex flex-col items-center justify-center p-6 space-y-4">
                <div class="w-20 h-20 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 shadow-inner">
                    <span class="material-symbols-outlined text-4xl">person</span>
                </div>
                <div class="text-center">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ selected?.driver || 'Driver Name' }}</h3>
                    <p class="text-sm text-gray-500">{{ selected?.vehicle || 'Vehicle Number' }}</p>
                </div>
                <div class="w-full bg-gray-50 dark:bg-black/20 rounded-lg border border-gray-200 dark:border-white/10 p-4 text-center mt-4">
                    <div class="text-xs text-gray-500 uppercase font-bold mb-1">Direct Line</div>
                    <div class="text-2xl font-bold text-gray-900 dark:text-white tracking-wider flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-green-500">phone_iphone</span>
                        {{ selected?.driverPhone || '+1 (555) 000-0000' }}
                    </div>
                </div>
            </div>
            <template #footer>
                <button @click="showCallModal = false" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                <a v-if="canCallDriver" :href="`tel:${selected?.driverPhone?.replace(/\s+/g, '')}`"
                    class="px-8 py-2 bg-green-500 text-white rounded-lg text-sm font-bold hover:bg-green-600 transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">call</span> Call Now
                </a>
                <span v-else class="px-8 py-2 bg-gray-200 dark:bg-white/10 text-gray-500 rounded-lg text-sm font-bold flex items-center gap-2 cursor-not-allowed">
                    <span class="material-symbols-outlined text-[18px]">call</span> No Phone
                </span>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { canCallDriver, selected, showCallModal } = inject(vendorTrackingPageKey)
</script>
