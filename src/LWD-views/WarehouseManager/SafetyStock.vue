<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Safety Stock Alerts</h2>
            <div class="flex gap-2">
                <button @click="showThresholdModal = true"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">tune</span> Set Thresholds
                </button>
                <button @click="submitAllRestocks"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">shopping_cart</span> Restock All Critical
                </button>
            </div>
        </div>

        <!-- Overview Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl border-l-4 border-red-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Critical Alerts</div>
                <div class="text-3xl font-bold text-red-600 dark:text-red-400 mt-1">{{ criticalCount }}</div>
                <div class="text-xs text-red-600/60 dark:text-red-400/60 mt-1">Needs immediate restock</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-yellow-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Warnings</div>
                <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">{{ warningCount }}</div>
                <div class="text-xs text-yellow-600/60 dark:text-yellow-400/60 mt-1">Approaching threshold</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-green-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Normal Stock</div>
                <div class="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">{{ normalCount }}</div>
                <div class="text-xs text-green-600/60 dark:text-green-400/60 mt-1">Above safety level</div>
            </div>
            <div class="glass-panel p-4 rounded-xl border-l-4 border-blue-500">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold">Pending Restocks</div>
                <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-1">{{ pendingRestockCount }}</div>
                <div class="text-xs text-blue-600/60 dark:text-blue-400/60 mt-1">Awaiting delivery</div>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading safety stock data...</div>
        </div>

        <!-- Alert Cards Grid -->
        <div v-else>
            <div v-if="stockItems.length === 0" class="glass-panel p-8 rounded-xl text-center text-gray-500">
                <span class="material-symbols-outlined text-4xl mb-2 opacity-50">inventory</span>
                <p>No inventory items found. Add stock to the Inventory page first.</p>
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div v-for="item in stockItems" :key="item.sku"
                    class="glass-panel p-5 rounded-xl relative overflow-hidden transition-all hover:scale-[1.01]"
                    :class="item.level === 'critical' ? 'border border-red-500/30' : item.level === 'warning' ? 'border border-yellow-500/30' : 'border border-gray-100 dark:border-white/5'">
                    <div v-if="item.level === 'critical'"
                        class="absolute top-0 right-0 w-24 h-24 bg-red-500/10 rounded-full -mr-8 -mt-8 blur-xl"></div>
                    <div v-if="item.level === 'warning'"
                        class="absolute top-0 right-0 w-24 h-24 bg-yellow-500/10 rounded-full -mr-8 -mt-8 blur-xl"></div>

                    <div class="flex items-start justify-between mb-3 relative">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/10 flex items-center justify-center">
                                <span class="material-symbols-outlined text-gray-600 dark:text-gray-400">inventory_2</span>
                            </div>
                            <div>
                                <div class="font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                <div class="text-xs text-gray-500 font-mono">{{ item.sku }}</div>
                            </div>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                            :class="getLevelClass(item.level)">{{ item.level }}</span>
                    </div>

                    <div class="space-y-2 mb-4">
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Current Stock</span>
                            <span class="font-bold"
                                :class="item.level === 'critical' ? 'text-red-600 dark:text-red-400' : item.level === 'warning' ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-900 dark:text-white'">
                                {{ item.current }} {{ item.unit }}
                            </span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Safety Threshold</span>
                            <span class="text-gray-600 dark:text-gray-300">{{ item.threshold }} {{ item.unit }}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Category</span>
                            <span class="text-gray-600 dark:text-gray-300 text-xs">{{ item.category }}</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-gray-600 dark:text-gray-400">Location</span>
                            <span class="text-gray-600 dark:text-gray-300 text-xs font-mono">{{ item.location }}</span>
                        </div>
                    </div>

                    <div class="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden mb-4">
                        <div class="h-full rounded-full transition-all"
                            :class="item.level === 'critical' ? 'bg-red-500' : item.level === 'warning' ? 'bg-yellow-500' : 'bg-green-500'"
                            :style="`width: ${Math.min((item.current / (item.threshold * 3)) * 100, 100)}%`"></div>
                    </div>

                    <div class="flex gap-2">
                        <button v-if="item.restockStatus === 'none'" @click="requestRestock(item)"
                            class="flex-1 py-2 rounded text-xs font-bold transition-colors"
                            :class="item.level === 'critical' ? 'bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400' : 'bg-primary/20 hover:bg-primary/30 text-primary'">
                            Request Restock
                        </button>
                        <div v-else-if="item.restockStatus === 'requested'"
                            class="flex-1 py-2 rounded text-xs font-bold text-center bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            ✓ Restock Requested
                        </div>
                        <button @click="escalateItem(item)"
                            class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:text-white py-2 px-3 rounded text-xs transition-colors"
                            title="Escalate to Logistics Manager">
                            <span class="material-symbols-outlined text-[16px]">arrow_upward</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Restock History -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">history</span>
                    Restock Request History
                </h3>
            </div>
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase">
                    <tr>
                        <th class="p-4">Request ID</th>
                        <th class="p-4">Item</th>
                        <th class="p-4">SKU</th>
                        <th class="p-4">Qty</th>
                        <th class="p-4">Requested On</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="req in restockHistory" :key="req.backendId"
                        class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                        <td class="p-4 font-mono text-gray-600 dark:text-gray-300 text-xs">{{ req.id }}</td>
                        <td class="p-4 text-gray-900 dark:text-white">{{ req.item }}</td>
                        <td class="p-4 font-mono text-xs text-gray-500">{{ req.sku }}</td>
                        <td class="p-4 text-gray-600 dark:text-gray-300">{{ req.qty }}</td>
                        <td class="p-4 text-gray-500 text-xs font-mono">{{ req.requestedOn }}</td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="req.statusClass">{{ req.status }}</span>
                            <span v-if="req.escalated" class="ml-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-500/20 text-orange-500 border border-orange-500/30">ESCALATED</span>
                        </td>
                        <td class="p-4">
                            <div v-if="req.status === 'PENDING'" class="flex gap-2">
                                <button @click="approveRestock(req)"
                                    class="px-2 py-1 text-[10px] font-bold rounded bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 border border-green-500/20 transition-colors"
                                    :disabled="req.processing">✓ Approve</button>
                                <button @click="rejectRestock(req)"
                                    class="px-2 py-1 text-[10px] font-bold rounded bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 border border-red-500/20 transition-colors"
                                    :disabled="req.processing">✗ Reject</button>
                            </div>
                            <span v-else class="text-gray-400 dark:text-gray-600 text-xs">—</span>
                        </td>
                    </tr>
                    <tr v-if="restockHistory.length === 0">
                        <td colspan="7" class="p-8 text-center text-gray-500">No restock requests yet</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Threshold Config Modal -->
        <Teleport to="body">
            <div v-if="showThresholdModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showThresholdModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Configure Safety Thresholds</h3>
                        <button @click="showThresholdModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                        <div v-for="item in stockItems" :key="item.sku"
                            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                <div class="text-xs text-gray-500 font-mono">{{ item.sku }} • Current: {{ item.current }}</div>
                            </div>
                            <div class="flex items-center gap-2">
                                <label class="text-xs text-gray-600 dark:text-gray-400">Threshold:</label>
                                <input type="number" v-model.number="thresholdEdits[item.sku]"
                                    class="w-20 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center focus:outline-none focus:border-primary/50" />
                            </div>
                        </div>
                    </div>
                    <div class="p-6 border-t border-gray-100 dark:border-white/5">
                        <button @click="saveThresholds"
                            class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Save
                            Thresholds</button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Toasts -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
        <div v-if="escalateToast"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">arrow_upward</span>
            <div>
                <div class="font-bold">{{ escalateToast }} — Escalated!</div>
                <div class="text-xs opacity-80">Sent to Logistics Manager</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'

