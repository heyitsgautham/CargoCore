<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Recurring Shipments</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Automate your regular shipping schedules</p>
            </div>
            <button @click="openCreateModal"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px]">add</span> Create Schedule
            </button>
        </div>

        <!-- Summary Chips -->
        <div class="flex flex-wrap gap-3">
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-500 text-[18px]">schedule</span>
                <span class="text-sm font-bold text-gray-900 dark:text-white">{{ store.recurringRules.length }}</span>
                <span class="text-xs text-gray-500">Total</span>
            </div>
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-green-500 text-[18px]">toggle_on</span>
                <span class="text-sm font-bold text-green-500">{{ activeCount }}</span>
                <span class="text-xs text-gray-500">Active</span>
            </div>
            <div class="glass-panel px-4 py-2 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-gray-400 text-[18px]">toggle_off</span>
                <span class="text-sm font-bold text-gray-400">{{ store.recurringRules.length - activeCount }}</span>
                <span class="text-xs text-gray-500">Paused</span>
            </div>
        </div>

        <!-- Loading skeleton -->
        <div v-if="store.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="i in 3" :key="i" class="glass-panel p-5 rounded-xl animate-pulse">
                <div class="flex justify-between mb-4">
                    <div class="h-5 w-20 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="flex gap-1">
                        <div class="h-7 w-7 bg-gray-200 dark:bg-white/10 rounded-lg"></div>
                        <div class="h-7 w-7 bg-gray-200 dark:bg-white/10 rounded-lg"></div>
                    </div>
                </div>
                <div class="h-5 w-3/4 bg-gray-200 dark:bg-white/10 rounded mb-2"></div>
                <div class="h-4 w-full bg-gray-200 dark:bg-white/10 rounded mb-4"></div>
                <div class="space-y-2 mb-4">
                    <div class="h-4 w-2/3 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-4 w-1/2 bg-gray-200 dark:bg-white/10 rounded"></div>
                </div>
                <div class="flex justify-between pt-3 border-t border-gray-100 dark:border-white/5">
                    <div class="h-4 w-24 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-5 w-9 bg-gray-200 dark:bg-white/10 rounded-full"></div>
                </div>
            </div>
        </div>

        <!-- Rules Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="rule in store.recurringRules" :key="rule.id"
                class="glass-panel p-5 rounded-xl border-l-4 transition-all duration-200"
                :class="rule.active ? 'border-blue-500' : 'border-gray-300 dark:border-gray-600 opacity-75'">
                <div class="flex justify-between items-start mb-3">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                        :class="rule.active ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-gray-500/20 text-gray-500'">{{ rule.frequency }}</span>
                    <div class="flex gap-1">
                        <button @click="openEditModal(rule)" class="p-1.5 rounded-lg hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="Edit">
                            <span class="material-symbols-outlined text-[16px]">edit</span>
                        </button>
                        <button @click="confirmDelete(rule)" class="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors" title="Delete">
                            <span class="material-symbols-outlined text-[16px]">delete</span>
                        </button>
                    </div>
                </div>

                <h3 class="font-bold text-gray-900 dark:text-white text-base mb-1">{{ rule.name }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ rule.description || '—' }}</p>

                <div class="space-y-2 mb-4">
                    <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                        <span class="material-symbols-outlined text-[14px] text-blue-500">warehouse</span>
                        Hub: {{ getRuleMeta(rule).hub || rule.route }}
                    </div>
                    <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                        <span class="material-symbols-outlined text-[14px] text-amber-500">schedule</span>
                        Vendor Drop Time: {{ getRuleMeta(rule).dropOffTime || 'Not set' }}
                    </div>
                    <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                        <span class="material-symbols-outlined text-[14px] text-emerald-500">pin_drop</span>
                        Destination: {{ formatRuleDestination(getRuleMeta(rule)) }}
                    </div>
                    <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                        <span class="material-symbols-outlined text-[14px] text-purple-500">inventory_2</span>
                        {{ getRuleMeta(rule).cargo }}
                    </div>
                    <div class="flex items-center gap-2 text-xs" :class="getRuleMeta(rule).autoDebitEnabled ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'">
                        <span class="material-symbols-outlined text-[14px]" :class="getRuleMeta(rule).autoDebitEnabled ? 'text-emerald-500' : 'text-amber-500'">
                            {{ getRuleMeta(rule).autoDebitEnabled ? 'account_balance_wallet' : 'warning' }}
                        </span>
                        {{ getRuleMeta(rule).autoDebitEnabled ? 'Wallet auto-debit enabled' : 'Wallet auto-debit disabled' }}
                    </div>
                </div>

                <div class="flex justify-between items-center border-t border-gray-100 dark:border-white/5 pt-3">
                    <div class="text-[10px] text-gray-500">
                        Next: <span class="font-bold text-gray-700 dark:text-gray-300">{{ formatNextRun(rule.nextRun) }}</span>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" :checked="rule.active" @change="toggleRule(rule)"
                            :disabled="togglingId === rule.id" class="sr-only peer">
                        <div class="w-9 h-5 rounded-full transition-colors"
                            :class="[
                                togglingId === rule.id ? 'opacity-50' : '',
                                rule.active ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-700'
                            ]">
                            <div class="absolute top-[2px] left-[2px] bg-white rounded-full h-4 w-4 shadow transition-all"
                                :class="rule.active ? 'translate-x-4' : 'translate-x-0'"></div>
                        </div>
                    </label>
                </div>
            </div>

            <!-- Empty state -->
            <div v-if="store.recurringRules.length === 0" class="col-span-full glass-panel p-12 rounded-xl flex flex-col items-center justify-center">
                <span class="material-symbols-outlined text-5xl text-gray-300 dark:text-gray-600 mb-3">event_repeat</span>
                <p class="text-gray-500 dark:text-gray-400 mb-4">No recurring schedules yet</p>
                <button @click="openCreateModal" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors">Create Your First Schedule</button>
            </div>
        </div>

        <!-- Create / Edit Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showFormModal" @close="closeFormModal">
                <template #title>{{ editingRule ? 'Edit Schedule' : 'Create Recurring Schedule' }}</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Schedule Name *</label>
                        <input v-model="form.name" type="text" placeholder="e.g. Weekly Restock - NY Store"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                            :class="formErrors.name ? 'border-red-400' : ''">
                        <p v-if="formErrors.name" class="text-xs text-red-500 mt-1">{{ formErrors.name }}</p>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description</label>
                        <input v-model="form.description" type="text" placeholder="Brief description"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Frequency *</label>
                            <select v-model="form.frequency"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                <option value="Daily" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Daily</option>
                                <option value="Every Monday" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Every Monday</option>
                                <option value="Every Wednesday" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Every Wednesday</option>
                                <option value="Every Friday" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Every Friday</option>
                                <option value="Bi-Weekly" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Bi-Weekly</option>
                                <option value="1st of Month" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">1st of Month</option>
                                <option value="15th of Month" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">15th of Month</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Next Run Date *</label>
                            <input v-model="form.nextRun" type="date" :min="todayISO"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                                :class="formErrors.nextRun ? 'border-red-400' : ''">
                            <p v-if="formErrors.nextRun" class="text-xs text-red-500 mt-1">{{ formErrors.nextRun }}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Hub *</label>
                            <select v-model="form.hub"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                                :class="formErrors.hub ? 'border-red-400' : ''">
                                <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Select hub</option>
                                <option v-for="hub in availableHubs" :key="hub.id" :value="hub.name" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ hub.name }}</option>
                            </select>
                            <p v-if="formErrors.hub" class="text-xs text-red-500 mt-1">{{ formErrors.hub }}</p>
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Vendor Drop Time (each schedule day) *</label>
                            <input v-model="form.dropOffTime" type="time"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                                :class="formErrors.dropOffTime ? 'border-red-400' : ''">
                            <p v-if="formErrors.dropOffTime" class="text-xs text-red-500 mt-1">{{ formErrors.dropOffTime }}</p>
                        </div>
                    </div>

                    <div class="space-y-3 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 p-4">
                        <div>
                            <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination Address *</label>
                            <button type="button" @click="openDestinationMapPicker"
                                class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-left flex items-center justify-between gap-2 hover:border-blue-500 transition-colors focus:outline-none focus:border-blue-500"
                                :class="form.destinationAddress ? 'text-gray-900 dark:text-white' : 'text-gray-400'">
                                <span class="truncate">{{ form.destinationAddress || 'Select destination on map...' }}</span>
                                <span class="material-symbols-outlined text-[20px] text-gray-400 flex-shrink-0">map</span>
                            </button>
                            <p v-if="formErrors.destinationAddress" class="text-xs text-red-500 mt-1">{{ formErrors.destinationAddress }}</p>
                            <p class="text-[11px] text-gray-400 mt-1">Use the same map-style destination picker as Commercial (B2B) orders.</p>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination City *</label>
                                <input v-model="form.destinationCity" type="text" placeholder="City name"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                                    :class="formErrors.destinationCity ? 'border-red-400' : ''">
                                <p v-if="formErrors.destinationCity" class="text-xs text-red-500 mt-1">{{ formErrors.destinationCity }}</p>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pincode *</label>
                                <input v-model="form.destinationPincode" type="text" placeholder="e.g. 560100"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                                    :class="formErrors.destinationPincode ? 'border-red-400' : ''">
                                <p v-if="formErrors.destinationPincode" class="text-xs text-red-500 mt-1">{{ formErrors.destinationPincode }}</p>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Cargo Details *</label>
                        <input v-model="form.details" type="text" placeholder="e.g. 12 Pallets • General Goods"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                            :class="formErrors.details ? 'border-red-400' : ''">
                        <p v-if="formErrors.details" class="text-xs text-red-500 mt-1">{{ formErrors.details }}</p>
                    </div>

                    <div class="rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10 p-3 space-y-2">
                        <label class="flex items-start gap-3 cursor-pointer">
                            <input v-model="form.autoDebitEnabled" type="checkbox" class="mt-0.5" />
                            <div>
                                <p class="text-sm font-bold text-amber-800 dark:text-amber-300">Enable Wallet Auto-Debit</p>
                                <p class="text-xs text-amber-700 dark:text-amber-400">For recurring orders only. Debits happen from wallet on scheduled date, or immediately when warehouse marks goods arrived early.</p>
                            </div>
                        </label>
                        <p class="text-[11px] text-amber-700 dark:text-amber-400">Keep sufficient wallet balance before schedule day/drop time to avoid skipped auto-debits.</p>
                    </div>

                    <!-- API error -->
                    <div v-if="submitError" class="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg">
                        <span class="material-symbols-outlined text-red-500 text-[16px]">error</span>
                        <p class="text-xs text-red-600 dark:text-red-400">{{ submitError }}</p>
                    </div>
                </div>
                <template #footer>
                    <button @click="closeFormModal" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitForm" :disabled="isSubmitting"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                        <span v-if="isSubmitting" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                        {{ editingRule ? 'Save Changes' : 'Create Schedule' }}
                    </button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Delete Confirmation Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showDeleteModal" @close="showDeleteModal = false">
                <template #title>Delete Schedule</template>
                <div class="text-center py-4">
                    <span class="material-symbols-outlined text-5xl text-red-500 mb-3">warning</span>
                    <p class="text-gray-600 dark:text-gray-300 text-sm">Are you sure you want to delete <strong class="text-gray-900 dark:text-white">{{ deletingRule?.name }}</strong>?</p>
                    <p class="text-xs text-gray-400 mt-2">This action cannot be undone.</p>
                    <p v-if="deleteError" class="text-xs text-red-500 mt-3">{{ deleteError }}</p>
                </div>
                <template #footer>
                    <button @click="showDeleteModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="executeDelete" :disabled="isDeleting"
                        class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                        <span v-if="isDeleting" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                        Delete
                    </button>
                </template>
            </BaseModal>
        </Teleport>

        <Teleport to="body">
            <MapPicker
                v-if="showDestinationMapPicker"
                :isOpen="showDestinationMapPicker"
                title="Select Recurring Destination on Map"
                :initial-lat="destinationMapInitialLat"
                :initial-lon="destinationMapInitialLon"
                @close="showDestinationMapPicker = false"
                @select="handleDestinationSelect"
            />
        </Teleport>
    </div>
