<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Order Status Control</h2>
                <p class="text-sm text-gray-400 mt-1">Track and control order lifecycle — Ready → Dispatched → In Transit (Completion by Driver PoD)</p>
            </div>
            <div class="flex gap-2">
                <select v-model="statusFilter" class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-gray-900 dark:text-white text-sm">
                    <option class="bg-white dark:bg-gray-800" value="">All Statuses</option>
                    <option class="bg-white dark:bg-gray-800" value="ready">Ready for Dispatch</option>
                    <option class="bg-white dark:bg-gray-800" value="dispatched">Dispatched</option>
                    <option class="bg-white dark:bg-gray-800" value="in-transit">In Transit</option>
                    <option class="bg-white dark:bg-gray-800" value="delivered">Delivered (PoD)</option>
                </select>
                <button @click="syncStatus" class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors text-sm">
                    <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': syncing }">refresh</span> {{ syncing ? 'Syncing...' : syncDone ? '✓ Synced' : 'Sync Status' }}
                </button>
            </div>
        </div>

        <!-- Status Pipeline -->
        <div class="glass-panel rounded-xl p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-gray-900 dark:text-white text-sm">Dispatch Pipeline Overview</h3>
                <span class="text-xs text-gray-400">Today: {{ new Date().toLocaleDateString() }}</span>
            </div>

            <div class="flex items-center gap-0">
                <!-- Ready -->
                <div class="flex-1 relative">
                    <div class="bg-yellow-100 dark:bg-yellow-500/10 border border-yellow-500/20 rounded-l-xl p-4 text-center">
                        <div class="text-3xl font-bold text-yellow-500 dark:text-yellow-400 mb-1">{{ readyCount }}</div>
                        <div class="text-xs text-yellow-600 dark:text-yellow-300 font-bold">READY</div>
                        <div class="text-[10px] text-gray-500 mt-1">Awaiting dispatch</div>
                    </div>
                </div>
                <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

                <!-- Dispatched -->
                <div class="flex-1 relative">
                    <div class="bg-blue-100 dark:bg-blue-500/10 border border-blue-500/20 p-4 text-center">
                        <div class="text-3xl font-bold text-blue-500 dark:text-blue-400 mb-1">{{ dispatchedCount }}</div>
                        <div class="text-xs text-blue-600 dark:text-blue-300 font-bold">DISPATCHED</div>
                        <div class="text-[10px] text-gray-500 mt-1">Assigned to driver</div>
                    </div>
                </div>
                <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

                <!-- In Transit -->
                <div class="flex-1 relative">
                    <div class="bg-purple-100 dark:bg-purple-500/10 border border-purple-500/20 p-4 text-center">
                        <div class="text-3xl font-bold text-purple-500 dark:text-purple-400 mb-1">{{ inTransitCount }}</div>
                        <div class="text-xs text-purple-600 dark:text-purple-300 font-bold">IN TRANSIT</div>
                        <div class="text-[10px] text-gray-500 mt-1">On the road</div>
                    </div>
                </div>
                <span class="material-symbols-outlined text-gray-600 mx-1">chevron_right</span>

                <!-- Delivered -->
                <div class="flex-1 relative">
                    <div class="bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-r-xl p-4 text-center">
                        <div class="text-3xl font-bold text-green-500 dark:text-green-400 mb-1">{{ deliveredCount }}</div>
                        <div class="text-xs text-green-600 dark:text-green-300 font-bold">DELIVERED</div>
                        <div class="text-[10px] text-gray-500 mt-1">PoD confirmed</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SLA Compliance Tracking -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400">Ready → Assigned Time</span>
                    <span class="material-symbols-outlined text-[16px] text-yellow-400">timer</span>
                </div>
                <div class="text-xl font-bold text-gray-900 dark:text-white">—</div>
                <div class="text-[10px] text-gray-500">Target: &lt;10 min</div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400">On-Time Pickup %</span>
                    <span class="material-symbols-outlined text-[16px] text-blue-400">local_shipping</span>
                </div>
                <div class="text-xl font-bold text-gray-900 dark:text-white">{{ dispatchedCount + inTransitCount + deliveredCount > 0 ? Math.round(((dispatchedCount + deliveredCount) / (orders.length || 1)) * 100) + '%' : '—' }}</div>
                <div class="text-[10px] text-gray-500">SLA target: 95%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400">On-Time Dispatch %</span>
                    <span class="material-symbols-outlined text-[16px] text-purple-400">send</span>
                </div>
                <div class="text-xl font-bold text-gray-900 dark:text-white">{{ orders.length > 0 ? Math.round(((orders.length - readyCount) / orders.length) * 100) + '%' : '—' }}</div>
                <div class="text-[10px] text-gray-500">SLA target: 95%</div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400">Missed Window</span>
                    <span class="material-symbols-outlined text-[16px] text-red-400">report</span>
                </div>
                <div class="text-xl font-bold" :class="overdueCount > 0 ? 'text-red-400' : 'text-gray-900 dark:text-white'">{{ overdueCount }}</div>
                <div class="text-[10px] text-gray-500">Orders delayed today</div>
            </div>
        </div>

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

        <!-- SLA Alerts -->
        <div class="glass-panel rounded-xl p-5">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-red-400">notification_important</span>
                SLA Violation Alerts
            </h3>
            <div v-if="overdueOrders.length" class="space-y-3">
                <div v-for="order in overdueOrders" :key="order.id" class="p-3 bg-red-100 dark:bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-red-500 dark:text-red-400">error</span>
                        <div>
                            <div class="text-sm text-red-700 dark:text-red-300 font-bold">{{ order.id }} — ETA Overdue</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">Driver: {{ order.driver || 'Unassigned' }} • Status: {{ order.statusLabel }}</div>
                        </div>
                    </div>
                    <button @click="resolveAlert(order.id)" class="text-xs px-3 py-1.5 rounded-lg font-bold transition-colors border"
                        :class="alertResolved[order.id] ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-red-100 dark:bg-red-500/20 hover:bg-red-200 dark:hover:bg-red-500/30 text-red-700 dark:text-red-400 border-red-300 dark:border-red-500/30'">
                        {{ alertResolved[order.id] ? '✓ Resolved' : 'Resolve Now' }}
                    </button>
                </div>
            </div>
            <div v-else class="text-center py-6 text-gray-500 text-sm">
                <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
                No active SLA violations
            </div>
        </div>

        <!-- PoD Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showPoD" @close="showPoD = false">
                <template #title>Proof of Delivery — {{ podOrder?.id }}</template>
                <div class="space-y-4">
                    <div v-if="podLoading" class="py-10 text-center text-sm text-gray-400">
                        <span class="material-symbols-outlined text-[32px] block mb-2 animate-spin">progress_activity</span>
                        Loading proof of delivery...
                    </div>

                    <div v-else-if="podError" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                        {{ podError }}
                    </div>

                    <template v-else-if="podOrder">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                                <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Recipient</div>
                                <div class="text-sm font-bold text-white">{{ podOrder.pod?.signedBy || podOrder.customerName || 'Receiver' }}</div>
                                <div v-if="podOrder.customerPhone" class="text-[11px] text-gray-400 mt-1">{{ podOrder.customerPhone }}</div>
                            </div>
                            <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                                <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Delivered At</div>
                                <div class="text-sm font-bold text-white">{{ podOrder.pod?.time || 'Not recorded' }}</div>
                            </div>
                            <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                                <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Signature</div>
                                <div class="text-sm font-bold" :class="podOrder.pod?.signatureCaptured ? 'text-emerald-400' : 'text-gray-300'">
                                    {{ podOrder.pod?.signatureCaptured ? 'Captured' : 'Not captured' }}
                                </div>
                            </div>
                            <div class="rounded-xl bg-white/5 border border-white/10 p-3">
                                <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Photo Proof</div>
                                <div class="text-sm font-bold" :class="podPhotoCount > 0 ? 'text-emerald-400' : 'text-gray-300'">
                                    {{ podPhotoCount > 0 ? `${podPhotoCount} photo${podPhotoCount === 1 ? '' : 's'} attached` : 'No photos attached' }}
                                </div>
                            </div>
                        </div>

                        <div class="rounded-xl bg-white/5 border border-white/10 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Delivery Address</div>
                            <div class="text-sm text-white">{{ podOrder.pod?.location || podOrder.deliveryAddr || 'Not available' }}</div>
                        </div>

                        <div v-if="podOrder.pod?.notes" class="rounded-xl bg-white/5 border border-white/10 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">POD Notes</div>
                            <div class="text-sm text-gray-200 whitespace-pre-line">{{ podOrder.pod.notes }}</div>
                        </div>

                        <div v-if="podOrder.pod?.signature" class="rounded-xl bg-white/5 border border-white/10 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Signature Preview</div>
                            <div class="h-28 rounded-lg bg-white overflow-hidden flex items-center justify-center">
                                <img :src="podOrder.pod.signature" alt="POD signature" class="h-full w-full object-contain" />
                            </div>
                        </div>

                        <div class="rounded-xl bg-white/5 border border-white/10 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-gray-500 mb-3">Photo Proof</div>
                            <div v-if="podPhotos.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div v-for="(photo, index) in podPhotos" :key="`${podOrder.id}-${index}`" class="overflow-hidden rounded-lg border border-white/10 bg-black/20">
                                    <img :src="photo" :alt="`POD photo ${index + 1}`" class="h-40 w-full object-cover" />
                                </div>
                            </div>
                            <div v-else class="text-sm text-gray-400">No POD photos were uploaded for this order.</div>
                        </div>
                    </template>
                </div>
                <template #footer>
                    <button
                        v-if="podOrder && !podLoading"
                        @click="openSlipWithData('proofOfDelivery', podOrder, authStore.currentUser)"
                        class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5"
                    >
                        <span class="material-symbols-outlined text-[15px]">verified</span>
                        Open POD Slip
                    </button>
                    <button @click="showPoD = false" class="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-bold hover:bg-white/15 transition-colors">Close</button>
                </template>
            </BaseModal>
        </Teleport>

        <Teleport to="body">
            <BaseModal :isOpen="showActionModal" @close="closeActionModal">
                <template #title>
                    {{ actionModal.type === 'cancel' ? 'Cancel Order' : 'Escalate Order' }} — {{ actionModal.order?.id }}
                </template>

                <div class="space-y-4">
                    <div
                        class="rounded-xl border px-4 py-3"
                        :class="actionModal.type === 'cancel'
                            ? 'border-red-500/30 bg-red-500/10'
                            : 'border-yellow-500/30 bg-yellow-500/10'">
                        <div class="text-sm font-bold" :class="actionModal.type === 'cancel' ? 'text-red-300' : 'text-yellow-300'">
                            {{ actionModal.type === 'cancel'
                                ? 'This will remove the order from the active dispatcher flow.'
                                : 'This will create a real escalation for the Logistics Manager queue.' }}
                        </div>
                        <div class="text-xs text-gray-300 mt-1">
                            Current status: {{ actionModal.order?.statusLabel || '—' }}
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs uppercase tracking-wider text-gray-400 mb-2">
                            Reason
                        </label>
                        <textarea
                            v-model="actionModal.reason"
                            rows="4"
                            class="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-primary/50 resize-none"
                            :placeholder="actionModal.type === 'cancel'
                                ? 'Why should this order be cancelled?'
                                : 'Why does this order need escalation?'"
                        ></textarea>
                    </div>

                    <div v-if="actionModal.error" class="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                        {{ actionModal.error }}
                    </div>
                </div>

                <template #footer>
                    <button
                        @click="closeActionModal"
                        :disabled="actionSubmitting"
                        class="px-4 py-2 bg-white/10 text-white rounded-lg text-sm font-bold hover:bg-white/15 transition-colors disabled:opacity-50"
                    >
                        Close
                    </button>
                    <button
                        @click="submitActionModal"
                        :disabled="actionSubmitting"
                        class="px-4 py-2 rounded-lg text-sm font-bold text-white transition-colors disabled:opacity-50 flex items-center gap-2"
                        :class="actionModal.type === 'cancel'
                            ? 'bg-red-600 hover:bg-red-700'
                            : 'bg-yellow-500 hover:bg-yellow-600 text-black'"
                    >
                        <span v-if="actionSubmitting" class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                        {{ actionSubmitting
                            ? (actionModal.type === 'cancel' ? 'Cancelling...' : 'Escalating...')
                            : (actionModal.type === 'cancel' ? 'Confirm Cancel' : 'Confirm Escalation') }}
                    </button>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { getStoredAccessToken } from '@/config/api'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useToast } from '@/composables/useToast'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const store = useDispatcherStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()
