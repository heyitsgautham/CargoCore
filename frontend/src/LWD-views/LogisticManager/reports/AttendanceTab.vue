<template>
    <div v-if="activeTab === 'attendance'" class="space-y-6 animate-fade-in">
        <!-- Overview Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div
                class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Present Today</h3>
                <span class="text-4xl font-black text-green-500">{{ attendancePresentCount }}</span>
                <p class="text-[10px] text-gray-400 mt-1">{{ attendancePresentPct }}% of Active Staff</p>
            </div>
            <div
                class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">On Leave</h3>
                <span class="text-4xl font-black text-yellow-500">{{ attendanceOnLeaveCount }}</span>
                <p class="text-[10px] text-gray-400 mt-1">Scheduled Absences</p>
            </div>
            <div
                class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Unplanned Absences</h3>
                <span class="text-4xl font-black text-red-500">{{ attendanceUnplannedCount }}</span>
                <p class="text-[10px] text-gray-400 mt-1">Requires Attention</p>
            </div>
            <div
                class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Total Workforce</h3>
                <span class="text-4xl font-black text-blue-500">{{ store.filteredUsers.length }}</span>
                <p class="text-[10px] text-gray-400 mt-1">Active Accounts</p>
            </div>
        </div>

        <!-- Detailed Leave Table -->
        <div
            class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col">
            <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                <h3 class="font-bold text-gray-900 dark:text-white">Attendance & Leave Tracker</h3>
            </div>
            <table class="w-full text-left text-xs">
                <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                    <tr>
                        <th class="p-4">Employee</th>
                        <th class="p-4">Status</th>
                        <th class="p-4 text-center">Allowed Leave</th>
                        <th class="p-4 text-center">Taken</th>
                        <th class="p-4 text-center">Balance</th>
                        <th class="p-4 text-center">Extra Absent</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="user in store.filteredUsers" :key="user.email"
                        class="hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-4 flex items-center gap-3">
                            <img :src="user.avatar" class="w-8 h-8 rounded-full">
                            <div>
                                <p class="font-bold text-gray-900 dark:text-white">{{ user.name }}</p>
                                <p class="text-[10px] text-gray-400">{{ user.email }}</p>
                            </div>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] uppercase font-bold"
                                :class="loginedToday(user) ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400'">
                                {{ loginedToday(user) ? 'Present' : 'Absent' }}
                            </span>
                        </td>
                        <td class="p-4 text-center font-mono font-bold">{{ userLeave(user).allowed }} Days</td>
                        <td class="p-4 text-center font-mono text-gray-500">{{ userLeave(user).taken }}</td>
                        <td class="p-4 text-center font-mono font-bold" :class="userLeave(user).balance > 5 ? 'text-green-600' : 'text-yellow-500'">{{ userLeave(user).balance }}</td>
                        <td class="p-4 text-center font-mono font-bold" :class="userLeave(user).extra > 0 ? 'text-red-500' : 'text-gray-400'">{{ userLeave(user).extra }}</td>
                    </tr>
                </tbody>
            </table>
        </div>

    </div>
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const {
    activeTab,
    attendanceOnLeaveCount,
    attendancePresentCount,
    attendancePresentPct,
    attendanceUnplannedCount,
    loginedToday,
    store,
    userLeave,
} = inject(reportsPageKey)
</script>
