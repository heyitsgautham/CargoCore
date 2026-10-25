<template>
    <Teleport to="body">
        <div v-if="show"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="emit('close')">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">group_add</span>
                            Assign Labourers
                        </h3>
                        <p class="text-xs text-gray-500 mt-1">
                            Order: {{ wave?.id }} requires
                            <span class="text-primary font-bold">{{ wave?.laborRequired || 1 }}</span> labourer(s)
                        </p>
                    </div>
                    <button @click="emit('close')" class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6">
                    <div v-if="loading" class="flex items-center justify-center py-4">
                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    </div>
                    <div v-else>
                        <!-- Selection Counter -->
                        <div class="flex items-center justify-between mb-4 p-3 rounded-lg"
                            :class="selected.length >= (wave?.laborRequired || 1)
                                ? 'bg-green-500/20 border border-green-500/30'
                                : 'bg-yellow-500/20 border border-yellow-500/30'">
                            <span class="text-sm font-medium"
                                :class="selected.length >= (wave?.laborRequired || 1)
                                    ? 'text-green-600 dark:text-green-400'
                                    : 'text-yellow-600 dark:text-yellow-400'">
                                {{ selected.length }} / {{ wave?.laborRequired || 1 }} labourers selected
                            </span>
                            <span v-if="selected.length >= (wave?.laborRequired || 1)"
                                class="material-symbols-outlined text-green-500 text-[18px]">check_circle</span>
                            <span v-else class="material-symbols-outlined text-yellow-500 text-[18px]">info</span>
                        </div>

                        <!-- Selected Labourers -->
                        <div v-if="selected.length > 0" class="mb-4">
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Selected:</label>
                            <div class="flex flex-wrap gap-2">
                                <span v-for="labourer in selected" :key="labourer.id"
                                    class="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/20 text-primary rounded-full text-sm font-medium">
                                    {{ labourer.name || labourer.full_name }}
                                    <button @click="emit('toggle', labourer)" class="hover:text-red-500">
                                        <span class="material-symbols-outlined text-[14px]">close</span>
                                    </button>
                                </span>
                            </div>
                        </div>

                        <!-- Available Labourers List -->
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Available Labourers:</label>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            <div v-for="labourer in available" :key="labourer.id"
                                @click="emit('toggle', labourer)"
                                class="p-3 rounded-lg border cursor-pointer transition-all"
                                :class="isSelected(labourer)
                                    ? 'bg-primary/20 border-primary'
                                    : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5 hover:border-primary/50'">
                                <div class="flex justify-between items-center">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                                            :class="isSelected(labourer)
                                                ? 'bg-primary text-white'
                                                : 'bg-primary/20 text-primary'">
                                            {{ (labourer.name || labourer.full_name || '?')[0].toUpperCase() }}
                                        </div>
                                        <div>
                                            <div class="font-bold text-gray-900 dark:text-white text-sm">
                                                {{ labourer.name || labourer.full_name }}
                                            </div>
                                            <div class="text-xs text-gray-500">
                                                {{ labourer.skill_tags?.join(', ') || 'Warehouse Labour' }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="px-2 py-0.5 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-[10px] font-bold">
                                            Available
                                        </span>
                                        <span v-if="isSelected(labourer)"
                                            class="material-symbols-outlined text-primary text-[18px]">check_circle</span>
                                    </div>
                                </div>
                            </div>
                            <div v-if="available.length === 0" class="text-center py-8 text-gray-500">
                                <span class="material-symbols-outlined text-4xl mb-2 opacity-50">group_off</span>
                                <p class="text-sm">No available labourers</p>
                                <p class="text-xs mt-1">All labourers are currently assigned to other orders</p>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="flex gap-2 mt-4">
                            <button @click="emit('close')"
                                class="flex-1 py-3 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg font-bold transition-colors hover:bg-gray-200 dark:hover:bg-white/20">
                                Cancel
                            </button>
                            <button @click="emit('assign')"
                                :disabled="selected.length < (wave?.laborRequired || 1) || assigning"
                                class="flex-1 py-3 bg-primary text-background-dark rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                                <span v-if="assigning" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                                <span>{{ assigning ? 'Assigning...' : 'Assign & Continue' }}</span>
                            </button>
                        </div>

                        <p v-if="selected.length < (wave?.laborRequired || 1)"
                            class="text-xs text-center text-yellow-600 dark:text-yellow-400 mt-3">
                            Select {{ (wave?.laborRequired || 1) - selected.length }} more labourer(s) to proceed
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
const props = defineProps({
    show: { type: Boolean, default: false },
    wave: { type: Object, default: null },
    loading: { type: Boolean, default: false },
    assigning: { type: Boolean, default: false },
    available: { type: Array, required: true },
    selected: { type: Array, required: true },
})

const emit = defineEmits(['close', 'toggle', 'assign'])

function isSelected(labourer) {
    return props.selected.some(l => l.id === labourer.id)
}
</script>
