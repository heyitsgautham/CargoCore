<template>
    <div class="glass-panel rounded-xl p-5">
        <div class="mb-4 flex items-center justify-between">
            <div>
                <h3 class="font-bold text-gray-900 dark:text-white">Dispatch Readiness Queue</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">Ready orders waiting for dispatcher AI review, including direct-dispatch recurring/vendor jobs.</p>
            </div>
            <div class="rounded-full bg-gray-100 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:bg-white/5 dark:text-gray-300">
                {{ dispatchQueue.length }} items
            </div>
        </div>

        <div v-if="dispatchQueue.length === 0" class="rounded-xl border border-dashed border-green-200 bg-green-50 p-8 text-center dark:border-green-500/20 dark:bg-green-500/10">
            <span class="material-symbols-outlined mb-2 block text-[32px] text-green-600 dark:text-green-400">check_circle</span>
            <div class="text-sm font-bold text-green-800 dark:text-green-300">No ready orders are waiting for AI assignment review</div>
            <div class="mt-1 text-xs text-green-700 dark:text-green-200">Released warehouse jobs and direct recurring/vendor non-packing jobs will appear here when they are ready.</div>
        </div>

        <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[920px] text-left text-sm">
                <thead class="bg-gray-50 text-[10px] uppercase tracking-wider text-gray-500 dark:bg-white/5 dark:text-gray-400">
                    <tr>
                        <th class="p-3">Order</th>
                        <th class="p-3">Warehouse Flow</th>
                        <th class="p-3">Vehicle</th>
                        <th class="p-3">AI Driver Match</th>
                        <th class="p-3">Risk</th>
                        <th class="p-3">Why AI Chose This</th>
                        <th class="p-3">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                    <tr v-for="item in dispatchQueue" :key="item.id" class="transition-colors hover:bg-gray-50 dark:hover:bg-white/5">
                        <td class="p-3 align-top">
                            <div class="font-bold text-gray-900 dark:text-white">{{ item.trackingCode || item.id }}</div>
                            <div class="mt-1 flex items-center gap-2">
                                <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="priorityBadgeClass(item.priority)">
                                    {{ item.priority || 'NORMAL' }}
                                </span>
                                <span class="text-[10px] text-gray-500 dark:text-gray-400">{{ item.type || 'Standard Move' }}</span>
                            </div>
                            <div class="mt-2 text-[11px] text-gray-500 dark:text-gray-400">
                                <div>Customer: <span class="text-gray-700 dark:text-gray-200">{{ item.customerName || 'Pending confirmation' }}</span></div>
                                <div>Deadline: <span class="text-gray-700 dark:text-gray-200">{{ formatDeadline(item.deadline) }}</span></div>
                            </div>
                        </td>
                        <td class="p-3 align-top">
                            <div class="text-xs font-medium text-gray-900 dark:text-white">{{ item.warehouse || 'Warehouse' }}</div>
                            <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                                <div>{{ isDirectDispatchAiCandidate(item) && !item.readyForDispatch ? 'Flow: Accepted by WM, dispatcher can plan now' : orderAllowsDirectVehicleSelection(item) ? 'Flow: Direct dispatcher vehicle selection' : 'Dock: Released by Warehouse Manager' }}</div>
                                <div>Pickup: {{ Number(item.packingAmount || 0) > 0 ? 'Packing items ready' : 'Non-packing pickup ready' }}</div>
                                <div>Destination: {{ item.deliveryAddr || 'Customer destination pending' }}</div>
                            </div>
                        </td>
                        <td class="p-3 align-top">
                            <div class="text-xs font-bold" :class="item.vehicleId ? 'text-blue-700 dark:text-blue-300' : (item.recommendedVehicle ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-600 dark:text-red-400')">
                                {{ item.vehicleId ? item.vehicle : item.recommendedVehicle?.label || 'No vehicle available' }}
                            </div>
                            <div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                                <div>{{ item.vehicleId ? 'Vehicle locked by warehouse' : orderAllowsDirectVehicleSelection(item) ? 'AI recommended for dispatcher selection' : 'Vehicle must be locked before dispatch' }}</div>
                                <div>Vehicle type: {{ item.vehicleType || item.recommendedVehicle?.type || 'General cargo' }}</div>
                                <div>Order weight: {{ item.weight || 0 }} kg</div>
                            </div>
                        </td>
                        <td class="p-3 align-top">
                            <div v-if="item.recommendedDriver" class="space-y-1">
                                <div class="font-bold text-gray-900 dark:text-white">{{ item.recommendedDriver.name }}</div>
                                <div class="text-[11px] text-gray-500 dark:text-gray-400">
                                    <div>Status: {{ item.recommendedDriver.status }}</div>
                                    <div>Shift used: {{ item.recommendedDriver.hours }}h</div>
                                    <div>Load: {{ item.recommendedDriver.load }}%</div>
                                </div>
                            </div>
                            <div v-else class="rounded-lg border border-red-200 bg-red-50 p-2 text-[11px] text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                                No driver currently available
                            </div>
                        </td>
                        <td class="p-3 align-top">
                            <span class="rounded-full px-2 py-0.5 text-[9px] font-bold" :class="riskBadgeClass(item.risk.level)">
                                {{ item.risk.level }}
                            </span>
                            <div class="mt-2 text-[11px] text-gray-500 dark:text-gray-400">{{ item.risk.text }}</div>
                        </td>
                        <td class="p-3 align-top">
                            <div class="text-[11px] leading-5 text-gray-600 dark:text-gray-300">
                                {{ item.recommendationReason }}
                            </div>
                        </td>
                        <td class="p-3 align-top">
                            <div v-if="deferredOrders.has(item.id)" class="flex flex-col gap-2">
                                <div class="rounded-lg border border-gray-200 bg-gray-50 p-2 text-[11px] font-bold text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
                                    Deferred for later review
                                </div>
                                <button @click="resumeReview(item.id)"
                                    class="rounded-lg border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-primary/20">
                                    Resume Review
                                </button>
                            </div>
                            <div v-else class="flex flex-col gap-2">
                                <button @click="assignRecommendedDriver(item)"
                                    :disabled="!orderHasAssignableResources(item) || assigningOrderId === item.id"
                                    class="rounded-lg border border-primary/30 bg-primary/15 px-3 py-1.5 text-xs font-bold text-primary transition-colors hover:bg-primary/25 disabled:cursor-not-allowed disabled:opacity-50">
                                    <span v-if="assigningOrderId === item.id">Assigning...</span>
                                    <span v-else-if="item.recommendedDriver && item.vehicleId">Assign {{ item.recommendedDriver.name }}</span>
                                    <span v-else-if="item.recommendedDriver && item.recommendedVehicle">Assign {{ item.recommendedDriver.name }} + {{ item.recommendedVehicle.label }}</span>
                                    <span v-else>No Resources Available</span>
                                </button>
                                <button @click="deferOrder(item.id)"
                                    class="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 transition-colors hover:bg-gray-50 dark:border-white/10 dark:bg-white/5 dark:text-gray-200 dark:hover:bg-white/10">
                                    Review Later
                                </button>
                                <div v-if="assignmentErrors[item.id]" class="text-[10px] font-bold text-red-600 dark:text-red-400">
                                    {{ assignmentErrors[item.id] }}
                                </div>
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
import { formatDeadline, orderHasAssignableResources } from './assignmentRules'
import { isDirectDispatchAiCandidate, orderAllowsDirectVehicleSelection } from '../dispatchRules'
import { smartAssignmentPageKey } from './smartAssignmentPageContext'

const {
    assignRecommendedDriver,
    assigningOrderId,
    assignmentErrors,
    deferOrder,
    deferredOrders,
    dispatchQueue,
    priorityBadgeClass,
    resumeReview,
    riskBadgeClass,
} = inject(smartAssignmentPageKey)
</script>
