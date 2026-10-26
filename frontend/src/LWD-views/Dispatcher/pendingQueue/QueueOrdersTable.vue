<template>
    <!-- Orders Table -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                    <tr>
                        <th class="p-4">Order ID</th>
                        <th class="p-4">Pickup Warehouse</th>
                        <th class="p-4">Weight / Volume</th>
                        <th class="p-4">Labor</th>
                        <th class="p-4">Priority</th>
                        <th class="p-4">Delivery Deadline</th>
                        <th class="p-4">Vehicle</th>
                        <th class="p-4">Feasibility</th>
                        <th class="p-4">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                    <tr v-for="order in filteredOrders" :key="order.id"
                        class="hover:bg-gray-100 dark:hover:bg-white/5 transition-colors group"
                        :class="order.type === 'PARCEL_PICKUP' ? 'bg-orange-50/40 dark:bg-orange-500/5 border-l-2 border-orange-400' : order.type === 'VENDOR' ? 'bg-blue-50/30 dark:bg-blue-500/5 border-l-2 border-blue-400' : order.loadingInProgress ? 'bg-amber-50/50 dark:bg-amber-500/5 opacity-80' : order.readyForDispatch ? 'bg-emerald-50/50 dark:bg-emerald-500/5' : ''">
                        <td class="p-4">
                            <div class="font-mono text-gray-900 dark:text-white font-bold">{{ order.displayId || order.trackingCode || order.id }}</div>
                            <span v-if="order.loadingInProgress"
                                class="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                                <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                                Loading in Progress
                            </span>
                            <span v-else-if="order.readyForDispatch"
                                class="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                Ready for Dispatch
                            </span>
                            <span v-if="order.type === 'PARCEL_PICKUP'"
                                class="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-500/30">
                                <span class="material-symbols-outlined text-[11px]">undo</span>
                                RETURN PICKUP
                            </span>
                        </td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <span
                                    class="material-symbols-outlined text-gray-500 text-[16px]">warehouse</span>
                                <span class="text-gray-600 dark:text-gray-300">{{ order.warehouse }}</span>
                            </div>
                        </td>
                        <td class="p-4">
                            <div class="text-gray-900 dark:text-white">{{ formatOrderWeight(order) }}</div>
                            <div class="text-[10px] text-gray-500">{{ formatOrderVolume(order) }}</div>
                        </td>
                        <td class="p-4">
                            <div class="flex items-center gap-1" v-if="order.laborCount > 0">
                                <span class="material-symbols-outlined text-blue-400 text-[16px]">groups</span>
                                <span class="text-blue-400 font-bold">{{ order.laborCount }}</span>
                            </div>
                            <span v-else class="text-gray-600">—</span>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] font-bold border"
                                :class="getPriorityClass(order.priority)">
                                {{ order.priority }}
                            </span>
                        </td>
                        <td class="p-4">
                            <div class="text-gray-900 dark:text-white text-xs">{{ order.deadline }}</div>
                            <div class="text-[10px]" :class="isDeadlineCritical(order.deadline) ? 'text-red-400' : 'text-gray-500'">
                                {{ getTimeRemaining(order.deadline) }}
                            </div>
                        </td>
                        <td class="p-4">
                            <div v-if="order.vehicleId" class="flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-emerald-400 text-[14px]">local_shipping</span>
                                <span class="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold">{{ order.vehicle }}</span>
                            </div>
                            <div v-else-if="orderAllowsDirectVehicleSelection(order)" class="flex items-center gap-1 text-blue-600 dark:text-blue-400 text-xs">
                                <span class="material-symbols-outlined text-[14px]">assignment_ind</span>
                                Dispatcher assigns
                            </div>
                            <div v-else class="flex items-center gap-1 text-amber-600 dark:text-amber-400 text-xs font-bold">
                                <span class="material-symbols-outlined text-[14px]">warning</span>
                                No vehicle
                            </div>
                        </td>
                        <td class="p-4">
                            <div v-if="order.feasibility === 'feasible'"
                                class="flex items-center gap-1 text-green-400 text-xs font-bold">
                                <span class="material-symbols-outlined text-[14px]">check_circle</span> Feasible
                            </div>
                            <div v-else-if="order.feasibility === 'infeasible'"
                                class="flex items-center gap-1 text-red-400 text-xs font-bold">
                                <span class="material-symbols-outlined text-[14px]">cancel</span> {{ order.failReason }}
                            </div>
                            <div v-else class="flex items-center gap-1 text-gray-500 text-xs">
                                <span class="material-symbols-outlined text-[14px]">pending</span> Unchecked
                            </div>
                        </td>
                        <td class="p-4">
                            <div class="flex gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
                                <button @click="runFeasibilityCheck(order)"
                                    class="p-1.5 bg-yellow-100 dark:bg-yellow-500/10 hover:bg-yellow-200 dark:hover:bg-yellow-500/20 rounded text-yellow-700 dark:text-yellow-400 transition-colors" title="Run Feasibility Check">
                                    <span class="material-symbols-outlined text-[16px]">verified</span>
                                </button>
                                <button @click="assignDriver(order)" :disabled="order.loadingInProgress"
                                    class="p-1.5 rounded transition-colors"
                                    :class="order.loadingInProgress ? 'bg-gray-100 dark:bg-white/5 text-gray-400 cursor-not-allowed opacity-50' : (order.vehicleId || orderAllowsDirectVehicleSelection(order)) ? 'bg-green-100 dark:bg-primary/10 hover:bg-green-200 dark:hover:bg-primary/20 text-green-700 dark:text-primary' : 'bg-amber-100 dark:bg-amber-500/10 hover:bg-amber-200 dark:hover:bg-amber-500/20 text-amber-700 dark:text-amber-400'"
                                    :title="order.loadingInProgress ? 'Awaiting warehouse release' : order.vehicleId ? 'Assign Driver' : orderAllowsDirectVehicleSelection(order) ? 'Assign Driver & Vehicle (vendor/service move — dispatcher selects)' : 'Assign Driver (no vehicle yet — warehouse must assign first)'">
                                    <span class="material-symbols-outlined text-[16px]">person_add</span>
                                </button>
                                <button @click="escalateOrder(order)" class="p-1.5 rounded transition-colors" :class="order.priority === 'URGENT' ? 'bg-yellow-100 dark:bg-yellow-500/10 hover:bg-yellow-200 dark:hover:bg-yellow-500/20 text-yellow-700 dark:text-yellow-400' : 'bg-blue-100 dark:bg-blue-500/10 hover:bg-blue-200 dark:hover:bg-blue-500/20 text-blue-700 dark:text-blue-400'" :title="order.priority === 'URGENT' ? 'Set Normal' : 'Escalate to Urgent'">
                                    <span class="material-symbols-outlined text-[16px]">{{ order.priority === 'URGENT' ? 'arrow_downward' : 'arrow_upward' }}</span>
                                </button>
                                <button @click="holdOrder(order)" class="p-1.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/15 rounded text-gray-600 dark:text-gray-400 transition-colors" title="Hold Order">
                                    <span class="material-symbols-outlined text-[16px]">pause_circle</span>
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const {
    assignDriver,
    escalateOrder,
    filteredOrders,
    formatOrderVolume,
    formatOrderWeight,
    getPriorityClass,
    getTimeRemaining,
    holdOrder,
    isDeadlineCritical,
    orderAllowsDirectVehicleSelection,
    runFeasibilityCheck,
} = inject(pendingQueuePageKey)
</script>
