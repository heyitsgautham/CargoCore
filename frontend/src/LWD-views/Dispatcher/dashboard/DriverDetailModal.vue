<template>
    <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="$emit('close')">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-md m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <div class="flex items-center gap-4 mb-5">
                <img :src="driver?.avatar" class="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 ring-2 ring-primary/30 object-cover">
                <div>
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ driver?.name }}</h3>
                    <p class="text-sm text-gray-500">{{ driver?.vehicle }} • {{ driver?.id }}</p>
                    <div class="flex items-center gap-1.5 mt-1">
                        <span class="w-2 h-2 rounded-full" :class="driver?.statusColor"></span>
                        <span class="text-xs" :class="driver?.statusColor === 'bg-green-500' ? 'text-green-500' : driver?.statusColor === 'bg-yellow-500' ? 'text-yellow-500' : 'text-gray-500'">{{ driver?.statusColor === 'bg-green-500' ? 'Active' : driver?.statusColor === 'bg-yellow-500' ? 'Busy' : 'Offline' }}</span>
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-3 gap-3 mb-5">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Load</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ driver?.load }}%</div>
                    <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full mt-1 overflow-hidden">
                        <div class="h-full rounded-full" :class="driver?.load > 80 ? 'bg-red-500' : 'bg-primary'" :style="{ width: driver?.load + '%' }"></div>
                    </div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Hours Left</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white">{{ driver?.hours }}h</div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                    <div class="text-xs text-gray-500 mb-1">Location</div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{{ driver?.location }}</div>
                </div>
            </div>
            <div class="flex gap-2">
                <button @click="$emit('chat', driver); $emit('close')" class="flex-1 bg-primary hover:bg-primary-dark text-black font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">chat</span> Chat
                </button>
                <button @click="$emit('assign')" class="flex-1 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-900 dark:text-white font-bold py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">add_circle</span> Assign Load
                </button>
                <button @click="$emit('close')" class="px-4 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-400 py-2 rounded-lg text-sm transition-colors">
                    <span class="material-symbols-outlined text-[16px]">close</span>
                </button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
defineProps({
    show: { type: Boolean, default: false },
    driver: { type: Object, default: null },
})

defineEmits(['close', 'chat', 'assign'])
</script>
