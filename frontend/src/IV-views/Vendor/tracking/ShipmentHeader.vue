<template>
    <!-- Header bar -->
    <div class="flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-3">
            <button @click="selected = null"
                class="w-9 h-9 flex items-center justify-center rounded-xl bg-gray-100 dark:bg-white/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-gray-600 dark:text-gray-300 hover:text-blue-600 transition-colors">
                <span class="material-symbols-outlined text-[20px]">arrow_back</span>
            </button>
            <div>
                <div class="flex items-center gap-2">
                    <span class="font-mono font-black text-gray-900 dark:text-white text-lg">{{ selected.id }}</span>
                    <span class="px-3 py-1 rounded-full text-xs font-bold" :class="statusClass(selected.statusKey)">{{ selected.status }}</span>
                </div>
                <div class="text-xs text-gray-400 mt-0.5">{{ selected.route }}</div>
            </div>
        </div>
        <!-- Actions -->
        <div v-if="selected.statusKey !== 'delivered' && selected.statusKey !== 'cancelled'" class="flex items-center gap-2">
            <!-- Update Address: hidden for recurring orders -->
            <button v-if="!selected.isRecurring" @click="showAddressModal = true" class="px-3 py-1.5 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[15px]">edit_location</span> Update Address
            </button>
            <!-- Reschedule: hidden for recurring orders -->
            <button v-if="!selected.isRecurring" @click="showRescheduleModal = true" class="px-3 py-1.5 bg-purple-50 dark:bg-purple-500/10 hover:bg-purple-100 text-purple-600 dark:text-purple-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[15px]">event</span> Reschedule
            </button>
            <button @click="showDamageModal = true" class="px-3 py-1.5 bg-orange-50 dark:bg-orange-500/10 hover:bg-orange-100 text-orange-600 dark:text-orange-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[15px]">report_problem</span> Report Issue
            </button>
            <button @click="handleCancel" class="px-3 py-1.5 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 text-red-600 dark:text-red-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[15px]">cancel</span> Cancel
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    handleCancel,
    selected,
    showAddressModal,
    showDamageModal,
    showRescheduleModal,
    statusClass,
} = inject(vendorTrackingPageKey)
</script>
