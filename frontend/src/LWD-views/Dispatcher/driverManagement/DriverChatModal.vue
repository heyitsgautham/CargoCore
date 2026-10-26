<template>
    <div v-if="showDriverChat" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverChat = false">
        <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-sm m-4 flex flex-col overflow-hidden" style="height:420px">
            <!-- Header -->
            <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between flex-shrink-0">
                <div class="flex items-center gap-2">
                    <img :src="chatTargetDriver?.avatar" class="w-8 h-8 rounded-full bg-gray-700 flex-shrink-0">
                    <div>
                        <div class="text-sm font-bold text-white">{{ chatTargetDriver?.name }}</div>
                        <div class="flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :class="chatTargetDriver?.suspended ? 'bg-red-500' : 'bg-green-500'"></span>
                            <span class="text-[10px] text-gray-400">{{ chatTargetDriver?.status }}</span>
                            <span v-if="chatThreadId" class="text-[9px] text-primary/70 ml-1">• Live</span>
                        </div>
                    </div>
                </div>
                <button @click="showDriverChat = false" class="text-gray-500 hover:text-white transition-colors">
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            </div>

            <!-- No thread warning -->
            <div v-if="!chatLoading && !chatThreadId" class="mx-4 mt-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-2 flex-shrink-0">
                <span class="material-symbols-outlined text-yellow-400 text-[14px]">warning</span>
                <span class="text-[10px] text-yellow-300">No chat thread found — message will be sent once a thread is created.</span>
            </div>

            <!-- Loading state -->
            <div v-if="chatLoading" class="flex-1 flex items-center justify-center">
                <span class="material-symbols-outlined text-primary animate-spin text-[28px]">progress_activity</span>
            </div>

            <!-- Messages -->
            <div v-else ref="chatMsgEl" class="flex-1 overflow-y-auto no-scrollbar px-4 py-3 space-y-2">
                <div v-if="driverChatMessages.length === 0" class="text-center py-8 text-gray-500 text-xs">No messages yet. Start the conversation.</div>
                <div v-for="msg in driverChatMessages" :key="msg.id"
                    class="flex flex-col max-w-[80%] text-xs"
                    :class="msg.from === 'dispatch' ? 'ml-auto items-end' : 'mr-auto items-start'">
                    <span class="text-[9px] text-gray-500 mb-0.5 px-1">{{ msg.from === 'dispatch' ? 'You' : chatTargetDriver?.name }}</span>
                    <div class="px-3 py-2 rounded-xl"
                        :class="msg.from === 'dispatch' ? 'bg-primary text-black font-medium rounded-br-none' : 'bg-white/10 text-gray-200 rounded-bl-none'">
                        {{ msg.text }}
                    </div>
                    <span v-if="msg.time" class="text-[9px] text-gray-600 mt-0.5 px-1">{{ msg.time }}</span>
                </div>
            </div>

            <!-- Input -->
            <div class="px-4 py-3 border-t border-white/10 flex gap-2 flex-shrink-0">
                <input v-model="driverChatMsg" @keyup.enter="sendDriverChatMsg" type="text" placeholder="Message driver..."
                    class="flex-1 bg-white/5 border border-white/10 focus:border-primary/50 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none transition-colors">
                <button @click="sendDriverChatMsg" :disabled="!driverChatMsg.trim()"
                    class="bg-primary hover:bg-primary-dark text-black px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[16px]">send</span>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { driverManagementPageKey } from './driverManagementPageContext'

const {
    chatLoading,
    chatMsgEl,
    chatTargetDriver,
    chatThreadId,
    driverChatMessages,
    driverChatMsg,
    sendDriverChatMsg,
    showDriverChat,
} = inject(driverManagementPageKey)
</script>
