<template>
    <div class="glass-panel p-4 rounded-xl">
        <div class="flex flex-col md:flex-row gap-3">
            <div class="flex-1 relative">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search by Order ID, Type..."
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50" />
            </div>
            <div class="flex flex-wrap gap-2">
                <button v-for="filter in statusFilters" :key="filter.value"
                    @click="$emit('toggle-status', filter.value)"
                    class="px-3 py-2 rounded-lg text-xs font-bold transition-all border"
                    :class="activeStatusFilters.includes(filter.value)
                        ? 'bg-primary text-background-dark border-primary'
                        : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-white/10 hover:border-primary/50'">
                    {{ filter.label }}
                </button>
                <select v-model="priorityFilter"
                    class="px-3 py-2 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white text-xs focus:outline-none focus:border-primary/50">
                    <option value="">All Priorities</option>
                    <option value="EXPRESS">🔥 Express</option>
                    <option value="STANDARD">📦 Standard</option>
                    <option value="ECONOMY">🐢 Economy</option>
                </select>
                <button v-if="hasActiveFilters" @click="$emit('clear')"
                    class="px-3 py-2 bg-red-500/10 text-red-500 rounded-lg text-xs font-bold hover:bg-red-500/20 transition-colors">
                    Clear
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
const searchQuery = defineModel('search', { type: String, required: true })
const priorityFilter = defineModel('priority', { type: String, required: true })

defineProps({
    statusFilters: { type: Array, required: true },
    activeStatusFilters: { type: Array, required: true },
    hasActiveFilters: { type: Boolean, default: false },
})

defineEmits(['toggle-status', 'clear'])
</script>
