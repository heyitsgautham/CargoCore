<template>
    <!-- Selected shipment bar -->
    <div class="px-4 py-2 border-b border-gray-100 dark:border-white/5 flex items-center justify-between bg-blue-50/60 dark:bg-blue-500/5 flex-shrink-0">
        <div class="flex items-center gap-2 text-xs">
            <span class="material-symbols-outlined text-blue-500 text-[14px]">{{ selectedShipment ? 'local_shipping' : 'chat' }}</span>
            <template v-if="selectedShipment">
                <span class="text-gray-600 dark:text-white/50">Shipment:</span>
                <span class="font-bold font-mono text-gray-900 dark:text-white">{{ selectedShipment.id }}</span>
            </template>
            <template v-else>
                <span class="text-gray-600 dark:text-white/50">General Support</span>
            </template>
        </div>
        <button @click="startNewChat" title="Change shipment / new chat"
            class="text-[10px] font-bold text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-1">
            <span class="material-symbols-outlined text-[12px]">close</span>
            Change
        </button>
    </div>

    <!-- Human-handoff locked banner -->
    <div v-if="humanHandoffLocked"
        class="mx-4 mt-2 flex items-start gap-2 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 px-3 py-2 text-xs text-orange-700 dark:text-orange-300 flex-shrink-0">
        <span class="material-symbols-outlined text-[14px] mt-0.5 flex-shrink-0">lock</span>
        <span>Human support session closed. AI assistance is still available.</span>
    </div>

    <!-- Messages area -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-gray-50/50 dark:bg-black/10">

        <!-- Welcome / empty state -->
        <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center h-full gap-4 text-center py-10">
            <div>
                <p class="font-bold text-gray-700 dark:text-white/80 text-sm">Cargo AI Assistant</p>
                <p class="text-gray-500 dark:text-white/40 text-xs mt-1 leading-relaxed max-w-[260px] mx-auto">
                    Ask me about shipments, invoices, wallet balance, or get connected to a human agent.
                </p>
            </div>
            <div class="flex flex-wrap gap-2 justify-center">
                <button v-for="chip in quickChips" :key="chip" @click="sendChip(chip)"
                    class="text-[11px] px-3 py-1.5 bg-white dark:bg-white/5 hover:bg-blue-50 dark:hover:bg-white/10 border border-gray-200 dark:border-white/10 rounded-full text-gray-600 dark:text-white/60 hover:text-blue-600 dark:hover:text-white transition-colors">
                    {{ chip }}
                </button>
            </div>
        </div>

        <!-- Message bubbles -->
        <template v-for="(msg, i) in chatMessages" :key="msg.id || i">
            <!-- Session-closed notice (centred pill) -->
            <div v-if="msg.role === 'closed'" class="flex justify-center">
                <div class="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 text-xs text-orange-600 dark:text-orange-300">
                    <span class="material-symbols-outlined text-[12px]">lock</span>
                    <span v-html="msg.text"></span>
                </div>
            </div>

            <!-- Agent-waiting status pill -->
            <div v-else-if="msg.role === 'status'" class="flex justify-center">
                <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-white/10 text-xs text-gray-400 dark:text-gray-500">
                    <span class="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse inline-block"></span>
                    {{ msg.text }}
                </div>
            </div>

            <!-- Normal bubble -->
            <div v-else-if="!['closed','status'].includes(msg.role)"
                class="flex gap-2.5"
                :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
                <div class="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5"
                    :class="msg.role === 'user'
                        ? 'bg-blue-100 dark:bg-white/10 text-blue-600 dark:text-white/70'
                        : msg.role === 'support'
                            ? 'bg-orange-500 text-white'
                            : 'bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] text-white'">
                    {{ msg.role === 'user' ? 'ME' : msg.role === 'support' ? 'SUP' : 'AI' }}
                </div>
                <div class="max-w-[78%] space-y-1">
                    <!-- Human agent label (only for actual agent replies) -->
                    <div v-if="msg.role === 'support'" class="flex items-center gap-1 px-1 mb-0.5">
                        <span class="material-symbols-outlined text-orange-400 text-[12px]">support_agent</span>
                        <span class="text-[10px] text-orange-400 font-medium">Human Agent</span>
                    </div>
                    <!-- Escalating badge on AI bubble when handover triggered -->
                    <div v-if="msg.role === 'ai' && msg.intent === 'handover'" class="flex items-center gap-1 px-1 mb-0.5">
                        <span class="material-symbols-outlined text-blue-400 text-[12px]">escalator_warning</span>
                        <span class="text-[10px] text-blue-400 font-medium">Connecting to Human Support…</span>
                    </div>
                    <!-- Ticket-created badge when handover confirmed -->
                    <div v-if="msg.role === 'ai' && msg.intent === 'handover'" class="flex items-center gap-1 px-1 mb-0.5">
                        <span class="material-symbols-outlined text-green-500 text-[12px]">confirmation_number</span>
                        <span class="text-[10px] text-green-500 font-medium">Support ticket created — a manager will follow up.</span>
                    </div>
                    <div class="px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed"
                        :class="msg.role === 'user'
                            ? 'bg-blue-500/15 border border-blue-200 dark:border-blue-500/30 rounded-tr-none text-gray-900 dark:text-white'
                            : msg.role === 'support'
                                ? 'bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/30 rounded-tl-none text-gray-900 dark:text-white/90'
                                : 'bg-white dark:bg-white/8 border border-gray-100 dark:border-white/10 rounded-tl-none text-gray-800 dark:text-white/90'">
                        <span v-html="msg.text"></span>
                    </div>
                    <div class="text-[10px] text-gray-400 px-1" :class="msg.role === 'user' ? 'text-right' : ''">{{ msg.time }}</div>
                    <!-- "Not helpful?" link under each normal AI reply (not handover) -->
                    <div v-if="msg.role === 'ai' && msg.intent !== 'handover' && !humanHandoffLocked"
                        class="px-1">
                        <button
                            @click="sendChip('I am not satisfied with this response. I need human support.')"
                            class="flex items-center gap-1 text-[10px] text-gray-400 hover:text-orange-500 dark:hover:text-orange-400 transition-colors">
                            <span class="material-symbols-outlined text-[12px]">thumb_down</span>
                            Not helpful? Talk to a human
                        </button>
                    </div>
                </div>
            </div>
        </template>

        <!-- Typing indicator -->
        <div v-if="isTyping" class="flex gap-2.5">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white">AI</div>
            <div class="bg-white dark:bg-white/8 border border-gray-100 dark:border-white/10 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-1">
                <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
                <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
                <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </div>
        </div>
    </div>

    <!-- Chat input -->
    <div class="px-4 py-3 border-t border-gray-100 dark:border-white/10 bg-white dark:bg-white/3 flex-shrink-0">
        <div class="flex items-center gap-2">
            <button @click="startNewChat" title="New conversation"
                class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors flex-shrink-0">
                <span class="material-symbols-outlined text-[18px]">add_comment</span>
            </button>
            <input v-model="userInput" @keydown.enter.exact.prevent="handleSend" type="text"
                placeholder="Type a message…"
                class="flex-1 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/30 focus:outline-none focus:border-blue-400 transition-colors" />
            <button @click="handleSend" :disabled="!userInput.trim() || isTyping"
                class="w-9 h-9 flex items-center justify-center bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0">
                <span class="material-symbols-outlined text-white text-[16px]">send</span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const {
    chatContainer,
    chatMessages,
    handleSend,
    humanHandoffLocked,
    isTyping,
    quickChips,
    selectedShipment,
    sendChip,
    startNewChat,
    userInput,
} = inject(vendorSupportPageKey)
</script>
