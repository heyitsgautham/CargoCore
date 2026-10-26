<template>
    <!-- Staff Detail Modal -->
    <Teleport to="body">
        <div v-if="showStaffDetail && selectedStaff"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showStaffDetail = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Staff Details</h3>
                    <button @click="showStaffDetail = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div class="flex items-center gap-4">
                        <div class="w-14 h-14 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center text-white text-lg font-bold">
                            {{ getInitials(selectedStaff.name) }}
                        </div>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white text-lg">{{ selectedStaff.name }}
                            </div>
                            <div class="text-sm text-gray-600 dark:text-gray-400">{{ selectedStaff.role }} • {{
                                selectedStaff.dept }}</div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Status</div>
                            <div class="text-gray-900 dark:text-white font-bold text-sm">{{ selectedStaff.status }}
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Performance</div>
                            <div class="text-gray-900 dark:text-white font-bold text-sm">{{ selectedStaff.perf }}%
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Current Task</div>
                            <div class="text-gray-900 dark:text-white font-bold text-sm">{{ selectedStaff.task }}
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Start Time</div>
                            <div class="text-gray-900 dark:text-white font-bold text-sm font-mono">{{
                                selectedStaff.startTime }}</div>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button v-if="canPrintAssignmentSlip(selectedStaff)" @click="openAssignmentSlip(selectedStaff)"
                            class="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-600 dark:text-indigo-300 py-2 px-4 rounded-lg text-sm font-bold transition-colors">
                            Assignment Slip
                        </button>
                        <button v-if="selectedStaff.status !== 'Off Duty'" @click="setOffDuty(selectedStaff)"
                            class="flex-1 bg-gray-500/20 hover:bg-gray-500/30 text-gray-600 dark:text-gray-400 py-2 rounded-lg text-sm font-bold transition-colors">Set
                            Off Duty</button>
                        <button v-if="selectedStaff.status === 'Off Duty'" @click="setOnDuty(selectedStaff)"
                            class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-2 rounded-lg text-sm font-bold transition-colors">Set
                            On Duty</button>
                        <button @click="deleteLabourer(selectedStaff)"
                            class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-2 px-4 rounded-lg text-sm font-bold transition-colors">
                            <span class="material-symbols-outlined text-[15px] align-middle">delete</span>
                        </button>
                        <button @click="showStaffDetail = false"
                            class="flex-1 bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm transition-colors">Close</button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const {
    canPrintAssignmentSlip,
    deleteLabourer,
    getInitials,
    openAssignmentSlip,
    selectedStaff,
    setOffDuty,
    setOnDuty,
    showStaffDetail,
} = inject(laborPageKey)
</script>
