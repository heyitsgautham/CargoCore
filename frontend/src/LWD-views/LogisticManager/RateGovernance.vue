<template>
    <div class="space-y-6">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Rate & Pricing Governance</h2>
                <p class="text-sm text-gray-500 mt-1">Central Authority for System-Wide Monetary Configuration</p>
            </div>

            <div class="flex items-center gap-4">
                <!-- One-time seed button — only visible when inventory has never been seeded -->
                <template v-if="!inventorySeeded">
                    <p v-if="seedError" class="text-xs text-red-500">{{ seedError }}</p>
                    <button @click="sendItemsToWarehouse" :disabled="isSeeding"
                        class="bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm text-sm">
                        <span class="material-symbols-outlined text-[18px]">{{ isSeeding ? 'hourglass_empty' : 'inventory_2' }}</span>
                        {{ isSeeding ? 'Sending...' : 'Send Items to Warehouse' }}
                    </button>
                </template>

                <p v-if="saveError" class="text-xs text-red-500">{{ saveError }}</p>
                <button v-if="!isEditMode" @click="isEditMode = true"
                    class="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm text-sm">
                    <span class="material-symbols-outlined text-[18px]">lock_open</span>
                    Unlock Edit Mode
                </button>

                <button v-else @click="saveAndLock" :disabled="isSaving"
                    class="bg-primary hover:bg-primary/90 disabled:opacity-60 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm text-sm">
                    <span class="material-symbols-outlined text-[18px]">{{ isSaving ? 'hourglass_empty' : 'cloud_upload' }}</span>
                    {{ isSaving ? 'Saving...' : 'Deploy & Lock Rates' }}
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <!-- Left Column: Revenue & Customers -->
            <div class="xl:col-span-2 flex flex-col gap-6">
                <CustomerChargesCard />

                <PayrollRatesCard />
            </div>

            <!-- Right Column: Fuel & Exceptions -->
            <div class="flex flex-col gap-6">

                <ExceptionsCard />

                <FuelReimbursementCard />

                <SeasonalRatesCard />

            </div>
        </div>

        <!-- Audit Note -->
        <div class="flex justify-center mt-4">
            <span
                class="text-xs text-gray-400 flex items-center gap-1 bg-gray-100 dark:bg-white/5 px-3 py-1 rounded-full"><span
                    class="material-symbols-outlined text-[14px]">history</span> Matrix last updated by sys_admin on Oct
                24, 09:41 AM</span>
        </div>

        <PendingMaterialRequests />

        <AddMaterialModal />
    </div>
</template>

<script setup>
import CustomerChargesCard from './rateGovernance/CustomerChargesCard.vue'
import PayrollRatesCard from './rateGovernance/PayrollRatesCard.vue'
import ExceptionsCard from './rateGovernance/ExceptionsCard.vue'
import FuelReimbursementCard from './rateGovernance/FuelReimbursementCard.vue'
import SeasonalRatesCard from './rateGovernance/SeasonalRatesCard.vue'
import PendingMaterialRequests from './rateGovernance/PendingMaterialRequests.vue'
import AddMaterialModal from './rateGovernance/AddMaterialModal.vue'
import { rateGovernancePageKey } from './rateGovernance/rateGovernancePageContext'
import { ref, computed, onMounted, provide } from 'vue'
import { useRates } from '@/composables/useRates'
import { getStoredAccessToken } from '@/config/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const isEditMode = ref(false)
const isSaving = ref(false)
const saveError = ref('')

// One-time inventory seeding — default false so button shows immediately on fresh DB
const inventorySeeded = ref(false)
const isSeeding = ref(false)
const seedError = ref('')

async function checkInventorySeeded() {
    seedError.value = '' // clear any stale error from previous navigation
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/rates/inventory-seeded`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
            const data = await res.json()
            inventorySeeded.value = data.seeded
        }
    } catch (e) {
        // silently fail — button stays visible, no error shown
    }
}

async function sendItemsToWarehouse() {
    isSeeding.value = true
    seedError.value = ''
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/rates/seed-inventory`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
            inventorySeeded.value = true
        } else {
            const err = await res.json().catch(() => ({}))
            seedError.value = err.detail || 'Failed to seed inventory'
        }
    } catch (e) {
        seedError.value = 'Network error. Please try again.'
    } finally {
        isSeeding.value = false
    }
}

