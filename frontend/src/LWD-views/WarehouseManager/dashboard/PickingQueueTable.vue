<template>
    <!-- Center: Interactive Picking Queue Table -->
    <div class="lg:col-span-2 glass-panel rounded-xl flex flex-col overflow-hidden">
        <div
            class="p-4 border-b border-gray-100 dark:border-white/5 flex flex-wrap gap-4 justify-between items-center bg-gray-100 dark:bg-black/20">
            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span class="material-symbols-outlined text-teal-500">list_alt</span>
                Live Picking Queue
            </h3>

            <!-- Dynamic Search & Filters -->
            <div class="flex gap-2 sm:gap-3 flex-1 justify-end flex-wrap">
                <div class="relative w-36 sm:w-48">
                    <span
                        class="material-symbols-outlined absolute left-2 top-1.5 text-gray-500 text-[18px]">search</span>
                    <input v-model="searchQuery" type="text" placeholder="Search ID or Staff..."
                        class="w-full bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg pl-8 pr-3 py-1 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-teal-500/50 transition-colors">
                </div>
                <select v-model="statusFilter"
                    class="bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1 text-sm text-gray-600 dark:text-gray-300 focus:outline-none focus:border-teal-500/50 transition-colors">
                    <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Statuses</option>
                    <option value="Pending" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pending</option>
                    <option value="In Progress" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Progress</option>
                    <option value="Unassigned" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Unassigned</option>
                    <option value="Review" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Review</option>
                </select>
            </div>
        </div>

        <div class="flex-1 overflow-auto">
            <table class="w-full text-left border-collapse min-w-[600px]">
                <thead class="bg-gray-50 dark:bg-white/5 sticky top-0 z-10 backdrop-blur-md">
                    <tr class="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                        <th class="p-3 font-medium">Order ID</th>
                        <th class="p-3 font-medium">Items</th>
                        <th class="p-3 font-medium">Zone</th>
                        <th class="p-3 font-medium">Priority</th>
                        <th class="p-3 font-medium">Assigned To</th>
                        <th class="p-3 font-medium">Status / Progress</th>
                        <th class="p-3 font-medium text-center">Action</th>
                    </tr>
                </thead>
                <tbody class="text-sm divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="order in filteredQueue" :key="order.id"
                        class="hover:bg-gray-50 dark:bg-white/5 transition-colors group">
                        <td class="p-3 font-mono text-teal-400">{{ order.id }}</td>
                        <td class="p-3 text-gray-600 dark:text-gray-300">{{ order.items }} items</td>
                        <td class="p-3 text-gray-600 dark:text-gray-300">
                            <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700/50 rounded text-xs">{{ order.zone }}</span>
                        </td>
                        <td class="p-3">
                            <span v-if="order.priority === 'High'"
                                class="text-red-600 dark:text-red-400 text-xs font-bold bg-red-500/10 px-2 py-0.5 rounded flex items-center gap-1 w-fit">
                                <span class="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse"></span> HIGH
                            </span>
                            <span v-else class="text-gray-600 dark:text-gray-400 text-xs">Normal</span>
                        </td>
                        <td class="p-3">
                            <div class="flex items-center gap-2" v-if="order.assigned">
                                <div
                                    class="w-6 h-6 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-[10px] shadow-sm">
                                    {{ order.assignedInitials }}</div>
                                <span class="text-gray-600 dark:text-gray-300">{{ order.assigned }}</span>
                            </div>
                            <span v-else class="text-gray-500 italic">-- Unassigned --</span>
                        </td>
                        <td class="p-3">
                            <div class="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                                <div class="bg-teal-500 h-full transition-all duration-500"
                                    :class="{ 'bg-blue-400': order.status === 'Review' }"
                                    :style="`width: ${order.progress}%`"></div>
                            </div>
                            <div class="text-[10px] text-gray-600 dark:text-gray-400 mt-1 font-medium">
                                <span v-if="order.status === 'Review'" class="text-blue-400">Reviewing</span>
                                <span v-else-if="order.status === 'Unassigned'"
                                    class="text-gray-500">Waiting</span>
                                <span v-else>{{ order.progress }}% Picked</span>
                            </div>
                        </td>
                        <!-- Dynamic Context Menu -->
                        <td class="p-3 relative text-center">
                            <button @click.stop="toggleActionMenu(order.id)"
                                class="text-gray-500 hover:text-gray-900 dark:text-white p-1 rounded hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">
                                <span class="material-symbols-outlined">more_horiz</span>
                            </button>
                            <div v-if="activeActionMenu === order.id"
                                class="absolute right-8 mt-1 w-36 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl py-1 z-20 text-left">
                                <button @click="markComplete(order)"
                                    class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-green-600 dark:text-green-400 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[14px]">check_circle</span> Mark
                                    Complete
                                </button>
                                <button @click="reassign(order)"
                                    class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-blue-600 dark:text-blue-400 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[14px]">person_add</span>
                                    Reassign
                                </button>
                                <button @click="toggleActionMenu(order.id)"
                                    class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[14px]">close</span> Close
                                </button>
                            </div>
                        </td>
                    </tr>
                    <tr v-if="filteredQueue.length === 0">
                        <td colspan="7" class="p-8 text-center text-gray-500">
                            <span class="material-symbols-outlined text-4xl mb-2 opacity-50">search_off</span>
                            <p>No matching orders found.</p>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { wmDashboardPageKey } from './wmDashboardPageContext'

const {
    activeActionMenu,
    filteredQueue,
    markComplete,
    reassign,
    searchQuery,
    statusFilter,
    toggleActionMenu,
} = inject(wmDashboardPageKey)
</script>