const authStore = useAuthStore()
const showThresholdModal = ref(false)
const toastMsg = ref('')
const escalateToast = ref('')
const loading = ref(false)

const stockItems = ref([])
const restockHistory = ref([])
const thresholdEdits = reactive({})

// Safety threshold per item: can be locally overridden
const thresholdOverrides = reactive({})

// Fetch real inventory and classify by safety stock level
async function fetchSafetyStock() {
    loading.value = true
    try {
        await authStore.ensureWarehouseContext()
        const warehouseId = authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || ''
        const invUrl = warehouseId ? `api/v1/inventory?page=1&page_size=100&warehouse_id=${warehouseId}` : 'api/v1/inventory?page=1&page_size=100'
        const reqUrl = warehouseId ? `api/v1/inventory/restock-requests?page=1&page_size=50&warehouse_id=${warehouseId}` : 'api/v1/inventory/restock-requests?page=1&page_size=50'

        const [invRes, reqRes] = await Promise.allSettled([
            fetch(apiUrl(invUrl), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }),
            fetch(apiUrl(reqUrl), {
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            })
        ])

        if (invRes.status === 'fulfilled' && invRes.value.ok) {
            const data = await invRes.value.json()
            const items = data.items || data || []

            stockItems.value = items.map(item => {
                const current = item.quantity || item.stock_quantity || item.quantity_available || item.quantity_on_hand || 0
                const apiThreshold = item.minimum_stock_level || item.safety_stock || item.reorder_point || 0
                const threshold = thresholdOverrides[item.sku] ?? (apiThreshold || Math.max(10, Math.floor(current * 0.25)))

                let level = 'normal'
                if (current <= threshold * 0.5) level = 'critical'
                else if (current <= threshold) level = 'warning'

                thresholdEdits[item.sku || item.id] = threshold

                return {
                    id: item.id,
                    sku: item.sku || item.id?.slice(0, 8).toUpperCase(),
                    name: item.name || item.product_name || 'Unknown Item',
                    category: item.category || item.product_category || 'General',
                    current,
                    threshold,
                    unit: item.unit || item.unit_of_measure || 'pcs',
                    location: item.location || item.warehouse_location || item.zone || '--',
                    level,
                    restockStatus: 'none',
                }
            })

            stockItems.value.forEach(item => {
                if (!thresholdEdits[item.sku]) thresholdEdits[item.sku] = item.threshold
            })
        }

        if (reqRes.status === 'fulfilled' && reqRes.value.ok) {
            const data = await reqRes.value.json()
            const restocks = Array.isArray(data) ? data : (data.items || [])
            
            restockHistory.value = restocks.map(m => {
                let statusClass = 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                if (m.status === 'APPROVED') {
                    statusClass = 'bg-green-500/10 text-green-500 border-green-500/20'
                } else if (m.status === 'REJECTED') {
                    statusClass = 'bg-red-500/10 text-red-500 border-red-500/20'
                }
                const notes = m.manager_notes || ''
                return {
                    backendId: m.id,
                    id: `RST-${(m.id || '').slice(0, 8).toUpperCase()}`,
                    item: m.item_name || 'Item',
                    sku: m.item_sku || 'N/A',
                    qty: m.quantity,
                    requestedOn: new Date(m.created_at).toLocaleString('en-CA', { hour12: false }).replace(',', ''),
                    status: m.status || 'PENDING',
                    statusClass,
                    escalated: notes.includes('[ESCALATED]'),
                    processing: false,
                }
            })

            // mark items as requested if they have a pending restock
            restocks.forEach(r => {
                const item = stockItems.value.find(i => i.id === r.item_id || i.sku === r.item_sku)
                if (item && r.status === 'PENDING') item.restockStatus = 'requested'
            })
        }

    } catch (error) {
        console.error('Error fetching safety stock:', error)
        showSuccess('Unable to load inventory data')
    } finally {
        loading.value = false
    }
}

