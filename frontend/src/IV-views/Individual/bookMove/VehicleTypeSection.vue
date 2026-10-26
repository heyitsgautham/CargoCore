<template>
    <!-- Section 2: Vehicle Type -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span
                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">2</span>
            Select Vehicle / Truck
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button v-for="v in store.vehicleTypes" :key="v.key"
                class="p-4 rounded-xl border transition-all text-left relative overflow-hidden group"
                :class="form.vehicleType === v.key
                    ? 'border-green-500 bg-green-500/5 dark:bg-green-500/10 ring-1 ring-green-500/30'
                    : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/50'"
                @click="form.vehicleType = v.key">
                <div v-if="v.key === 'tempo'"
                    class="absolute top-0 right-0 px-2 py-0.5 bg-amber-500 text-white text-[8px] font-bold rounded-bl-lg">
                    POPULAR</div>
                <div class="flex items-center gap-3 mb-2">
                    <span class="material-symbols-outlined text-3xl"
                        :class="form.vehicleType === v.key ? 'text-green-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                        {{ v.icon }}
                    </span>
                    <div>
                        <div class="font-bold text-sm text-gray-900 dark:text-white">{{ v.name }}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">{{ v.capacity }}</div>
                    </div>
                </div>
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-500 dark:text-gray-400"><span
                            class="material-symbols-outlined text-[11px] align-middle">airline_seat_recline_extra</span>
                        {{ v.seats }} seats</span>
                    <span class="font-mono font-bold"
                        :class="form.vehicleType === v.key ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">×{{
                        v.priceMultiplier }}</span>
                </div>
                <div class="text-[10px] text-gray-400 mt-1">{{ v.desc }}</div>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { form, store } = inject(bookMovePageKey)
</script>
