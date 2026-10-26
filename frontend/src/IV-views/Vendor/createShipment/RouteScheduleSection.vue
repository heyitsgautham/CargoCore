<template>
    <!-- Route & Schedule -->
    <div class="glass-panel p-6 rounded-xl space-y-4">
        <h3
            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
            2. Route & Schedule</h3>

        <!-- Pickup Toggle -->
        <div class="flex gap-4 p-1 bg-gray-100 dark:bg-white/5 rounded-lg w-max">
            <button @click="form.pickupType = 'hub'"
                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
                :class="form.pickupType === 'hub' ? 'bg-white dark:bg-gray-700 shadow text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
                Hub Pickup
            </button>
            <button @click="form.pickupType = 'doorstep'"
                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
                :class="form.pickupType === 'doorstep' ? 'bg-white dark:bg-gray-700 shadow text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
                Shop/Doorstep Pickup
            </button>
        </div>

        <div
            v-if="warehouseBookingBlocked"
            class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
            {{ warehouseBookingMessage }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div v-if="form.pickupType === 'hub'">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                    Drop-off Hub *
                    <span class="text-gray-400 font-normal normal-case">(you bring goods here)</span>
                </label>
                <select v-model="form.pickupHub"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <option value="" disabled class="bg-white dark:bg-gray-800 text-gray-400">Select a warehouse...</option>
                    <option v-for="w in store.warehouses" :key="w.id" :value="w.name"
                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        {{ w.name }}
                    </option>
                </select>
            </div>
            <div v-else class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="sm:col-span-2">
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Address *</label>
                    <button type="button" @click="openMapPicker('pickup')"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-left flex items-center justify-between gap-2 hover:border-blue-500 transition-colors focus:outline-none focus:border-blue-500"
                        :class="form.pickupAddress ? 'text-gray-900 dark:text-white' : 'text-gray-400'">
                        <span class="truncate">{{ form.pickupAddress || 'Select your pickup location on map...' }}</span>
                        <span class="material-symbols-outlined text-[20px] text-gray-400 flex-shrink-0">map</span>
                    </button>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup City
                        *</label>
                    <input v-model="form.pickupCity" type="text" placeholder="City name"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Pincode
                        *</label>
                    <input v-model="form.pickupPincode" type="text" placeholder="e.g. 400001"
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
            </div>

            <div v-if="form.category === 'b2c'">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Customer Name
                    *</label>
                <input v-model="form.customerName" type="text" placeholder="John Doe"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div v-if="form.category === 'b2c'">
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Customer Phone
                    *</label>
                <input v-model="form.customerPhone" type="tel" placeholder="+91 0000000000"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination Address *</label>
                <button type="button" @click="openMapPicker('destination')"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-left flex items-center justify-between gap-2 hover:border-blue-500 transition-colors focus:outline-none focus:border-blue-500"
                    :class="form.destination ? 'text-gray-900 dark:text-white' : 'text-gray-400'">
                    <span class="truncate">{{ form.destination || 'Select destination on map...' }}</span>
                    <span class="material-symbols-outlined text-[20px] text-gray-400 flex-shrink-0">map</span>
                </button>
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination City
                    *</label>
                <input v-model="form.destinationCity" type="text" placeholder="City name"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pincode *</label>
                <input v-model="form.pincode" type="text" placeholder="e.g. 400001"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Date
                    *</label>
                <input v-model="form.pickupDate" type="date"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Time
                    Window</label>
                <select v-model="form.timeWindow"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">08:00 AM - 12:00 PM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">12:00 PM - 04:00 PM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">04:00 PM - 08:00 PM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Night (08 PM - 06 AM)</option>
                </select>
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Expected Delivery
                    Date</label>
                <input v-model="form.deliveryDate" type="date"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Priority</label>
                <select v-model="form.priority"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Standard</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Express</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Urgent</option>
                </select>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const {
    form,
    openMapPicker,
    store,
    warehouseBookingBlocked,
    warehouseBookingMessage,
} = inject(createShipmentPageKey)
</script>
