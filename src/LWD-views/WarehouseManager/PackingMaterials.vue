<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Packing Materials & Returnable Assets</h2>
                <div class="flex items-center gap-1.5 mt-0.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                    <span class="text-xs text-green-600 dark:text-green-400 font-medium">Live · auto-refreshes every 30s</span>
                </div>
            </div>
            <div class="flex gap-2">
                <button @click="showIssueModal = true"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">output</span> Issue to Order
                </button>
                <button @click="showRestockModal = true"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">add</span> Request Restock
                </button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading packing materials...</div>
        </div>

        <template v-else>
        <!-- Inventory Cards — from real inventory data -->
        <div v-if="packingItems.length === 0" class="glass-panel p-8 rounded-xl text-center text-gray-500">
            <span class="material-symbols-outlined text-4xl mb-2 opacity-50">inventory_2</span>
            <p>No packing materials found in inventory. Add items via the Inventory page.</p>
        </div>
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div v-for="item in packingItems" :key="item.id"
                class="glass-panel p-4 rounded-xl text-center group hover:border-primary/30 transition-colors cursor-pointer"
                :class="item.stock <= item.threshold ? 'border-red-500/30 bg-red-900/5' : ''">
                <div class="text-3xl mb-2">{{ item.emoji }}</div>
                <div class="text-sm font-bold text-gray-900 dark:text-white leading-tight">{{ item.name }}</div>
                <div class="text-2xl font-bold mt-1"
                    :class="item.stock <= item.threshold ? 'text-red-600 dark:text-red-400' : 'text-primary'">{{ item.stock }}</div>
                <div class="text-[10px] text-gray-500 uppercase">{{ item.unit }}</div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all"
                        :class="item.stock <= item.threshold ? 'bg-red-500' : 'bg-primary'"
                        :style="`width: ${Math.min((item.stock / item.max) * 100, 100)}%`"></div>
                </div>
                <div v-if="item.stock <= item.threshold" class="text-[10px] text-red-600 dark:text-red-400 mt-1 font-bold animate-pulse">⚠ LOW STOCK</div>
                <div class="text-[10px] text-gray-500 font-mono mt-1">{{ item.sku }}</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Issuance Log -->
            <div class="lg:col-span-2 glass-panel rounded-xl overflow-hidden">
                <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-100 dark:bg-black/20">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary">inventory_2</span>
                        Material Issuance Log
                    </h3>
                    <div class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-0.5 flex">
                        <button
                            :class="logTab === 'issued' ? 'bg-primary rounded text-background-dark text-xs font-bold px-3 py-1' : 'px-3 py-1 text-gray-600 dark:text-gray-400 text-xs'"
                            @click="logTab = 'issued'">Issued</button>
                        <button
                            :class="logTab === 'reserved' ? 'bg-primary rounded text-background-dark text-xs font-bold px-3 py-1' : 'px-3 py-1 text-gray-600 dark:text-gray-400 text-xs'"
                            @click="logTab = 'reserved'">Reserved</button>
                    </div>
                </div>
                <div class="overflow-auto max-h-[400px]">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase sticky top-0">
                            <tr>
                                <th class="p-4">Order ID</th>
                                <th class="p-4">Material</th>
                                <th class="p-4">Qty</th>
                                <th class="p-4">Issued To</th>
                                <th class="p-4">Time</th>
                                <th class="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="log in filteredLog" :key="log.id" class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                                <td class="p-4 font-mono text-primary font-bold">{{ log.orderId }}</td>
                                <td class="p-4 text-gray-900 dark:text-white">{{ log.material }}</td>
                                <td class="p-4 text-gray-600 dark:text-gray-300">{{ log.qty }}</td>
                                <td class="p-4 text-gray-600 dark:text-gray-400">{{ log.issuedTo }}</td>
                                <td class="p-4 text-gray-500 text-xs font-mono">{{ log.time }}</td>
                                <td class="p-4">
                                    <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="log.statusClass">{{ log.status }}</span>
                                </td>
                            </tr>
                            <tr v-if="filteredLog.length === 0">
                                <td colspan="6" class="p-8 text-center text-gray-500">No {{ logTab }} records found</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Returnable Assets -->
            <div class="glass-panel rounded-xl overflow-hidden">
                <div class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                    <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-yellow-600 dark:text-yellow-400">assignment_return</span>
                        Returnable Assets
                    </h3>
                </div>
                <div class="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                    <div v-for="asset in returnableAssets" :key="asset.id"
                        class="p-3 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-lg hover:border-white/20 transition-colors">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ asset.name }}</div>
                                <div class="text-xs text-gray-500 font-mono">{{ asset.orderId }}</div>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold border" :class="asset.statusClass">{{ asset.status }}</span>
                        </div>
                        <div class="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                            <span>Issued: {{ asset.qty }} pcs</span>
                            <span>Returned: {{ asset.returned }} pcs</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                            <div class="bg-blue-500 h-full" :style="`width: ${asset.qty > 0 ? (asset.returned / asset.qty) * 100 : 0}%`"></div>
                        </div>
                        <div class="flex gap-2 mt-2">
                            <button @click="verifyReturn(asset)"
                                class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-1 rounded text-xs font-bold transition-colors"
                                :class="asset.status === 'Returned' ? 'opacity-50 cursor-not-allowed' : ''">
                                {{ asset.status === 'Returned' ? '✓ Verified' : 'Verify Return' }}
                            </button>
                            <button @click="flagAsset(asset)"
                                class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-1 px-3 rounded text-xs font-bold transition-colors"
                                :class="asset.flagged ? 'bg-red-500/40 border border-red-500/50' : ''">
                                {{ asset.flagged ? '🚩 Flagged' : 'Flag' }}
                            </button>
                        </div>
                    </div>
                    <div v-if="returnableAssets.length === 0" class="text-center text-gray-500 py-6 text-sm">
                        No returnable assets tracked yet
                    </div>
                </div>
            </div>
        </div>
        </template>

        <!-- Issue to Order Modal -->
        <Teleport to="body">
            <div v-if="showIssueModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showIssueModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-2xl border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Issue Materials to Order</h3>
                        <button @click="closeIssueModal" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4 overflow-y-auto flex-1">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Select Order</label>
                            <select v-model="issueForm.orderId" @change="onOrderSelected"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option value="">Select an active order...</option>
                                <option v-for="o in ordersAvailableForIssuance" :key="o.id" :value="o.tracking_code">
                                    {{ o.tracking_code }} — {{ o.status }}
                                </option>
                                <option v-if="ordersAvailableForIssuance.length === 0" disabled value="">
                                    No orders pending material issuance
                                </option>
                            </select>
                        </div>

                        <!-- Order Details & Requirements -->
                        <div v-if="selectedOrderDetails" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-500/30 rounded-lg p-4 space-y-3">
                            <div class="flex items-start justify-between">
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-1">Order Details</h4>
                                    <div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                        <div><span class="font-semibold">Tracking:</span> {{ selectedOrderDetails.tracking_code }}</div>
                                        <div><span class="font-semibold">Status:</span> {{ selectedOrderDetails.status }}</div>
                                        <div v-if="selectedOrderDetails.customer_name" class="capitalize">
                                            <span class="font-semibold">Customer:</span> {{ selectedOrderDetails.customer_name }}
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-xs text-gray-500 dark:text-gray-400">Estimated Items</div>
                                    <div class="text-2xl font-bold text-primary">{{ selectedOrderDetails.estimated_items || '—' }}</div>
                                </div>
                            </div>

                            <!-- Recommended Materials -->
                            <div v-if="recommendedMaterials.length > 0" class="pt-2 border-t border-blue-200 dark:border-blue-500/20">
                                <div class="text-xs font-bold text-blue-600 dark:text-blue-400 mb-2 flex items-center gap-1">
                                    <span class="material-symbols-outlined text-sm">lightbulb</span>
                                    Recommended Packing Materials
                                </div>
                                <div class="grid grid-cols-2 gap-2">
                                    <div v-for="rec in recommendedMaterials" :key="rec.id"
                                        class="text-xs bg-white dark:bg-gray-800/50 rounded p-2 flex items-center justify-between">
                                        <span class="text-gray-900 dark:text-white">{{ rec.emoji }} {{ rec.name }}</span>
                                        <span class="font-bold text-primary">{{ rec.suggestedQty }} {{ rec.unit }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Material Selection -->
                        <div v-if="issueForm.orderId">
                            <div class="flex items-center justify-between mb-2">
                                <label class="text-xs text-gray-600 dark:text-gray-400 block">Select Materials to Issue</label>
                                <button v-if="recommendedMaterials.length > 0" @click="applyRecommendedQuantities"
                                    class="text-xs bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1 rounded-lg font-semibold transition-colors">
                                    Apply Recommended
                                </button>
                            </div>
                            <div class="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto p-1">
                                <div v-for="item in packingItems" :key="item.id"
                                    class="bg-gray-50 dark:bg-white/5 border rounded-lg p-3 transition-colors"
                                    :class="issueForm.items[item.id] > 0 ? 'border-primary/50 bg-primary/5' : 'border-gray-200 dark:border-white/10'">
                                    <div class="flex items-center gap-2 mb-2">
                                        <span class="text-2xl">{{ item.emoji }}</span>
                                        <div class="flex-1">
                                            <div class="text-xs font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                            <div class="text-[10px] text-gray-500">Available: {{ item.stock }} {{ item.unit }}</div>
                                        </div>
                                    </div>
                                    <div class="relative">
                                        <input type="number" min="0" :max="item.stock" placeholder="0"
                                            v-model.number="issueForm.items[item.id]"
                                            class="w-full bg-white dark:bg-black/40 border rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center font-bold focus:outline-none focus:border-primary/50"
                                            :class="issueForm.items[item.id] > item.stock ? 'border-red-500' : 'border-gray-200 dark:border-white/10'" />
                                        <div v-if="issueForm.items[item.id] > item.stock" class="text-[10px] text-red-500 mt-1 text-center font-semibold">
                                            ⚠ Exceeds stock
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-else class="text-center py-8 text-gray-500 text-sm">
                            <span class="material-symbols-outlined text-4xl mb-2 opacity-30">inbox</span>
                            <p>Select an order to see recommended materials</p>
                        </div>

                        <div v-if="issueForm.orderId">
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-2">
                                <span>Issue To (Driver / Laborer)</span>
                                <span class="text-[10px] text-green-500 font-semibold">{{ issuableLabourers.length }} selectable</span>
                            </label>
                            <select v-model="issueForm.issuedTo"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option value="">Select staff...</option>
                                <option v-for="l in issuableLabourers" :key="l.id" :value="l.name || l.full_name">
                                    {{ l.name || l.full_name }} ({{ labourerIssueLabel(l) }})
                                </option>
                            </select>
                            <div v-if="issuableLabourers.length === 0" class="text-xs text-orange-500 mt-1 flex items-center gap-1">
                                <span class="material-symbols-outlined text-sm">warning</span>
                                No workers currently selectable. All staff are assigned to other orders or off duty.
                            </div>
                        </div>
                    </div>

                    <div class="p-6 border-t border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-black/20">
                        <button @click="submitIssue"
                            class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            :disabled="!canSubmitIssue || issuingMaterials">
                            <span v-if="issuingMaterials" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                            {{ issuingMaterials ? 'Issuing...' : 'Issue Materials' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Restock Modal -->
        <Teleport to="body">
            <div v-if="showRestockModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showRestockModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Request Material Restock</h3>
                        <button @click="showRestockModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div v-for="item in lowStockItems" :key="item.id"
                            class="flex items-center justify-between p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                            <div class="flex items-center gap-3">
                                <span class="text-2xl">{{ item.emoji }}</span>
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                    <div class="text-xs text-red-600 dark:text-red-400">Current: {{ item.stock }} / Threshold: {{ item.threshold }}</div>
                                </div>
                            </div>
                            <input type="number" v-model.number="restockForm[item.id]"
                                class="w-20 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center focus:outline-none focus:border-primary/50" />
                        </div>
                        <div v-if="lowStockItems.length === 0" class="text-center text-gray-500 py-4">
                            All materials are above threshold ✓
                        </div>
                        <div class="flex gap-3">
                            <button @click="submitRestock"
                                class="flex-1 bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                :disabled="restocking">
                                <span v-if="restocking" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                                {{ restocking ? 'Restocking...' : 'Submit Restock Request' }}
                            </button>
                            <button @click="escalateRestock"
                                class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-3 px-5 rounded-lg font-bold transition-colors">Escalate to Manager</button>
                        </div>
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
        <div v-if="errorMsg"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">error</span>
            <div class="font-bold">{{ errorMsg }}</div>
        </div>
        <div v-if="escalateMsg"
            class="fixed bottom-6 right-6 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">arrow_upward</span>
            <div>
                <div class="font-bold">Escalated to Logistics Manager!</div>
                <div class="text-xs opacity-80">{{ escalateMsg }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'

const authStore = useAuthStore()

const logTab = ref('issued')
const showIssueModal = ref(false)
const showRestockModal = ref(false)
const toastMsg = ref('')
const escalateMsg = ref('')
const errorMsg = ref('')
const loading = ref(false)
const issuingMaterials = ref(false)
const restocking = ref(false)

const issueForm = reactive({ orderId: '', issuedTo: '', items: {} })
const restockForm = reactive({})
const selectedOrderDetails = ref(null)
const recommendedMaterials = ref([])

// Live data
const allInventory = ref([])
const activeOrders = ref([])
const labourers = ref([])
const issuanceLogs = ref([])
const returnableAssets = ref([])
const MAX_CACHED_ISSUANCE_LOGS = 200

// Emoji map by category/name
function getEmoji(name = '', category = '') {
    const n = (name + category).toLowerCase()
    if (n.includes('box') || n.includes('carton')) return '📦'
    if (n.includes('bubble') || n.includes('wrap')) return '🫧'
    if (n.includes('tape') || n.includes('adhesive')) return '🔖'
    if (n.includes('blanket') || n.includes('pad')) return '🛡️'
    if (n.includes('crate') || n.includes('plastic')) return '📥'
    if (n.includes('stretch') || n.includes('film')) return '🔄'
    if (n.includes('label') || n.includes('sheet')) return '🏷️'
    if (n.includes('dolly') || n.includes('cart')) return '🛒'
    if (n.includes('corner') || n.includes('protector')) return '📐'
    if (n.includes('bag')) return '🛍️'
    if (n.includes('pallet')) return '🪵'
    return '📦'
}

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
}

function issuanceLogStorageKey(warehouseId) {
    return `warehouse-material-issuance-log:${warehouseId || 'unassigned'}`
}

function readCachedIssuanceLogs(warehouseId) {
    if (typeof window === 'undefined') return []

    try {
        const raw = window.localStorage.getItem(issuanceLogStorageKey(warehouseId))
        const parsed = raw ? JSON.parse(raw) : []
        return Array.isArray(parsed) ? parsed : []
    } catch {
        return []
    }
}

function writeCachedIssuanceLogs(warehouseId, logs) {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(
        issuanceLogStorageKey(warehouseId),
        JSON.stringify((logs || []).slice(0, MAX_CACHED_ISSUANCE_LOGS))
    )
}

function formatIssuanceTime(createdAt) {
    const date = createdAt ? new Date(createdAt) : new Date()
    if (Number.isNaN(date.getTime())) return ''
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

function normalizeIssuanceLog(log = {}) {
    const movementType = (log.movement_type || log.type || '').toUpperCase()
    const type = movementType === 'RESERVED' || log.type === 'reserved' ? 'reserved' : 'issued'
    // PACK movements are auto-deductions triggered by complete_packing; label them clearly
    const isPack = movementType === 'PACK'
    const createdAt = log.created_at || log.createdAt || new Date().toISOString()
    const orderId = log.reference_order_tracking || log.orderId || (
        typeof log.reference_order_id === 'string' ? log.reference_order_id.slice(0, 8) : null
    ) || 'N/A'
    const material = log.item_name || log.material || 'Item'
    const qty = Number(log.quantity ?? log.qty ?? 0)
    const issuedTo = log.issuedTo || log.performed_by_name || log.performedByName || 'System'

    const displayStatus = isPack ? 'Auto-Packed' : (type === 'issued' ? 'Issued' : 'Reserved')
    const displayStatusClass = isPack
        ? 'bg-blue-500/10 text-blue-500 border-blue-500/20'
        : (type === 'issued' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20')

    return {
        id: String(log.id || `${type}-${orderId}-${material}-${qty}-${createdAt}`),
        orderId,
        material,
        qty,
        issuedTo: isPack ? 'System (Packing)' : issuedTo,
        time: formatIssuanceTime(createdAt),
        createdAt,
        status: displayStatus,
        statusClass: displayStatusClass,
        type: isPack ? 'issued' : type,  // PACK shows in "Issued" tab
    }
}

function mergeIssuanceLogs(...logGroups) {
    const merged = new Map()

    for (const group of logGroups) {
        for (const log of group || []) {
            const normalized = normalizeIssuanceLog(log)
            const existing = merged.get(normalized.id)

            if (existing) {
                merged.set(normalized.id, {
                    ...existing,
                    ...normalized,
                    issuedTo: normalized.issuedTo || existing.issuedTo,
                })
                continue
            }

            merged.set(normalized.id, normalized)
        }
    }

    return [...merged.values()].sort((left, right) => {
        const leftTime = Date.parse(left.createdAt || '') || 0
        const rightTime = Date.parse(right.createdAt || '') || 0
        return rightTime - leftTime
    })
}

// Filter inventory to packing-related items (category or name match)
const packingItems = computed(() => {
    const packingKeywords = ['pack', 'wrap', 'box', 'carton', 'tape', 'label', 'blanket', 'crate', 'film', 'pallet', 'protector', 'bag', 'rope', 'bubble', 'foam', 'sheet']
    const items = allInventory.value.filter(item => {
        const text = ((item.name || '') + (item.category || '') + (item.product_category || '')).toLowerCase()
        return packingKeywords.some(kw => text.includes(kw))
    })
    // If no matches, show all inventory
    const source = items.length > 0 ? items : allInventory.value.slice(0, 12)
    return source.map(item => {
        const stock = item.quantity_on_hand || item.quantity || item.stock_quantity || item.quantity_available || 0
        const threshold = item.safety_stock || item.minimum_stock_level || item.reorder_point || Math.max(10, Math.floor(stock * 0.3))
        const max = item.max_capacity || item.maximum_stock || Math.max(stock * 2, threshold * 3, 1)
        return {
            id: item.id,
            sku: item.sku || item.id?.slice(0, 8).toUpperCase(),
            name: item.name || item.product_name || 'Item',
            emoji: getEmoji(item.name, item.category),
            stock,
            max,
            threshold,
            unit: item.unit || item.unit_of_measure || 'pcs',
        }
    })
})

function normalizeSku(value = '') {
    return String(value || '').trim().toUpperCase()
}

function inventoryIdTokenFromSku(sku = '') {
    return normalizeSku(sku).replace(/^PKG-/, '')
}

function keywordsForSku(sku = '') {
    const normalized = normalizeSku(sku)
    const keywordMap = {
        'PKG-CARTON': ['carton', 'box'],
        'PKG-BUBBLE-WRAP': ['bubble', 'wrap'],
        'PKG-PLASTIC-CRATE': ['crate', 'plastic'],
        'PKG-BLANKET': ['blanket', 'pad'],
        'PKG-WARDROBE-BOX': ['wardrobe', 'box'],
        'PKG-TAPE': ['tape'],
        'PKG-BOX': ['box', 'carton'],
        'FOAM-SHEET': ['foam', 'sheet'],
        'PKG-FOAM-SHEET': ['foam', 'sheet'],
    }
    const tokens = normalized
        .replace(/^PKG-/, '')
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .filter(token => token.length > 2)
    const phrase = normalized.replace(/^PKG-/, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
    return [...new Set([...(keywordMap[normalized] || []), ...tokens, phrase].filter(Boolean))]
}

const lowStockItems = computed(() => {
    const items = packingItems.value.filter(i => i.stock <= i.threshold)
    items.forEach(i => { if (!restockForm[i.id]) restockForm[i.id] = i.threshold * 2 })
    return items
})

const filteredLog = computed(() => issuanceLogs.value.filter(l => l.type === logTab.value))

// Tracking codes of orders that have already had materials issued
const issuedOrderTrackingCodes = computed(() => {
    return new Set(
        issuanceLogs.value
            .filter(l => l.type === 'issued')
            .map(l => l.orderId)
            .filter(id => id && id !== 'N/A')
    )
})

// Only show orders that haven't had materials issued yet
const ordersAvailableForIssuance = computed(() => {
    return activeOrders.value.filter(o => !issuedOrderTrackingCodes.value.has(o.tracking_code))
})

// Filter laborers by availability status
const availableLabourers = computed(() => {
    return labourers.value.filter(l => l.status === 'AVAILABLE')
})

const orderAssignedLabourers = computed(() => {
    return labourers.value.filter(l => l.status === 'ASSIGNED' && l.assigned_order_tracking === issueForm.orderId)
})

const offDutyLabourers = computed(() => {
    return labourers.value.filter(l => l.status === 'OFF_DUTY')
})

const issuableLabourers = computed(() => {
    const byId = new Map()
    for (const labourer of orderAssignedLabourers.value) byId.set(String(labourer.id), labourer)
    for (const labourer of availableLabourers.value) byId.set(String(labourer.id), labourer)
    return [...byId.values()]
})

function labourerIssueLabel(labourer) {
    if (labourer.assigned_order_tracking === issueForm.orderId) return 'Assigned to this order'
    return labourer.role || labourer.designation || 'Available Labourer'
}

function issuableItemsForSelectedOrder() {
    const byId = new Map(packingItems.value.map(item => [String(item.id), item]))
    for (const item of recommendedMaterials.value) {
        byId.set(String(item.id), item)
    }
    return [...byId.values()]
}

// Validation: check if any item qty exceeds available stock
const issueValidationErrors = computed(() => {
    const errors = []
    for (const item of issuableItemsForSelectedOrder()) {
        const qty = issueForm.items[item.id]
        if (qty && qty > 0 && qty > item.stock) {
            errors.push(`${item.name}: requested ${qty}, only ${item.stock} available`)
        }
    }
    return errors
})

const canSubmitIssue = computed(() => {
    if (!issueForm.orderId || !issueForm.issuedTo) return false
    if (issueValidationErrors.value.length > 0) return false
    // At least one item must be issued
    const hasItems = issuableItemsForSelectedOrder().some(item => {
        const qty = issueForm.items[item.id]
        return qty && qty > 0
    })
    return hasItems
})

// Calculate recommended materials based on order details
function calculateRecommendedMaterials(order) {
    if (!order) return []

    const recommendations = []

    // Estimate number of items (from order details or default)
    const numItems = order.estimated_items || order.item_count || 5
    const isFragile = order.is_fragile || false
    const isLarge = order.is_large || numItems > 10

    // Find materials by keywords
    const findMaterial = (keywords) => {
        return packingItems.value.find(item => {
            const text = item.name.toLowerCase()
            return keywords.some(kw => text.includes(kw))
        })
    }

    // Boxes/Cartons - base on items
    const box = findMaterial(['box', 'carton'])
    if (box) {
        recommendations.push({
            ...box,
            suggestedQty: Math.max(1, Math.ceil(numItems / 3))
        })
    }

    // Bubble wrap for fragile items
    const bubbleWrap = findMaterial(['bubble', 'wrap'])
    if (bubbleWrap && (isFragile || numItems > 5)) {
        recommendations.push({
            ...bubbleWrap,
            suggestedQty: Math.ceil(numItems / 2)
        })
    }

    // Tape - always needed
    const tape = findMaterial(['tape'])
    if (tape) {
        recommendations.push({
            ...tape,
            suggestedQty: Math.max(2, Math.ceil(numItems / 4))
        })
    }

    // Labels
    const label = findMaterial(['label'])
    if (label) {
        recommendations.push({
            ...label,
            suggestedQty: Math.max(1, Math.ceil(numItems / 2))
        })
    }

    return recommendations
}

async function onOrderSelected() {
    const selected = activeOrders.value.find(o => o.tracking_code === issueForm.orderId)
    selectedOrderDetails.value = selected
    recommendedMaterials.value = []

    if (!selected) return

    // Fetch the customer's actual material selections saved at booking time
    try {
        const res = await fetch(apiUrl(`api/v1/orders/${selected.id}/items`), {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json',
            },
        })
        if (res.ok) {
            const orderItems = await res.json()
            console.log(`[PackingMaterials] Order ${selected.tracking_code} items from DB:`, orderItems)
            const withQty = (orderItems || []).filter(item => item.quantity > 0)

            // Always stop here — either show customer-selected items or nothing.
            // Never fall through to the formula so we never show items the customer didn't pick.
            if (withQty.length === 0) {
                console.log(`[PackingMaterials] No items with qty>0 stored for ${selected.tracking_code} — customer selected no packing materials`)
                recommendedMaterials.value = []
                return
            }
            console.log(`[PackingMaterials] Items to resolve:`, withQty)

            const headers2 = { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }

            // Resolve each order item to a real WM inventory item
            const resolved = await Promise.all(withQty.map(async (item) => {
                const itemInventoryIdToken = inventoryIdTokenFromSku(item.sku)

                // 1. Exact SKU or legacy PKG-<inventory-id> match in local packing inventory
                let invItem = packingItems.value.find(p => normalizeSku(p.sku) === normalizeSku(item.sku))
                    || packingItems.value.find(p => normalizeSku(p.id) === itemInventoryIdToken)
                if (invItem) {
                    return { id: invItem.id, sku: item.sku, name: invItem.name, emoji: getEmoji(invItem.name, ''), unit: invItem.unit || 'pcs', suggestedQty: item.quantity, stock: invItem.stock ?? null }
                }

                // 2. Exact SKU or legacy PKG-<inventory-id> match in full local inventory
                const raw = allInventory.value.find(p => normalizeSku(p.sku) === normalizeSku(item.sku))
                    || allInventory.value.find(p => normalizeSku(p.id) === itemInventoryIdToken)
                if (raw) {
                    return { id: raw.id, sku: item.sku, name: raw.name, emoji: getEmoji(raw.name, ''), unit: raw.unit || 'pcs', suggestedQty: item.quantity, stock: raw.quantity_on_hand ?? null }
                }

                // 3. Keyword name match in packing inventory (PKG-* legacy SKUs)
                const keywords = keywordsForSku(item.sku)
                const kwMatch = packingItems.value.find(p => {
                    const text = `${p.name || ''} ${p.sku || ''} ${p.category || ''}`.toLowerCase()
                    return keywords.some(kw => text.includes(kw))
                })
                if (kwMatch) {
                    return { id: kwMatch.id, sku: item.sku, name: kwMatch.name, emoji: getEmoji(kwMatch.name, ''), unit: kwMatch.unit || 'pcs', suggestedQty: item.quantity, stock: kwMatch.stock ?? null }
                }

                // 4. Backend SKU lookup — handles cross-warehouse SKUs not in local allInventory
                try {
                    const skuRes = await fetch(apiUrl(`api/v1/inventory?sku=${encodeURIComponent(item.sku)}&page_size=1`), { headers: headers2 })
                    if (skuRes.ok) {
                        const skuData = await skuRes.json()
                        const found = (skuData.items || [])[0]
                        if (found) {
                            console.log(`[PackingMaterials] Resolved ${item.sku} via backend SKU lookup:`, found.name)
                            return { id: found.id, sku: item.sku, name: found.name, emoji: getEmoji(found.name, ''), unit: found.unit || 'pcs', suggestedQty: item.quantity, stock: found.quantity_on_hand ?? null }
                        }
                    }
                } catch { /* ignore */ }

                console.warn(`[PackingMaterials] Could not resolve inventory item for SKU: ${item.sku}`)
                return null
            }))

            recommendedMaterials.value = resolved.filter(Boolean)
            console.log(`[PackingMaterials] Resolved ${recommendedMaterials.value.length}/${withQty.length} items`)
            return
        }
    } catch { /* network error — show nothing */ }

    // API failed entirely — show nothing rather than guessing
    recommendedMaterials.value = []
}

function applyRecommendedQuantities() {
    recommendedMaterials.value.forEach(rec => {
        issueForm.items[rec.id] = rec.suggestedQty
    })
    showSuccess('Recommended quantities applied')
}

function closeIssueModal() {
    showIssueModal.value = false
    issueForm.orderId = ''
    issueForm.issuedTo = ''
    issueForm.items = {}
    selectedOrderDetails.value = null
    recommendedMaterials.value = []
}

async function fetchData() {
    loading.value = true
    try {
        await authStore.ensureWarehouseContext()
        const warehouseId = getWarehouseId()
        const cachedIssuanceLogs = readCachedIssuanceLogs(warehouseId)
        issuanceLogs.value = cachedIssuanceLogs
        
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        const [inventoryRes, ordersRes, labourRes, movementsRes, returnsRes] = await Promise.allSettled([
            fetch(apiUrl(`api/v1/inventory?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            fetch(apiUrl('api/v1/orders?page=1&page_size=100'), { headers }),
            fetch(apiUrl(`api/v1/labourers?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            fetch(apiUrl(`api/v1/inventory/movements?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers }),
            warehouseId ? fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/returns?page=1&page_size=20`), { headers }) : Promise.resolve({ ok: false })
        ])

        if (inventoryRes.status === 'fulfilled' && inventoryRes.value.ok) {
            const data = await inventoryRes.value.json()
            allInventory.value = data.items || data || []
        }

        if (ordersRes.status === 'fulfilled' && ordersRes.value.ok) {
            const data = await ordersRes.value.json()
            activeOrders.value = (data.items || []).filter(order => {
                const sameWarehouse = warehouseId ? order.warehouse_id === warehouseId : true
                return sameWarehouse && ['CONFIRMED', 'ASSIGNED', 'IN_TRANSIT'].includes(order.status)
            })
        }

        if (labourRes.status === 'fulfilled' && labourRes.value.ok) {
            const data = await labourRes.value.json()
            labourers.value = data.items || []
        }

        // Load issuance logs from inventory movements (ISSUE, PACK, RESERVED types)
        if (movementsRes.status === 'fulfilled') {
            if (movementsRes.value.ok) {
                const data = await movementsRes.value.json()
                const movements = Array.isArray(data) ? data : (data.items || [])
                const movementLogs = movements
                    .filter(m => {
                        const t = (m.movement_type || '').toUpperCase()
                        return t === 'ISSUE' || t === 'RESERVED' || t === 'PACK'
                    })
                    .map(m => normalizeIssuanceLog(m))

                issuanceLogs.value = mergeIssuanceLogs(movementLogs, cachedIssuanceLogs)
                writeCachedIssuanceLogs(warehouseId, issuanceLogs.value)
            } else {
                const errorText = await movementsRes.value.text()
                console.error('Failed to load movements:', errorText)
                if (cachedIssuanceLogs.length === 0) {
                    showError('Failed to load issuance logs. Please check your permissions.')
                }
            }
        } else if (movementsRes.status === 'rejected') {
            console.error('Error loading movements:', movementsRes.reason)
            if (cachedIssuanceLogs.length === 0) {
                showError('Error loading issuance logs. Please try again.')
            }
        }

        // Load returnable assets from returns endpoint
        if (returnsRes.status === 'fulfilled' && returnsRes.value && returnsRes.value.ok) {
            const data = await returnsRes.value.json()
            returnableAssets.value = (data.items || []).map(r => ({
                id: r.id,
                name: r.rma_code || 'Return Item',
                orderId: r.order_tracking || r.order_id?.slice(0, 8) || 'N/A',
                qty: 1,
                returned: r.status === 'COMPLETED' ? 1 : 0,
                missing: 0,
                status: r.status === 'COMPLETED' ? 'Returned' : (r.status === 'PENDING' ? 'Pending' : r.status),
                statusClass: r.status === 'COMPLETED'
                    ? 'bg-green-500/10 text-green-500 border-green-500/20'
                    : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
                flagged: false,
                gradeId: r.id
            }))
        }

    } catch (error) {
        console.error('Error fetching packing materials:', error)
    } finally {
        loading.value = false
    }
}

function showSuccess(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

function showError(msg) {
    errorMsg.value = msg
    setTimeout(() => { errorMsg.value = '' }, 3500)
}

async function verifyReturn(asset) {
    if (asset.status === 'Returned') return

    const warehouseId = getWarehouseId()
    if (!warehouseId || !asset.gradeId) {
        showError('Cannot verify return - missing warehouse')
        return
    }

    try {
        const response = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/returns/${asset.gradeId}/complete`), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (response.ok || response.status === 404) {
            asset.returned = asset.qty
            asset.missing = 0
            asset.status = 'Returned'
            asset.statusClass = 'bg-green-500/10 text-green-500 border-green-500/20'
            showSuccess(`${asset.name} return verified for ${asset.orderId}`)
        } else {
            showError('Failed to verify return')
        }
    } catch (error) {
        console.error('Error verifying return:', error)
        showError('Error verifying return')
    }
}

function flagAsset(asset) {
    asset.flagged = !asset.flagged
    if (asset.flagged) showSuccess(`${asset.name} flagged — notified Logistics Manager`)
}

async function submitIssue() {
    if (!canSubmitIssue.value) {
        if (issueValidationErrors.value.length > 0) {
            showError(issueValidationErrors.value[0])
        }
        return
    }

    issuingMaterials.value = true
    const issuedAt = new Date().toISOString()
    const warehouseId = getWarehouseId()

    // Find the selected order to get its ID
    const selectedOrder = activeOrders.value.find(o => o.tracking_code === issueForm.orderId)
    const referenceOrderId = selectedOrder?.id || null

    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        let successCount = 0
        let errorCount = 0
        const newLogs = []

        const allIssuableItems = issuableItemsForSelectedOrder()

        for (const item of allIssuableItems) {
            const qty = issueForm.items[item.id]
            if (qty && qty > 0) {
                // Call inventory movement API
                const response = await fetch(apiUrl('api/v1/inventory/movements'), {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        item_id: item.id,
                        movement_type: 'ISSUE',
                        quantity: qty,
                        reference_order_id: referenceOrderId
                    })
                })

                if (response.ok) {
                    successCount++
                    const movement = await response.json().catch(() => null)
                    newLogs.push(normalizeIssuanceLog(movement ? {
                        ...movement,
                        issuedTo: issueForm.issuedTo,
                    } : {
                        id: `local-${item.id}-${Date.now()}`,
                        movement_type: 'ISSUE',
                        quantity: qty,
                        reference_order_tracking: issueForm.orderId,
                        item_name: item.name,
                        issuedTo: issueForm.issuedTo,
                        created_at: issuedAt,
                    }))

                    // Update local stock count
                    const inv = allInventory.value.find(i => i.id === item.id)
                    if (inv) {
                        if (inv.quantity_on_hand !== undefined) inv.quantity_on_hand = Math.max(0, inv.quantity_on_hand - qty)
                        else if (inv.quantity !== undefined) inv.quantity = Math.max(0, inv.quantity - qty)
                        else if (inv.stock_quantity !== undefined) inv.stock_quantity = Math.max(0, inv.stock_quantity - qty)
                        else if (inv.quantity_available !== undefined) inv.quantity_available = Math.max(0, inv.quantity_available - qty)
                    }
                } else {
                    errorCount++
                    console.error('Failed to issue material:', item.name, await response.text())
                }
            }
        }

        if (newLogs.length > 0) {
            issuanceLogs.value = mergeIssuanceLogs(issuanceLogs.value, newLogs)
            writeCachedIssuanceLogs(warehouseId, issuanceLogs.value)
        }

        closeIssueModal()

        if (successCount > 0 && errorCount === 0) {
            showSuccess(`Materials issued successfully (${successCount} items)`)
        } else if (successCount > 0) {
            showSuccess(`Partially issued: ${successCount} items (${errorCount} failed)`)
        } else {
            showError('Failed to issue materials')
        }

    } catch (error) {
        console.error('Error issuing materials:', error)
        showError('Error issuing materials')
    } finally {
        issuingMaterials.value = false
    }
}

async function submitRestock() {
    restocking.value = true
    const warehouseId = getWarehouseId()

    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        let successCount = 0
        let errorCount = 0

        for (const item of lowStockItems.value) {
            const qty = restockForm[item.id]
            if (qty && qty > 0) {
                // Call inventory movement API with RESTOCK type
                const response = await fetch(apiUrl('api/v1/inventory/movements'), {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        item_id: item.id,
                        movement_type: 'RESTOCK',
                        quantity: qty,
                        reference_order_id: null
                    })
                })

                if (response.ok) {
                    successCount++
                    // Update local stock count
                    const inv = allInventory.value.find(i => i.id === item.id)
                    if (inv) {
                        if (inv.quantity_on_hand !== undefined) inv.quantity_on_hand += qty
                        else if (inv.quantity !== undefined) inv.quantity += qty
                        else if (inv.stock_quantity !== undefined) inv.stock_quantity += qty
                        else if (inv.quantity_available !== undefined) inv.quantity_available += qty
                    }
                } else {
                    errorCount++
                    console.error('Failed to restock:', item.name)
                }
            }
        }

        showRestockModal.value = false

        if (successCount > 0 && errorCount === 0) {
            showSuccess(`Restock completed (${successCount} items)`)
        } else if (successCount > 0) {
            showSuccess(`Partial restock: ${successCount} items (${errorCount} failed)`)
        } else if (errorCount === 0) {
            showSuccess('Restock request submitted')
        } else {
            showError('Failed to restock materials')
        }

    } catch (error) {
        console.error('Error restocking materials:', error)
        showError('Error restocking materials')
    } finally {
        restocking.value = false
    }
}

function escalateRestock() {
    showRestockModal.value = false
    escalateMsg.value = 'Low stock items escalated for urgent procurement'
    setTimeout(() => { escalateMsg.value = '' }, 3000)
}

const AUTO_REFRESH_INTERVAL_MS = 30_000
let autoRefreshTimer = null

async function silentRefreshInventory() {
    const warehouseId = getWarehouseId()
    const headers = {
        'Authorization': `Bearer ${authStore.authToken}`,
        'Content-Type': 'application/json'
    }
    try {
        const res = await fetch(apiUrl(`api/v1/inventory?page=1&page_size=100${warehouseId ? `&warehouse_id=${warehouseId}` : ''}`), { headers })
        if (res.ok) {
            const data = await res.json()
            allInventory.value = data.items || data || []
        }
    } catch { /* silent — don't interrupt user */ }
}

onMounted(() => {
    fetchData()
    autoRefreshTimer = setInterval(silentRefreshInventory, AUTO_REFRESH_INTERVAL_MS)
})

onUnmounted(() => {
    clearInterval(autoRefreshTimer)
})
</script>
