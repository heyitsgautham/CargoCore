<template>
    <!-- Assign Vehicle Modal -->
    <Teleport to="body">
        <div v-if="showAssignVehicleModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showAssignVehicleModal = false">
            <div class="bg-white dark:bg-card-darker rounded-2xl p-6 w-full max-w-sm m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
                    <span class="material-symbols-outlined text-orange-400">local_shipping</span>
                    Assign Vehicle
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
                    Order <strong class="text-gray-900 dark:text-white">{{ assignVehicleOrder?.id }}</strong>
                    · Driver <strong class="text-gray-900 dark:text-white">{{ assignVehicleOrder?.driver || '—' }}</strong>
                </p>
                <div class="space-y-3">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Select Vehicle <span class="text-red-500">*</span></label>
                        <p v-if="assignVehicleLoading" class="text-xs text-gray-400">Loading vehicles...</p>
                        <select v-else v-model="assignVehicleSelected"
                            class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                            <option value="">— Select Vehicle —</option>
                            <option v-for="v in assignVehicleOptions" :key="v.id" :value="v.id">
                                {{ v.code }} · {{ v.type || '' }} ({{ v.license_plate || 'no plate' }})
                            </option>
                        </select>
                        <p v-if="!assignVehicleLoading && assignVehicleOptions.length === 0" class="text-xs text-red-400 mt-1">No available vehicles right now.</p>
                    </div>
                </div>
                <div v-if="assignVehicleError" class="mt-3 text-xs text-red-400 font-bold">{{ assignVehicleError }}</div>
                <div v-if="assignVehicleSuccess" class="mt-3 text-xs text-green-400 font-bold">{{ assignVehicleSuccess }}</div>
                <div class="flex gap-2 mt-5">
                    <button @click="confirmAssignVehicle" :disabled="!assignVehicleSelected || assignVehicleSaving"
                        class="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                        <span v-if="assignVehicleSaving" class="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin"></span>
                        {{ assignVehicleSaving ? 'Saving...' : 'Confirm' }}
                    </button>
                    <button @click="showAssignVehicleModal = false" class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-900 dark:text-white py-2 rounded-lg text-sm transition-colors">Cancel</button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { orderStatusPageKey } from './orderStatusPageContext'

const {
    assignVehicleError,
    assignVehicleLoading,
    assignVehicleOptions,
    assignVehicleOrder,
    assignVehicleSaving,
    assignVehicleSelected,
    assignVehicleSuccess,
    confirmAssignVehicle,
    showAssignVehicleModal,
} = inject(orderStatusPageKey)
</script>