const criticalCount = computed(() => stockItems.value.filter(i => i.level === 'critical').length)
const warningCount = computed(() => stockItems.value.filter(i => i.level === 'warning').length)
const normalCount = computed(() => stockItems.value.filter(i => i.level === 'normal').length)
const pendingRestockCount = computed(() => stockItems.value.filter(i => i.restockStatus === 'requested').length)

function getLevelClass(level) {
    if (level === 'critical') return 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
    if (level === 'warning') return 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border border-yellow-500/30'
    return 'bg-green-500/20 text-green-600 dark:text-green-400 border border-green-500/30'
}

function showSuccess(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

async function requestRestock(item) {
    if (item.restockStatus === 'requested') return
    item.restockStatus = 'requested'
    
    try {
        const qtyToOrder = item.threshold * 2
        const response = await fetch(apiUrl('api/v1/inventory/restock-requests'), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_id: item.id,
                quantity: qtyToOrder
            })
        })

        if (!response.ok) throw new Error('Failed to request restock')
        const data = await response.json()

        restockHistory.value.unshift({
            backendId: data.id,
            id: `RST-${(data.id || '').slice(0, 8).toUpperCase()}`,
            item: item.name,
            sku: item.sku,
            qty: qtyToOrder,
            requestedOn: new Date().toLocaleString('en-CA', { hour12: false }).replace(',', ''),
            status: 'PENDING',
            statusClass: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
            escalated: false,
            processing: false,
        })
        showSuccess(`Restock requested for ${item.name}`)
    } catch (e) {
        console.error(e)
        item.restockStatus = 'none'
        showSuccess(`Failed to request restock for ${item.name}`)
    }
}

