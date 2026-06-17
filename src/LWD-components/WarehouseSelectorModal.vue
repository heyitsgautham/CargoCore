<template>
    <BaseModal :is-open="isOpen" @close="$emit('close')">
        <template #title>Select Warehouse Context</template>

        <div class="grid grid-cols-1 gap-3">
            <button @click="selectWarehouse('all')"
                class="flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 group text-left"
                :class="activeId === 'all' ? 'bg-primary/10 border-primary' : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-300 dark:hover:border-white/20'">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                    :class="activeId === 'all' ? 'bg-primary/20 text-primary' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'">
                    <span class="material-symbols-outlined">public</span>
                </div>
                <div>
                    <div class="font-bold text-gray-900 dark:text-white">All Warehouses</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Global View</div>
                </div>
                <div v-if="activeId === 'all'" class="ml-auto text-primary">
                    <span class="material-symbols-outlined">check_circle</span>
                </div>
            </button>

            <div v-for="hub in hubs" :key="hub.id" @click="selectWarehouse(hub.id)"
                class="flex items-center gap-4 p-4 rounded-xl border transition-all duration-200 group cursor-pointer"
                :class="activeId === hub.id ? 'bg-primary/10 border-primary' : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-300 dark:hover:border-white/20'">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white shadow-lg"
                    :class="hub.bg || 'bg-gray-700'">
                    {{ hub.name.charAt(0) }}
                </div>
                <div class="flex-1">
                    <div class="flex justify-between items-start">
                        <div class="font-bold text-gray-900 dark:text-white">{{ hub.name }}</div>
                        <span class="text-[10px] px-1.5 py-0.5 rounded border" :class="getStatusClass(hub.status)">{{
                            hub.status
                            }}</span>
                    </div>
                    <div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>Cap: {{ hub.capacity }}%</span>
                        <span>•</span>
                        <span>{{ hub.processRate }} pkgs/hr</span>
                    </div>
                </div>
            </div>
        </div>
    </BaseModal>
</template>

<script setup>
import BaseModal from '../components/BaseModal.vue'

const props = defineProps({
    isOpen: Boolean,
    hubs: Array,
    activeId: [String, Number]
})

const emit = defineEmits(['close', 'select'])

function selectWarehouse(id) {
    emit('select', id)
}

function getStatusClass(status) {
    if (!status) return ''
    switch (status.toLowerCase()) {
        case 'optimal': return 'bg-green-500/20 text-green-400 border-green-500/30'
        case 'congested': return 'bg-red-500/20 text-red-400 border-red-500/30'
        case 'high load': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
        default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
}
</script>
