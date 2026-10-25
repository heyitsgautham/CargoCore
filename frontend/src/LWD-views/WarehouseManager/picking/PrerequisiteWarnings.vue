<template>
    <div v-if="warnings.length > 0"
        class="glass-panel p-4 rounded-xl border border-amber-500/40 bg-amber-500/5">
        <div class="flex items-center gap-2 mb-3">
            <span class="material-symbols-outlined text-amber-500 text-[22px]">warning</span>
            <span class="font-bold text-amber-600 dark:text-amber-400 text-sm">Picking Prerequisites Not Met</span>
        </div>
        <ul class="space-y-2 mb-3">
            <li v-for="(warning, idx) in warnings" :key="idx"
                class="flex items-start gap-2 text-xs text-amber-700 dark:text-amber-300">
                <span class="material-symbols-outlined text-[14px] mt-0.5 shrink-0">error_outline</span>
                {{ warning }}
            </li>
        </ul>
        <p class="text-xs text-amber-600 dark:text-amber-400 font-medium">
            Orders cannot be moved to picking until all prerequisites above are resolved.
        </p>
    </div>
</template>

<script setup>
defineProps({
    warnings: { type: Array, required: true },
})
</script>
