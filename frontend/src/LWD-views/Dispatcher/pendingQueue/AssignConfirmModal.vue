<template>
    <Teleport to="body">
    <div v-if="showAssignConfirm" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showAssignConfirm = false">
        <div class="bg-white dark:bg-card-darker rounded-2xl p-6 w-full max-w-md m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">assignment_turned_in</span> Assign Driver
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
                Order <strong class="text-gray-900 dark:text-white">{{ assignConfirmOrder?.displayId || assignConfirmOrder?.trackingCode || assignConfirmOrder?.id }}</strong>
                · {{ assignConfirmOrder?.priority }}
            </p>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Driver <span class="text-red-500">*</span></label>
                    <select v-model="assignDriverId"
                        class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                        <option value="" class="bg-white dark:bg-gray-800">— Select Driver —</option>
                        <option v-for="d in assignDrivers" :key="d.id" :value="d.id" class="bg-white dark:bg-gray-800">
                            {{ d.name }} ({{ d.status }})
                        </option>
                    </select>
                    <p v-if="assignDriversLoading" class="text-xs text-gray-400 mt-1">Loading drivers...</p>
                    <p v-if="!assignDriversLoading && assignDrivers.length === 0" class="text-xs text-red-400 mt-1">No active drivers available. Drivers must start their shift in the driver app to appear here.</p>
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
                        Vehicle
                        <span v-if="orderAllowsDirectVehicleSelection(assignConfirmOrder) && assignConfirmOrder?.type === 'VENDOR'" class="text-blue-400 font-normal normal-case">(vendor order — dispatcher assigns vehicle)</span>
                        <span v-else-if="orderAllowsDirectVehicleSelection(assignConfirmOrder)" class="text-orange-400 font-normal normal-case">(dispatcher can select directly)</span>
                        <span v-else class="text-gray-400 font-normal normal-case">(assigned by warehouse)</span>
                    </label>
                    <p v-if="assignVehiclesLoading" class="text-xs text-gray-400 mt-1">Loading...</p>
                    <div v-else-if="assignVehicles.length > 0">
                        <select v-model="assignVehicleId" :disabled="!orderAllowsDirectVehicleSelection(assignConfirmOrder)"
                            class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none"
                            :class="!orderAllowsDirectVehicleSelection(assignConfirmOrder) ? 'opacity-70 cursor-not-allowed' : ''">
                            <option value="" class="bg-white dark:bg-gray-800">— Select Vehicle —</option>
                            <option v-for="v in assignVehicles" :key="v.id" :value="v.id" class="bg-white dark:bg-gray-800">
                                {{ v.code }} · {{ v.type }}{{ v.license_plate ? ' (' + v.license_plate + ')' : '' }}
                            </option>
                        </select>
                    </div>
                    <div v-else class="flex items-center gap-2 px-3 py-2 rounded-lg text-xs border"
                        :class="orderAllowsDirectVehicleSelection(assignConfirmOrder) ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-600 dark:text-yellow-400'">
                        <span class="material-symbols-outlined text-[14px]">warning</span>
                        <span v-if="orderAllowsDirectVehicleSelection(assignConfirmOrder)">No available vehicles — all vehicles are currently in use</span>
                        <span v-else>Not yet assigned — Warehouse Manager must assign a vehicle via Loading Dock first</span>
                    </div>
                </div>
            </div>
            <div v-if="assignError" class="mt-3 text-xs text-red-400 font-bold">{{ assignError }}</div>
            <div v-if="assignSuccess" class="mt-3 text-xs text-green-400 font-bold">{{ assignSuccess }}</div>
            <div class="flex gap-2 mt-5">
                <button @click="confirmAssign" :disabled="!assignDriverId || isAssigning"
                    class="flex-1 bg-primary hover:bg-primary-dark text-black font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                    <span v-if="isAssigning" class="w-3.5 h-3.5 rounded-full border-2 border-black/30 border-t-black animate-spin"></span>
                    {{ isAssigning ? 'Assigning...' : 'Confirm Assignment' }}
                </button>
                <button @click="showAssignConfirm = false" class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-900 dark:text-white py-2 rounded-lg text-sm transition-colors">Cancel</button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { pendingQueuePageKey } from './pendingQueuePageContext'

const {
    assignConfirmOrder,
    assignDriverId,
    assignDrivers,
    assignDriversLoading,
    assignError,
    assignSuccess,
    assignVehicleId,
    assignVehicles,
    assignVehiclesLoading,
    confirmAssign,
    isAssigning,
    orderAllowsDirectVehicleSelection,
    showAssignConfirm,
} = inject(pendingQueuePageKey)
</script>
