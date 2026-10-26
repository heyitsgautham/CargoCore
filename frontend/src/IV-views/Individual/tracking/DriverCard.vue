<template>
    <!-- Driver Card -->
    <div class="glass-panel p-4 sm:p-5 rounded-xl" v-if="activeMove.driver">
        <h3 class="font-bold text-gray-900 dark:text-white mb-3 text-sm">Driver & Crew</h3>
        <div class="flex items-center gap-3 mb-3">
            <div
                class="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
                {{activeMove.driver.name.split(' ').map(n => n[0]).join('')}}
            </div>
            <div>
                <div class="font-bold text-gray-900 dark:text-white">{{ activeMove.driver.name }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ activeMove.driver.rating }} ★ ·
                    Team Lead</div>
            </div>
        </div>
        <div class="flex gap-2 mb-3">
            <button @click="showCallModal = true"
                class="flex-1 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-1"><span
                    class="material-symbols-outlined text-sm">call</span> Call</button>
            <button @click="showChatModal = true"
                class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white text-sm font-bold rounded-lg hover:bg-gray-200 dark:hover:bg-white/20 transition-colors flex items-center justify-center gap-1"><span
                    class="material-symbols-outlined text-sm">chat</span> Chat</button>
        </div>
        <!-- Crew Check-in -->
        <div v-if="activeMove.crewCheckin" class="space-y-2">
            <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Crew Check-In</div>
            <div v-for="laborer in activeMove.crewCheckin.laborers" :key="laborer.name"
                class="flex items-center justify-between text-xs p-2 bg-gray-50 dark:bg-white/5 rounded-lg">
                <span class="text-gray-900 dark:text-white font-medium">{{ laborer.name }}</span>
                <span v-if="laborer.checkedIn"
                    class="text-green-500 font-bold flex items-center gap-1"><span
                        class="material-symbols-outlined text-xs">check_circle</span>Checked In</span>
                <span v-else class="text-red-500 font-bold">Absent</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove, showCallModal, showChatModal } = inject(customerTrackingPageKey)
</script>
