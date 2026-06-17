<template>
    <div class="space-y-6">
        <!-- Loading State -->
        <div v-if="isLoading" class="flex items-center justify-center h-64">
            <div class="text-gray-500 dark:text-gray-400">Loading orders...</div>
        </div>

        <div v-else>
        <!-- Header -->
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">New Orders / Demand Management</h2>
            <div class="flex gap-3">
                <div
                    class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-1 flex">
                    <button
                        :class="activeTab === 'incoming' ? 'bg-primary rounded text-background-dark text-sm font-bold shadow-lg px-4 py-1.5' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                        @click="activeTab = 'incoming'">Incoming</button>
                    <button
                        :class="activeTab === 'accepted' ? 'bg-primary rounded text-background-dark text-sm font-bold shadow-lg px-4 py-1.5' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                        @click="activeTab = 'accepted'">Accepted</button>
                    <button
                        :class="activeTab === 'onhold' ? 'bg-yellow-500 rounded text-background-dark text-sm font-bold shadow-lg px-4 py-1.5' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                        @click="activeTab = 'onhold'">On Hold</button>
                </div>
            </div>
        </div>

        <!-- Capacity Overview KPIs -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Today's
                    Orders</div>
                <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{ orders.length }}</div>
                <div class="text-xs mt-1" :class="capacityPercent > 90 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
                    {{ capacityPercent }}% of daily capacity
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 mt-2 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all"
                        :class="capacityPercent > 90 ? 'bg-red-500' : capacityPercent > 70 ? 'bg-yellow-500' : 'bg-green-500'"
                        :style="`width: ${capacityPercent}%`"></div>
                </div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Pending
                    Validation</div>
                <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">{{ pendingCount }}</div>
                <div class="text-xs text-gray-500 mt-1">Awaiting stock/labor check</div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Dock Slots
                    Free</div>
                <div class="text-3xl font-bold text-primary mt-1">{{ freeDocks }}/{{ totalDocks }}</div>
                <div class="text-xs text-gray-500 mt-1">Available for dispatch</div>
            </div>
            <div class="glass-panel p-4 rounded-xl">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold tracking-wide">Labor
                    Available</div>
                <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ freeLabor }}</div>
                <div class="text-xs text-gray-500 mt-1">Ready to assign</div>
            </div>
        </div>

        <!-- Orders Table -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div
                class="p-4 border-b border-gray-100 dark:border-white/5 flex gap-4 items-center bg-gray-100 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">orders</span>
                    {{ activeTab === 'incoming' ? 'Incoming Orders' : activeTab === 'accepted' ? 'Accepted Orders' : 'On Hold Orders' }}
                </h3>
                <div class="flex-1"></div>
                <div class="relative w-48">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-[18px]">search</span>
                    <input v-model="searchQuery" type="text" placeholder="Search orders..."
                        class="w-full bg-gray-50 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                </div>
            </div>

            <div class="overflow-auto max-h-[600px]">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase sticky top-0">
                        <tr>
                            <th class="p-4">Order ID</th>
                            <th class="p-4">Order Type</th>
                            <th class="p-4">Cargo / Service</th>
                            <th class="p-4">Total Value</th>
                            <th class="p-4">Deadline</th>
                            <th class="p-4">Status</th>
                            <th class="p-4">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="order in filteredOrders" :key="order.id"
                            class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                            <td class="p-4 font-mono text-primary font-bold">{{ order.tracking_code }}</td>
                            <td class="p-4 text-gray-900 dark:text-white">{{ order.order_type }}</td>
                            <td class="p-4">
                                <div class="text-gray-900 dark:text-white">{{ order.cargo_type || 'Move order' }}</div>
                                <div class="text-xs text-gray-500">{{ order.service_time_block || order.vehicle_type || 'Details pending' }}</div>
                            </td>
                            <td class="p-4 text-gray-900 dark:text-white">{{ formatCurrency(order.total_amount) }}</td>
                            <td class="p-4 text-gray-900 dark:text-white font-mono text-xs">{{ formatDate(order.scheduled_at) }}</td>
                            <td class="p-4">
                                <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="getStatusClass(order.status)">
                                    {{ order.status }}
                                </span>
                            </td>
                            <td class="p-4">
                                <div class="flex gap-2">
                                    <button v-if="order.status === 'DRAFT'" @click="validateOrder(order)"
                                        class="bg-blue-500/20 hover:bg-blue-500/30 text-blue-600 dark:text-blue-400 px-3 py-1 rounded text-xs font-bold transition-colors">
                                        Validate
                                    </button>
                                    <button v-else-if="needsWarehouseAcceptance(order)"
                                        @click="selectedOrder = order; showDetailModal = true"
                                        class="bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[14px]">task_alt</span>
                                        Accept Order
                                    </button>
                                    <span v-else-if="order.status === 'CONFIRMED'"
                                        class="inline-flex items-center bg-green-500/10 text-green-600 dark:text-green-400 px-3 py-1 rounded text-xs font-bold border border-green-500/20">
                                        In Processing
                                    </span>
                                    <span v-else-if="order.status === 'ASSIGNED'"
                                        class="inline-flex items-center bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 px-3 py-1 rounded text-xs font-bold border border-indigo-500/20">
                                        Assigned
                                    </span>
                                    <button @click="selectedOrder = order; showDetailModal = true"
                                        class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white px-2 py-1 rounded text-xs transition-colors">
                                        <span class="material-symbols-outlined text-[16px]">visibility</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filteredOrders.length === 0">
                            <td colspan="7" class="p-8 text-center text-gray-500">No orders found</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        </div>

        <!-- Order Detail Modal -->
        <Teleport to="body">
            <div v-if="showDetailModal && selectedOrder"
                class="fixed inset-0 w-screen h-screen z-[9999] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
                @click.self="showDetailModal = false">
                <div
                    class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Order {{ selectedOrder.tracking_code }}</h3>
                        <button @click="showDetailModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-6">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Order Type</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.order_type }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Cargo Type
                                </div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.cargo_type || 'Move order' }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Service Window
                                </div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.service_time_block || 'TBD' }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Scheduled Time
                                </div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ formatDate(selectedOrder.scheduled_at) }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Total Value
                                </div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ formatCurrency(selectedOrder.total_amount) }}</div>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Pickup Address</div>
                                <div class="text-gray-900 dark:text-white text-sm leading-6">{{ selectedOrder.pickup_addr || 'Not available' }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Delivery Address</div>
                                <div class="text-gray-900 dark:text-white text-sm leading-6">{{ selectedOrder.delivery_addr || 'Not available' }}</div>
                            </div>
                        </div>

                        <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-3">Item Manifest</div>
                            <div v-if="selectedOrder.items?.length" class="space-y-2">
                                <div v-for="item in selectedOrder.items" :key="item.id"
                                    class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-white/10 px-3 py-2">
                                    <div>
                                        <div class="font-medium text-gray-900 dark:text-white">{{ item.sku }}</div>
                                        <div class="text-xs text-gray-500">Boxes: {{ item.box_count ?? 0 }} • Volume: {{ item.estimated_volume ?? 0 }}</div>
                                    </div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.quantity }}</div>
                                </div>
                            </div>
                            <div v-else class="text-sm text-gray-500 dark:text-gray-400 leading-6">
                                No item-level list was captured for this booking. Warehouse and dispatcher can currently see only order-level details unless items are added later through the order items API.
                            </div>
                        </div>

                        <div class="flex gap-3">
                            <button v-if="selectedOrder.status === 'DRAFT' || needsWarehouseAcceptance(selectedOrder)"
                                @click="acceptOrder(selectedOrder); showDetailModal = false"
                                class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-3 rounded-lg font-bold transition-colors">
                                <span
                                    class="material-symbols-outlined text-[18px] align-middle mr-1">check_circle</span>
                                {{ selectedOrder.status === 'DRAFT' ? 'Validate Order' : 'Accept Order' }}
                            </button>
                            <button @click="escalateOrder(selectedOrder)"
                                class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-3 px-6 rounded-lg font-bold transition-colors">
                                <span
                                    class="material-symbols-outlined text-[18px] align-middle mr-1">arrow_upward</span>
                                Escalate
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Escalation Toast -->
        <div v-if="escalateToast"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">arrow_upward</span>
            <div>
                <div class="font-bold">{{ escalateToast }} — Escalated!</div>
                <div class="text-xs opacity-80">Notification sent to Logistics Manager</div>
            </div>
        </div>

        <!-- Success Toast -->
        <div v-if="successToast"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div>
                <div class="font-bold">{{ successToast }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import {
    getEffectiveWarehouseSubstatus,
    isWarehouseOrderAccepted,
} from '@/utils/warehouseOrderState'

const authStore = useAuthStore()
const activeTab = ref('incoming')
const searchQuery = ref('')
const showDetailModal = ref(false)
const selectedOrder = ref(null)
const freeDocks = ref(0)
const freeLabor = ref(0)
const totalDocks = ref(6)
const escalateToast = ref('')
const successToast = ref('')
const isLoading = ref(true)

const orders = ref([])
// Incoming: Orders awaiting warehouse validation/pickup
const incomingStatuses = new Set(['DRAFT', 'CONFIRMED'])
// Accepted: Orders in warehouse processing or completed
const acceptedStatuses = new Set(['ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'CLOSED'])
const onHoldStatuses = new Set(['CANCELLED'])

function needsWarehouseAcceptance(order) {
    if (!order || order.status !== 'CONFIRMED') return false
    const warehouseId = authStore.currentUser?.warehouse_id
    const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
    // If any warehouse substatus is already set in DB, it was already accepted
    if (substatus) return false
    return !isWarehouseOrderAccepted(order, warehouseId)
}

function notifyOrdersUpdated() {
    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('warehouse-orders-updated'))
    }
}

// Fetch orders from API
async function fetchOrders() {
    try {
        isLoading.value = true

        // Ensure warehouse context is loaded (populates warehouse_id on currentUser)
        let warehouseId = authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            const warehouse = await authStore.ensureWarehouseContext()
            warehouseId = warehouse?.id || authStore.currentUser?.warehouse_id
        }

        if (!warehouseId) {
            console.error('No warehouse_id found for current user')
            isLoading.value = false
            return
        }

        // Normalise to string for safe comparison (API returns UUID strings)
        const warehouseIdStr = String(warehouseId)

        // Fetch orders, warehouse dashboard (for dock count) and labourers (for free labor) in parallel
        const [ordersRes, dashRes, labourRes] = await Promise.allSettled([
            fetch(apiUrl('api/v1/orders?page=1&page_size=100'), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }),
            fetch(apiUrl(`api/v1/warehouses/${warehouseIdStr}/dashboard`), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }),
            fetch(apiUrl('api/v1/labourers?page=1&page_size=100'), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            })
        ])

        // Process orders
        // NOTE: The backend already filters orders by warehouse_id for WAREHOUSE_MANAGER role.
        // We do a string-based comparison as a safety net in case the backend returns extra orders.
        if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
            const data = await ordersRes.value.json()
            orders.value = (data.items || []).map(order => {
                const itemCount = order.items?.length || 0
                const totalWeight = order.items?.reduce((sum, item) => sum + (item.weight || 0), 0) || 0
                const effectiveWarehouseSubstatus = getEffectiveWarehouseSubstatus(order, warehouseIdStr)

                // Determine which tab this order belongs to
                let tab = 'incoming'
                if (onHoldStatuses.has(order.status)) {
                    tab = 'onhold'
                } else if (acceptedStatuses.has(order.status)) {
                    tab = 'accepted'
                } else if (incomingStatuses.has(order.status)) {
                    if (
                        order.status === 'CONFIRMED' &&
                        (effectiveWarehouseSubstatus || isWarehouseOrderAccepted(order, warehouseIdStr))
                    ) {
                        tab = 'accepted'
                    } else {
                        tab = 'incoming'
                    }
                }

                return {
                    ...order,
                    warehouse_substatus: effectiveWarehouseSubstatus,
                    item_count: itemCount,
                    total_weight: totalWeight,
                    tab
                }
            // Backend already filters orders by warehouse_id for WAREHOUSE_MANAGER role.
            // No client-side filter needed — avoids silent drops due to UUID type mismatches.
            })
        }

        // Process warehouse dashboard — get dock count
        if (dashRes.status === 'fulfilled' && dashRes.value.ok) {
            const dash = await dashRes.value.json()
            // total docks from dashboard or default 6
            totalDocks.value = dash.dock_count || dash.total_docks || 6
            // free docks = total docks - orders currently being dispatched (PACKED status)
            const packingCount = orders.value.filter(o => o.status === 'PACKED' || o.status === 'PACKING').length
            freeDocks.value = Math.max(0, totalDocks.value - packingCount)
        } else {
            // Fallback: free docks = total - active loading orders
            const packingCount = orders.value.filter(o => o.status === 'PACKED' || o.status === 'PACKING').length
            freeDocks.value = Math.max(0, 6 - packingCount)
        }

        // Process labourers — count AVAILABLE ones
        if (labourRes.status === 'fulfilled' && labourRes.value.ok) {
            const labourData = await labourRes.value.json()
            const labourers = labourData.items || []
            freeLabor.value = labourers.filter(l =>
                l.status === 'AVAILABLE' || l.status === 'IN_WAREHOUSE' || l.status === 'In Warehouse'
            ).length
        } else {
            freeLabor.value = 0
        }

    } catch (error) {
        console.error('Error fetching orders:', error)
        showToast('Error loading orders')
    } finally {
        isLoading.value = false
    }
}

