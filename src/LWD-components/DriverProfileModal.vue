<template>
    <BaseModal :is-open="isOpen" @close="handleClose">
        <template #title>Driver Profile</template>

        <div v-if="driver" class="space-y-6">
            <template v-if="activeView === 'profile'">
                <!-- Header Profile -->
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold text-white shadow-lg ring-2 ring-gray-200 dark:ring-white/10"
                        :class="driver.avatarColor || 'bg-gray-700'">
                        {{ driver.name.charAt(0) }}
                    </div>
                    <div>
                        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ driver.name }}</h2>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border"
                                :class="getStatusClass(driver.status)">
                                {{ driver.status }}
                            </span>
                            <span class="text-gray-500 dark:text-gray-400 text-xs">• ID: {{ driver.id }}</span>
                        </div>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-2 gap-3">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5">
                        <div class="text-xs text-gray-500 dark:text-gray-500">Current Vehicle</div>
                        <div class="text-lg font-semibold text-gray-900 dark:text-white mt-1">{{ driver.vehicle }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5">
                        <div class="text-xs text-gray-500 dark:text-gray-500">Efficiency Score</div>
                        <div class="text-lg font-semibold text-green-600 dark:text-green-400 mt-1">{{ driver.efficiency
                        }}%
                        </div>
                    </div>
                </div>

                <!-- Current Status -->
                <div class="flex flex-col gap-3">
                    <div
                        class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5 space-y-3">
                        <div
                            class="flex justify-between items-center text-sm border-b border-gray-200 dark:border-white/5 pb-2">
                            <span class="text-gray-500 dark:text-gray-400">Current Job</span>
                            <span class="text-gray-900 dark:text-white font-medium">{{ driver.currentJob }}</span>
                        </div>
                        <div class="flex justify-between items-center text-sm pb-1">
                            <span class="text-gray-500 dark:text-gray-400">Location</span>
                            <span class="text-gray-900 dark:text-white flex items-center gap-1 font-medium">
                                <span class="material-symbols-outlined text-[16px] text-primary">location_on</span>
                                {{ driver.location }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="grid grid-cols-1 gap-3">
                    <button @click="openChat"
                        class="flex items-center justify-center gap-2 py-3 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl text-sm font-bold transition-colors border border-primary/20">
                        <span class="material-symbols-outlined text-[18px]">chat</span>
                        Message Driver
                    </button>
                </div>
            </template>

            <!-- Chat Interface Mock -->
            <template v-else>
                <div class="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-white/10">
                    <button @click="activeView = 'profile'"
                        class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg text-gray-500 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">arrow_back</span>
                    </button>
                    <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-sm"
                        :class="driver.avatarColor || 'bg-gray-700'">
                        {{ driver.name.charAt(0) }}
                    </div>
                    <div>
                        <h3 class="font-bold text-sm text-gray-900 dark:text-white leading-tight">{{ driver.name }}</h3>
                        <span class="text-[10px] text-green-500 font-medium">Online</span>
                    </div>
                </div>

                <div class="h-64 overflow-y-auto pr-2 space-y-4 no-scrollbar flex flex-col pt-2">
                    <div v-if="chatLoading" class="flex items-center justify-center h-full text-gray-400 text-sm">
                        <span class="material-symbols-outlined animate-spin mr-2">progress_activity</span> Connecting...
                    </div>
                    <div v-for="msg in chatMessages" :key="msg.id" class="flex gap-2 max-w-[85%]"
                        :class="isManagerOutgoing(msg) ? 'self-end flex-row-reverse' : 'items-end'">

                        <!-- Avatar (only for driver) -->
                        <div v-if="!isManagerOutgoing(msg)"
                            class="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white mt-auto"
                            :class="driver.avatarColor || 'bg-gray-700'">
                            {{ driver.name.charAt(0) }}
                        </div>

                        <!-- Message Bubble -->
                        <div class="p-3 text-sm break-words whitespace-pre-wrap border shadow-sm" :class="[
                            isManagerOutgoing(msg)
                                ? 'bg-emerald-600 border-emerald-500 text-white rounded-2xl rounded-tr-sm'
                                : 'bg-slate-800 border-slate-700 text-slate-100 rounded-2xl rounded-tl-sm'
                        ]">
                            {{ msg.text }}
                            <div class="text-[9px] mt-1"
                                :class="isManagerOutgoing(msg) ? 'text-emerald-100/80 text-right' : 'text-slate-400'">
                                {{ msg.time }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="pt-4 border-t border-gray-200 dark:border-white/10">
                    <div class="relative">
                        <input type="text" v-model="newMessage" @keyup.enter="sendMessage"
                            :disabled="chatLoading || chatSending"
                            placeholder="Type a message..."
                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full py-2.5 pl-4 pr-12 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/50">
                        <button @click="sendMessage"
                            :disabled="chatLoading || chatSending || !newMessage.trim()"
                            class="absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full bg-primary text-white hover:bg-primary-dark transition-colors"
                            :class="{ 'opacity-50 cursor-not-allowed': chatLoading || chatSending || !newMessage.trim() }">
                            <span class="material-symbols-outlined text-[16px] ml-0.5">send</span>
                        </button>
                    </div>
                </div>
            </template>
        </div>
    </BaseModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import BaseModal from '../components/BaseModal.vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useUiStore } from '@/stores/uiStore'

const props = defineProps({
    isOpen: Boolean,
    driver: Object
})

const emit = defineEmits(['close'])
const store = useLogisticStore()
const uiStore = useUiStore()

const activeView = ref('profile')
const newMessage = ref('')
const chatThreadId = ref(null)
const chatLoading = ref(false)
const chatSending = ref(false)
const MANAGER_SENDERS = new Set(['me', 'manager', 'logistics manager'])

const driverContext = computed(() => {
    if (!props.driver) return null
    const liveDriver = store.drivers.find((item) => (
        String(item.id) === String(props.driver.id)
        || String(item.name || '').trim().toLowerCase() === String(props.driver.name || '').trim().toLowerCase()
    ))
    if (!liveDriver) return props.driver
    return {
        ...liveDriver,
        ...props.driver,
        phone: props.driver.phone || liveDriver.phone || null,
        hubId: props.driver.hubId || liveDriver.hubId || null,
        warehouseId: props.driver.warehouseId || liveDriver.warehouseId || null,
        avatarColor: props.driver.avatarColor || liveDriver.avatarColor || 'bg-gray-700',
    }
})

const chatMessages = computed(() => {
    if (chatThreadId.value) {
        const thread = store.chats.find(c => c.id === chatThreadId.value)
        return thread?.messages || []
    }
    return []
})

const openChat = async () => {
    activeView.value = 'chat'
    if (!driverContext.value || chatThreadId.value) return
    chatLoading.value = true
    try {
        const thread = await store.ensureManagerDriverThread(driverContext.value)
        chatThreadId.value = String(thread.id)
    } finally {
        chatLoading.value = false
    }
}

const sendMessage = async () => {
    const text = newMessage.value.trim()
    if (!text || chatSending.value) return

    chatSending.value = true
    let optimisticMessageId = null
    try {
        if (!chatThreadId.value && driverContext.value) {
            chatLoading.value = true
            const thread = await store.ensureManagerDriverThread(driverContext.value)
            chatThreadId.value = String(thread.id)
            chatLoading.value = false
        }
        if (!chatThreadId.value) return

        const thread = store.chats.find((item) => item.id === chatThreadId.value)
        if (thread) {
            optimisticMessageId = `pending-${Date.now()}`
            const optimisticTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            thread.messages.push({
                id: optimisticMessageId,
                text,
                sender: 'me',
                time: optimisticTime,
            })
            thread.lastMessage = text
            thread.time = 'Just now'
        }

        newMessage.value = ''
        await store.sendChatMessage(chatThreadId.value, text)
    } catch (error) {
        if (optimisticMessageId && chatThreadId.value) {
            const thread = store.chats.find((item) => item.id === chatThreadId.value)
            if (thread) {
                thread.messages = thread.messages.filter((msg) => msg.id !== optimisticMessageId)
            }
        }
        newMessage.value = text
        uiStore.showToast?.(error?.message || 'Failed to send message', 'error', 2500)
    } finally {
        chatLoading.value = false
        chatSending.value = false
    }
}

function isManagerOutgoing(msg) {
    return MANAGER_SENDERS.has(String(msg?.sender || '').toLowerCase())
}

const handleClose = () => {
    setTimeout(() => {
        activeView.value = 'profile'
        chatThreadId.value = null
        newMessage.value = ''
        chatLoading.value = false
        chatSending.value = false
    }, 300)
    emit('close')
}

function getStatusClass(status) {
    if (!status) return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    switch (status.toLowerCase()) {
        case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30'
        case 'breakdown': return 'bg-red-500/20 text-red-400 border-red-500/30'
        case 'deviation': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
        default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
}

watch(
    () => [props.isOpen, driverContext.value?.id, driverContext.value?.name],
    async ([isOpen]) => {
        if (!isOpen) return
        newMessage.value = ''
        if (!driverContext.value) {
            chatThreadId.value = null
            return
        }
        chatLoading.value = true
        try {
            const thread = await store.ensureManagerDriverThread(driverContext.value)
            chatThreadId.value = String(thread.id)
        } catch (_) {
            chatThreadId.value = null
        } finally {
            chatLoading.value = false
        }
    },
    { immediate: true }
)
</script>
