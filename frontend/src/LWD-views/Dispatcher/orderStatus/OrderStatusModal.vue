<template>
    <Teleport to="body">
        <BaseModal :isOpen="showActionModal" @close="closeActionModal">
            <template #title>
                {{ actionModal.type === 'cancel' ? 'Cancel Order' : 'Escalate Order' }} — {{ actionModal.order?.id }}
            </template>

            <div class="space-y-4">
                <div
                    class="rounded-xl border px-4 py-3"
                    :class="actionModal.type === 'cancel'
                        ? 'border-red-500/30 bg-red-500/10'
                        : 'border-yellow-500/30 bg-yellow-500/10'">
                    <div class="text-sm font-bold" :class="actionModal.type === 'cancel' ? 'text-red-300' : 'text-yellow-300'">
                        {{ actionModal.type === 'cancel'
                            ? 'This will remove the order from the active dispatcher flow.'
                            : 'This will create a real escalation for the Logistics Manager queue.' }}
                    </div>
                    <div class="text-xs text-gray-300 mt-1">
                        Current status: {{ actionModal.order?.statusLabel || '—' }}
                    </div>
                </div>

                <div>
                    <label class="block text-xs uppercase tracking-wider text-gray-400 mb-2">
                        Reason
                    </label>
                    <textarea
                        v-model="actionModal.reason"
                        rows="4"
                        class="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-primary/50 resize-none"
                        :placeholder="actionModal.type === 'cancel'
                            ? 'Why should this order be cancelled?'
                            : 'Why does this order need escalation?'"
                    ></textarea>
                </div>

                <div v-if="actionModal.error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {{ actionModal.error }}
                </div>
            </div>

            <template #footer>
                <button
                    @click="closeActionModal"
                    :disabled="actionSubmitting"
                    class="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-bold hover:bg-white/15 transition-colors disabled:opacity-50"
                >
                    Close
                </button>
                <button
                    @click="submitActionModal"
                    :disabled="actionSubmitting"
                    class="px-4 py-2 rounded-lg text-sm font-bold text-white transition-colors disabled:opacity-50 flex items-center gap-2"
                    :class="actionModal.type === 'cancel'
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-yellow-500 hover:bg-yellow-600 text-black'"
                >
                    <span v-if="actionSubmitting" class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                    {{ actionSubmitting
                        ? (actionModal.type === 'cancel' ? 'Cancelling...' : 'Escalating...')
                        : (actionModal.type === 'cancel' ? 'Confirm Cancel' : 'Confirm Escalation') }}
                </button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const {
    actionModal,
    actionSubmitting,
    closeActionModal,
    showActionModal,
    submitActionModal,
} = inject(orderStatusPageKey)
</script>
