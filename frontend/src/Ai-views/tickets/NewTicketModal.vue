<template>
    <div v-if="showNewTicketModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="showNewTicketModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-lg shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
            <div class="p-6 border-b border-gray-100 dark:border-white/5">
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">Create New Ticket</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Open a new support request manually</p>
            </div>
            <div class="p-6 space-y-5">
                <div class="grid grid-cols-2 gap-4">
                    <div class="col-span-2">
                        <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Title</label>
                        <input v-model="newForm.title" type="text"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors"
                            placeholder="Brief summary of the issue" />
                    </div>
                    <div>
                        <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Priority</label>
                        <select v-model="newForm.priority" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors">
                            <option value="urgent">Urgent</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Category</label>
                        <select v-model="newForm.category" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors">
                            <option value="technical">Technical Issue</option>
                            <option value="billing">Billing Dispute</option>
                            <option value="logistics">Logistics Delay</option>
                            <option value="damage">Damage Claim</option>
                            <option value="account">Account Access</option>
                            <option value="refund">Refund</option>
                            <option value="general">General</option>
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Customer / Vendor (Optional)</label>
                        <input v-model="newForm.customer_name" type="text"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors"
                            placeholder="Name or ID" />
                    </div>
                    <div class="col-span-2">
                        <label class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Description</label>
                        <textarea v-model="newForm.description" rows="4"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-3 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors resize-none"
                            placeholder="Provide detailed information about the issue..."></textarea>
                    </div>
                </div>
            </div>
            <div class="p-6 border-t border-gray-100 dark:border-white/5 flex gap-3 bg-gray-50 dark:bg-white/5">
                <button @click="showNewTicketModal = false" class="flex-1 py-2.5 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-lg transition-colors">Cancel</button>
                <button @click="submitNewTicket" :disabled="!newForm.title || creating"
                    class="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-colors shadow-sm">
                    {{ creating ? 'Creating…' : 'Create Ticket' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { ticketsPageKey } from './ticketsPageContext'

const { creating, newForm, showNewTicketModal, submitNewTicket } = inject(ticketsPageKey)
</script>
