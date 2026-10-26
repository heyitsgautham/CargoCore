<template>
    <!-- Contact Crew Modal -->
    <Teleport to="body">
    <div v-if="showCrewChat" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showCrewChat = false">
        <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-md m-4 overflow-hidden">
            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary text-[20px]">chat</span>
                    <div>
                        <div class="text-sm font-bold text-white">{{ crewChatMove?.title }}</div>
                        <div class="text-[10px] text-gray-400">{{ crewChatMove?.crew?.[0]?.name || 'Crew' }} · {{ crewChatMove?.id }}</div>
                    </div>
                </div>
                <button @click="showCrewChat = false" class="text-gray-500 hover:text-white transition-colors">
                    <span class="material-symbols-outlined text-[20px]">close</span>
                </button>
            </div>

            <!-- Warning if no thread -->
            <div v-if="!crewThreadId" class="mx-5 mt-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-2">
                <span class="material-symbols-outlined text-yellow-400 text-[14px]">warning</span>
                <span class="text-xs text-yellow-300">No chat thread found — message will be sent once a thread is created.</span>
            </div>

            <!-- Messages -->
            <div class="px-5 py-4 space-y-2 max-h-56 overflow-y-auto no-scrollbar">
                <div v-if="crewMessages.length === 0" class="text-center py-8 text-gray-500 text-xs">No messages yet. Start the conversation.</div>
                <div v-for="msg in crewMessages" :key="msg.id"
                    class="flex flex-col max-w-[80%] text-xs"
                    :class="msg.from === 'dispatch' ? 'ml-auto items-end' : 'mr-auto items-start'">
                    <span class="text-[9px] text-gray-500 mb-0.5 px-1">{{ msg.from === 'dispatch' ? 'You' : msg.from }}</span>
                    <div class="px-3 py-2 rounded-xl"
                        :class="msg.from === 'dispatch' ? 'bg-primary text-black font-medium rounded-br-none' : 'bg-white/10 text-gray-200 rounded-bl-none'">
                        {{ msg.text }}
                    </div>
                </div>
            </div>

            <!-- Input -->
            <div class="px-5 py-4 border-t border-white/10 flex gap-2">
                <input v-model="crewMsg" type="text" placeholder="Message crew..." @keyup.enter="sendCrewMsg"
                    class="flex-1 bg-white/5 border border-white/10 focus:border-primary/50 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none transition-colors">
                <button @click="sendCrewMsg" class="bg-primary hover:bg-primary-dark text-black px-5 py-2.5 rounded-xl text-sm font-bold transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">send</span>
                </button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const {
    crewChatMove,
    crewMessages,
    crewMsg,
    crewThreadId,
    sendCrewMsg,
    showCrewChat,
} = inject(serviceMovesPageKey)
</script>
