<template>
    <div v-if="isBroadcastModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
        <div
            class="bg-slate-950/98 w-full max-w-md rounded-2xl shadow-xl border border-white/10 overflow-hidden backdrop-blur-xl">
            <div
                class="p-5 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                <h3 class="font-bold text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-600">campaign</span> New System Broadcast
                </h3>
                <button @click="isBroadcastModalOpen = false"
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors"><span
                        class="material-symbols-outlined">close</span></button>
            </div>
            <div class="p-6 space-y-5">
                <div class="space-y-1.5">
                    <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Target Audience</label>
                    <select v-model="broadcastForm.audience"
                        class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all">
                        <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Personnel</option>
                        <option value="drivers" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Drivers (On-Duty)</option>
                        <option value="warehouses" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Warehouse Managers</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Alert Type</label>
                    <select v-model="broadcastForm.type"
                        class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all">
                        <option value="info" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">General Information</option>
                        <option value="warning" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">System Warning</option>
                        <option value="emergency" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Emergency Recall / Halt</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Message Details</label>
                    <textarea v-model="broadcastForm.message" rows="4" placeholder="Enter broadcast message here..."
                        class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-slate-400 outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all resize-none"></textarea>
                </div>
            </div>
            <div
                class="p-5 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                <button @click="isBroadcastModalOpen = false"
                    class="px-5 py-2.5 rounded-xl text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 font-bold text-sm transition-colors">Cancel</button>
                <button @click="sendBroadcast"
                    class="px-6 py-2.5 rounded-xl font-bold text-sm text-white shadow-lg flex items-center gap-2 transition-all hover:scale-105"
                    :class="broadcastForm.type === 'emergency' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/30' : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-purple-500/30'">
                    <span class="material-symbols-outlined text-[18px]">send_time_extension</span> Deploy Alert
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const { broadcastForm, isBroadcastModalOpen, sendBroadcast } = inject(communicationPageKey)
</script>
