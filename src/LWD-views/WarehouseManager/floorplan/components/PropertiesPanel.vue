<template>
    <div class="glass-panel rounded-xl p-4 space-y-3" v-if="element">
        <h3 class="font-bold text-gray-900 dark:text-white text-sm flex items-center gap-1">
            <span class="material-symbols-outlined text-[16px] text-primary">settings</span>Properties
        </h3>
        <div>
            <label class="text-[10px] text-gray-500 block">Label</label>
            <input v-model="element.label"
                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
        </div>
        <!-- Category selector (sections only) -->
        <div v-if="isSection">
            <label class="text-[10px] text-gray-500 block">Category</label>
            <select v-model="element.groupId"
                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none">
                <option :value="null" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Uncategorized</option>
                <option v-for="category in categories" :key="category.id" :value="category.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ category.name }}</option>
            </select>
        </div>
        <!-- Dimensions -->
        <div class="grid grid-cols-2 gap-2">
            <div>
                <label class="text-[10px] text-gray-500 block">W</label>
                <input type="number" v-model.number="element.w" min="40"
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
                <label class="text-[10px] text-gray-500 block">H</label>
                <input type="number" v-model.number="element.h" min="40"
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
        </div>
        <!-- Rows/Cols for racks -->
        <div v-if="isRack" class="grid grid-cols-2 gap-2">
            <div>
                <label class="text-[10px] text-gray-500 block">Rows</label>
                <input type="number" v-model.number="element.rows" min="1" max="20"
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
                <label class="text-[10px] text-gray-500 block">Cols</label>
                <input type="number" v-model.number="element.cols" min="1" max="20"
                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    element: { type: Object, default: null },
    elementType: { type: String, default: 'section' },
    categories: { type: Array, default: () => [] }
})

const isSection = computed(() => props.elementType === 'section')
const isRack = computed(() => props.elementType === 'rack')
</script>
