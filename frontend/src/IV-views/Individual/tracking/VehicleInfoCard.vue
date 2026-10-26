<template>
    <!-- Vehicle Info -->
    <div class="glass-panel p-4 sm:p-5 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Vehicle & Order</h3>
        <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Order
                    ID</span><span class="font-mono font-bold text-green-600 dark:text-green-400">{{
                        activeMove.id }}</span></div>
            <div class="flex justify-between"><span
                    class="text-gray-500 dark:text-gray-400">Vehicle</span><span
                    class="text-gray-900 dark:text-white font-medium uppercase">{{ activeMove.vehicleType
                    }}</span></div>
            <div class="flex justify-between"><span
                    class="text-gray-500 dark:text-gray-400">Cargo</span><span
                    class="text-gray-900 dark:text-white font-medium">{{ activeMove.cargoType }}</span>
            </div>
            <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Service
                    Block</span><span class="text-purple-600 dark:text-purple-400 font-medium">{{
                        activeMove.serviceTimeBlock }}</span></div>
            <div class="flex justify-between"><span
                    class="text-gray-500 dark:text-gray-400">Helpers</span><span
                    class="text-gray-900 dark:text-white font-medium">{{ activeMove.laborCount }}
                    assigned</span></div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove } = inject(customerTrackingPageKey)
</script>
