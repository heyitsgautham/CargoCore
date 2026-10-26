<template>
    <!-- Ticket Detail Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="!!detailTicket" @close="detailTicket = null">
            <template #title>{{ detailTicket?.id }} — {{ detailTicket?.subject }}</template>
            <div v-if="detailTicket" class="space-y-4">
                <div class="flex gap-3 text-xs">
                    <span class="px-2 py-0.5 rounded font-bold" :class="ticketStatusClass(detailTicket.status)">{{ detailTicket.status }}</span>
                    <span class="font-bold uppercase" :class="priorityClass(detailTicket.priority)">{{ detailTicket.priority }}</span>
                    <span class="text-gray-400">{{ detailTicket.created }}</span>
                </div>
                <div class="space-y-3 max-h-64 overflow-y-auto pr-1">
                    <div v-for="(msg, idx) in detailTicket.replies" :key="idx"
                        class="p-3 rounded-lg text-xs"
                        :class="msg.from === 'You' ? 'bg-blue-500/10 ml-6' : 'bg-gray-100 dark:bg-white/5 mr-6'">
                        <div class="flex justify-between mb-1">
                            <span class="font-bold text-gray-900 dark:text-white">{{ msg.from }}</span>
                            <span class="text-gray-400 text-[10px]">{{ msg.time }}</span>
                        </div>
                        <p class="text-gray-600 dark:text-gray-300">{{ msg.message }}</p>
                    </div>
                </div>
                <div v-if="detailTicket.status !== 'Resolved'" class="flex gap-2">
                    <input v-model="replyText" type="text" placeholder="Type a reply..."
                        class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                        @keyup.enter="sendReply">
                    <button @click="sendReply" :disabled="!replyText.trim()"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">Send</button>
                </div>
            </div>
            <template #footer>
                <button @click="detailTicket = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                <button v-if="detailTicket?.status !== 'Resolved'"
                    @click="markResolved(detailTicket); detailTicket = null"
                    class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-bold hover:bg-green-700 transition-colors">
                    Mark Resolved
                </button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    detailTicket,
    markResolved,
    priorityClass,
    replyText,
    sendReply,
    ticketStatusClass,
} = inject(vendorSupportPageKey)
</script>