</template>

<script setup>
import { computed, defineAsyncComponent, ref } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import BaseModal from '@/components/BaseModal.vue'

const store = useVendorStore()
const MapPicker = defineAsyncComponent(() => import('@/components/MapPicker.vue'))

// Modal state
const showFormModal = ref(false)
const showDeleteModal = ref(false)
const editingRule = ref(null)
const deletingRule = ref(null)
const showDestinationMapPicker = ref(false)
const destinationMapInitialLat = ref(12.9716)
const destinationMapInitialLon = ref(77.5946)

// Loading/error state
const isSubmitting = ref(false)
const isDeleting = ref(false)
const togglingId = ref(null)
const submitError = ref('')
const deleteError = ref('')
const formErrors = ref({})

// Form
const defaultForm = {
    name: '',
    description: '',
    frequency: 'Every Monday',
    hub: '',
    dropOffTime: '09:00',
    destinationAddress: '',
    destinationCity: '',
    destinationPincode: '',
    destinationLat: null,
    destinationLon: null,
    details: '',
    autoDebitEnabled: false,
    nextRun: '',
}
const form = ref({ ...defaultForm })

// Today's date for the date picker minimum
const todayISO = new Date().toISOString().split('T')[0]

const activeCount = computed(() => store.recurringRules.filter(r => r.active).length)
const availableHubs = computed(() => (store.warehouses || []).map((hub) => ({ id: hub.id, name: hub.name })))

