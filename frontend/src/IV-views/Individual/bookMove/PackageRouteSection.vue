<template>
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-blue-500">route</span> Pickup & Delivery
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Hub Assignment</label>
                <select v-model="form.hubId"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all">
                    <option value="">Auto-select best available hub</option>
                    <option v-for="warehouse in store.warehouses" :key="warehouse.id" :value="warehouse.id">
                        {{ warehouse.name }}
                    </option>
                </select>
            </div>
            <div class="rounded-lg border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/5 px-4 py-3">
                <div class="text-[11px] uppercase tracking-wider font-bold text-blue-700 dark:text-blue-300">
                    {{ routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'Routing Preview' }}
                </div>
                <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                    {{ routingPreview?.warehouse_name || 'Resolving best available hub...' }}
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                    {{ routingPreview?.message || 'We will choose the best available operational hub if you do not select one.' }}
                </div>
            </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Pickup
                    Address</label>
                <div class="relative">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-green-500 text-lg">trip_origin</span>
                    <button type="button" @click="openMapPicker('pickup')"
                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all flex items-center justify-between"
                        title="Select pickup on map">
                        <span :class="form.pickup ? '' : 'text-gray-400'">{{ form.pickup || 'Select pickup on map' }}</span>
                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                    </button>
                </div>
            </div>
            <div>
                <label
                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Delivery
                    Address</label>
                <div class="relative">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-500 text-lg">location_on</span>
                    <button type="button" @click="openMapPicker('destination')"
                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all flex items-center justify-between"
                        title="Select destination on map">
                        <span :class="form.destination ? '' : 'text-gray-400'">{{ form.destination || 'Select destination on map' }}</span>
                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                    </button>
                </div>
            </div>
            <div>
                <label
                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Preferred
                    Pickup Date</label>
                <input v-model="pkg.preferredDate" type="date"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none" />
            </div>
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Est.
                    Delivery</label>
                <div
                    class="px-4 py-2.5 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-blue-700 dark:text-blue-400 font-bold text-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-lg">schedule</span>
                    {{ estimatedDelivery || 'Select pickup date' }}
                </div>
            </div>
        </div>
        <div
            class="mt-4 p-3 bg-blue-50 dark:bg-blue-500/5 border border-blue-200 dark:border-blue-500/20 rounded-lg flex items-center gap-3 text-sm">
            <span class="material-symbols-outlined text-blue-500">info</span>
            <span class="text-gray-700 dark:text-gray-300">Auto-scheduled pickup. Our driver will
                collect from your address on the selected date.</span>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const {
    estimatedDelivery,
    form,
    openMapPicker,
    pkg,
    routingPreview,
    store,
} = inject(bookMovePageKey)
</script>
