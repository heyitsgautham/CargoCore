<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Inventory Management</h2>
            <div class="flex gap-2">
                <button @click="showRequestMaterialModal = true"
                    class="bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-500/20 py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm">
                    <span class="material-symbols-outlined">add_shopping_cart</span> Request Material
                </button>
                <button @click="openScanner('scan')"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">qr_code_scanner</span> Scan Item
                </button>
            </div>
        </div>

        <InventoryStats />

        <InventoryTable />

        <EditSkuModal />

        <MoveSkuModal />

        <!-- Deprecated Local Scan Item Modal - Replaced by Global SmartScannerModal -->
        <ScanResultPanel />
        <div v-if="scanError"
            class="glass-panel rounded-xl p-4 border border-red-500/30 animate-fade-in flex items-center gap-3">
            <span class="material-symbols-outlined text-red-500">error</span>
            <div class="text-red-600 dark:text-red-400 text-sm flex-1">{{ scanError }}</div>
            <button @click="clearScan" class="text-gray-400 hover:text-gray-900 dark:hover:text-white"><span
                    class="material-symbols-outlined text-[18px]">close</span></button>
        </div>

        <AddStockModal />

        <CreateCategoryModal />

        <!-- Toasts -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>

        <RequestMaterialModal />

        <RejectedRequestsPanel />
    </div>
</template>

<script setup>
import InventoryStats from './inventory/InventoryStats.vue'
import InventoryTable from './inventory/InventoryTable.vue'
import EditSkuModal from './inventory/EditSkuModal.vue'
import MoveSkuModal from './inventory/MoveSkuModal.vue'
import ScanResultPanel from './inventory/ScanResultPanel.vue'
import AddStockModal from './inventory/AddStockModal.vue'
import CreateCategoryModal from './inventory/CreateCategoryModal.vue'
import RequestMaterialModal from './inventory/RequestMaterialModal.vue'
import RejectedRequestsPanel from './inventory/RejectedRequestsPanel.vue'
import { inventoryPageKey } from './inventory/inventoryPageContext'
import { ref, computed, reactive, inject, watch, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL } from '@/config/api'
import { useMaterialRequests } from './inventory/useMaterialRequests'
import { useStockItemActions } from './inventory/useStockItemActions'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const authStore = useAuthStore()
const openScanner = inject('openScanner')
const lastGlobalScan = inject('lastGlobalScan')

const searchQuery = ref('')
const categoryFilter = ref('')
const zoneFilter = ref('')
const showFastMoving = ref(false)
const showEditModal = ref(false)
const showMoveModal = ref(false)
const showAddModal = ref(false)
const showAddCategoryModal = ref(false)
const newCategoryName = ref('')
const customCategories = ref([])
const editItem = ref(null)
const moveItem = ref(null)
const scanResult = ref(null)
const scanError = ref('')
const toastMsg = ref('')
const loading = ref(false)
const newLocation = reactive({ zone: 'A', aisle: '01', rack: 'R1', shelf: 'S1', bin: 'B01' })
const addForm = reactive({ sku: '', name: '', stock: 0, weight: 0, zone: 'A', category: '' })

const inventory = ref([])
const categories = ref([])
const CATEGORY_STORAGE_PREFIX = 'warehouse-manager-inventory-categories'

const {
    showRequestMaterialModal,
    submittingRequest,
    myMaterialRequests,
    materialRequestForm,
    approvedMaterials,
    pendingMaterials,
    rejectedMaterials,
    fetchMyMaterialRequests,
    submitMaterialRequest,
    addApprovedMaterial,
} = useMaterialRequests({
    API_BASE,
    addForm,
    customCategories,
    persistCustomCategories,
    showAddModal,
    toastMsg,
})

// Watch for global scans and handle them here
watch(lastGlobalScan, (newScanObj) => {
    if (newScanObj) {
        lookupScan(newScanObj)
        // Reset it back to null so we can scan the same item twice if needed
        lastGlobalScan.value = null
    }
})

// Currency formatter for INR
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value || 0)
}

function getWarehouseId() {
    return authStore.currentUser?.warehouse_id || authStore.currentWarehouse?.id || null
}

function normalizeCategory(value) {
    const normalized = String(value || '').trim()
    if (!normalized || normalized.toLowerCase() === 'uncategorized') return 'General'
    return normalized
}

