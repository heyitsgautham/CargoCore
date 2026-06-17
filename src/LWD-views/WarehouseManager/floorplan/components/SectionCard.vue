<template>
    <div class="absolute select-none" :style="posStyle" :class="containerClasses" @mousedown.stop="onMouseDown"
        @click.stop="$emit('click')">

        <!-- Card body -->
        <div class="w-full h-full rounded-lg border-2 flex flex-col items-center justify-center gap-1 text-[10px] font-bold relative overflow-hidden group hover:shadow-xl transition-all duration-200"
            :style="cardStyle">
            <span class="material-symbols-outlined text-[20px] opacity-60"
                :style="{ color: groupColor }">inventory_2</span>
            <span :style="{ color: groupColor }">{{ section.label }}</span>
            <span class="text-[8px] opacity-50" :style="{ color: groupColor }">{{ categoryName }}</span>

            <!-- Rack count badge -->
            <span class="absolute top-1 right-1 text-[8px] px-1 py-0.5 rounded font-bold"
                :style="{ background: groupColor + '20', color: groupColor }">{{ rackCount }} racks</span>

            <!-- Item count badge -->
            <span v-if="productCount"
                class="absolute bottom-1 right-1 text-[7px] px-1 py-0.5 rounded bg-primary/20 text-primary font-bold">
                {{ productCount }} items</span>

            <!-- OPEN button overlay (hover) -->
            <div v-if="!isEditMode"
                class="absolute inset-0 bg-black/0 group-hover:bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 rounded-lg">
                <span
                    class="bg-white/90 text-gray-900 px-4 py-1.5 rounded-full text-[11px] font-bold shadow-lg flex items-center gap-1 transform scale-90 group-hover:scale-100 transition-transform">
                    <span class="material-symbols-outlined text-[14px]">open_in_full</span>
                    Open
                </span>
            </div>
        </div>

        <!-- Resize handle (edit mode) -->
        <div v-if="isEditMode && isSelected" class="absolute bottom-0 right-0 w-5 h-5 cursor-se-resize z-30"
            @mousedown.stop="$emit('resizestart', $event)">
            <div class="w-3 h-3 border-r-2 border-b-2 border-primary rounded-br absolute bottom-0.5 right-0.5">
            </div>
        </div>

        <!-- Search highlight tooltip (only on the highlighted section) -->
        <div v-if="isHighlighted && highlightProducts.length"
            class="absolute -top-20 left-1/2 -translate-x-1/2 w-52 bg-gray-900 dark:bg-black text-white p-2.5 rounded-xl shadow-2xl z-50 search-tooltip pointer-events-none border border-primary/40">
            <div class="text-[10px] font-bold text-primary mb-1">📦 {{ highlightProducts.length }} product(s) found
            </div>
            <div v-for="p in highlightProducts.slice(0, 3)" :key="p.sku" class="text-[9px] text-gray-300">
                • {{ p.name }} <span class="text-gray-500">({{ p.sku }})</span>
            </div>
            <div v-if="highlightProducts.length > 3" class="text-[9px] text-gray-500 mt-0.5">
                +{{ highlightProducts.length - 3 }} more...
            </div>
            <div
                class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2.5 h-2.5 bg-gray-900 dark:bg-black rotate-45 border-r border-b border-primary/40">
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    section: { type: Object, required: true },
    groupColor: { type: String, default: '#6b7280' },
    categoryName: { type: String, default: '' },
    rackCount: { type: Number, default: 0 },
    productCount: { type: Number, default: 0 },
    isSelected: { type: Boolean, default: false },
    isHighlighted: { type: Boolean, default: false },
    isEditMode: { type: Boolean, default: false },
    highlightProducts: { type: Array, default: () => [] }
})

const emit = defineEmits(['click', 'dragstart', 'resizestart'])

const posStyle = computed(() => ({
    left: props.section.x + 'px',
    top: props.section.y + 'px',
    width: props.section.w + 'px',
    height: props.section.h + 'px'
}))

const containerClasses = computed(() => [
    props.isSelected ? 'ring-2 ring-primary shadow-lg shadow-primary/20 z-20' : 'z-10',
    props.isEditMode ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
    props.isHighlighted ? 'search-highlight z-30' : ''
])

const cardStyle = computed(() => ({
    borderColor: props.groupColor + '80',
    background: props.groupColor + '18'
}))

function onMouseDown(e) {
    if (props.isEditMode) {
        emit('dragstart', e)
    }
}
</script>