const toast = useToast()
onMounted(async () => {
    await store.initialize().catch(() => {})
    await store.fetchActiveOrders().catch(() => {})
})

const searchQuery = ref('')
const statusFilter = ref('')
const syncing = ref(false)
const syncDone = ref(false)
const showPoD = ref(false)
const podOrder = ref(null)
const podLoading = ref(false)
const podError = ref('')
const orderMenu = ref(null)
const showActionModal = ref(false)
const actionSubmitting = ref(false)
const actionModal = ref({
    type: 'cancel',
    order: null,
    reason: '',
    error: '',
})
const alertResolved = ref({})
const alertRerouted = ref({})
const actionPending = ref({})
const transitionPending = ref({})
const bulkUpdating = ref(false)
const selectedOrderIds = ref(new Set())
const selectAllCheckbox = ref(null)

const orders = ref([])

const STATUS_TRANSITIONS = {
    dispatched: { backendStatus: 'ASSIGNED', label: 'Dispatched' },
    'in-transit': { backendStatus: 'IN_TRANSIT', label: 'In Transit' },
    delivered: { backendStatus: 'DELIVERED', label: 'Delivered' },
}

function mapStatusToUI(backendStatus) {
    const statusMap = {
        'CONFIRMED': 'ready',
        'ASSIGNED': 'dispatched',
        'IN_TRANSIT': 'in-transit',
        'DELIVERED': 'delivered',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase().replace('_', '-') || 'ready'
}

function mapStatusLabel(backendStatus) {
    const labelMap = {
        'CONFIRMED': 'Ready',
        'ASSIGNED': 'Dispatched',
        'IN_TRANSIT': 'In Transit',
        'DELIVERED': 'Delivered',
    }
    return labelMap[backendStatus] || backendStatus || 'Ready'
}

function formatTimeOnly(value) {
    if (!value || value === '—') return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return String(value)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function toUiOrder(o) {
    const podTime = o.pod?.time || o.pod?.timestamp || (o.deliveredAt ? new Date(o.deliveredAt).toLocaleString() : null)
    return {
        id: o.trackingCode || o.id,
        backendId: o.backendId || o.id,
        status: mapStatusToUI(o.status),
        statusLabel: mapStatusLabel(o.status),
        driver: o.driver || null,
        driverId: o.driverId || null,
        vehicle: o.vehicle || null,
        vehicleId: o.vehicleId || null,
        eta: o.eta || null,
        etaOverdue: o.etaOverdue || false,
        slaStatus: o.slaStatus || 'Pending',
        slaClass: o.slaClass || 'bg-gray-500/20 text-gray-400',
        lastUpdatedRaw: o.lastUpdated || o.deliveredAt || o.createdAt || null,
        lastUpdated: formatTimeOnly(o.lastUpdated || o.deliveredAt || o.createdAt),
        customerName: o.customerName || null,
        customerPhone: o.customerPhone || null,
        createdAt: o.createdAt || null,
        deliveredAt: o.deliveredAt || null,
        deliveryAddr: o.deliveryAddr || '',
        pickupAddr: o.pickupAddr || '',
        deliveryNotes: o.deliveryNotes || null,
        escalated: o.escalated || false,
        escalationId: o.escalationId || null,
        escalationStatus: o.escalationStatus || null,
        pod: o.pod ? {
            ...o.pod,
            time: podTime || o.pod.time || 'Delivered',
            timestamp: o.pod.timestamp || podTime || 'Delivered',
        } : null,
    }
}

watch(() => store.activeOrders, (list) => {
    const currentSelection = new Set(selectedOrderIds.value)
    orders.value = list.map(toUiOrder)
    const activeIds = new Set(orders.value.map(order => getOrderKey(order)))
    selectedOrderIds.value = new Set([...currentSelection].filter(id => activeIds.has(id)))
}, { immediate: true })

const readyCount = computed(() => orders.value.filter(o => o.status === 'ready').length)
const dispatchedCount = computed(() => orders.value.filter(o => o.status === 'dispatched').length)
const inTransitCount = computed(() => orders.value.filter(o => o.status === 'in-transit').length)
const deliveredCount = computed(() => orders.value.filter(o => o.status === 'delivered').length)
const overdueOrders = computed(() => orders.value.filter(o => o.etaOverdue || o.slaStatus === 'ESCALATED'))
const overdueCount = computed(() => overdueOrders.value.length)
const podPhotos = computed(() => Array.isArray(podOrder.value?.pod?.photos) ? podOrder.value.pod.photos : [])
const podPhotoCount = computed(() => podPhotos.value.length)

const statusTabs = computed(() => [
    { label: 'All', value: '', count: orders.value.length, activeClass: 'bg-white/10 text-gray-900 dark:text-white' },
    { label: 'Ready', value: 'ready', count: readyCount.value, activeClass: 'bg-yellow-500/20 text-yellow-400' },
    { label: 'Dispatched', value: 'dispatched', count: dispatchedCount.value, activeClass: 'bg-blue-500/20 text-blue-400' },
    { label: 'In Transit', value: 'in-transit', count: inTransitCount.value, activeClass: 'bg-purple-500/20 text-purple-400' },
    { label: 'Delivered', value: 'delivered', count: deliveredCount.value, activeClass: 'bg-green-500/20 text-green-400' },
])

const filteredOrders = computed(() => {
    return orders.value.filter(o => {
        if (statusFilter.value && o.status !== statusFilter.value) return false
        if (searchQuery.value) {
            const q = searchQuery.value.toLowerCase()
            const matchesId = o.id?.toLowerCase().includes(q)
            const matchesBackendId = o.backendId?.toLowerCase().includes(q)
            const matchesDriver = o.driver?.toLowerCase().includes(q)
            if (!matchesId && !matchesBackendId && !matchesDriver) return false
        }
        return true
    })
})

const selectedOrders = computed(() => orders.value.filter(order => selectedOrderIds.value.has(getOrderKey(order))))
const selectedReadyOrders = computed(() => selectedOrders.value.filter(order => order.status === 'ready'))
const selectedDispatchableReadyOrders = computed(() => selectedReadyOrders.value.filter(order => canDispatchOrder(order)))
const selectedDispatchedOrders = computed(() => selectedOrders.value.filter(order => order.status === 'dispatched'))
const selectedTransitOrders = computed(() => selectedOrders.value.filter(order => order.status === 'in-transit'))
const visibleSelectableOrders = computed(() => filteredOrders.value.filter(order => isSelectableOrder(order)))
const allVisibleSelected = computed(() =>
    visibleSelectableOrders.value.length > 0 &&
    visibleSelectableOrders.value.every(order => selectedOrderIds.value.has(getOrderKey(order)))
)
const someVisibleSelected = computed(() =>
    visibleSelectableOrders.value.some(order => selectedOrderIds.value.has(getOrderKey(order)))
)

watch([allVisibleSelected, someVisibleSelected], ([allSelected, partiallySelected]) => {
    if (!selectAllCheckbox.value) return
    selectAllCheckbox.value.indeterminate = !allSelected && partiallySelected
})

function getOrderKey(order) {
    return String(order?.backendId || order?.id || '')
}

function clearSelection(orderIds = null) {
    if (!orderIds) {
        selectedOrderIds.value = new Set()
        return
    }
    const next = new Set(selectedOrderIds.value)
    orderIds.forEach(id => next.delete(String(id)))
    selectedOrderIds.value = next
}

function isOrderSelected(order) {
    return selectedOrderIds.value.has(getOrderKey(order))
}

function canDispatchOrder(order) {
    return order.status === 'ready' && Boolean(order.driverId)
}

function isSelectableOrder(order) {
    if (order.status === 'ready') return canDispatchOrder(order) && !isTransitionPending(order)
    return ['dispatched', 'in-transit'].includes(order.status) && !isTransitionPending(order)
}

function toggleOrderSelection(order, checked) {
    const key = getOrderKey(order)
    const next = new Set(selectedOrderIds.value)
    if (checked) next.add(key)
    else next.delete(key)
    selectedOrderIds.value = next
}

function toggleSelectAllVisible(event) {
    const checked = Boolean(event?.target?.checked)
    const next = new Set(selectedOrderIds.value)
    visibleSelectableOrders.value.forEach(order => {
        const key = getOrderKey(order)
        if (checked) next.add(key)
        else next.delete(key)
    })
    selectedOrderIds.value = next
}

function getStatusDotClass(status) {
    const map = { 'ready': 'bg-yellow-500', 'dispatched': 'bg-blue-500', 'in-transit': 'bg-purple-500 animate-pulse', 'delivered': 'bg-green-500' }
    return map[status] || 'bg-gray-500'
}

function getStatusTextClass(status) {
    const map = { 'ready': 'text-yellow-400', 'dispatched': 'text-blue-400', 'in-transit': 'text-purple-400', 'delivered': 'text-green-400' }
    return map[status] || 'text-gray-400'
}

function setTransitionPending(order, pending) {
    const key = getOrderKey(order)
    transitionPending.value = { ...transitionPending.value, [key]: pending }
}

function isTransitionPending(order) {
    return Boolean(transitionPending.value[getOrderKey(order)]) || bulkUpdating.value
}

function applyTransitionLocally(order, newStatus) {
    const config = STATUS_TRANSITIONS[newStatus]
    if (!config) return

    order.status = newStatus
    order.statusLabel = config.label
    order.lastUpdated = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    if (newStatus === 'dispatched') {
        order.slaStatus = 'On Track'
        order.slaClass = 'bg-green-500/20 text-green-400'
    } else if (newStatus === 'in-transit') {
        order.slaStatus = 'In Transit'
        order.slaClass = 'bg-purple-500/20 text-purple-400'
    } else if (newStatus === 'delivered') {
        order.slaStatus = 'Delivered'
        order.slaClass = 'bg-green-500/20 text-green-400'
    }
}

async function transitionOrderStatus(order, newStatus, options = {}) {
    const { silent = false, refresh = true } = options
    const config = STATUS_TRANSITIONS[newStatus]
    if (!config) return false

    if (newStatus === 'dispatched' && !canDispatchOrder(order)) {
        const message = `Assign a driver before dispatching ${order.id}`
        if (!silent) {
            toast.warning(message)
        }
        throw new Error(message)
    }

    const orderId = order.backendId || order.id
    if (!orderId) {
        const message = 'No backend order ID available for transition'
        if (!silent) {
            console.error(message)
            toast.error(message)
        }
        throw new Error(message)
    }

    setTransitionPending(order, true)
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/transition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
            body: JSON.stringify({ next_status: config.backendStatus }),
        })

        if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || res.statusText || 'Status update failed')
        }

        applyTransitionLocally(order, newStatus)
        clearSelection([getOrderKey(order)])

        if (refresh) {
            await store.fetchActiveOrders().catch(() => {})
        }

        if (!silent) {
            toast.success(`${config.label} updated for ${order.id}`)
        }
        return true
    } catch (error) {
        console.error('Transition error:', error)
        if (!silent) {
            const message = error instanceof Error
                ? error.message
                : 'Network error while updating order status. Please try again.'
            toast.error(message)
        }
        throw error
    } finally {
        setTransitionPending(order, false)
    }
}

