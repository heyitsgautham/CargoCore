<template>
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
                    <select v-model="form.hubId"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                        :class="formErrors.hub ? 'border-red-400' : ''">
                        <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Select hub</option>
                        <option v-for="hub in availableHubs" :key="hub.id" :value="hub.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ hub.name }}</option>
                    </select>
                    <p v-if="formErrors.hub" class="text-xs text-red-500 mt-1">{{ formErrors.hub }}</p>
                    <div v-if="selectedHub" class="mt-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 px-3 py-2">
                        <div class="text-[11px] font-semibold text-gray-700 dark:text-gray-200">{{ selectedHub.name }}</div>
                        <div class="text-[11px] text-gray-500 dark:text-gray-400">{{ selectedHub.address || 'Warehouse address not saved yet' }}</div>
                    </div>
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

            <!-- ── Cost Estimate Card ───────────────────────────────────────────── -->
            <div v-if="costEstimateLoading"
                class="rounded-xl border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/10 p-4 animate-pulse">
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-blue-500 text-[18px]">calculate</span>
                    <div class="h-3 bg-blue-200 dark:bg-blue-400/30 rounded w-40"></div>
                </div>
                <div class="grid grid-cols-3 gap-3">
                    <div class="h-8 bg-blue-200 dark:bg-blue-400/20 rounded"></div>
                    <div class="h-8 bg-blue-200 dark:bg-blue-400/20 rounded"></div>
                    <div class="h-8 bg-blue-200 dark:bg-blue-400/20 rounded"></div>
                </div>
            </div>

            <div v-else-if="costEstimate"
                class="rounded-2xl border p-4 space-y-4"
                :class="costEstimate.pickup_source === 'missing_coordinates'
                    ? 'border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10'
                    : 'border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/10'">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-600 dark:text-blue-400 text-[18px]">calculate</span>
                            <span class="text-xs font-bold text-blue-800 dark:text-blue-300 uppercase tracking-wide">Estimated Wallet Debit Per Run</span>
                        </div>
                        <p class="mt-2 text-sm font-semibold text-gray-900 dark:text-white">
                            {{ costEstimate.resolved_hub_name || selectedHub?.name || 'Selected Hub' }}
                        </p>
                        <p class="text-[11px] text-gray-500 dark:text-gray-400">
                            Pickup source: {{ formatPickupSourceLabel(costEstimate.pickup_source) }}
                            <span v-if="costEstimate.pickup_reference"> · {{ costEstimate.pickup_reference }}</span>
                        </p>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        <span class="rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide"
                            :class="costEstimate.pickup_source === 'geofence_zone'
                                ? 'border-cyan-200 bg-cyan-50 text-cyan-700 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-300'
                                : costEstimate.pickup_source === 'missing_coordinates'
                                    ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300'
                                    : 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300'">
                            {{ formatPickupSourceLabel(costEstimate.pickup_source) }}
                        </span>
                        <span class="rounded-full border border-blue-200 bg-white/80 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-blue-700 dark:border-blue-500/20 dark:bg-black/20 dark:text-blue-300">
                            {{ formatDistanceMethodLabel(costEstimate.distance_method) }}
                        </span>
                    </div>
                </div>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div class="bg-white dark:bg-black/20 rounded-xl p-3 border border-blue-100 dark:border-blue-500/20">
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase mb-1">Distance</div>
                        <div class="text-base font-extrabold text-gray-900 dark:text-white">~{{ costEstimate.distance_km }} km</div>
                    </div>
                    <div class="bg-white dark:bg-black/20 rounded-xl p-3 border border-blue-100 dark:border-blue-500/20">
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase mb-1">Base Fee</div>
                        <div class="text-base font-bold text-gray-900 dark:text-white">₹{{ costEstimate.base_fee }}</div>
                    </div>
                    <div class="bg-white dark:bg-black/20 rounded-xl p-3 border border-blue-100 dark:border-blue-500/20">
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase mb-1">Distance Charge</div>
                        <div class="text-base font-bold text-gray-900 dark:text-white">₹{{ costEstimate.distance_cost }}</div>
                        <div class="text-[10px] text-gray-400 mt-1">₹{{ costEstimate.rate_per_km }}/km</div>
                    </div>
                    <div class="rounded-xl p-3 border"
                        :class="costEstimate.pickup_source === 'missing_coordinates'
                            ? 'border-amber-300 dark:border-amber-500/30 bg-amber-100/70 dark:bg-amber-500/10'
                            : 'border-blue-500/30 dark:border-blue-400/30 bg-blue-100/70 dark:bg-blue-500/10'">
                        <div class="text-[10px] uppercase mb-1 font-bold"
                            :class="costEstimate.pickup_source === 'missing_coordinates'
                                ? 'text-amber-700 dark:text-amber-300'
                                : 'text-blue-700 dark:text-blue-300'">Estimated Total</div>
                        <div class="text-lg font-extrabold"
                            :class="costEstimate.pickup_source === 'missing_coordinates'
                                ? 'text-amber-800 dark:text-amber-200'
                                : 'text-blue-700 dark:text-blue-300'">₹{{ costEstimate.total_estimate }}</div>
                    </div>
                </div>
                <div class="rounded-xl border px-3 py-2.5 flex items-start gap-2"
                    :class="costEstimate.pickup_source === 'missing_coordinates'
                        ? 'border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10'
                        : 'border-gray-200 dark:border-white/10 bg-white/70 dark:bg-black/20'">
                    <span class="material-symbols-outlined text-[15px] mt-0.5 flex-shrink-0"
                        :class="costEstimate.pickup_source === 'missing_coordinates' ? 'text-amber-500' : 'text-blue-500'">info</span>
                    <p class="text-[11px]"
                        :class="costEstimate.pickup_source === 'missing_coordinates'
                            ? 'text-amber-800 dark:text-amber-300'
                            : 'text-gray-600 dark:text-gray-400'">{{ costEstimate.note }}</p>
                </div>
                <div v-if="form.autoDebitEnabled"
                    class="flex items-start gap-2 rounded-xl px-3 py-2 border"
                    :class="costEstimate.pickup_source === 'missing_coordinates'
                        ? 'bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20'
                        : 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-700/40'">
                    <span class="material-symbols-outlined text-[15px] mt-0.5 flex-shrink-0"
                        :class="costEstimate.pickup_source === 'missing_coordinates' ? 'text-amber-500' : 'text-slate-500 dark:text-slate-300'">account_balance_wallet</span>
                    <p class="text-[11px] font-medium"
                        :class="costEstimate.pickup_source === 'missing_coordinates'
                            ? 'text-amber-800 dark:text-amber-300'
                            : 'text-slate-700 dark:text-slate-200'">
                        ₹{{ costEstimate.total_estimate }} will be auto-debited from your wallet on each scheduled run.
                        Keep at least ₹{{ costEstimate.total_estimate }} available before each schedule date.
                    </p>
                </div>
            </div>

            <!-- ── API error ────────────────────────────────────────────────────── -->
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
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { recurringPageKey } from './recurringPageContext'

const {
    availableHubs,
    closeFormModal,
    costEstimate,
    costEstimateLoading,
    editingRule,
    form,
    formErrors,
    formatDistanceMethodLabel,
    formatPickupSourceLabel,
    isSubmitting,
    openDestinationMapPicker,
    selectedHub,
    showFormModal,
    submitError,
    submitForm,
    todayISO,
} = inject(recurringPageKey)
</script>
