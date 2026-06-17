<template>
    <div class="h-[calc(100vh-8rem)] flex gap-6">
        <!-- Thread List -->
        <div class="w-72 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20">
                <div class="font-bold text-sm text-gray-900 dark:text-white">Dispatcher Inbox</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">Messages from Dispatch Console</div>
            </div>

            <!-- Loading -->
            <div v-if="isLoading" class="flex-1 flex items-center justify-center">
                <span class="material-symbols-outlined text-2xl text-gray-400 animate-spin">progress_activity</span>
            </div>

            <!-- Empty state -->
            <div v-else-if="!myThreads.length"
                class="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <span class="material-symbols-outlined text-5xl text-gray-300 dark:text-gray-600 mb-3">mark_chat_unread</span>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">No messages yet</p>
                <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1">Messages from the Dispatcher will appear
                    here</p>
            </div>

            <!-- Thread items -->
            <div v-else class="flex-1 overflow-y-auto no-scrollbar">
                <div v-for="thread in myThreads" :key="thread.id" @click="activeThreadId = thread.id"
                    class="p-4 border-b border-gray-200 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors flex items-center gap-3"
                    :class="activeThreadId === thread.id ? 'bg-gray-50 dark:bg-white/5 border-l-2 border-l-primary' : ''">
                    <div
                        class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                        <span class="material-symbols-outlined text-primary text-[18px]">headset_mic</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-center">
                            <div class="font-bold text-gray-900 dark:text-white text-sm">Dispatcher</div>
                            <div class="text-[9px] text-gray-500 dark:text-gray-500">{{ thread.time }}</div>
                        </div>
                        <div class="text-[11px] text-gray-500 dark:text-gray-400 truncate mt-0.5">
                            {{ thread.lastMessage || 'Start of conversation' }}
                        </div>
                        <div class="text-[9px] mt-1 font-semibold px-1.5 py-0.5 rounded-full inline-block"
                            :class="thread.status === 'Online' ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-white/10 text-gray-500 dark:text-gray-400'">
                            {{ thread.status }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Refresh -->
            <div class="p-3 border-t border-gray-200 dark:border-white/5">
                <button @click="loadChats" :disabled="isLoading"
                    class="w-full py-2 text-xs text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50">
                    <span class="material-symbols-outlined text-[16px]"
                        :class="isLoading ? 'animate-spin' : ''">refresh</span>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Chat Area -->
        <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
            <!-- No thread selected -->
            <div v-if="!activeThread" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <span class="material-symbols-outlined text-6xl text-gray-300 dark:text-gray-600 mb-4">forum</span>
                <p class="text-base font-medium text-gray-500 dark:text-gray-400">
                    {{ myThreads.length ? 'Select a conversation' : 'No messages from Dispatcher yet' }}
                </p>
                <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">
                    {{ myThreads.length ? 'Choose a thread from the left to view messages' : 'When the Dispatcher sends you a message it will appear here' }}
                </p>
            </div>

            <template v-else>
                <!-- Header -->
                <div
                    class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center justify-between bg-gray-100 dark:bg-black/20">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                            <span class="material-symbols-outlined text-primary text-[18px]">headset_mic</span>
                        </div>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white">Dispatcher</div>
                            <div class="text-xs"
                                :class="activeThread.status === 'Online' ? 'text-green-500 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                                {{ activeThread.status }}
                            </div>
                        </div>
                    </div>
                    <div class="text-[10px] text-gray-400 dark:text-gray-500">
                        Thread #{{ activeThread.id?.toString().slice(0, 8) }}
                    </div>
                </div>

                <!-- Messages -->
                <div class="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 dark:bg-black/10" ref="chatAreaRef">
                    <div v-if="!currentMessages.length"
                        class="flex flex-col items-center justify-center h-full text-center">
                        <span
                            class="material-symbols-outlined text-4xl text-gray-300 dark:text-gray-600 mb-3">chat_bubble_outline</span>
                        <p class="text-sm text-gray-500 dark:text-gray-400">No messages yet</p>
                        <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1">Send a message to start the
                            conversation</p>
                    </div>

                    <div v-for="msg in currentMessages" :key="msg.id"
                        :class="msg.sender === 'me' ? 'flex gap-3 flex-row-reverse' : 'flex gap-3'">
                        <!-- WM's own message — right, teal -->
                        <template v-if="msg.sender === 'me'">
                            <div
                                class="w-8 h-8 rounded-full bg-teal-500/20 flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-teal-600 dark:text-teal-400">
                                WM</div>
                            <div class="max-w-[70%]">
                                <div
                                    class="bg-teal-100 dark:bg-teal-500/20 border border-teal-200 dark:border-teal-500/30 p-3 rounded-xl rounded-tr-none text-gray-900 dark:text-white text-sm break-words">
                                    {{ msg.text }}</div>
                                <div class="text-[9px] text-gray-500 dark:text-gray-600 mt-1 text-right">{{ msg.time }}
                                </div>
                            </div>
                        </template>
                        <!-- Dispatcher message — left, green/primary -->
                        <template v-else>
                            <div
                                class="w-8 h-8 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-primary">
                                DISP</div>
                            <div class="max-w-[70%]">
                                <div
                                    class="bg-emerald-100 dark:bg-primary/20 border border-emerald-200 dark:border-primary/30 p-3 rounded-xl rounded-tl-none text-gray-900 dark:text-white text-sm break-words">
                                    {{ msg.text }}</div>
                                <div class="text-[9px] text-gray-500 dark:text-gray-600 mt-1">{{ msg.time }}</div>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Input -->
                <div class="p-4 bg-gray-100 dark:bg-black/20 border-t border-gray-200 dark:border-white/5">
                    <div class="flex gap-2 items-stretch">
                        <input v-model="newMessage" type="text" placeholder="Reply to Dispatcher..."
                            class="flex-1 bg-white dark:bg-white/5 border-2 border-gray-300 dark:border-white/10 rounded-full py-3 pl-4 pr-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm"
                            @keyup.enter="sendReply" :disabled="isSending">
                        <button @click="sendReply" :disabled="!newMessage.trim() || isSending"
                            class="px-4 bg-primary rounded-full text-black hover:scale-105 transition-transform disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 flex-shrink-0 flex items-center justify-center">
                            <span class="material-symbols-outlined text-[20px]">{{ isSending ? 'hourglass_empty' :
                                'send' }}</span>
                        </button>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'

const store = useLogisticStore()
const authStore = useAuthStore()

const isLoading = ref(false)
const activeThreadId = ref(null)
const newMessage = ref('')
const isSending = ref(false)
const chatAreaRef = ref(null)

// Local message history per thread (optimistic updates)
const messageHistory = ref({})

const wmName = computed(() => authStore.currentUser?.name?.trim().toLowerCase() || '')

// Only show threads whose name matches this WM
const myThreads = computed(() =>
    store.chats.filter(t => t.name?.trim().toLowerCase() === wmName.value)
)

// Auto-select first thread when loaded
watch(myThreads, (list) => {
    if (list.length && activeThreadId.value === null) {
        activeThreadId.value = list[0].id
    }
}, { immediate: true })

const activeThread = computed(() =>
    myThreads.value.find(t => t.id === activeThreadId.value) || null
)

// Seed message history from thread data
watch(myThreads, (list) => {
    list.forEach(t => {
        if (t.messages?.length && !messageHistory.value[t.id]) {
            messageHistory.value[t.id] = t.messages.map(m => ({ ...m }))
        }
    })
}, { immediate: true, deep: true })

watch(activeThreadId, (id) => {
    if (!id) return
    const thread = myThreads.value.find(t => t.id === id)
    if (thread?.messages?.length && !messageHistory.value[id]) {
        messageHistory.value[id] = thread.messages.map(m => ({ ...m }))
    }
    nextTick(() => scrollToBottom())
})

const currentMessages = computed(() =>
    messageHistory.value[activeThreadId.value] || activeThread.value?.messages || []
)

function scrollToBottom() {
    if (chatAreaRef.value) chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
}

async function loadChats() {
    isLoading.value = true
    try {
        await store.fetchWmChats()
    } catch (e) {
        console.warn('[WM Communication] fetchWmChats failed', e)
    } finally {
        isLoading.value = false
    }
}

async function sendReply() {
    const text = newMessage.value.trim()
    if (!text || isSending.value || !activeThread.value) return

    const threadId = activeThreadId.value
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    // Optimistic add
    if (!messageHistory.value[threadId]) messageHistory.value[threadId] = []
    messageHistory.value[threadId].push({ id: `temp-${Date.now()}`, sender: 'me', text, time: now })
    newMessage.value = ''
    nextTick(() => scrollToBottom())

    isSending.value = true
    try {
        const updated = await store.sendChatMessage(threadId, text)
        if (updated?.messages) {
            messageHistory.value[threadId] = updated.messages.map(m => ({ ...m }))
            nextTick(() => scrollToBottom())
        }
    } catch (_) {
        // Message already shown optimistically
    } finally {
        isSending.value = false
    }
}

onMounted(() => loadChats())
</script>