function parseRuleDetails(details) {
    try {
        const parsed = JSON.parse(details)
        if (parsed && typeof parsed === 'object' && parsed.cargo) {
            return {
                cargo: parsed.cargo,
                hub: parsed.hub || '',
                dropOffTime: parsed.dropOffTime || '',
                destinationAddress: parsed.destinationAddress || '',
                destinationCity: parsed.destinationCity || '',
                destinationPincode: parsed.destinationPincode || '',
                destinationLat: parsed.destinationLat ?? null,
                destinationLon: parsed.destinationLon ?? null,
                autoDebitEnabled: !!parsed.autoDebitEnabled,
            }
        }
    } catch (e) {
        // Ignore parse errors for legacy plain-text details
    }
    return {
        cargo: details || '—',
        hub: '',
        dropOffTime: '',
        destinationAddress: '',
        destinationCity: '',
        destinationPincode: '',
        destinationLat: null,
        destinationLon: null,
        autoDebitEnabled: false,
    }
}

function getRuleMeta(rule) {
    return parseRuleDetails(rule.details)
}

function inferDestinationFromRoute(route) {
    if (!route) return ''
    const parts = String(route).split('→').map((part) => part.trim()).filter(Boolean)
    return parts[parts.length - 1] || ''
}

function inferHubFromRoute(route) {
    if (!route) return ''
    const parts = String(route).split('→').map((part) => part.trim()).filter(Boolean)
    return parts[0] || ''
}

