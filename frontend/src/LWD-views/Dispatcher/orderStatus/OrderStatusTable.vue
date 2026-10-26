<template>
    <!-- Order List Table -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center justify-between">
            <div class="flex gap-2">
                <button v-for="tab in statusTabs" :key="tab.value"
                    @click="statusFilter = tab.value"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                    :class="statusFilter === tab.value ? tab.activeClass : 'bg-gray-50 dark:bg-white/5 text-gray-400 hover:bg-white/10'">
                    {{ tab.label }} ({{ tab.count }})
                </button>
            </div>
            <div class="relative">
                <span class="material-symbols-outlined absolute left-2 top-2 text-gray-500 text-[16px]">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search orders..."
                    class="bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-1.5 pl-8 pr-4 text-gray-900 dark:text-white text-xs focus:outline-none focus:border-primary/50 w-48">
            </div>
        </div>

        <div class="px-4 py-3 border-b border-gray-200 dark:border-white/5 bg-gray-50/60 dark:bg-white/[0.03] flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div class="flex flex-wrap items-center gap-3 text-xs">
                <label class="inline-flex items-center gap-2 text-gray-700 dark:text-gray-200 font-semibold">
                    <input
                        ref="selectAllCheckbox"
                        type="checkbox"
                        :checked="allVisibleSelected"
                        :disabled="!visibleSelectableOrders.length || bulkUpdating"
                        @change="toggleSelectAllVisible"
                        class="w-4 h-4 rounded border-gray-300 dark:border-white/20 bg-white dark:bg-white/5 text-primary focus:ring-primary/40 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                    <span>Select all visible</span>
                </label>
                <span class="text-gray-500 dark:text-gray-400">
                    {{ selectedOrders.length }} selected
                </span>
                <button
                    v-if="selectedOrders.length"
                    @click="clearSelection()"
                    :disabled="bulkUpdating"
                    class="px-2.5 py-1 rounded-lg border border-gray-300 dark:border-white/10 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors disabled:opacity-50"
                >
                    Clear selection
                </button>
            </div>

            <div class="flex flex-wrap items-center gap-2">
                <button
                    v-if="selectedDispatchableReadyOrders.length"
                    @click="applyBulkStatus('dispatched')"
                    :disabled="bulkUpdating"
                    class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {{ bulkUpdating ? 'Processing...' : `Dispatch Selected (${selectedDispatchableReadyOrders.length})` }}
                </button>
                <button
                    v-if="selectedDispatchedOrders.length"
                    @click="applyBulkStatus('in-transit')"
                    :disabled="bulkUpdating"
                    class="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {{ bulkUpdating ? 'Processing...' : `Mark In Transit (${selectedDispatchedOrders.length})` }}
                </button>
                <button
                    v-if="selectedTransitOrders.length"
                    @click="applyBulkStatus('delivered')"
                    :disabled="bulkUpdating"
                    class="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                    {{ bulkUpdating ? 'Processing...' : `Mark Delivered (${selectedTransitOrders.length})` }}
                </button>
            </div>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                    <tr>
                        <th class="p-4 w-12">Select</th>
                        <th class="p-4">Order ID</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Driver</th>
                        <th class="p-4">Vehicle</th>
                        <th class="p-4">ETA</th>
                        <th class="p-4">SLA Status</th>
                        <th class="p-4">Last Updated</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                    <tr v-for="order in filteredOrders" :key="order.backendId || order.id"
                        class="hover:bg-gray-100 dark:hover:bg-white/5 transition-colors group">
                        <td class="p-4">
                            <input
                                type="checkbox"
                                :checked="isOrderSelected(order)"
                                :disabled="!isSelectableOrder(order)"
                                @change="toggleOrderSelection(order, $event.target.checked)"
                                class="w-4 h-4 rounded border-gray-300 dark:border-white/20 bg-white dark:bg-white/5 text-primary focus:ring-primary/40 disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                        </td>
                        <td class="p-4 font-mono text-gray-900 dark:text-white font-bold">{{ order.id }}</td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full" :class="getStatusDotClass(order.status)"></span>
                                <span class="text-xs font-bold" :class="getStatusTextClass(order.status)">{{ order.statusLabel }}</span>
                            </div>
                        </td>
                        <td class="p-4 text-gray-600 dark:text-gray-300 text-xs">{{ order.driver || '—' }}</td>
                        <td class="p-4 text-gray-600 dark:text-gray-300 text-xs">{{ order.vehicle || '—' }}</td>
                        <td class="p-4">
                            <span class="text-xs" :class="order.etaOverdue ? 'text-red-400' : 'text-gray-900 dark:text-white'">
                                {{ order.eta || '—' }}
                            </span>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-0.5 rounded text-[9px] font-bold" :class="order.slaClass">
                                {{ order.slaStatus }}
                            </span>
                        </td>
                        <td class="p-4 text-gray-500 text-xs">{{ order.lastUpdated }}</td>
                        <td class="p-4">
                            <div class="flex gap-1.5">
                                <button v-if="order.status === 'ready'"
                                    @click="updateStatus(order, 'dispatched')"
                                    :disabled="!canDispatchOrder(order) || isTransitionPending(order)"
                                    class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg text-xs font-bold transition-all hover:scale-105 shadow-md border border-blue-700 dark:border-blue-400 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100">
                                    {{ canDispatchOrder(order) ? 'Dispatch' : 'Assign Driver First' }}
                                </button>
                                <button v-if="order.status === 'dispatched'"
                                    @click="updateStatus(order, 'in-transit')"
                                    :disabled="isTransitionPending(order)"
                                    class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 dark:bg-purple-500 dark:hover:bg-purple-600 text-white rounded-lg text-xs font-bold transition-all hover:scale-105 shadow-md border border-purple-700 dark:border-purple-400 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100">
                                    Mark In Transit
                                </button>
                                <button v-if="order.status === 'in-transit'"
                                    @click="updateStatus(order, 'delivered')"
                                    :disabled="isTransitionPending(order)"
                                    class="px-3 py-1.5 bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600 text-white rounded-lg text-xs font-bold transition-all hover:scale-105 shadow-md border border-green-700 dark:border-green-400 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100">
                                    Mark Delivered
                                </button>
                                <button v-if="order.status === 'delivered'"
                                    @click="viewPoD(order)"
                                    class="px-3 py-1.5 bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600 text-white rounded-lg text-xs font-bold transition-all hover:scale-105 shadow-md border border-green-700 dark:border-green-400">
                                    View PoD
                                </button>
                                <!-- Assign Vehicle: shown for active orders with no vehicle assigned -->
                                <button
                                    v-if="['dispatched', 'in-transit'].includes(order.status) && !order.vehicleId"
                                    @click="openAssignVehicle(order)"
                                    class="p-1.5 rounded-lg bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 transition-colors"
                                    title="No vehicle assigned — click to assign">
                                    <span class="material-symbols-outlined text-[16px]">local_shipping</span>
                                </button>
                                <button
                                    v-if="hasMenuActions(order)"
                                    @click="toggleOrderMenu(order)"
                                    :disabled="isActionPending(order) || isTransitionPending(order)"
                                    class="p-1.5 hover:bg-gray-200 dark:hover:bg-white/10 rounded-lg text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white relative transition-colors disabled:opacity-50">
                                    <span class="material-symbols-outlined text-[16px]">more_vert</span>
                                    <div v-if="orderMenu === (order.backendId || order.id)" class="absolute top-full right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl z-20 w-40">
                                    <button
                                        v-if="canCancelOrder(order)"
                                        @click.stop="cancelOrder(order)"
                                        class="w-full text-left px-3 py-2 text-sm font-semibold text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
                                        :class="canEscalateOrder(order) ? 'rounded-t-lg' : 'rounded-lg'">Cancel Order</button>
                                    <button
                                        v-if="canEscalateOrder(order)"
                                        @click.stop="escalateOrder(order)"
                                        class="w-full text-left px-3 py-2 text-sm font-semibold text-yellow-600 dark:text-yellow-400 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
                                        :class="canCancelOrder(order) ? 'rounded-b-lg' : 'rounded-lg'">{{ order.escalated ? 'Escalated' : 'Escalate' }}</button>
                                    </div>
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
import { orderStatusPageKey } from './orderStatusPageContext'

const {
    allVisibleSelected,
    applyBulkStatus,
    bulkUpdating,
    canCancelOrder,
    canDispatchOrder,
    canEscalateOrder,
    cancelOrder,
    clearSelection,
    escalateOrder,
    filteredOrders,
    getStatusDotClass,
    getStatusTextClass,
    hasMenuActions,
    isActionPending,
    isOrderSelected,
    isSelectableOrder,
    isTransitionPending,
    openAssignVehicle,
    orderMenu,
    searchQuery,
    selectAllCheckbox,
    selectedDispatchableReadyOrders,
    selectedDispatchedOrders,
    selectedOrders,
    selectedTransitOrders,
    statusFilter,
    statusTabs,
    toggleOrderMenu,
    toggleOrderSelection,
    toggleSelectAllVisible,
    updateStatus,
    viewPoD,
    visibleSelectableOrders,
} = inject(orderStatusPageKey)
</script>
