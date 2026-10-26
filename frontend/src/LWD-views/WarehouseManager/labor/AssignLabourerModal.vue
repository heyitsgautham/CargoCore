<template>
    <!-- Assign to Order Modal -->
    <Teleport to="body">
        <div v-if="showAssignModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showAssignModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Assign Labor to Order</h3>
                    <button @click="showAssignModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div v-if="assignTarget">
                        <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">Selected Worker</div>
                        <div
                            class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 mb-4">
                            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                                {{ getInitials(assignTarget.name) }}
                            </div>
                            <div class="flex-1">
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ assignTarget.name }}
                                </div>
                                <div class="text-xs text-gray-500">{{ assignTarget.role }}</div>
                            </div>
                            <button @click="assignTarget = null" class="text-gray-400 hover:text-red-500 transition-colors">
                                <span class="material-symbols-outlined text-[16px]">close</span>
                            </button>
                        </div>
                    </div>
                    <div v-else>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Select Available Worker</label>
                        <select v-model="assignTarget"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 mb-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option :value="null">Select a worker...</option>
                            <option v-for="staff in availableStaffList" :key="staff.id" :value="staff">
                                {{ staff.name }} ({{ staff.role }})
                            </option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Order ID</label>
                        <input type="text" v-model="assignOrderId" placeholder="ORD-XXXXX"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 font-mono" />
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Assignment Type</label>
                        <select v-model="assignType"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Picking</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Packing</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Loading</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Field Duty (With Driver)</option>
                        </select>
                    </div>
                    <div
                        class="flex items-center gap-2 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 text-xs text-blue-600 dark:text-blue-400">
                        <span class="material-symbols-outlined text-[16px]">info</span>
                        Seat compatibility will be verified by Dispatcher before dispatch.
                    </div>
                    <button @click="assignWorker" :disabled="isAssigning || !assignOrderId || !assignTarget"
                        class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50">
                        {{ isAssigning ? 'Assigning...' : 'Assign to Order' }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const {
    assignOrderId,
    assignTarget,
    assignType,
    assignWorker,
    availableStaffList,
    getInitials,
    isAssigning,
    showAssignModal,
} = inject(laborPageKey)
</script>