async function updateStatus(order, newStatus) {
    try {
        await transitionOrderStatus(order, newStatus)
    } catch (_) {}
}

async function applyBulkStatus(newStatus) {
    const statusGroups = {
        dispatched: selectedDispatchableReadyOrders.value,
        'in-transit': selectedDispatchedOrders.value,
        delivered: selectedTransitOrders.value,
    }
    const targets = statusGroups[newStatus] || []
    const label = STATUS_TRANSITIONS[newStatus]?.label || 'Updated'

    if (!targets.length) return

    bulkUpdating.value = true
    try {
        const results = await Promise.allSettled(
            targets.map(order => transitionOrderStatus(order, newStatus, { silent: true, refresh: false }))
        )

        const successCount = results.filter(result => result.status === 'fulfilled').length
        const failureCount = results.length - successCount

        await store.fetchActiveOrders().catch(() => {})

        if (failureCount === 0) {
            toast.success(`${label} updated for ${successCount} order${successCount === 1 ? '' : 's'}`)
        } else if (successCount > 0) {
            toast.warning(`${label} updated for ${successCount} orders. ${failureCount} failed and stayed selected.`)
        } else {
            toast.error(`Unable to update selected orders to ${label.toLowerCase()}.`)
        }
    } finally {
        bulkUpdating.value = false
    }
}

