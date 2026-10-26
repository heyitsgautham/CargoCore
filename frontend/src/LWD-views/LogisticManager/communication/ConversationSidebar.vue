<template>
    <div class="w-80 glass-panel rounded-xl flex flex-col overflow-hidden">
        <!-- Tabs + New Chat button -->
        <div class="flex items-center border-b border-gray-200 dark:border-white/5">
            <button @click="activeTab = 'chats'" class="flex-1 py-3 text-sm font-bold text-center transition-colors"
                :class="activeTab === 'chats' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-white/5'">Messages</button>
            <button @click="activeTab = 'escalations'"
                class="flex-1 py-3 text-sm font-bold text-center transition-colors flex items-center justify-center gap-1"
                :class="activeTab === 'escalations' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-white/5'">
                Escalations <span v-if="filteredEscalations.length"
                    class="bg-red-500 text-white text-[10px] px-1.5 rounded-full">{{ filteredEscalations.length
                    }}</span>
            </button>
            <!-- New Chat Button -->
            <div class="relative flex-shrink-0">
                <button @click="isNewChatOpen = !isNewChatOpen"
                    class="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-full transition-colors mx-1"
                    title="New Chat">
                    <span class="material-symbols-outlined text-[20px]">edit_square</span>
                </button>
                <!-- Contact Picker Dropdown -->
                <div v-if="isNewChatOpen"
                    class="absolute right-0 top-12 w-64 bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden z-50 animate-fade-in-up origin-top-right">
                    <div class="p-3 border-b border-gray-100 dark:border-white/5">
                        <input v-model="contactSearchQuery" type="text" placeholder="Search contacts..."
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-1.5 px-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors"
                            autofocus />
                    </div>
                    <div class="max-h-72 overflow-y-auto no-scrollbar">
                        <!-- Drivers -->
                        <div v-if="filteredContactDrivers.length">
                            <div class="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-black/20">Drivers</div>
                            <button v-for="d in filteredContactDrivers" :key="'dr-'+d.id"
                                @click="startChatWith(d, 'driver')"
                                class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-primary/5 dark:hover:bg-white/5 transition-colors text-left">
                                <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
                                    :class="d.avatarColor || 'bg-gray-600'">
                                    {{ d.name?.substring(0, 2).toUpperCase() }}
                                </div>
                                <div>
                                    <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ d.name }}</div>
                                    <div class="text-[10px] text-gray-400 flex items-center gap-1">
                                        <span class="w-1.5 h-1.5 rounded-full"
                                            :class="d.status === 'Active' ? 'bg-green-500' : 'bg-gray-400'"></span>
                                        {{ d.status }}
                                    </div>
                                </div>
                            </button>
                        </div>
                        <!-- Warehouse Managers -->
                        <div v-if="filteredContactWMs.length">
                            <div class="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-black/20">Warehouse Managers</div>
                            <button v-for="wm in filteredContactWMs" :key="'wm-'+wm.id"
                                @click="startChatWith(wm, 'wm')"
                                class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-primary/5 dark:hover:bg-white/5 transition-colors text-left">
                                <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white bg-purple-600">
                                    {{ wm.name?.substring(0, 2).toUpperCase() }}
                                </div>
                                <div>
                                    <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ wm.name }}</div>
                                    <div class="text-[10px] text-gray-400">Warehouse Manager</div>
                                </div>
                            </button>
                        </div>
                        <div v-if="!filteredContactDrivers.length && !filteredContactWMs.length"
                            class="p-6 text-center text-sm text-gray-400">No contacts found.</div>
                    </div>
                </div>
                <div v-if="isNewChatOpen" @click="isNewChatOpen = false" class="fixed inset-0 z-40"></div>
            </div>
        </div>
        <div class="p-4 border-b border-gray-200 dark:border-white/5">
            <div class="relative">
                <span
                    class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 dark:text-gray-500">search</span>
                <input type="text" :placeholder="activeTab === 'chats' ? 'Search chats...' : 'Search tickets...'"
                    v-model="searchQuery"
                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-10 pr-4 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50 transition-colors">
            </div>
        </div>
        <div class="flex-1 overflow-y-auto no-scrollbar">
            <!-- Chats List -->
            <div v-if="activeTab === 'chats'">
                <div v-for="chat in displayChats" :key="chat.id"
                    class="p-4 border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
                    :class="activeChatId === chat.id ? 'bg-primary/5 border-l-2 border-l-primary dark:bg-white/5' : ''"
                    @click="activeChatId = chat.id">
                    <div class="flex justify-between items-start mb-1">
                        <div class="font-bold text-gray-900 dark:text-white text-sm">{{ chatDisplayName(chat.name) }}</div>
                        <div class="text-[10px] text-gray-500">{{ chat.time }}</div>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ chat.lastMessage }}</div>
                </div>
            </div>

            <!-- Escalations List -->
            <div v-if="activeTab === 'escalations'">
                <div v-for="ticket in displayEscalations" :key="ticket.id"
                    class="p-4 border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
                    :class="activeTicketId === ticket.id ? 'bg-red-500/5 border-l-2 border-l-red-500 dark:bg-white/5' : ''"
                    @click="activeTicketId = ticket.id">
                    <div class="flex justify-between items-start mb-1">
                        <div class="font-bold text-gray-900 dark:text-white text-sm truncate pr-2">{{ ticket.title
                        }}</div>
                        <div class="text-[10px] text-gray-500 flex-shrink-0">{{ ticket.time }}</div>
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                            :class="ticket.priority === 'High' ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'">
                            {{ ticket.priority }}
                        </span>
                        <span class="text-xs text-gray-500 truncate">From: {{ ticket.from }}</span>
                    </div>
                </div>
                <div v-if="filteredEscalations.length === 0" class="p-8 text-center text-sm text-gray-500">
                    No pending escalations.
                </div>
                <div v-else-if="displayEscalations.length === 0" class="p-8 text-center text-sm text-gray-500">
                    No escalations match "{{ searchQuery }}".
                </div>
            </div>
        </div>

        <!-- Broadcast Button -->
        <div class="p-4 border-t border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/20">
            <button @click="isBroadcastModalOpen = true"
                class="w-full py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-transform hover:scale-[1.02]">
                <span class="material-symbols-outlined text-[18px]">campaign</span> System Broadcast
            </button>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const {
    activeChatId,
    activeTab,
    activeTicketId,
    chatDisplayName,
    contactSearchQuery,
    displayChats,
    displayEscalations,
    filteredContactDrivers,
    filteredContactWMs,
    filteredEscalations,
    isBroadcastModalOpen,
    isNewChatOpen,
    searchQuery,
    startChatWith,
} = inject(communicationPageKey)
</script>
