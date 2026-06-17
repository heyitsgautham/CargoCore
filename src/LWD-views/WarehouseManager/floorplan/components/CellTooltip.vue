<template>
    <div class="absolute select-none p-2 rounded-lg text-[9px] z-50 pointer-events-none" :style="tooltipStyle">
        <div class="bg-black/95 text-white p-3 rounded-xl shadow-2xl border border-primary/30 min-w-[180px]">
            <!-- Full path breadcrumb -->
            <div class="flex items-center gap-1 text-[8px] text-gray-500 mb-2 pb-1.5 border-b border-white/10">
                <span>{{ path.floor }}</span>
                <span class="text-gray-600">›</span>
                <span>{{ path.section }}</span>
                <span class="text-gray-600">›</span>
                <span>{{ path.rack }}</span>
                <span class="text-gray-600">›</span>
                <span class="text-primary font-bold">{{ path.cell }}</span>
            </div>
            <!-- Product info -->
            <div class="font-bold text-primary text-[11px] mb-1">{{ product.name }}</div>
            <div class="space-y-0.5">
                <div class="text-gray-400">
                    SKU: <span class="text-gray-200 font-bold">{{ product.sku }}</span>
                </div>
                <div class="text-gray-400">
                    Qty: <span class="text-white font-bold">{{ product.qty }} {{ product.unit }}</span>
                </div>
                <div class="text-gray-400">
                    Order: <span class="text-gray-200">{{ product.orderId }}</span>
                </div>
                <div v-if="product.rma" class="text-yellow-400 font-bold">
                    ⚠ RMA: {{ product.rma }}
                </div>
            </div>
            <!-- Arrow -->
            <div
                class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2.5 h-2.5 bg-black/95 rotate-45 border-r border-b border-primary/30">
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    product: { type: Object, required: true },
    path: { type: Object, required: true },
    x: { type: Number, default: 0 },
    y: { type: Number, default: 0 }
})

const tooltipStyle = computed(() => ({
    left: props.x + 'px',
    top: (props.y - 8) + 'px',
    transform: 'translate(-50%, -100%)'
}))
</script>
