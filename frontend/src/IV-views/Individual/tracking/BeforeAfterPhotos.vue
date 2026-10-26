<template>
    <!-- Before/After Photos -->
    <div v-if="activeMove.beforeAfterPhotos && Object.keys(activeMove.beforeAfterPhotos).length > 0"
        class="glass-panel p-4 sm:p-5 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm flex items-center gap-2">
            <span class="material-symbols-outlined text-amber-500 text-lg">photo_camera</span> Move Photos
        </h3>
        <div class="space-y-2">
            <div v-for="(val, key) in activeMove.beforeAfterPhotos" :key="key"
                class="flex items-center justify-between p-2 bg-gray-50 dark:bg-white/5 rounded-lg text-xs">
                <span class="text-gray-700 dark:text-gray-300 font-medium capitalize">{{
                    key.replace(/([A-Z])/g, ' $1') }}</span>
                <span :class="val ? 'text-green-500' : 'text-gray-400'">{{ val || 'Pending' }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove } = inject(customerTrackingPageKey)
</script>
