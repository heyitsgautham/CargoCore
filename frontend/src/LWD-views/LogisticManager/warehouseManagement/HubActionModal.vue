<template>
    <BaseModal :is-open="isHubActionModalOpen" @close="closeHubActionModal">
        <template #title>
            <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-2xl flex items-center justify-center border"
                    :class="hubActionModal.iconWrapClass">
                    <span class="material-symbols-outlined text-[20px]" :class="hubActionModal.iconClass">
                        {{ hubActionModal.icon }}
                    </span>
                </div>
                <div>
                    <div class="text-lg font-bold text-white">{{ hubActionModal.title }}</div>
                    <div class="text-xs uppercase tracking-[0.25em] text-slate-400">{{ hubActionModal.hubName }}</div>
                </div>
            </div>
        </template>

        <div class="space-y-4 text-sm">
            <p class="leading-7 text-slate-200">
                {{ hubActionModal.message }}
            </p>

            <div class="rounded-2xl border p-4" :class="hubActionModal.panelClass">
                <div class="text-[11px] font-semibold uppercase tracking-[0.3em]" :class="hubActionModal.labelClass">
                    What Happens Next
                </div>
                <p class="mt-2 leading-6" :class="hubActionModal.noteClass">
                    {{ hubActionModal.note }}
                </p>
            </div>
        </div>

        <template #footer>
            <button @click="closeHubActionModal" :disabled="isHubActionPending"
                class="px-5 py-2 rounded-lg text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 border border-white/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                Cancel
            </button>
            <button @click="confirmHubAction" :disabled="isHubActionPending"
                class="px-5 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                :class="hubActionModal.confirmButtonClass">
                {{ isHubActionPending ? hubActionModal.pendingLabel : hubActionModal.confirmLabel }}
            </button>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { warehouseManagementPageKey } from './warehouseManagementPageContext'

const {
    closeHubActionModal,
    confirmHubAction,
    hubActionModal,
    isHubActionModalOpen,
    isHubActionPending,
} = inject(warehouseManagementPageKey)
</script>
