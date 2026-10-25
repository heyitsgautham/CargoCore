<template>
    <transition name="slide-right">
    <div v-show="show" class="w-80 bg-white dark:bg-card-dark border-l border-gray-200 dark:border-white/5 flex flex-col z-10 glass-panel flex-shrink-0">
        <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Pending Loads ({{ pendingLoads.length }})</h3>
            <button @click="$emit('open-assign')"
                class="flex items-center gap-1 text-xs bg-primary text-black font-semibold px-2.5 py-1 rounded-md hover:bg-primary-dark transition-colors shadow-sm">
                <span class="material-symbols-outlined text-[14px]">add</span> Assign
            </button>
        </div>

        <div class="flex-1 overflow-y-auto no-scrollbar p-2 space-y-3">
            <!-- Drag hint -->
            <div v-if="pendingLoads.length" class="flex items-center gap-1.5 px-2 py-1 text-[10px] text-gray-400">
                <span class="material-symbols-outlined text-[12px]">drag_indicator</span>
                Drag load to an available driver on the left to assign
            </div>
            <div v-for="load in pendingLoads" :key="load.id"
                draggable="true" @dragstart="$emit('drag-start', $event, load)" @dragend="$emit('drag-end')"
                :class="[draggingLoad?.id === load.id ? 'opacity-50 scale-95 border-primary/40' : 'border-gray-200/60 dark:border-transparent hover:border-primary/30']"
                class="p-3 rounded-lg bg-gray-50 dark:bg-white/5 border transition-all select-none cursor-grab active:cursor-grabbing">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-gray-400 text-[14px] cursor-grab">drag_indicator</span>
                        <span class="text-xs font-mono text-gray-500 dark:text-gray-400">#{{ load.id }}</span>
                    </div>
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-bold"
                        :class="load.priority === 'URGENT' ? 'bg-red-500/20 text-red-400' : load.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'">{{ load.priority }}</span>
                </div>

                <div class="space-y-2 mb-3">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-gray-500 text-[14px]">inventory_2</span>
                        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ load.type }}</span>
                    </div>
                    <div class="flex justify-between text-[11px] text-gray-500 dark:text-gray-400">
                        <span>{{ load.weight }} kg</span>
                        <span>{{ load.volume }} m³</span>
                    </div>
                </div>

                <div class="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-white/5">
                    <div class="text-[10px] text-gray-500 dark:text-gray-400">Hub: <span class="text-gray-700 dark:text-gray-300 font-medium">{{ load.hub }}</span>
                    </div>
                    <button @click.stop="$emit('toggle-detail', load)" class="text-xs font-bold px-2 py-0.5 rounded transition-colors"
                        :class="expandedLoad?.id === load.id ? 'bg-primary/10 text-primary' : 'text-primary hover:bg-primary/10'">{{ expandedLoad?.id === load.id ? 'Close' : 'Details' }}</button>
                </div>
                <div v-if="expandedLoad?.id === load.id" class="mt-2 pt-2 border-t border-gray-200 dark:border-white/5 space-y-2">
                    <div class="grid grid-cols-2 gap-2">
                        <div class="p-1.5 bg-gray-100 dark:bg-black/20 rounded text-[10px]">
                            <span class="text-gray-500 block">Origin</span>
                            <span class="text-gray-900 dark:text-white font-medium">{{ load.hub }} Warehouse</span>
                        </div>
                        <div class="p-1.5 bg-gray-100 dark:bg-black/20 rounded text-[10px]">
                            <span class="text-gray-500 block">Window (Today)</span>
                            <span class="text-gray-900 dark:text-white font-medium">{{ load.deadline ? new Date(load.deadline).toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', hour12:false}) : 'TBD' }}</span>
                        </div>
                    </div>
                    <div class="p-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded text-[10px] flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-yellow-400 text-[12px]">schedule</span>
                        <span class="text-yellow-600 dark:text-yellow-300 font-medium">Unassigned — Awaiting dispatch</span>
                    </div>
                    <button @click.stop="$emit('assign-load', load)" class="w-full text-center bg-primary hover:bg-primary-dark text-black font-bold py-1.5 rounded-lg text-xs transition-colors flex items-center justify-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">assignment_turned_in</span>
                        Quick Assign
                    </button>
                </div>
            </div>
        </div>

        <!-- Bottom Summary -->
        <div class="p-4 border-t border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20">
            <div class="text-xs text-gray-500 mb-2">Overall SLA Projection</div>
            <div class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-1">
                <div class="h-full bg-gradient-to-r from-yellow-500 to-green-500 transition-all" :style="{ width: slaProjection.pct + '%' }"></div>
            </div>
            <div class="flex justify-between text-[10px]">
                <span class="text-gray-900 dark:text-white">{{ slaProjection.pct }}% Predicted</span>
                <span :class="slaProjection.delta >= 0 ? 'text-green-400' : 'text-red-400'">{{ slaProjection.delta >= 0 ? '+' : '' }}{{ slaProjection.delta }}% vs Target</span>
            </div>
        </div>
    </div>
    </transition>
</template>

<script setup>
defineProps({
    show: { type: Boolean, default: false },
    pendingLoads: { type: Array, required: true },
    draggingLoad: { type: Object, default: null },
    expandedLoad: { type: Object, default: null },
    slaProjection: { type: Object, required: true },
})

defineEmits(['open-assign', 'drag-start', 'drag-end', 'toggle-detail', 'assign-load'])
</script>

<style scoped>
.slide-right-enter-active, .slide-right-leave-active {
    transition: width 0.3s ease, opacity 0.3s ease;
    overflow: hidden;
}
.slide-right-enter-from, .slide-right-leave-to {
    width: 0 !important;
    opacity: 0;
}
</style>
