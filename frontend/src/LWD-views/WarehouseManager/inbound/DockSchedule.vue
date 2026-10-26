<template>
    <!-- Dock Schedule -->
    <div class="glass-panel p-6 rounded-xl xl:col-span-1">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Dock Schedule (Today)</h3>
        <div class="space-y-3">
            <div v-for="slot in dockSchedule" :key="slot.id" @click="selectedSlot = slot; showSlotDetail = true"
                class="p-3 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 hover:border-white/20 rounded-lg cursor-pointer transition-all"
                :class="slot.status === 'Completed' ? 'opacity-50' : ''">
                <div class="flex justify-between items-center mb-1">
                    <span
                        :class="slot.status === 'Completed' ? 'text-gray-600 dark:text-gray-400' : 'text-primary'"
                        class="font-bold">{{ slot.time }}</span>
                    <span class="text-xs px-2 py-0.5 rounded font-bold" :class="slot.statusClass">{{ slot.status }}</span>
                </div>
                <div class="text-gray-900 dark:text-white text-sm">Supplier: {{ slot.supplier }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">{{ slot.dock }} • {{ slot.pallets }}
                    Pallets</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { dockSchedule, selectedSlot, showSlotDetail } = inject(inboundPageKey)
</script>
