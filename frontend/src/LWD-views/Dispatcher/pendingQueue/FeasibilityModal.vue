<template>
    <!-- Feasibility Check Modal -->
    <Teleport to="body">
    <div v-if="showFeasibilityModal"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div class="bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-2xl p-6 w-full max-w-2xl shadow-2xl">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-yellow-400">verified</span>
                    Dispatch Feasibility Validator
                </h3>
                <button @click="showFeasibilityModal = false" class="text-gray-400 hover:text-gray-900 dark:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="space-y-4">
                <!-- Vehicle Capacity Check -->
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-400 text-[18px]">local_shipping</span>
                            Vehicle Capacity Check
                        </span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="feasCheckOrder?.weight <= 1000 ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'">
                            {{ feasCheckOrder?.weight <= 1000 ? 'PASS' : 'HEAVY' }}
                        </span>
                    </div>
                    <div class="grid grid-cols-3 gap-3 text-xs">
                        <div>
                            <span class="text-gray-500 block">Weight</span>
                            <span class="text-gray-900 dark:text-white">{{ formatCapacityValue(feasCheckOrder?.weight, feasCheckOrder?.hasWeight, 2000, 'kg') }}</span>
                            <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded mt-1">
                                <div class="h-full rounded" :class="(feasCheckOrder?.weight / 2000 * 100) > 70 ? 'bg-yellow-500' : 'bg-green-500'" :style="{ width: Math.min(100, (feasCheckOrder?.weight / 2000) * 100) + '%' }"></div>
                            </div>
                        </div>
                        <div>
                            <span class="text-gray-500 block">Volume</span>
                            <span class="text-gray-900 dark:text-white">{{ formatCapacityValue(feasCheckOrder?.volume, feasCheckOrder?.hasVolume, 12, 'm³') }}</span>
                            <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded mt-1">
                                <div class="h-full bg-green-500 rounded" :style="{ width: Math.min(100, (feasCheckOrder?.volume / 12) * 100) + '%' }"></div>
                            </div>
                        </div>
                        <div>
                            <span class="text-gray-500 block">Labor</span>
                            <span class="text-gray-900 dark:text-white">{{ feasCheckOrder?.laborCount || 0 }} crew needed</span>
                            <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded mt-1">
                                <div class="h-full rounded" :class="feasCheckOrder?.laborCount > 2 ? 'bg-yellow-500' : 'bg-green-500'" :style="{ width: Math.min(100, ((feasCheckOrder?.laborCount || 0) / 5) * 100) + '%' }"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Driver Availability -->
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                            <span class="material-symbols-outlined text-purple-400 text-[18px]">badge</span>
                            Driver Availability
                        </span>
                        <span class="px-2 py-0.5 rounded bg-green-500/20 text-green-400 text-[10px] font-bold">AVAILABLE</span>
                    </div>
                    <div class="grid grid-cols-3 gap-3 text-xs">
                        <div>
                            <span class="text-gray-500 block">Driver Status</span>
                            <span class="text-green-400 font-bold">Free</span>
                        </div>
                        <div>
                            <span class="text-gray-500 block">Working Hours</span>
                            <span class="text-gray-900 dark:text-white">4.2h / 10h max</span>
                        </div>
                        <div>
                            <span class="text-gray-500 block">HOS Compliance</span>
                            <span class="text-green-400 flex items-center gap-1">
                                <span class="material-symbols-outlined text-[12px]">check</span> Within limits
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Delivery Window -->
                <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-2">
                            <span class="material-symbols-outlined text-orange-400 text-[18px]">schedule</span>
                            Delivery Window Check
                        </span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                            :class="isDeadlineCritical(feasCheckOrder?.deadline) ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'">
                            {{ isDeadlineCritical(feasCheckOrder?.deadline) ? 'TIGHT' : 'ON TRACK' }}
                        </span>
                    </div>
                    <div class="grid grid-cols-3 gap-3 text-xs">
                        <div>
                            <span class="text-gray-500 block">Deadline</span>
                            <span class="text-gray-900 dark:text-white">{{ feasCheckOrder?.deadline }}</span>
                        </div>
                        <div>
                            <span class="text-gray-500 block">Remaining</span>
                            <span :class="isDeadlineCritical(feasCheckOrder?.deadline) ? 'text-red-400' : 'text-gray-900 dark:text-white'">{{ getTimeRemaining(feasCheckOrder?.deadline) }}</span>
                        </div>
                        <div>
                            <span class="text-gray-500 block">Priority</span>
                            <span class="text-gray-900 dark:text-white">{{ feasCheckOrder?.priority }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex gap-3 mt-6">
                <button @click="approveAndAssign"
                    class="flex-1 bg-primary hover:bg-primary-dark text-black font-bold py-2.5 rounded-lg transition-colors">
                    Approve & Assign
                </button>
                <button @click="holdFeasOrder"
                    class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 text-gray-900 dark:text-white font-bold py-2.5 rounded-lg transition-colors">
                    Hold Order
                </button>
                <button @click="escalateFeasOrder"
                    class="bg-red-500/10 dark:bg-red-500/20 hover:bg-red-500/20 dark:hover:bg-red-500/30 text-red-600 dark:text-red-400 font-bold py-2.5 px-4 rounded-lg transition-colors">
                    Escalate
                </button>
            </div>
            <div v-if="feasibilityToast" class="mt-3 text-center text-xs font-bold" :class="feasibilityToast.includes('Assigned') ? 'text-green-400' : feasibilityToast.includes('Hold') ? 'text-yellow-400' : 'text-red-400'">
                {{ feasibilityToast }}
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const {
    approveAndAssign,
    escalateFeasOrder,
    feasCheckOrder,
    feasibilityToast,
    formatCapacityValue,
    getTimeRemaining,
    holdFeasOrder,
    isDeadlineCritical,
    showFeasibilityModal,
} = inject(pendingQueuePageKey)
</script>
