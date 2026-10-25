<template>
    <div class="flex overflow-x-auto px-4 gap-1 pb-0">
        <button @click="selectedStatusTab = 'ALL'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'ALL'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            All
            <span class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-gray-200 dark:bg-white/10">
                {{ totalCount }}
            </span>
        </button>
        <button @click="selectedStatusTab = 'ON_HOLD'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'ON_HOLD'
                ? 'border-red-500 text-red-600 dark:text-red-400 bg-red-500/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            <span class="inline-flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-red-500"></span>
                On Hold
            </span>
            <span v-if="wavesByStatus.ON_HOLD?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-red-500/20 text-red-600 dark:text-red-400">
                {{ wavesByStatus.ON_HOLD.length }}
            </span>
        </button>
        <button @click="selectedStatusTab = 'AWAITING_PICK'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'AWAITING_PICK'
                ? 'border-yellow-500 text-yellow-600 dark:text-yellow-400 bg-yellow-500/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            <span class="inline-flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
                Awaiting
            </span>
            <span v-if="wavesByStatus.AWAITING_PICK?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-yellow-500/20 text-yellow-600 dark:text-yellow-400">
                {{ wavesByStatus.AWAITING_PICK.length }}
            </span>
        </button>
        <button @click="selectedStatusTab = 'PICKING'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'PICKING'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-500/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            <span class="inline-flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                Picking
            </span>
            <span v-if="wavesByStatus.PICKING?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-blue-500/20 text-blue-600 dark:text-blue-400">
                {{ wavesByStatus.PICKING.length }}
            </span>
        </button>
        <button @click="selectedStatusTab = 'PICKED'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'PICKED'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-cyan-500/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            <span class="inline-flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-cyan-500"></span>
                Picked
            </span>
            <span v-if="wavesByStatus.PICKED?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-600 dark:text-cyan-400">
                {{ wavesByStatus.PICKED.length }}
            </span>
        </button>
        <button @click="selectedStatusTab = 'PACKING'"
            class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
            :class="selectedStatusTab === 'PACKING'
                ? 'border-green-500 text-green-600 dark:text-green-400 bg-green-500/5'
                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
            <span class="inline-flex items-center gap-1">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                Packing
            </span>
            <span v-if="wavesByStatus.PACKING?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-green-500/20 text-green-600 dark:text-green-400">
                {{ wavesByStatus.PACKING.length }}
            </span>
        </button>
    </div>
</template>

<script setup>
const selectedStatusTab = defineModel({ type: String, required: true })

defineProps({
    totalCount: { type: Number, required: true },
    wavesByStatus: { type: Object, required: true },
})
</script>
