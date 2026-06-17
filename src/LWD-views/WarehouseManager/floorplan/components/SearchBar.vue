<template>
    <div class="relative w-80">
        <span
            class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-[20px]">search</span>
        <input :value="modelValue" @input="$emit('update:modelValue', $event.target.value); $emit('search')" type="text"
            placeholder="Search Order ID, SKU, RMA, product..."
            class="w-full pl-10 pr-8 py-2 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />

        <!-- Clear button -->
        <button v-if="modelValue"
            @click="$emit('update:modelValue', ''); $emit('clear')"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
            <span class="material-symbols-outlined text-[16px]">close</span>
        </button>

        <!-- Results dropdown -->
        <div v-if="results.length && modelValue"
            class="absolute top-full mt-1 left-0 right-0 bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto">
            <div v-for="r in results" :key="r.product.sku + r.rackId" @click="$emit('focus-result', r)"
                class="px-4 py-2.5 hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer border-b border-gray-100 dark:border-white/5 last:border-0">
                <div class="flex justify-between items-center">
                    <span class="text-sm font-bold text-gray-900 dark:text-white">{{ r.product.name }}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded bg-primary/10 text-primary font-bold">
                        {{ r.sectionLabel }} → {{ r.rackLabel }}
                    </span>
                </div>
                <div class="flex gap-3 mt-0.5 text-[10px] text-gray-500">
                    <span>SKU: <b class="text-gray-700 dark:text-gray-300">{{ r.product.sku }}</b></span>
                    <span>Order: <b class="text-gray-700 dark:text-gray-300">{{ r.product.orderId }}</b></span>
                    <span v-if="r.product.rma">RMA: <b class="text-yellow-500">{{ r.product.rma }}</b></span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    modelValue: { type: String, default: '' },
    results: { type: Array, default: () => [] }
})

defineEmits(['update:modelValue', 'search', 'focus-result', 'clear'])
</script>
