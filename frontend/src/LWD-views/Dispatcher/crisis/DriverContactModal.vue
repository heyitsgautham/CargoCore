<template>
    <Teleport to="body">
    <div v-if="showDriverContact" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverContact = false">
        <div class="bg-white dark:bg-card-dark shadow-2xl border border-gray-200 dark:border-white/10 rounded-2xl p-6 w-full max-w-md m-4">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">support_agent</span> Contact Driver
            </h3>
            <div class="space-y-4">
                <div class="flex items-center gap-4">
                    <img :src="contactDriver?.avatar" class="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700">
                    <div>
                        <div class="font-bold text-gray-900 dark:text-white text-lg">{{ contactDriver?.name }}</div>
                        <div class="text-sm text-gray-500 dark:text-gray-400">{{ contactDriver?.vehicle }}</div>
                    </div>
                </div>
                <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Phone Number</div>
                    <div class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary">phone</span>
                        {{ contactDriver?.phone }}
                    </div>
                </div>
                <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Status</div>
                    <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ contactDriver?.status }}</div>
                </div>
                <div class="p-4 bg-gray-100 dark:bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Last Known Location</div>
                    <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ contactDriver?.location }}</div>
                </div>
            </div>
            <div class="flex gap-2 mt-6">
                <button @click="callDriver" class="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-colors shadow-md">
                    <span class="material-symbols-outlined text-[18px]">call</span> Call Now
                </button>
                <button @click="showDriverContact = false" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2.5 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors font-bold">Close</button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { crisisPageKey } from './crisisPageContext'

const { callDriver, contactDriver, showDriverContact } = inject(crisisPageKey)
</script>
