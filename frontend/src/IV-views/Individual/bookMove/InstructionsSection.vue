<template>
    <!-- Section 5: Instructions -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span
                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">5</span>
            Special Instructions
        </h3>
        <textarea v-model="form.instructions" rows="3"
            placeholder="e.g., Handle fragile items carefully, use service elevator..."
            class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 outline-none resize-none"></textarea>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { form } = inject(bookMovePageKey)
</script>