async function syncStatus() {
    syncing.value = true
    try {
        await store.fetchActiveOrders()
    } catch (_) {}
    syncing.value = false
    syncDone.value = true
    setTimeout(() => { syncDone.value = false }, 2000)
}

async function viewPoD(order) {
    podOrder.value = order
    podError.value = ''
    podLoading.value = true
    showPoD.value = true

    try {
        const orderId = order.backendId || order.id
        if (!orderId) throw new Error('Order ID missing for POD lookup.')
        const detailedOrder = await store.fetchOrderDetail(orderId)
        podOrder.value = toUiOrder(detailedOrder)
    } catch (error) {
        podError.value = error instanceof Error ? error.message : 'Unable to load proof of delivery.'
    } finally {
        podLoading.value = false
    }
}

function toggleOrderMenu(order) {
    const key = order.backendId || order.id
    orderMenu.value = orderMenu.value === key ? null : key
}

function setActionPending(order, pending) {
    const key = order.backendId || order.id
    actionPending.value = { ...actionPending.value, [key]: pending }
}

function isActionPending(order) {
    const key = order.backendId || order.id
    return Boolean(actionPending.value[key])
}

function canCancelOrder(order) {
    return ['ready', 'dispatched'].includes(order.status)
}

function canEscalateOrder(order) {
    return ['ready', 'dispatched', 'in-transit', 'delivered'].includes(order.status) && !order.escalated
}

