<template>
    <!-- Photo Modal -->
    <Teleport to="body">
        <div v-if="showPhotoModal && photoItem"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showPhotoModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Damage Photo — {{ photoItem.name }}</h3>
                    <button @click="showPhotoModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4">
                    <div class="w-full h-56 bg-gray-100 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10 flex flex-col items-center justify-center overflow-hidden">
                        <img v-if="photoItem?.photoUrl" :src="photoItem.photoUrl" alt="Damage photo" class="w-full h-full object-contain" />
                        <template v-else>
                            <span class="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-500">image</span>
                            <div class="text-sm text-gray-500 mt-2">Damage photo captured during inspection</div>
                        </template>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">RMA</div>
                            <div class="font-mono text-sm text-gray-900 dark:text-white font-bold">{{ photoItem.rma }}</div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Condition</div>
                            <div class="text-sm text-gray-900 dark:text-white font-bold">{{ photoItem.condition }}</div>
                        </div>
                    </div>
                    <button @click="showPhotoModal = false"
                        class="w-full bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white py-3 rounded-lg text-sm font-bold transition-colors">Close</button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { returnsWarehousePageKey } from './returnsWarehousePageContext'

const { photoItem, showPhotoModal } = inject(returnsWarehousePageKey)
</script>
