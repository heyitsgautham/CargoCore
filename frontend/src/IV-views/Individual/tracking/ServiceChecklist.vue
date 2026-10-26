<template>
    <!-- Service Checklist -->
    <div class="glass-panel p-4 sm:p-5 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
            <span class="material-symbols-outlined text-purple-500 text-lg">checklist</span> Service
            Checklist
        </h3>
        <div class="space-y-2">
            <div v-for="task in serviceChecklist" :key="task.text" class="flex items-center gap-3 text-sm">
                <span class="material-symbols-outlined text-lg"
                    :class="task.done ? 'text-green-500' : 'text-gray-300 dark:text-gray-600'">{{ task.done
                        ? 'check_circle' : 'radio_button_unchecked' }}</span>
                <span :class="task.done ? 'text-gray-400 line-through' : 'text-gray-900 dark:text-white'">{{
                    task.text }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { serviceChecklist } = inject(customerTrackingPageKey)
</script>
