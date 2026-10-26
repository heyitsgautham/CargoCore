<template>
    <div v-if="showModal && selectedTicket"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-6"
        @click.self="showModal = false">
        <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-2xl shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden flex flex-col max-h-[90vh]">

            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-start bg-gray-50 dark:bg-white/5 shrink-0">
                <div class="flex-1 pr-4">
                    <div class="flex items-center gap-3 mb-2">
                        <span class="text-xs font-mono font-bold px-2 py-0.5 rounded"
                            :class="selectedTicket.status === 'resolved' ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400'">
                            {{ selectedTicket.reference_code }}
                        </span>
                        <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border" :class="priorityClass(selectedTicket.priority)">
                            {{ selectedTicket.priority }} Priority
                        </span>
                    </div>
                    <h3 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white leading-tight">{{ selectedTicket.title }}</h3>
                </div>
                <button @click="showModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-white bg-white dark:bg-black/20 p-2 rounded-full border border-gray-200 dark:border-white/10 transition-colors">
                    <span class="material-symbols-outlined text-sm">close</span>
                </button>
            </div>

            <div class="p-6 overflow-y-auto custom-scrollbar flex-1 bg-white dark:bg-black/10 space-y-6">
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Status</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full" :class="selectedTicket.status === 'new' ? 'bg-blue-500' : selectedTicket.status === 'in_progress' ? 'bg-yellow-500' : 'bg-green-500'"></span>
                            {{ statusLabel(selectedTicket.status) }}
                        </div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Source</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ selectedTicket.source_label }}</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Assignee</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ selectedTicket.assigned_agent_name || '—' }}</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">{{ selectedTicket.requester_type || 'Customer' }}</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ selectedTicket.customer_name || '—' }}</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Order Ref</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ selectedTicket.linked_order_tracking_code || '—' }}</div>
                    </div>
                    <div>
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Created</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ formatFull(selectedTicket.created_at) }}</div>
                    </div>
                    <div v-if="selectedTicket.linked_vendor_ticket_code">
                        <div class="text-[10px] uppercase font-bold text-gray-400 mb-1 tracking-wider">Vendor Ticket</div>
                        <div class="font-medium text-sm text-gray-900 dark:text-white">{{ selectedTicket.linked_vendor_ticket_code }}</div>
                    </div>
                </div>

                <div>
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-2 tracking-wider">Description</div>
                    <div class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 border border-gray-100 dark:border-white/5">
                        <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">{{ selectedTicket.description }}</p>
                    </div>
                </div>

                <div v-if="selectedTicket.source !== 'manual'" class="rounded-xl border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/10 p-4 text-xs text-blue-700 dark:text-blue-300">
                    {{ selectedTicket.source === 'warehouse_inbound'
                        ? 'This ticket came from the Warehouse Manager inbound flow. Reply here to coordinate with the vendor, then choose whether the shipment moves to picking or goes back to the vendor.'
                        : selectedTicket.source === 'vendor_portal'
                        ? 'This ticket was raised in the Vendor Portal and mirrored into the AI Support queue. It is routed to the Support Manager queue for manual handling.'
                        : 'This ticket was auto-created from an AI chat handoff so the Support Manager can track and handle it from the ticket queue.' }}
                </div>

                <div v-if="selectedTicket.source === 'warehouse_inbound' && selectedTicket.resolution_label" class="rounded-xl border border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/10 p-4 text-xs text-green-700 dark:text-green-300">
                    <div class="font-bold uppercase tracking-wider mb-1">Inbound Outcome</div>
                    <div>{{ selectedTicket.resolution_label }}</div>
                    <div class="mt-1 text-[11px] text-green-600 dark:text-green-200">{{ warehouseResolutionHint(selectedTicket.resolution_action) }}</div>
                </div>

                <div v-if="selectedTicket.linked_vendor_replies?.length" class="space-y-3">
                    <div class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Vendor Support Thread</div>
                    <div class="space-y-3 max-h-64 overflow-y-auto pr-1">
                        <div v-for="(reply, idx) in selectedTicket.linked_vendor_replies" :key="`${reply.created_at}-${idx}`"
                            class="rounded-xl border border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 p-4">
                            <div class="flex items-center justify-between gap-3 mb-1">
                                <span class="text-xs font-bold text-gray-900 dark:text-white">{{ reply.from_name }}</span>
                                <span class="text-[10px] text-gray-400">{{ formatFull(reply.created_at) }}</span>
                            </div>
                            <p class="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line">{{ reply.message }}</p>
                        </div>
                    </div>
                </div>

                <div v-if="selectedTicket.linked_vendor_ticket_id" class="space-y-3 border-t border-gray-100 dark:border-white/10 pt-4">
                    <div class="text-[10px] uppercase font-bold text-gray-500 tracking-wider">Vendor Chat Reply</div>
                    <div v-if="supportReplyLocked" class="rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300">
                        This vendor chat is closed because support marked the issue as resolved.
                    </div>
                    <div v-else-if="isSupportManager" class="flex gap-2">
                        <textarea v-model="replyDraft" rows="3" placeholder="Reply to the vendor from support..."
                            class="flex-1 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"></textarea>
                        <button @click="sendVendorReply" :disabled="!replyDraft.trim()"
                            class="px-4 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg text-xs transition-colors">
                            Send Reply
                        </button>
                    </div>
                    <div v-else class="rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300">
                        Only the Support Manager can reply in this vendor thread.
                    </div>
                </div>

                <!-- Update Status -->
                <div v-if="selectedTicket.status !== 'resolved' && isSupportManager" class="space-y-4 border-t border-gray-100 dark:border-white/10 pt-4">
                    <div class="text-[10px] uppercase font-bold text-gray-500 tracking-wider">CS Actions</div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Update Status</label>
                        <div class="flex gap-2 flex-wrap">
                            <button v-for="s in statusOptionsForSelectedTicket" :key="s.value" @click="updateStatus(s.value)"
                                class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-all"
                                :class="selectedTicket.status === s.value ? s.activeClass : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-white/20'">
                                {{ s.label }}
                            </button>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Notes</label>
                        <div class="flex gap-2">
                            <textarea v-model="editNotes" rows="2" placeholder="Add notes..."
                                class="flex-1 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"></textarea>
                            <button @click="saveNotes" class="px-3 bg-gray-800 dark:bg-white/10 hover:bg-gray-900 dark:hover:bg-white/20 text-white font-bold rounded-lg text-xs transition-colors">Save</button>
                        </div>
                    </div>
                    <div v-if="selectedTicket.source === 'warehouse_inbound'" class="space-y-2">
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400">Inbound Resolution</label>
                        <div class="flex gap-2 flex-wrap">
                            <button @click="resolveWarehouseIssue('vendor_accept_move')"
                                class="px-3 py-2 rounded-lg text-xs font-bold border border-green-200 bg-green-50 text-green-700 dark:border-green-500/30 dark:bg-green-500/10 dark:text-green-300">
                                Vendor Cleared For Move
                            </button>
                            <button @click="resolveWarehouseIssue('vendor_take_back')"
                                class="px-3 py-2 rounded-lg text-xs font-bold border border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
                                Vendor Will Take Back
                            </button>
                        </div>
                    </div>
                </div>

                <div v-else-if="selectedTicket.status !== 'resolved'" class="rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300">
                    Only the Support Manager can update this ticket.
                </div>
            </div>

            <div class="p-6 border-t border-gray-100 dark:border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50 dark:bg-white/5 shrink-0">
                <button v-if="selectedTicket.can_delete && isSupportManager" @click="removeTicket" class="text-xs text-red-500 hover:text-red-700 font-bold flex items-center gap-1 transition-colors">
                    <span class="material-symbols-outlined text-[14px]">delete</span> Delete
                </button>
                <div class="flex gap-3 w-full sm:w-auto">
                    <button @click="showModal = false" class="flex-1 sm:flex-none px-6 py-2 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-lg transition-colors shadow-sm">Close</button>
                    <button v-if="selectedTicket.status !== 'resolved' && isSupportManager && !isWarehouseInboundSelected" @click="updateStatus('resolved')"
                        class="flex-1 sm:flex-none px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-colors shadow-sm flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-sm">check_circle</span> Mark Resolved
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { ticketsPageKey } from './ticketsPageContext'

const {
    editNotes,
    formatFull,
    isSupportManager,
    isWarehouseInboundSelected,
    priorityClass,
    removeTicket,
    replyDraft,
    resolveWarehouseIssue,
    saveNotes,
    selectedTicket,
    sendVendorReply,
    showModal,
    statusLabel,
    statusOptionsForSelectedTicket,
    supportReplyLocked,
    updateStatus,
    warehouseResolutionHint,
} = inject(ticketsPageKey)
</script>