const { rates, saveRates } = useRates()

// Materials as array (reactive, synced with rates)
const materialsArray = computed({
    get() {
        return Array.isArray(rates.value.materials) ? rates.value.materials : []
    },
    set(val) {
        rates.value.materials = val
    }
})

// Add Material Modal
const showAddMaterialModal = ref(false)
const newMaterial = ref({ name: '', rate: null, unit: 'pcs' })

function generateMaterialId(name) {
    return name.split(' ').map((w, i) => i === 0 ? w.toLowerCase() : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join('')
}

function addMaterial() {
    if (!newMaterial.value.name || !newMaterial.value.rate) return
    
    const id = generateMaterialId(newMaterial.value.name)
    const existing = materialsArray.value.find(m => m.id === id)
    if (existing) {
        alert('A material with this name already exists')
        return
    }
    
    materialsArray.value = [...materialsArray.value, {
        id,
        name: newMaterial.value.name,
        rate: newMaterial.value.rate,
        unit: newMaterial.value.unit
    }]
    
    showAddMaterialModal.value = false
    newMaterial.value = { name: '', rate: null, unit: 'pcs' }
}

function removeMaterial(index) {
    materialsArray.value = materialsArray.value.filter((_, i) => i !== index)
}

// Pending Material Requests
const pendingMaterialRequests = ref([])
const approvalRates = ref({})

async function fetchMaterialRequests() {
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/inventory/material-requests?status_filter=PENDING`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
            const data = await res.json()
            pendingMaterialRequests.value = data.items || []
            // Pre-fill approval rates with suggested rates
            data.items?.forEach(req => {
                if (req.suggested_rate) approvalRates.value[req.id] = req.suggested_rate
            })
        }
    } catch (e) {
        console.error('Failed to fetch material requests:', e)
    }
}

async function approveMaterialRequest(req) {
    const rate = approvalRates.value[req.id]
    if (!rate) return
    
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/inventory/material-requests/${req.id}/approve`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ approved_rate: rate })
        })
        if (res.ok) {
            // Remove from pending list
            pendingMaterialRequests.value = pendingMaterialRequests.value.filter(r => r.id !== req.id)
            // Add to materials array
            const id = generateMaterialId(req.material_name)
            if (!materialsArray.value.find(m => m.id === id)) {
                materialsArray.value = [...materialsArray.value, {
                    id,
                    name: req.material_name,
                    rate: rate,
                    unit: req.unit
                }]
            }
        }
    } catch (e) {
        console.error('Failed to approve material request:', e)
    }
}

async function rejectMaterialRequest(req) {
    try {
        const token = getStoredAccessToken()
        const res = await fetch(`${API_BASE}/api/v1/inventory/material-requests/${req.id}/reject`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ manager_notes: 'Rejected by Logistics Manager' })
        })
        if (res.ok) {
            pendingMaterialRequests.value = pendingMaterialRequests.value.filter(r => r.id !== req.id)
        }
    } catch (e) {
        console.error('Failed to reject material request:', e)
    }
}

// Legacy quote functions
const pendingQuotes = ref([])

const approveQuote = (id) => {
    if (!isEditMode.value) return;
    pendingQuotes.value = pendingQuotes.value.filter(q => q.id !== id);
}

const denyQuote = (id) => {
    if (!isEditMode.value) return;
    pendingQuotes.value = pendingQuotes.value.filter(q => q.id !== id);
}

const saveAndLock = async () => {
    isSaving.value = true
    saveError.value = ''
    try {
        await saveRates(rates.value)
        isEditMode.value = false
    } catch (e) {
        saveError.value = 'Failed to save rates. Please try again.'
    } finally {
        isSaving.value = false
    }
}

onMounted(() => {
    fetchMaterialRequests()
    checkInventorySeeded()
})

provide(rateGovernancePageKey, {
    addMaterial,
    approvalRates,
    approveMaterialRequest,
    approveQuote,
    denyQuote,
    isEditMode,
    materialsArray,
    newMaterial,
    pendingMaterialRequests,
    pendingQuotes,
    rates,
    rejectMaterialRequest,
    removeMaterial,
    showAddMaterialModal,
})
</script>