function formatRuleDestination(meta) {
    const address = meta.destinationAddress || ''
    const city = meta.destinationCity || ''
    const pincode = meta.destinationPincode || ''
    if (address && city) return `${address}, ${city}${pincode ? ` - ${pincode}` : ''}`
    if (address) return address
    if (city) return `${city}${pincode ? ` - ${pincode}` : ''}`
    return '—'
}

function buildDetailsPayload() {
    return JSON.stringify({
        cargo: form.value.details,
        hub: form.value.hub,
        dropOffTime: form.value.dropOffTime,
        destinationAddress: form.value.destinationAddress,
        destinationCity: form.value.destinationCity,
        destinationPincode: form.value.destinationPincode,
        destinationLat: form.value.destinationLat,
        destinationLon: form.value.destinationLon,
        autoDebitEnabled: !!form.value.autoDebitEnabled,
    })
}

function buildRoutePayload() {
    const hubLabel = (form.value.hub || 'Vendor Hub').trim()
    const destinationLabel = (form.value.destinationCity || form.value.destinationAddress || 'Destination').trim()
    const compactRoute = `${hubLabel} → ${destinationLabel}`
    return compactRoute.length > 240 ? `${hubLabel} → ${destinationLabel.slice(0, 180)}…` : compactRoute
}

