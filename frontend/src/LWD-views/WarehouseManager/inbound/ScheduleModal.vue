<template>
    <!-- Schedule Modal -->
    <Teleport to="body">
        <div v-if="showScheduleModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showScheduleModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Schedule Inbound
                        Delivery</h3>
                    <button @click="showScheduleModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Supplier
                            Name</label>
                        <input type="text" v-model="scheduleForm.supplier" placeholder="Supplier name"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Expected
                                Qty</label>
                            <input type="number" v-model.number="scheduleForm.qty"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">ETA</label>
                            <input type="datetime-local" v-model="scheduleForm.eta"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                        </div>
                    </div>
                    <button @click="scheduleDelivery" :disabled="!scheduleForm.supplier"
                        class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Schedule
                        Delivery</button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { scheduleDelivery, scheduleForm, showScheduleModal } = inject(inboundPageKey)
</script>
