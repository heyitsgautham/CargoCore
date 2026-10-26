<template>
    <!-- ── TICKETS TAB ── -->
    <div v-if="activeTab === 'tickets'" class="flex-1 flex flex-col overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0">
            <select v-model="statusFilter"
                class="text-xs bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1 text-gray-700 dark:text-gray-300 focus:outline-none">
                <option value="all" class="bg-white dark:bg-gray-800">All</option>
                <option value="Open" class="bg-white dark:bg-gray-800">Open</option>
                <option value="In Progress" class="bg-white dark:bg-gray-800">In Progress</option>
                <option value="Resolved" class="bg-white dark:bg-gray-800">Resolved</option>
            </select>
            <button @click="openCreateModal"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">add</span> Create Ticket
            </button>
        </div>

        <div v-if="loadingTickets" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Loading tickets...
        </div>
        <div v-else class="flex-1 overflow-auto">
            <table class="w-full text-left text-sm min-w-[600px]">
                <thead class="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 uppercase text-[10px] sticky top-0">
                    <tr>
                        <th class="px-4 py-3">Ticket</th>
                        <th class="px-4 py-3">Subject</th>
                        <th class="px-4 py-3">Created</th>
                        <th class="px-4 py-3">Priority</th>
                        <th class="px-4 py-3">Status</th>
                        <th class="px-4 py-3 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-if="filteredTickets.length === 0">
                        <td colspan="6" class="px-4 py-8 text-center text-gray-400 text-sm">No tickets found</td>
                    </tr>
                    <tr v-for="t in filteredTickets" :key="t.id"
                        class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                        @click="openTicketDetail(t)">
                        <td class="px-4 py-3 font-mono text-blue-500 text-xs font-bold">{{ t.id }}</td>
                        <td class="px-4 py-3 text-gray-900 dark:text-white text-xs font-medium">{{ t.subject }}</td>
                        <td class="px-4 py-3 text-gray-500 text-xs">{{ t.created }}</td>
                        <td class="px-4 py-3">
                            <span class="text-[10px] font-bold uppercase" :class="priorityClass(t.priority)">{{ t.priority }}</span>
                        </td>
                        <td class="px-4 py-3">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="ticketStatusClass(t.status)">{{ t.status }}</span>
                        </td>
                        <td class="px-4 py-3 text-right" @click.stop>
                            <button @click="openTicketDetail(t)"
                                class="p-1 rounded hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="View Details">
                                  <span class="material-symbols-outlined text-[16px]">visibility</span>
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    activeTab,
    filteredTickets,
    loadingTickets,
    openCreateModal,
    openTicketDetail,
    priorityClass,
    statusFilter,
    ticketStatusClass,
} = inject(vendorSupportPageKey)
</script>