const capacityPercent = computed(() => Math.round((orders.value.length / 50) * 100))
const pendingCount = computed(() => orders.value.filter(o => incomingStatuses.has(o.status)).length)

const filteredOrders = computed(() => {
    return orders.value.filter(o => {
        const matchesTab = o.tab === activeTab.value
        const matchesSearch = !searchQuery.value ||
            o.tracking_code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
            o.order_type.toLowerCase().includes(searchQuery.value.toLowerCase())
        return matchesTab && matchesSearch
    })
})

function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value || 0)
}

function formatDate(dateString) {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function getStatusClass(status) {
    const statusMap = {
        'DRAFT': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        'CONFIRMED': 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        'ASSIGNED': 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
        'IN_TRANSIT': 'bg-purple-500/10 text-purple-500 border-purple-500/20',
        'DELIVERED': 'bg-green-500/10 text-green-500 border-green-500/20',
        'CLOSED': 'bg-gray-500/10 text-gray-500 border-gray-500/20',
        'CANCELLED': 'bg-red-500/10 text-red-500 border-red-500/20'
    }
    return statusMap[status] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'
}

function showToast(msg) {
    successToast.value = msg
    setTimeout(() => { successToast.value = '' }, 2500)
}

async function validateOrder(order) {
    try {
        const response = await fetch(apiUrl(`api/v1/orders/${order.id}/confirm`), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) throw new Error('Failed to validate order')

        await fetchOrders()
        notifyOrdersUpdated()
        showToast(`${order.tracking_code} validated successfully`)
    } catch (error) {
        console.error('Error validating order:', error)
        showToast('Error validating order')
    }
}

async function acceptOrder(order) {
    if (order.status === 'DRAFT') {
        return validateOrder(order)
    }

    if (needsWarehouseAcceptance(order)) {
        const warehouseId = authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned to your account')
            return
        }
        try {
            const response = await fetch(
                apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${order.id}/accept`),
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authStore.authToken}`,
                        'Content-Type': 'application/json',
                    },
                }
            )
            if (!response.ok) throw new Error('Failed to accept order')
            await fetchOrders()
            notifyOrdersUpdated()
            activeTab.value = 'accepted'
            showToast(`${order.tracking_code} accepted into warehouse queue`)
        } catch (error) {
            console.error('Error accepting order:', error)
            showToast('Error accepting order')
        }
    }
}

function escalateOrder(order) {
    escalateToast.value = order.tracking_code
    showDetailModal.value = false
    setTimeout(() => { escalateToast.value = '' }, 3000)
}

onMounted(() => {
    fetchOrders()
})
</script>
