<template>
    <div v-if="showAssignModal && assignDock"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showAssignModal = false">
        <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg">Assign Truck to Dock {{
                    assignDock.id }}</h3>
                <button @click="showAssignModal = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Vehicle</label>
                    <select v-if="fleetVehicles.length" v-model="assignForm.truck"
                        class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                        <option value="">— Select vehicle —</option>
                        <option v-for="v in availableVehicles" :key="v.id" :value="v.id"
                            class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                            {{ v.code }}{{ v.license_plate ? ' · ' + v.license_plate : '' }} — {{ v.type }}{{ v.status !== 'Active' ? ' (' + v.status + ')' : '' }}
                        </option>
                    </select>
                    <input v-else type="text" v-model="assignForm.truck" placeholder="TRK-XXXX"
                        class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 font-mono" />
                </div>
                <div>
                    <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Dispatch Order</label>
                    <select v-model="assignForm.orderId"
                        class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                        <option value="" disabled>— Select Order (required) —</option>
                        <option v-for="order in availableOrders" :key="order.id" :value="order.id">
                            {{ order.tracking }} - {{ order.status }}
                        </option>
                    </select>
                </div>
                <button @click="confirmAssign" :disabled="!assignForm.truck || !assignForm.orderId"
                    class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50">Assign
                    to Dock</button>
                <button @click="openSlip('assetCheckout')"
                    class="w-full flex items-center justify-center gap-2 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-bold transition-colors">
                    <span class="material-symbols-outlined text-[16px]">inventory_2</span>
                    Print Asset Checkout Slip
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const {
    assignDock,
    assignForm,
    availableOrders,
    availableVehicles,
    confirmAssign,
    fleetVehicles,
    openSlip,
    showAssignModal,
} = inject(loadingDockPageKey)
</script>
