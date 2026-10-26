<template>
    <!-- Slot Detail Modal -->
    <Teleport to="body">
        <div v-if="showSlotDetail && selectedSlot"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showSlotDetail = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock Slot Details</h3>
                    <button @click="showSlotDetail = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-3">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Supplier</div>
                            <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.supplier }}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Time</div>
                            <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.time }}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Dock</div>
                            <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.dock }}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Pallets</div>
                            <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.pallets }}</div>
                        </div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400">Status</div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="selectedSlot.statusClass">{{
                            selectedSlot.status }}</span>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { selectedSlot, showSlotDetail } = inject(inboundPageKey)
</script>
