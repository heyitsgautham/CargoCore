<template>
    <div v-if="showVerifyModal && verifyDock"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showVerifyModal = false">
        <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock {{ verifyDock.id }} —
                    Pre-Departure Verification</h3>
                <button @click="showVerifyModal = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-4">
                <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-bold mb-2">Manifest Check
                </div>
                <div class="space-y-2">
                    <div v-for="item in verifyChecklist" :key="item.label"
                        class="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors"
                        :class="item.checked ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 hover:border-white/20'"
                        @click="item.checked = !item.checked">
                        <span class="material-symbols-outlined text-[18px]"
                            :class="item.checked ? 'text-green-600 dark:text-green-400' : 'text-gray-600'">
                            {{ item.checked ? 'check_circle' : 'radio_button_unchecked' }}
                        </span>
                        <span class="text-sm"
                            :class="item.checked ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'">{{
                                item.label
                            }}</span>
                    </div>
                </div>
                <div
                    class="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-2">
                    <span class="material-symbols-outlined text-[16px]">warning</span>
                    Driver must confirm receipt before departure
                </div>
                <div class="flex gap-3">
                    <button @click="completeDock" :disabled="!allChecked"
                        class="flex-1 py-3 rounded-lg font-bold transition-colors"
                        :class="allChecked ? 'bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'">
                        <span
                            class="material-symbols-outlined text-[18px] align-middle mr-1">check_circle</span>
                        Confirm & Release Truck
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const {
    allChecked,
    completeDock,
    showVerifyModal,
    verifyChecklist,
    verifyDock,
} = inject(loadingDockPageKey)
</script>
