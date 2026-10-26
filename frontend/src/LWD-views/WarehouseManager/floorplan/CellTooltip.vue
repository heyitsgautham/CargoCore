<template>
    <!-- ═══ Floating Tooltip (pinned to canvas container) ═══ -->
    <div v-if="tooltipData" class="absolute z-[100] pointer-events-auto" :style="tooltipFloatStyle">
        <div
            class="bg-gray-900/95 dark:bg-black/95 text-white p-4 rounded-xl shadow-2xl border border-primary/30 min-w-[240px] max-w-[320px] backdrop-blur-sm">
            <div class="text-[9px] text-gray-500 mb-1.5 flex items-center gap-1 flex-wrap">
                <span>{{ currentFloorLabel }}</span><span>›</span>
                <span>{{ activeSection?.label || tooltipData.sectionLabel }}</span><span>›</span>
                <span>{{ tooltipData.rackLabel }}</span><span>›</span>
                <span class="text-primary font-bold">R{{ tooltipData.cell.row }}C{{
                    tooltipData.cell.col
                    }}</span>
            </div>
            <div class="font-bold text-primary text-sm mb-1">{{ tooltipData.product.name }}</div>
            <div class="space-y-0.5 text-[11px]">
                <div class="flex justify-between"><span class="text-gray-400">SKU</span><span
                        class="font-bold text-gray-200">{{ tooltipData.product.sku }}</span></div>
                <div class="flex justify-between"><span class="text-gray-400">Qty</span><span
                        class="font-bold text-white">{{ tooltipData.product.qty }} {{
                            tooltipData.product.unit }}</span>
                </div>
                <div class="flex justify-between"><span class="text-gray-400">Order</span><span
                        class="font-bold text-gray-200">{{ tooltipData.product.orderId }}</span>
                </div>
                <div v-if="tooltipData.product.rma" class="flex justify-between"><span
                        class="text-yellow-400">⚠
                        RMA</span><span class="font-bold text-yellow-400">{{ tooltipData.product.rma
                        }}</span></div>
            </div>
            <button @click="tooltipData = null"
                class="absolute top-2 right-2 text-gray-500 hover:text-white w-5 h-5 flex items-center justify-center rounded-full hover:bg-white/10">
                <span class="material-symbols-outlined text-[14px]">close</span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { floorPlanPageKey } from './floorPlanPageContext'

const { activeSection, currentFloorLabel, tooltipData, tooltipFloatStyle } = inject(floorPlanPageKey)
</script>
