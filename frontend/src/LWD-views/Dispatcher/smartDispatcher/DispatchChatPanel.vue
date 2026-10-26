<template>
    <div v-if="showChat" class="glass-panel rounded-xl flex flex-col h-[540px]">
        <div
            class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20 flex items-center gap-2">
            <div
                class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center">
                <span class="material-symbols-outlined text-black text-[16px]">smart_toy</span>
            </div>
            <div>
                <div class="text-sm font-bold text-gray-900 dark:text-white">AI Dispatch Agent</div>
                <div class="text-[10px] text-green-400">Online • Reasoning</div>
            </div>
        </div>

        <div ref="chatContainer" class="flex-1 overflow-y-auto no-scrollbar p-4 space-y-3">
            <div v-for="msg in chatMessages" :key="msg.id"
                :class="msg.sender === 'ai' ? 'flex gap-2' : 'flex gap-2 flex-row-reverse'">
                <div v-if="msg.sender === 'ai'"
                    class="w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center shadow-sm">
                    <span class="material-symbols-outlined text-black text-[14px]">smart_toy</span>
                </div>
                <div v-else
                    class="w-7 h-7 flex-shrink-0 rounded-full bg-primary flex items-center justify-center text-[9px] text-black font-bold shadow-sm">
                    YOU
                </div>
                <div class="max-w-[85%] p-3 rounded-xl text-sm shadow-sm font-medium"
                    :class="msg.sender === 'ai' ? 'bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 text-gray-800 dark:text-gray-100 rounded-tl-none' : 'bg-primary/30 border border-primary/40 text-black dark:text-white rounded-tr-none'">
                    <span v-if="msg.sender === 'ai'" v-html="msg.text"></span>
                    <span v-else>{{ msg.text }}</span>
                </div>
            </div>
            <div v-if="chatTyping" class="flex gap-2">
                <div
                    class="w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center">
                    <span class="material-symbols-outlined text-black text-[14px]">smart_toy</span>
                </div>
                <div
                    class="bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 p-3 rounded-xl rounded-tl-none text-gray-500 text-sm shadow-sm">
                    <span class="inline-flex gap-1"><span
                            class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"></span><span
                            class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
                            style="animation-delay:0.15s"></span><span
                            class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
                            style="animation-delay:0.3s"></span></span>
                </div>
            </div>
        </div>

        <div class="p-4 border-t border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/40">
            <div class="flex items-center gap-2 relative">
                <input v-model="chatInput" type="text" placeholder="Ask the AI agent..."
                    class="flex-1 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/20 shadow-sm rounded-full py-2.5 pl-4 pr-12 text-gray-900 dark:text-white text-sm font-medium focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                    @keyup.enter="sendChat" />
                <button @click="sendChat"
                    class="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 bg-primary rounded-full text-black hover:scale-105 transition-transform flex items-center justify-center shadow-md">
                    <span class="material-symbols-outlined text-[18px]">send</span>
                </button>
            </div>
            <div class="flex gap-2 mt-3 overflow-x-auto no-scrollbar pb-1 max-w-full"
                @wheel.prevent="handleChipsScroll" style="max-width: 75vw;">
                <button v-for="chip in chatChips" :key="chip" @click="chatInput = chip; sendChat()"
                    class="whitespace-nowrap flex-shrink-0 text-[11px] font-medium bg-white dark:bg-black/30 border border-gray-200 dark:border-white/10 hover:border-primary/50 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-1 rounded-full shadow-sm transition-all">{{
                        chip }}</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { smartDispatcherPageKey } from './smartDispatcherPageContext'

const {
    chatChips,
    chatContainer,
    chatInput,
    chatMessages,
    chatTyping,
    handleChipsScroll,
    sendChat,
    showChat,
} = inject(smartDispatcherPageKey)
</script>
