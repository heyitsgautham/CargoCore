<template>
    <div
        class="p-6 border-b border-gray-200 dark:border-white/5 bg-gray-50/50 dark:bg-black/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <div class="flex items-center gap-3 mb-2">
                <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">Ticket
                    #{{ activeTicket.id }}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="activeTicket.priority === 'High' ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'">
                    {{ activeTicket.priority }} Priority
                </span>
            </div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ activeTicket.title }}</h2>
        </div>
        <div class="flex gap-2 shrink-0">
            <button @click="resolveTicket('Approved')" :disabled="ticketActionPending"
                class="px-5 py-2.5 bg-green-500 hover:bg-green-600 text-white rounded-xl font-bold text-sm transition-colors shadow-sm flex items-center gap-2">
                <span class="material-symbols-outlined text-[20px]">check_circle</span> {{ ticketActionPending ? 'Working...' : 'Approve' }}
            </button>
            <button @click="resolveTicket('Denied')" :disabled="ticketActionPending"
                class="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold text-sm transition-colors shadow-sm flex items-center gap-2">
                <span class="material-symbols-outlined text-[20px]">cancel</span> {{ ticketActionPending ? 'Working...' : 'Deny' }}
            </button>
        </div>
    </div>
    <div class="flex-1 p-6 overflow-y-auto bg-gray-50/30 dark:bg-black/10">
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 p-6 rounded-2xl shadow-sm space-y-6">
            <div class="flex items-center gap-4 pb-6 border-b border-gray-100 dark:border-white/10">
                <div
                    class="w-12 h-12 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center font-bold text-gray-700 dark:text-white text-lg shadow-inner">
                    {{ activeTicket.from.substring(0, 2).toUpperCase() }}</div>
                <div>
                    <div class="font-bold text-gray-900 dark:text-white text-lg">{{ activeTicket.from }}
                    </div>
                    <div class="text-sm text-gray-500">{{ activeTicket.role }} • <span
                            class="font-mono text-xs">{{ activeTicket.time }}</span></div>
                </div>
            </div>
            <div>
                <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">report</span> Issue Description
                </h4>
                <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{
                    activeTicket.description }}</p>
            </div>
            <div
                class="bg-blue-50 dark:bg-blue-900/10 p-5 rounded-xl border border-blue-100 dark:border-blue-500/20">
                <h4
                    class="text-xs font-bold text-blue-800 dark:text-blue-300 uppercase tracking-wider mb-2">
                    Requested Action Override</h4>
                <p
                    class="text-sm font-mono text-blue-900 dark:text-blue-200 font-bold bg-white/50 dark:bg-black/20 p-2 rounded">
                    {{ activeTicket.actionDetails }}</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const { activeTicket, resolveTicket, ticketActionPending } = inject(communicationPageKey)
</script>