function formatNextRun(val) {
    if (!val) return '—'
    // If ISO date string (YYYY-MM-DD), format nicely
    if (/^\d{4}-\d{2}-\d{2}/.test(val)) {
        return new Date(val + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    }
    return val
}

function validateForm() {
    const errs = {}
    if (!form.value.name?.trim()) errs.name = 'Schedule name is required'
    if (!form.value.hub?.trim()) errs.hub = 'Hub is required'
    if (!form.value.dropOffTime) errs.dropOffTime = 'Drop time is required'
    if (!form.value.destinationAddress?.trim()) errs.destinationAddress = 'Destination is required'
    if (!form.value.destinationCity?.trim()) errs.destinationCity = 'Destination city is required'
    if (!form.value.destinationPincode?.trim()) errs.destinationPincode = 'Destination pincode is required'
    if (!form.value.details?.trim()) errs.details = 'Cargo details are required'
    if (!form.value.nextRun) errs.nextRun = 'Next run date is required'
    formErrors.value = errs
    return Object.keys(errs).length === 0
}

async function toggleRule(rule) {
    if (togglingId.value) return
    togglingId.value = rule.id
    try {
        await store.toggleRecurringRule(rule.id)
        showToast(rule.active ? `"${rule.name}" paused` : `"${rule.name}" activated`)
    } catch (e) {
        showToast(e?.message || 'Failed to toggle schedule', 'error')
    } finally {
        togglingId.value = null
    }
}

async function openCreateModal() {
    if (!availableHubs.value.length) {
        await store.fetchWarehouses().catch(() => {})
    }
    editingRule.value = null
    form.value = { ...defaultForm }
    formErrors.value = {}
    submitError.value = ''
    showFormModal.value = true
}

function openEditModal(rule) {
    editingRule.value = rule
    const parsedDetails = parseRuleDetails(rule.details)
    // Normalize nextRun to ISO date if possible
    let nextRun = rule.nextRun || ''
    if (nextRun && !/^\d{4}-\d{2}-\d{2}/.test(nextRun)) {
        const parsed = new Date(nextRun)
        if (!isNaN(parsed)) nextRun = parsed.toISOString().split('T')[0]
    }
    const destinationAddress = parsedDetails.destinationAddress || inferDestinationFromRoute(rule.route) || ''
    form.value = {
        name: rule.name,
        description: rule.description || '',
        frequency: rule.frequency,
        hub: parsedDetails.hub || inferHubFromRoute(rule.route) || '',
        dropOffTime: parsedDetails.dropOffTime || '09:00',
        destinationAddress,
        destinationCity: parsedDetails.destinationCity || '',
        destinationPincode: parsedDetails.destinationPincode || '',
        destinationLat: parsedDetails.destinationLat ?? null,
        destinationLon: parsedDetails.destinationLon ?? null,
        details: parsedDetails.cargo,
        autoDebitEnabled: !!parsedDetails.autoDebitEnabled,
        nextRun,
    }
    formErrors.value = {}
    submitError.value = ''
    showFormModal.value = true
}

function closeFormModal() {
    showFormModal.value = false
    submitError.value = ''
    formErrors.value = {}
}

function openDestinationMapPicker() {
    destinationMapInitialLat.value = Number(form.value.destinationLat ?? 12.9716)
    destinationMapInitialLon.value = Number(form.value.destinationLon ?? 77.5946)
    showDestinationMapPicker.value = true
}

function handleDestinationSelect(data) {
    form.value.destinationAddress = data.address
    form.value.destinationLat = data.lat
    form.value.destinationLon = data.lon
}

async function submitForm() {
    if (!validateForm()) return
    isSubmitting.value = true
    submitError.value = ''
    try {
        if (editingRule.value) {
            await store.updateRecurringRule(editingRule.value.id, {
                ...form.value,
                route: buildRoutePayload(),
                details: buildDetailsPayload(),
                active: editingRule.value.active,
            })
            showToast('Schedule updated')
        } else {
            await store.addRecurringRule({
                ...form.value,
                route: buildRoutePayload(),
                details: buildDetailsPayload(),
                active: true,
            })
            showToast('Schedule created')
        }
        closeFormModal()
    } catch (e) {
        submitError.value = e?.message || 'Something went wrong. Please try again.'
    } finally {
        isSubmitting.value = false
    }
}

function confirmDelete(rule) {
    deletingRule.value = rule
    deleteError.value = ''
    showDeleteModal.value = true
}

async function executeDelete() {
    if (!deletingRule.value) return
    isDeleting.value = true
    deleteError.value = ''
    try {
        await store.deleteRecurringRule(deletingRule.value.id)
        showDeleteModal.value = false
        showToast('Schedule deleted')
        deletingRule.value = null
    } catch (e) {
        deleteError.value = e?.message || 'Failed to delete. Please try again.'
    } finally {
        isDeleting.value = false
    }
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    t.className = `fixed right-4 bottom-4 z-[9999] text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}
</script>