function normalizeCategoryList(values = []) {
    const seen = new Set()
    return values.reduce((list, value) => {
        const normalized = normalizeCategory(
            typeof value === 'string'
                ? value
                : (value?.category || value?.name || value?.label || '')
        )
        const key = normalized.toLowerCase()
        if (!seen.has(key)) {
            seen.add(key)
            list.push(normalized)
        }
        return list
    }, []).sort((a, b) => a.localeCompare(b))
}

function getCategoryStorageKey(warehouseId = getWarehouseId()) {
    return `${CATEGORY_STORAGE_PREFIX}:${warehouseId || 'default'}`
}

function loadCustomCategories(warehouseId = getWarehouseId()) {
    if (typeof window === 'undefined' || !warehouseId) {
        customCategories.value = []
        return
    }

    try {
        const raw = JSON.parse(window.localStorage.getItem(getCategoryStorageKey(warehouseId)) || '[]')
        customCategories.value = normalizeCategoryList(Array.isArray(raw) ? raw : [])
    } catch (error) {
        console.error('Error loading custom categories:', error)
        customCategories.value = []
    }
}

function persistCustomCategories(warehouseId = getWarehouseId()) {
    if (typeof window === 'undefined' || !warehouseId) return

    window.localStorage.setItem(
        getCategoryStorageKey(warehouseId),
        JSON.stringify(normalizeCategoryList(customCategories.value))
    )
}

const categoryOptions = computed(() => {
    const fromInventory = inventory.value.map(item => normalizeCategory(item.category))
    const merged = [...categories.value, ...customCategories.value, ...fromInventory, 'General']
    return normalizeCategoryList(merged.filter(Boolean))
})

function ensureCategoryAvailable(value, warehouseId = getWarehouseId()) {
    const category = normalizeCategory(value)
    if (!category) return ''

    const existing = categoryOptions.value.find(option => option.toLowerCase() === category.toLowerCase())
    if (existing) return existing

    customCategories.value = normalizeCategoryList([...customCategories.value, category])
    persistCustomCategories(warehouseId)
    return category
}

function createCategory() {
    const category = ensureCategoryAvailable(newCategoryName.value)
    if (!category) return

    addForm.category = category
    newCategoryName.value = ''
    showAddCategoryModal.value = false
    showToast(`Category "${category}" created`)

    // Notify other components (e.g. FloorPlan) so they can sync the new category
    window.dispatchEvent(new CustomEvent('warehouse-category-created', {
        detail: { category, warehouseId: getWarehouseId() }
    }))
}

async function fetchCategories() {
    const warehouseId = getWarehouseId()
    if (!warehouseId) return

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/inventory/categories?warehouse_id=${warehouseId}`, {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })
        if (!response.ok) return
        const data = await response.json()
        const rows = Array.isArray(data) ? data : (data?.items || data?.categories || [])
        categories.value = normalizeCategoryList(rows)
    } catch (error) {
        console.error('Error fetching categories:', error)
    }
}

// Fetch inventory from backend
async function fetchInventory() {
    loading.value = true
    try {
        const warehouseId = getWarehouseId()
        if (!warehouseId) {
            console.error('No warehouse_id found for current user')
            loading.value = false
            return
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/inventory?page=1&page_size=100&warehouse_id=${warehouseId}`, {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error(`Failed to fetch inventory: ${response.statusText}`)
        }

        const payload = await response.json()
        const items = Array.isArray(payload) ? payload : (payload.items || [])

        inventory.value = items.map((item) => {
            const stock = Number(item.quantity_on_hand ?? item.stock ?? 0)
            const threshold = Number(item.safety_stock ?? item.threshold ?? 100)
            const rawAisle = item.aisle || '01'
            const zoneFromAisle = rawAisle.includes('-') ? rawAisle.split('-')[0] : ''
            const aisle = rawAisle.includes('-') ? (rawAisle.split('-').pop() || '01') : rawAisle
            const zone = item.zone || zoneFromAisle || 'A'
            const shelf = item.shelf || 'S1'
            const category = normalizeCategory(item.category)

            return {
                ...item,
                stock,
                stockPercentage: Math.min((stock / (threshold || 100)) * 100, 100),
                fastMoving: item.fast_moving || false,
                dimensions: item.dimensions || '--',
                category,
                zone,
                aisle,
                rack: item.rack || 'R1',
                shelf,
                bin: item.bin || 'B01'
            }
        })
    } catch (error) {
        console.error('Error fetching inventory:', error)
    } finally {
        loading.value = false
    }
}