function hasMenuActions(order) {
    return canCancelOrder(order) || canEscalateOrder(order)
}

function openActionModal(type, order) {
    actionModal.value = {
        type,
        order,
        reason: type === 'cancel'
            ? 'Dispatcher cancelled before route execution'
            : 'Order needs logistics manager review',
        error: '',
    }
    showActionModal.value = true
}

function closeActionModal() {
    showActionModal.value = false
    actionModal.value = {
        type: 'cancel',
        order: null,
        reason: '',
        error: '',
    }
}

async function cancelOrder(order) {
    orderMenu.value = null
    openActionModal('cancel', order)
}

async function submitCancel(order, reason) {
    const orderId = order.backendId || order.id
    if (!orderId) throw new Error('Order ID is missing. Please refresh and try again.')

    setActionPending(order, true)
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
            body: JSON.stringify({ reason }),
        })

        if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || res.statusText)
        }

        orders.value = orders.value.filter(o => (o.backendId || o.id) !== orderId)
        await store.fetchActiveOrders().catch(() => {})
        toast.success(`Order ${order.id} cancelled`)
    } catch (error) {
        console.error('Cancel error:', error)
        throw error
    } finally {
        setActionPending(order, false)
    }
}

async function escalateOrder(order) {
    orderMenu.value = null
    if (order.escalated) return
    openActionModal('escalate', order)
}

