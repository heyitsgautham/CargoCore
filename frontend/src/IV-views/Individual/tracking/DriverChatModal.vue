<template>
    <!-- Chat Modal -->
    <Teleport to="body">
        <div v-if="showChatModal && activeMove?.driver" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl flex flex-col h-[600px] max-h-[85vh] animate-slide-up border border-gray-100 dark:border-white/10 relative">
                <!-- Chat Header -->
                <div class="p-4 border-b border-gray-100 dark:border-white/10 flex items-center justify-between shrink-0 bg-gray-50 dark:bg-black/50 rounded-t-2xl">
                    <div class="flex items-center gap-3">
                        <div class="relative">
                            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                                {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                            </div>
                            <div class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-900 rounded-full"></div>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-sm">{{ activeMove.driver.name }}</h3>
                            <div class="text-[10px] text-green-600 dark:text-green-400 font-bold">Online</div>
                        </div>
                    </div>
                    <button @click="showChatModal = false" class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full text-gray-500 transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Chat Messages Area -->
                <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 dark:bg-black/20" ref="chatScrollContainer">
                    <div class="text-center py-2">
                        <span class="bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-gray-400 text-[10px] px-3 py-1 rounded-full font-bold uppercase">Today</span>
                    </div>

                    <!-- Incoming Message -->
                    <div class="flex gap-2">
                        <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-[10px] shrink-0 mt-1">
                            {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                        </div>
                        <div class="bg-white dark:bg-gray-800 p-3 rounded-2xl rounded-tl-none shadow-sm border border-gray-100 dark:border-white/5 max-w-[80%]">
                            <p class="text-sm text-gray-800 dark:text-gray-200">Hi sir, I am reaching the pickup location in about 10 minutes.</p>
                            <div class="text-[10px] text-gray-400 mt-1 text-right">10:45 AM</div>
                        </div>
                    </div>

                    <!-- System Message -->
                    <div class="text-center py-2">
                        <span class="text-gray-400 dark:text-gray-500 text-xs italic">Crew is nearing the location</span>
                    </div>

                    <!-- Appended Dynamic Messages -->
                    <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex gap-2 justify-end">
                        <div class="bg-green-600 p-3 rounded-2xl rounded-tr-none shadow-sm text-white max-w-[80%]">
                            <p class="text-sm">{{ msg.text }}</p>
                            <div class="text-[10px] text-green-200 mt-1 flex justify-end items-center gap-1">
                                {{ msg.time }}
                                <span class="material-symbols-outlined text-[12px]">done_all</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Chat Input Area -->
                <div class="p-3 border-t border-gray-100 dark:border-white/10 bg-white dark:bg-gray-900 rounded-b-2xl shrink-0">
                    <form @submit.prevent="sendChatMessage" class="flex items-center gap-2">
                        <input type="text" v-model="pendingMessage" placeholder="Message driver..." class="flex-1 bg-gray-100 dark:bg-white/5 border border-transparent focus:border-green-500 focus:ring-1 focus:ring-green-500 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none transition-all">
                        <button type="submit" :disabled="!pendingMessage.trim()" class="p-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:hover:bg-green-600 transition-colors flex items-center justify-center">
                            <span class="material-symbols-outlined text-sm">send</span>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const {
    activeMove,
    chatMessages,
    chatScrollContainer,
    pendingMessage,
    sendChatMessage,
    showChatModal,
} = inject(customerTrackingPageKey)
</script>
