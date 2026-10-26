<template>
    <div v-if="showSettingsModal && settingsDock"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        @click.self="showSettingsModal = false">
        <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock {{ settingsDock.id }} Settings
                </h3>
                <button @click="showSettingsModal = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Dock Status</label>
                    <select v-model="settingsForm.status"
                        class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Free</option>
                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Maintenance</option>
                    </select>
                </div>
                <div
                    class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 text-xs text-gray-600 dark:text-gray-400">
                    <div>Current Status: <span class="text-gray-900 dark:text-white font-bold">{{
                            settingsDock.status }}</span></div>
                    <div>Truck: <span class="text-gray-900 dark:text-white">{{ settingsDock.truck || 'None'
                            }}</span></div>
                </div>
                <button @click="saveSettings"
                    class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Save
                    Settings</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { loadingDockPageKey } from './loadingDockPageContext'

const { saveSettings, settingsDock, settingsForm, showSettingsModal } = inject(loadingDockPageKey)
</script>
