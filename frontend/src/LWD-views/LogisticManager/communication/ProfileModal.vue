<template>
    <div v-if="isProfileModalOpen && activeChat"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
        <div
            class="bg-slate-950/98 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col md:flex-row h-[500px] backdrop-blur-xl">
            <!-- Left: Profile Details -->
            <div
                class="w-full md:w-1/2 p-8 bg-slate-900/90 flex flex-col items-center justify-center text-center border-r border-white/10">
                <div
                    class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl font-bold text-white mb-4 shadow-lg shadow-purple-500/30">
                    {{ chatDisplayName(activeChat.name).substring(0, 2).toUpperCase() }}
                </div>
                <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">{{ chatDisplayName(activeChat.name) }}</h3>
                <p class="text-sm text-gray-500 mb-4">{{ activeChatDriver?.vehicle || activeChat.role || 'Logistic Partner' }}</p>

                <div class="flex gap-2 mb-6">
                    <span
                        class="px-3 py-1 rounded-full text-xs font-bold border border-gray-200 dark:border-white/10"
                        :class="activeChat.status === 'Online' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                        {{ activeChatDriver?.status || activeChat.status || 'Offline' }}
                    </span>
                    <span v-if="activeChat.muted"
                        class="px-3 py-1 rounded-full text-xs font-bold bg-yellow-50 text-yellow-600 border border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20 flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">notifications_off</span> Muted
                    </span>
                </div>

                <div class="w-full space-y-3 text-left">
                    <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                        <span class="text-gray-500">Phone</span>
                        <span class="font-mono text-gray-900 dark:text-white">{{ activeChat.phone || activeChatDriver?.phone || 'N/A' }}</span>
                    </div>
                    <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                        <span class="text-gray-500">Location</span>
                        <span class="text-gray-900 dark:text-white">{{ activeChatDriver?.location || 'N/A' }}</span>
                    </div>
                    <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                        <span class="text-gray-500">Current Job</span>
                        <span class="text-gray-900 dark:text-white truncate max-w-[160px]">{{ activeChatDriver?.currentJob || 'Unassigned' }}</span>
                    </div>
                </div>
            </div>

            <!-- Right: Stats / Actions -->
            <div class="w-full md:w-1/2 p-8 flex flex-col">
                <div class="flex justify-between items-center mb-6">
                    <h4 class="font-bold text-gray-900 dark:text-white">Performance Metrics</h4>
                    <button @click="isProfileModalOpen = false" class="text-gray-400 hover:text-gray-600"><span
                            class="material-symbols-outlined">close</span></button>
                </div>

                <div class="space-y-4 mb-auto">
                    <div
                        class="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl border border-blue-100 dark:border-blue-500/20">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase">Efficiency Score</span>
                            <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.efficiency != null ? activeChatDriver.efficiency + '%' : 'N/A' }}</span>
                        </div>
                        <div v-if="activeChatDriver?.efficiency != null" class="w-full h-1.5 bg-blue-200 dark:bg-blue-900/30 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500" :style="{ width: activeChatDriver.efficiency + '%' }"></div>
                        </div>
                    </div>
                    <div
                        class="bg-purple-50 dark:bg-purple-900/10 p-4 rounded-xl border border-purple-100 dark:border-purple-500/20">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase">Driver Rating</span>
                            <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.rating != null ? activeChatDriver.rating + ' / 5' : 'N/A' }}</span>
                        </div>
                    </div>
                    <div
                        class="bg-green-50 dark:bg-green-900/10 p-4 rounded-xl border border-green-100 dark:border-green-500/20">
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-bold text-green-600 dark:text-green-400 uppercase">Avg Speed</span>
                            <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.avgSpeed != null ? activeChatDriver.avgSpeed + ' km/h' : 'N/A' }}</span>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3 mt-6">
                    <button @click="handleMuteChat"
                        class="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-gray-100 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2 border border-white/10">
                        <span class="material-symbols-outlined text-[18px]">{{ activeChat.muted ? 'notifications' :
                            'notifications_off' }}</span> {{ activeChat.muted ? 'Unmute' : 'Mute' }}
                    </button>
                    <button @click="isProfileModalOpen = false"
                        class="px-4 py-3 bg-primary hover:bg-primary/90 text-white rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">chat</span> Message
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const {
    activeChat,
    activeChatDriver,
    chatDisplayName,
    handleMuteChat,
    isProfileModalOpen,
} = inject(communicationPageKey)
</script>