async function submitEscalation(order, reason) {
    const orderId = order.backendId || order.id
    if (!orderId) throw new Error('Order ID is missing. Please refresh and try again.')

    setActionPending(order, true)
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/escalate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
            body: JSON.stringify({ reason }),
        })

        if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            throw new Error(err.detail || res.statusText)
        }

        const escalation = await res.json().catch(() => null)
        order.escalated = true
        order.escalationId = escalation?.id || order.escalationId || null
        order.escalationStatus = escalation?.status || 'OPEN'
        order.slaStatus = 'ESCALATED'
        order.slaClass = 'bg-red-500/20 text-red-400'
        await store.fetchActiveOrders().catch(() => {})
        toast.success(`Order ${order.id} escalated`)
    } catch (error) {
        console.error('Escalation error:', error)
        throw error
    } finally {
        setActionPending(order, false)
    }
}

async function submitActionModal() {
    const order = actionModal.value.order
    const trimmedReason = actionModal.value.reason.trim()
    if (!order) return

    if (trimmedReason.length < 3) {
        actionModal.value.error = 'Please enter a short reason before continuing.'
        return
    }

    actionModal.value.error = ''
    actionSubmitting.value = true
    try {
        if (actionModal.value.type === 'cancel') {
            await submitCancel(order, trimmedReason)
        } else {
            await submitEscalation(order, trimmedReason)
        }
        closeActionModal()
    } catch (error) {
        const message = error instanceof Error ? error.message : 'Something went wrong. Please try again.'
        actionModal.value.error = message
        toast.error(message)
    } finally {
        actionSubmitting.value = false
    }
}

function resolveAlert(orderId) {
    alertResolved.value[orderId] = true
    const order = orders.value.find(o => o.id === orderId || o.backendId === orderId)
    if (order && order.status === 'ready') {
        updateStatus(order, 'dispatched')
        order.driver = 'Auto-assigned'
        order.vehicle = 'Van T-20'
    }
}

function rerouteAlert(orderId) {
    alertRerouted.value[orderId] = true
    const order = orders.value.find(o => o.id === orderId || o.backendId === orderId)
    if (order) {
        order.etaOverdue = false
        order.slaStatus = 'Rerouted'
        order.slaClass = 'bg-blue-500/20 text-blue-400'
    }
}
</script>
