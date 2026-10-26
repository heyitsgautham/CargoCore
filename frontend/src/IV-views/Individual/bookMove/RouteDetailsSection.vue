<template>
    <!-- Section 3: Route Details -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span
                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">3</span>
            Route Details
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Hub Assignment</label>
                <select v-model="form.hubId"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all">
                    <option value="">Auto-select best available hub</option>
                    <option v-for="warehouse in store.warehouses" :key="warehouse.id" :value="warehouse.id">
                        {{ warehouse.name }}
                    </option>
                </select>
            </div>
            <div
                class="rounded-lg px-4 py-3"
                :class="warehouseBookingBlocked
                    ? 'border border-red-200 bg-red-50 dark:border-red-500/30 dark:bg-red-500/10'
                    : 'border border-green-200 bg-green-50 dark:border-green-500/20 dark:bg-green-500/5'">
                <div
                    class="text-[11px] uppercase tracking-wider font-bold"
                    :class="warehouseBookingBlocked ? 'text-red-700 dark:text-red-300' : 'text-green-700 dark:text-green-300'">
                    {{ warehouseBookingBlocked ? 'Hub Availability' : (routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'Routing Preview') }}
                </div>
                <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                    {{ warehouseBookingBlocked ? 'Currently no warehouse is available' : (routingPreview?.warehouse_name || 'Resolving best available hub...') }}
                </div>
                <div
                    class="text-xs mt-1"
                    :class="warehouseBookingBlocked ? 'text-red-600 dark:text-red-200' : 'text-gray-600 dark:text-gray-300'">
                    {{ warehouseBookingBlocked ? warehouseBookingMessage : (routingPreview?.message || 'We will choose the best available operational hub if you do not select one.') }}
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
                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all flex items-center justify-between"
                        title="Select pickup on map">
                        <span :class="form.pickup ? '' : 'text-gray-400'">{{ form.pickup || 'Select pickup on map' }}</span>
                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                    </button>
                </div>
            </div>
            <div>
                <label
                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Destination
                    Address</label>
                <div class="relative">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-500 text-lg">location_on</span>
                    <button type="button" @click="openMapPicker('destination')"
                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all flex items-center justify-between"
                        title="Select destination on map">
                        <span :class="form.destination ? '' : 'text-gray-400'">{{ form.destination || 'Select destination on map' }}</span>
                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                    </button>
                </div>
            </div>
            <div>
                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Move
                    Date</label>
                <input v-model="form.date" type="date"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
            </div>
            <div>
                <label
                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium flex items-center gap-2">
                    Time Window
                    <span
                        class="px-1.5 py-0.5 text-[10px] bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded font-bold flex items-center gap-0.5">
                        <span class="material-symbols-outlined text-[10px]">auto_awesome</span> AI Smart
                    </span>
                </label>
                <div class="grid grid-cols-2 gap-2">
                    <button v-for="slot in timeSlots" :key="slot.value" type="button"
                        @click="form.timeWindow = slot.value"
                        class="relative p-2.5 rounded-lg border text-left transition-all text-xs"
                        :class="form.timeWindow === slot.value
                            ? 'border-green-500 bg-green-500/5 dark:bg-green-500/10'
                            : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/50'">
                        <div v-if="slot.recommended"
                            class="absolute -top-2 right-2 px-1.5 py-0.5 bg-purple-500 text-white text-[8px] font-bold rounded-full">
                            AI Pick</div>
                        <div class="font-medium text-gray-900 dark:text-white">{{ slot.label }}</div>
                        <div class="flex items-center justify-between mt-1">
                            <span class="text-[10px]" :class="slot.demandColor">{{ slot.demand }}</span>
                            <span class="text-[10px] font-mono" :class="slot.priceColor">{{
                                slot.priceTag }}</span>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const {
    form,
    openMapPicker,
    routingPreview,
    store,
    timeSlots,
    warehouseBookingBlocked,
    warehouseBookingMessage,
} = inject(bookMovePageKey)
</script>