function submitAllRestocks() {
    let count = 0
    stockItems.value.forEach(item => {
        if (item.level === 'critical' && item.restockStatus === 'none') {
            requestRestock(item)
            count++
        }
    })
    if (count === 0) showSuccess('All critical items already have restock requests')
}

async function approveRestock(req) {
    if (req.processing) return
    req.processing = true
    try {
        const response = await fetch(apiUrl(`api/v1/inventory/restock-requests/${req.backendId}/status`), {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'APPROVED', manager_notes: 'Approved by Warehouse Manager' })
        })
        if (!response.ok) throw new Error('Failed to approve')
        req.status = 'APPROVED'
        req.statusClass = 'bg-green-500/10 text-green-500 border-green-500/20'
        // Update the stock card to reflect increased stock
        await fetchSafetyStock()
        showSuccess(`✓ Approved — stock updated for ${req.item}`)
    } catch (e) {
        console.error(e)
        showSuccess('Failed to approve request')
    } finally {
        req.processing = false
    }
}

async function rejectRestock(req) {
    if (req.processing) return
    req.processing = true
    try {
        const response = await fetch(apiUrl(`api/v1/inventory/restock-requests/${req.backendId}/status`), {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'REJECTED', manager_notes: 'Rejected by Warehouse Manager' })
        })
        if (!response.ok) throw new Error('Failed to reject')
        req.status = 'REJECTED'
        req.statusClass = 'bg-red-500/10 text-red-500 border-red-500/20'
        const card = stockItems.value.find(i => i.sku === req.sku)
        if (card) card.restockStatus = 'none'
        showSuccess(`✗ Rejected restock for ${req.item}`)
    } catch (e) {
        console.error(e)
        showSuccess('Failed to reject request')
    } finally {
        req.processing = false
    }
}

async function escalateItem(item) {
    // Find the pending restock request for this item
    const req = restockHistory.value.find(r => r.sku === item.sku && r.status === 'PENDING')
    if (!req?.backendId) {
        // No pending request — guide user to request restock first
        showSuccess(`Request restock for ${item.name} first, then escalate`)
        return
    }
    try {
        const response = await fetch(apiUrl(`api/v1/inventory/restock-requests/${req.backendId}/escalate`), {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authStore.authToken}` }
        })
        if (!response.ok) throw new Error('Failed to escalate')
        req.escalated = true
        escalateToast.value = item.name
        setTimeout(() => { escalateToast.value = '' }, 3000)
    } catch (e) {
        console.error(e)
        showSuccess(`Failed to escalate ${item.name}`)
    }
}


function saveThresholds() {
    stockItems.value.forEach(item => {
        const newThreshold = thresholdEdits[item.sku]
        if (newThreshold !== undefined) {
            item.threshold = newThreshold
            thresholdOverrides[item.sku] = newThreshold
            if (item.current <= newThreshold * 0.5) item.level = 'critical'
            else if (item.current <= newThreshold) item.level = 'warning'
            else item.level = 'normal'
        }
    })
    showThresholdModal.value = false
    showSuccess('Thresholds updated — stock levels recalculated')
}

onMounted(() => {
    fetchSafetyStock()
})
</script>
