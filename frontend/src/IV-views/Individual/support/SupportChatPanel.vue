<template>
    <div class="lg:col-span-2 glass-panel rounded-xl flex flex-col" style="height: min(72vh, 620px);">

        <!-- Chat header -->
        <div class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center">
                <span class="material-symbols-outlined text-white">smart_toy</span>
            </div>
            <div class="flex-1 min-w-0">
                <div class="font-bold text-gray-900 dark:text-white text-sm">Cargo-Core AI</div>
                <div class="flex items-center gap-1 text-xs text-green-500">
                    <span class="w-1.5 h-1.5 rounded-full bg-green-500 inline-block"></span>
                    <template v-if="selectedOrder">Order: <span class="font-mono ml-1">{{ selectedOrder.trackingCode || selectedOrder.id }}</span></template>
                    <template v-else>General Support</template>
                </div>
            </div>
            <button @click="resetSession" title="Change order / new chat"
                class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
        </div>

        <!-- Session-closed banner -->
        <div v-if="humanHandoffLocked"
            class="mx-4 mt-3 flex items-start gap-2 rounded-lg bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 px-4 py-3 text-xs text-orange-700 dark:text-orange-300">
            <span class="material-symbols-outlined text-[16px] mt-0.5 flex-shrink-0">lock</span>
            <span>Your human support session has been resolved and closed. You can continue chatting with AI, but human support is no longer available for this session.</span>
        </div>

        <!-- Messages -->
        <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar">
            <div
                v-for="msg in messages"
                :key="msg.id"
                :class="msg.sender === 'user' ? 'flex justify-end' : 'flex justify-start'"
            >
                <!-- Session closed notice -->
                <div v-if="msg.sender === 'closed'"
                    class="w-full flex justify-center">
                    <div class="flex items-center gap-2 px-4 py-2 rounded-full bg-orange-50 border border-orange-200 dark:bg-orange-500/10 dark:border-orange-500/20 text-xs text-orange-600 dark:text-orange-300">
                        <span class="material-symbols-outlined text-[14px]">lock</span>
                        {{ msg.text }}
                    </div>
                </div>

                <!-- Agent-waiting status pill (shown instead of AI reply when human has taken over) -->
                <div v-else-if="msg.sender === 'status'"
                    class="w-full flex justify-center">
                    <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-white/10 text-xs text-gray-400 dark:text-gray-500">
                        <span class="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse inline-block"></span>
                        {{ msg.text }}
                    </div>
                </div>

                <!-- Regular message bubbles -->
                <div
                    v-else-if="!['closed','status'].includes(msg.sender)"
                    class="max-w-[80%] sm:max-w-[70%]"
                >
                    <div
                        class="p-3 rounded-xl text-sm"
                        :class="msg.sender === 'user'
                            ? 'bg-green-600 text-white rounded-br-sm'
                            : msg.sender === 'support'
                                ? 'bg-orange-50 border border-orange-200 text-gray-900 dark:bg-orange-500/10 dark:border-orange-500/20 dark:text-white rounded-bl-sm'
                                : 'bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-bl-sm'"
                    >
                        <!-- Human Support label (only for actual agent replies) -->
                        <div v-if="msg.sender === 'support'" class="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-orange-500">
                            <span class="material-symbols-outlined text-[12px]">support_agent</span>
                            Human Support
                        </div>
                        <!-- Escalating badge on bot bubble when handover was triggered -->
                        <div v-if="msg.sender === 'bot' && msg.intent === 'handover'" class="mb-1 flex items-center gap-1 text-[10px] font-semibold text-blue-500 dark:text-blue-400">
                            <span class="material-symbols-outlined text-[12px]">escalator_warning</span>
                            Connecting to Human Support…
                        </div>
                        <!-- Ticket-created badge when handover confirmed -->
                        <div v-if="msg.sender === 'bot' && msg.intent === 'handover'" class="mt-1 flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
                            <span class="material-symbols-outlined text-[12px]">confirmation_number</span>
                            Support ticket created — a manager will follow up shortly.
                        </div>
                        <p v-if="msg.sender === 'user'" class="whitespace-pre-wrap">{{ msg.text }}</p>
                        <div v-else class="whitespace-pre-wrap" v-html="msg.html || msg.text"></div>
                        <div
                            class="text-[10px] mt-1"
                            :class="msg.sender === 'user' ? 'text-green-200' : msg.sender === 'support' ? 'text-orange-400' : 'text-gray-400'"
                        >{{ msg.time }}</div>
                    </div>
                    <!-- "Not helpful?" link shown under each normal bot reply (not handover, not user msg) -->
                    <div v-if="msg.sender === 'bot' && msg.intent !== 'handover' && !humanHandoffLocked"
                        class="mt-1 flex items-center gap-1">
                        <button
                            @click="sendQuickAction('I am not satisfied with this response. I need human support.')"
                            class="flex items-center gap-1 text-[10px] text-gray-400 hover:text-orange-500 dark:hover:text-orange-400 transition-colors">
                            <span class="material-symbols-outlined text-[12px]">thumb_down</span>
                            Not helpful? Talk to a human
                        </button>
                    </div>
                </div>
            </div>

            <div v-if="typing" class="flex justify-start">
                <div class="bg-gray-100 dark:bg-white/10 px-4 py-2 rounded-xl text-gray-400 text-sm">
                    <span class="animate-pulse">● ● ●</span>
                </div>
            </div>
        </div>

        <!-- Input -->
        <div class="p-4 border-t border-gray-200 dark:border-white/5">
            <div class="flex gap-2">
                <input
                    v-model="newMessage"
                    @keyup.enter="sendMessage"
                    type="text"
                    placeholder="Type your message…"
                    class="flex-1 px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none text-sm"
                />
                <button
                    @click="sendMessage"
                    :disabled="typing || !newMessage.trim()"
                    class="px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <span class="material-symbols-outlined text-sm">send</span>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { individualSupportPageKey } from './individualSupportPageContext'

const {
    chatContainer,
    humanHandoffLocked,
    messages,
    newMessage,
    resetSession,
    selectedOrder,
    sendMessage,
    sendQuickAction,
    typing,
} = inject(individualSupportPageKey)
</script>
