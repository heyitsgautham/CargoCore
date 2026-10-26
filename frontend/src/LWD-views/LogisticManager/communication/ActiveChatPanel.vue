<template>
    <div
        class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-black/20">
        <div class="flex items-center gap-3">
            <div
                class="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold shadow-sm">
                {{ chatDisplayName(activeChat.name).substring(0, 2).toUpperCase() }}</div>
            <div>
                <div class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    {{ chatDisplayName(activeChat.name) }}
                    <span v-if="activeChat.muted"
                        class="material-symbols-outlined text-gray-400 text-[16px]"
                        title="Chat Muted">notifications_off</span>
                </div>
                <div class="text-xs flex items-center gap-2">
                    <span class="flex items-center gap-1"
                        :class="activeChat.status === 'Online' ? 'text-green-500' : 'text-gray-400'">
                        <span class="w-1.5 h-1.5 rounded-full"
                            :class="activeChat.status === 'Online' ? 'bg-green-500' : 'bg-gray-400'"></span>
                        {{ activeChat.status }}
                    </span>
                    <span v-if="activeChat.phone"
                        class="text-gray-400 border-l border-gray-300 dark:border-gray-600 pl-2 font-mono">{{
                            activeChat.phone }}</span>
                </div>
            </div>
        </div>
        <div class="flex gap-2 relative">
            <button ref="menuButtonRef" @click="toggleMenu"
                class="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"><span
                    class="material-symbols-outlined">more_vert</span></button>

            <!-- Dropdown Menu teleported to body to escape overflow-hidden -->
            <Teleport to="body">
                <div v-if="isMenuOpen" @click.stop
                    :style="{ top: menuPosition.top + 'px', right: menuPosition.right + 'px' }"
                    class="fixed w-48 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-100 dark:border-white/10 overflow-hidden z-[9999] animate-fade-in-up origin-top-right">
                    <button
                        class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 flex items-center gap-3 transition-colors"
                        @click="handleViewProfile">
                        <span class="material-symbols-outlined text-[18px] text-gray-400">person</span> View
                        Profile
                    </button>
                    <button
                        class="w-full text-left px-4 py-3 text-sm hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 flex items-center gap-3 transition-colors"
                        @click="handleMuteChat">
                        <span class="material-symbols-outlined text-[18px] text-gray-400">{{ activeChat.muted ?
                            'notifications' : 'notifications_off' }}</span> {{ activeChat.muted ? 'Unmute Chat'
                                : 'Mute Chat' }}
                    </button>
                    <button
                        class="w-full text-left px-4 py-3 text-sm hover:bg-red-50 dark:hover:bg-red-900/10 text-red-600 dark:text-red-400 flex items-center gap-3 transition-colors"
                        @click="handleDeleteChat">
                        <span class="material-symbols-outlined text-[18px]">delete</span> Delete Chat
                    </button>
                </div>
                <!-- Click Outside Overlay -->
                <div v-if="isMenuOpen" @click="isMenuOpen = false" class="fixed inset-0 z-[9998]"></div>
            </Teleport>
        </div>
    </div>

    <div ref="chatHistoryContainer"
        class="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50/30 dark:bg-black/10 scroll-smooth">
        <div v-for="msg in activeChat.messages" :key="msg.id" class="flex gap-3"
            :class="{ 'flex-row-reverse': msg.sender === 'me' }">
            <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold shadow-sm"
                :class="msg.sender === 'me' ? 'bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-white' : 'bg-purple-600 text-white'">
                {{ msg.sender === 'me' ? 'ME' : chatDisplayName(activeChat.name).substring(0, 2).toUpperCase() }}
            </div>
            <div class="max-w-[70%]">
                <div class="p-3 rounded-xl text-sm shadow-sm"
                    :class="msg.sender === 'me'
                        ? 'bg-primary/10 border border-primary/20 dark:bg-primary/20 dark:border-primary/30 rounded-tr-none text-gray-900 dark:text-white'
                        : 'bg-white border border-gray-100 dark:bg-white/5 dark:border-white/10 rounded-tl-none text-gray-700 dark:text-gray-300'">
                    {{ msg.text }}
                </div>
                <div class="text-[10px] text-gray-400 mt-1" :class="{ 'text-right': msg.sender === 'me' }">
                    {{
                        msg.time }}</div>
            </div>
        </div>
    </div>

    <div class="p-4 bg-gray-50 dark:bg-black/20 border-t border-gray-200 dark:border-white/5">
        <div class="relative">
            <input v-model="messageInput" @keyup.enter="sendMessage" type="text"
                placeholder="Type a message..."
                class="w-full bg-white border border-gray-200 dark:bg-white/5 dark:border-white/10 rounded-full py-3 pl-4 pr-12 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all shadow-sm">
            <button @click="sendMessage"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 flex items-center justify-center bg-primary rounded-full text-white hover:bg-primary/90 hover:scale-105 transition-all shadow-sm">
                <span class="material-symbols-outlined text-[18px] ml-0.5">send</span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const {
    activeChat,
    chatDisplayName,
    chatHistoryContainer,
    handleDeleteChat,
    handleMuteChat,
    handleViewProfile,
    isMenuOpen,
    menuButtonRef,
    menuPosition,
    messageInput,
    sendMessage,
    toggleMenu,
} = inject(communicationPageKey)
</script>
