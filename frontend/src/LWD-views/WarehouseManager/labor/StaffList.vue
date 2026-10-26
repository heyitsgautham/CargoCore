<template>
    <!-- Loading State -->
    <div v-if="loading" class="glass-panel rounded-xl p-8 text-center">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <div class="mt-2 text-gray-600 dark:text-gray-400">Loading staff data...</div>
    </div>

    <!-- Staff List -->
    <div v-else class="glass-panel rounded-xl overflow-hidden">
        <div
            class="p-4 border-b border-gray-100 dark:border-white/5 flex gap-4 items-center bg-gray-100 dark:bg-black/20">
            <input type="text" v-model="searchQuery" placeholder="Search staff..."
                class="flex-1 bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 px-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
            <select v-model="deptFilter"
                class="bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white">
                <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Departments</option>
                <option value="Picking" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Picking</option>
                <option value="Packing" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Packing</option>
                <option value="Receiving" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Receiving</option>
                <option value="Loading" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Loading</option>
            </select>
            <div v-if="statusFilter"
                class="flex items-center gap-2 bg-primary/20 text-primary px-3 py-1.5 rounded-lg text-xs font-bold">
                {{ statusFilter }}
                <button @click="statusFilter = ''" class="hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined text-[14px]">close</span></button>
            </div>
        </div>

        <div class="overflow-auto max-h-[500px]">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase sticky top-0">
                    <tr>
                        <th class="p-4">Name</th>
                        <th class="p-4">Role</th>
                        <th class="p-4">Current Task</th>
                        <th class="p-4">Order ID</th>
                        <th class="p-4">Time Log</th>
                        <th class="p-4">Performance</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="staff in filteredStaff" :key="staff.id"
                        class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                        <td class="p-4 flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                                {{ getInitials(staff.name) }}
                            </div>
                            <span class="font-bold text-gray-900 dark:text-white">{{ staff.name }}</span>
                        </td>
                        <td class="p-4 text-gray-600 dark:text-gray-300">{{ staff.role }}</td>
                        <td class="p-4">
                            <div class="text-gray-600 dark:text-gray-400">{{ staff.task }}</div>
                            <div v-if="staff.assignmentHint" class="text-[10px] text-gray-500 dark:text-gray-500 mt-1">
                                {{ staff.assignmentHint }}
                            </div>
                        </td>
                        <td class="p-4">
                            <div v-if="staff.orderId" class="space-y-1">
                                <div class="font-mono text-primary text-xs">{{ staff.orderId }}</div>
                                <div v-if="staff.orderScope" class="text-[10px] text-gray-500 dark:text-gray-500">
                                    {{ staff.orderScope }}
                                </div>
                            </div>
                            <span v-else class="text-gray-600">—</span>
                        </td>
                        <td class="p-4">
                            <div class="text-xs space-y-0.5">
                                <div class="text-gray-600 dark:text-gray-400">In: <span
                                        class="text-gray-900 dark:text-white font-mono">{{ staff.startTime
                                        }}</span></div>
                                <div v-if="staff.fieldTime" class="text-purple-600 dark:text-purple-400">Field: <span
                                        class="font-mono">{{ staff.fieldTime }}</span></div>
                                <div v-if="staff.returnTime" class="text-green-600 dark:text-green-400">Return: <span
                                        class="font-mono">{{ staff.returnTime }}</span></div>
                            </div>
                        </td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div class="bg-green-500 h-full" :style="`width: ${staff.perf}%`"></div>
                                </div>
                                <span class="text-xs">{{ staff.perf }}%</span>
                            </div>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] font-bold" :class="staff.statusClass">
                                {{ staff.status }}
                            </span>
                        </td>
                        <td class="p-4">
                            <div class="flex gap-1">
                                <button v-if="staff.status === 'In Warehouse'" @click="openAssign(staff)"
                                    class="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 px-2 py-1 rounded text-xs font-bold transition-colors"
                                    title="Assign to Order">
                                    <span class="material-symbols-outlined text-[14px]">link</span>
                                </button>
                                <button v-if="canPrintAssignmentSlip(staff)" @click="openAssignmentSlip(staff)"
                                    class="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-500 dark:text-indigo-300 px-2 py-1 rounded text-xs font-bold transition-colors"
                                    title="Assignment Slip">
                                    <span class="material-symbols-outlined text-[14px]">print</span>
                                </button>
                                <button @click="openStaffDetail(staff)"
                                    class="text-gray-500 hover:text-gray-900 dark:text-white" title="More">
                                    <span class="material-symbols-outlined text-[16px]">more_horiz</span>
                                </button>
                            </div>
                        </td>
                    </tr>
                    <tr v-if="filteredStaff.length === 0 && !loading">
                        <td colspan="8" class="p-8 text-center text-gray-500">
                            <span class="material-symbols-outlined text-4xl mb-2 opacity-50">group_off</span>
                            <p>{{ searchQuery || deptFilter || statusFilter ? 'No staff match the current filters' : 'No labour staff found for this warehouse' }}</p>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const {
    canPrintAssignmentSlip,
    deptFilter,
    filteredStaff,
    getInitials,
    loading,
    openAssign,
    openAssignmentSlip,
    openStaffDetail,
    searchQuery,
    statusFilter,
} = inject(laborPageKey)
</script>