watch(
    () => authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null,
    async (warehouseId) => {
        inventory.value = []
        categories.value = []
        loadCustomCategories(warehouseId)

        if (!warehouseId) return

        await Promise.all([fetchInventory(), fetchCategories(), fetchMyMaterialRequests()])
    },
    { immediate: true }
)

const totalItems = computed(() => inventory.value.reduce((sum, i) => sum + i.stock, 0))
const lowStockCount = computed(() => inventory.value.filter(i => i.stock < 20).length)
const fastMovingCount = computed(() => inventory.value.filter(i => i.fastMoving).length)
const totalValue = computed(() => {
    const value = inventory.value.reduce((sum, i) => sum + (i.stock * (i.unit_price || 0)), 0)
    return formatCurrency(value)
})

const filteredInventory = computed(() => {
    return inventory.value.filter(item => {
        const matchesSearch = !searchQuery.value ||
            item.sku.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
            item.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
            `${item.zone}-${item.aisle}-${item.rack}-${item.shelf}-${item.bin}`.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchesCategory = !categoryFilter.value || item.category === categoryFilter.value
        const matchesZone = !zoneFilter.value || item.zone === zoneFilter.value
        const matchesFastMoving = !showFastMoving.value || item.fastMoving
        return matchesSearch && matchesCategory && matchesZone && matchesFastMoving
    })
})

function showToast(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

const {
    openEditModal,
    saveEdit,
    openMoveModal,
    confirmMove,
    printLabel,
    lookupScan,
    clearScan,
} = useStockItemActions({
    API_BASE,
    editItem,
    fetchInventory,
    getWarehouseId,
    inventory,
    moveItem,
    newLocation,
    scanError,
    scanResult,
    showEditModal,
    showMoveModal,
    showToast,
})

async function addNewStock() {
    const warehouseId = getWarehouseId()
    if (!warehouseId) {
        showToast('Warehouse is not linked to this account')
        return
    }

    try {
        const category = ensureCategoryAvailable(addForm.category || 'General', warehouseId)
        const response = await fetch(`${API_BASE_URL}/api/v1/inventory`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                warehouse_id: warehouseId,
                sku: addForm.sku.trim(),
                name: addForm.name.trim(),
                category,
                unit: 'pcs',
                quantity_on_hand: Math.max(Number(addForm.stock) || 0, 0),
                safety_stock: 0,
                aisle: `${addForm.zone}-01`,
                shelf: 'S1',
                bin: 'B01'
            })
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            const message = errData.detail || `Failed to add stock (${response.status})`
            throw new Error(typeof message === 'string' ? message : 'Failed to add stock')
        }

        await fetchInventory()
        await fetchCategories()
        window.dispatchEvent(new CustomEvent('warehouse-inventory-updated', {
            detail: {
                warehouseId,
                sku: addForm.sku.trim()
            }
        }))

        showAddModal.value = false
        addForm.sku = ''
        addForm.name = ''
        addForm.stock = 0
        addForm.weight = 0
        addForm.zone = 'A'
        addForm.category = ''
        newCategoryName.value = ''
        showToast('New stock item added to inventory')
    } catch (error) {
        console.error('Error adding stock:', error)
        showToast(error.message || 'Failed to add stock')
    }
}

provide(inventoryPageKey, {
    addApprovedMaterial,
    addForm,
    addNewStock,
    approvedMaterials,
    categoryFilter,
    categoryOptions,
    clearScan,
    confirmMove,
    createCategory,
    editItem,
    fastMovingCount,
    filteredInventory,
    loading,
    lowStockCount,
    materialRequestForm,
    moveItem,
    myMaterialRequests,
    newCategoryName,
    newLocation,
    openEditModal,
    openMoveModal,
    pendingMaterials,
    printLabel,
    rejectedMaterials,
    saveEdit,
    scanResult,
    searchQuery,
    showAddCategoryModal,
    showAddModal,
    showEditModal,
    showFastMoving,
    showMoveModal,
    showRequestMaterialModal,
    submitMaterialRequest,
    submittingRequest,
    totalItems,
    totalValue,
    zoneFilter,
})
</script>
