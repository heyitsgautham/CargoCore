<template>
    <!-- Rack container — sized to fill available space when in section view -->
    <div class="relative select-none rounded-xl border transition-all duration-200 overflow-hidden"
        :style="containerStyle" :class="[isSelected ? 'ring-2 ring-primary shadow-lg shadow-primary/20' : '',
        isHighlighted ? 'search-highlight' : '',
        isEditMode ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer']" @mousedown.stop="onMouseDown"
        @click.stop="$emit('rackclick')">

        <!-- Rack header -->
        <div class="flex items-center justify-between px-3 py-1.5 border-b border-purple-500/20 bg-purple-500/10">
            <span class="text-xs font-bold text-purple-400 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">grid_view</span>
                {{ rack.label }}
            </span>
            <span class="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">
                {{ totalProducts }}/{{ rack.rows * rack.cols }} cells
            </span>
        </div>

        <!-- Cell grid — fills the remaining space -->
        <div class="grid gap-[2px] p-2 flex-1" :style="gridStyle">
            <div v-for="cell in cellGrid" :key="cell.id"
                class="rounded border flex items-center justify-center text-[10px] relative group/cell transition-all duration-150 min-h-[24px]"
                :class="getCellClasses(cell)" @click.stop="onCellClick(cell, $event)"
                @mouseenter="onCellHover(cell, $event)" @mouseleave="hoveredCell = null">
                <template v-if="cell.product">
                    <span class="font-bold">●</span>
                </template>
                <template v-else>
                    <span class="text-purple-500/30">○</span>
                </template>
            </div>
        </div>

        <!-- Open/expand button overlay (non-edit mode) -->
        <div v-if="!isEditMode"
            class="absolute inset-0 bg-black/0 group-hover:bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200">
            <span
                class="bg-white/90 text-gray-900 px-4 py-1.5 rounded-full text-[11px] font-bold shadow-lg flex items-center gap-1 transform scale-90 group-hover:scale-100 transition-transform">
                <span class="material-symbols-outlined text-[14px]">zoom_in</span>
                View Cells
            </span>
        </div>

        <!-- Resize handle (edit mode) -->
        <div v-if="isEditMode && isSelected" class="absolute bottom-0 right-0 w-5 h-5 cursor-se-resize z-30"
            @mousedown.stop="$emit('resizestart', $event)">
            <div class="w-3 h-3 border-r-2 border-b-2 border-primary rounded-br absolute bottom-0.5 right-0.5">
            </div>
        </div>

        <!-- Search highlight tooltip (only on the highlighted rack) -->
        <div v-if="isHighlighted && highlightProducts.length"
            class="absolute -top-16 left-1/2 -translate-x-1/2 w-52 bg-gray-900 dark:bg-black text-white p-2.5 rounded-xl shadow-2xl z-50 search-tooltip pointer-events-none border border-primary/40">
            <div class="text-[10px] font-bold text-primary mb-1">📦 {{ rack.label }}</div>
            <div v-for="p in highlightProducts" :key="p.sku" class="text-[9px] text-gray-300">
                • {{ p.name }} <span class="text-white font-bold">{{ p.qty }} {{ p.unit }}</span>
            </div>
            <div
                class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2.5 h-2.5 bg-gray-900 dark:bg-black rotate-45 border-r border-b border-primary/40">
            </div>
        </div>

        <!-- Inline hover tooltip -->
        <div v-if="hoveredCell?.product && !activeTooltipCell"
            class="absolute bg-black/95 text-white p-2.5 rounded-lg text-[9px] z-[60] pointer-events-none shadow-xl min-w-[160px] border border-white/10"
            :style="hoverTooltipStyle">
            <div class="font-bold text-primary text-[10px]">{{ hoveredCell.product.name }}</div>
            <div class="text-gray-400 mt-0.5">{{ hoveredCell.product.sku }} · {{ hoveredCell.product.qty }} {{
                hoveredCell.product.unit }}</div>
            <div class="text-gray-500">Order: {{ hoveredCell.product.orderId }}</div>
            <div v-if="hoveredCell.product.rma" class="text-yellow-400 font-bold">⚠ RMA: {{ hoveredCell.product.rma }}
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
    rack: { type: Object, required: true },
    cellGrid: { type: Array, required: true },
    totalProducts: { type: Number, default: 0 },
    isSelected: { type: Boolean, default: false },
    isHighlighted: { type: Boolean, default: false },
    isEditMode: { type: Boolean, default: false },
    highlightProducts: { type: Array, default: () => [] },
    highlightedCellKeys: { type: Array, default: () => [] },
    activeTooltipCell: { type: Object, default: null },
    // For absolute positioning in floor canvas
    useAbsolutePosition: { type: Boolean, default: false }
})

const emit = defineEmits(['dragstart', 'resizestart', 'rackclick', 'cellclick'])

const hoveredCell = ref(null)
const hoverPos = ref({ x: 0, y: 0 })

const containerStyle = computed(() => {
    const base = {
        borderColor: 'rgba(168, 85, 247, 0.3)',
        background: 'rgba(168, 85, 247, 0.05)'
    }
    if (props.useAbsolutePosition) {
        return {
            ...base,
            position: 'absolute',
            left: props.rack.x + 'px',
            top: props.rack.y + 'px',
            width: props.rack.w + 'px',
            height: props.rack.h + 'px'
        }
    }
    return base
})

const gridStyle = computed(() => ({
    gridTemplateColumns: `repeat(${props.rack.cols || 4}, 1fr)`,
    gridTemplateRows: `repeat(${props.rack.rows || 3}, 1fr)`
}))

const hoverTooltipStyle = computed(() => {
    // Position tooltip below if near top, otherwise above
    const nearTop = hoverPos.value.y < 80
    return {
        left: Math.max(10, Math.min(hoverPos.value.x, 200)) + 'px',
        ...(nearTop
            ? { top: (hoverPos.value.y + 30) + 'px' }
            : { top: (hoverPos.value.y - 8) + 'px', transform: 'translate(-50%, -100%)' }
        )
    }
})

function getCellClasses(cell) {
    const isHighlightedCell = props.highlightedCellKeys.includes(`${props.rack.id}:${cell.index}`)
    const isActiveTooltip = props.activeTooltipCell?.id === cell.id
    if (isActiveTooltip) {
        return 'border-primary bg-primary/40 text-primary scale-110 ring-2 ring-primary/50 cursor-pointer z-10'
    }
    if (isHighlightedCell) {
        return 'border-primary bg-primary/30 text-primary animate-pulse cursor-pointer'
    }
    if (cell.product) {
        return 'border-purple-400/60 bg-purple-500/25 text-purple-300 cursor-pointer hover:bg-purple-500/40 hover:border-purple-400 hover:scale-105'
    }
    return 'border-purple-500/20 bg-purple-500/5 text-transparent cursor-default'
}

function onMouseDown(e) {
    if (props.isEditMode) {
        emit('dragstart', e)
    }
}

function onCellClick(cell, event) {
    if (cell.product) {
        event.stopPropagation()
        emit('cellclick', { cell, rackId: props.rack.id, event })
    }
}

function onCellHover(cell, event) {
    if (!cell.product) return
    hoveredCell.value = cell
    const rect = event.target.getBoundingClientRect()
    const container = event.target.closest('.relative.select-none')
    const containerRect = container?.getBoundingClientRect()
    if (containerRect) {
        hoverPos.value = {
            x: rect.left - containerRect.left + rect.width / 2,
            y: rect.top - containerRect.top
        }
    }
}
</script>
