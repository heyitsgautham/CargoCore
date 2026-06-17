<template>
    <div class="h-[calc(100vh-8rem)] flex gap-6">
        <!-- Conversation & Escalation Sidebar -->
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

        <!-- Active Chat / Ticket Area -->
        <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
            <template v-if="activeTab === 'chats' && activeChat">
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

            <!-- Escalation Detail View -->
            <template v-else-if="activeTab === 'escalations' && activeTicket">
                <div
                    class="p-6 border-b border-gray-200 dark:border-white/5 bg-gray-50/50 dark:bg-black/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="flex items-center gap-3 mb-2">
                            <span
                                class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">Ticket
                                #{{ activeTicket.id }}</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                                :class="activeTicket.priority === 'High' ? 'bg-red-100 text-red-600' : 'bg-yellow-100 text-yellow-600'">
                                {{ activeTicket.priority }} Priority
                            </span>
                        </div>
                        <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ activeTicket.title }}</h2>
                    </div>
                    <div class="flex gap-2 shrink-0">
                        <button @click="resolveTicket('Approved')" :disabled="ticketActionPending"
                            class="px-5 py-2.5 bg-green-500 hover:bg-green-600 text-white rounded-xl font-bold text-sm transition-colors shadow-sm flex items-center gap-2">
                            <span class="material-symbols-outlined text-[20px]">check_circle</span> {{ ticketActionPending ? 'Working...' : 'Approve' }}
                        </button>
                        <button @click="resolveTicket('Denied')" :disabled="ticketActionPending"
                            class="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold text-sm transition-colors shadow-sm flex items-center gap-2">
                            <span class="material-symbols-outlined text-[20px]">cancel</span> {{ ticketActionPending ? 'Working...' : 'Deny' }}
                        </button>
                    </div>
                </div>
                <div class="flex-1 p-6 overflow-y-auto bg-gray-50/30 dark:bg-black/10">
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 p-6 rounded-2xl shadow-sm space-y-6">
                        <div class="flex items-center gap-4 pb-6 border-b border-gray-100 dark:border-white/10">
                            <div
                                class="w-12 h-12 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center font-bold text-gray-700 dark:text-white text-lg shadow-inner">
                                {{ activeTicket.from.substring(0, 2).toUpperCase() }}</div>
                            <div>
                                <div class="font-bold text-gray-900 dark:text-white text-lg">{{ activeTicket.from }}
                                </div>
                                <div class="text-sm text-gray-500">{{ activeTicket.role }} • <span
                                        class="font-mono text-xs">{{ activeTicket.time }}</span></div>
                            </div>
                        </div>
                        <div>
                            <h4 class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                                <span class="material-symbols-outlined text-[18px]">report</span> Issue Description
                            </h4>
                            <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{
                                activeTicket.description }}</p>
                        </div>
                        <div
                            class="bg-blue-50 dark:bg-blue-900/10 p-5 rounded-xl border border-blue-100 dark:border-blue-500/20">
                            <h4
                                class="text-xs font-bold text-blue-800 dark:text-blue-300 uppercase tracking-wider mb-2">
                                Requested Action Override</h4>
                            <p
                                class="text-sm font-mono text-blue-900 dark:text-blue-200 font-bold bg-white/50 dark:bg-black/20 p-2 rounded">
                                {{ activeTicket.actionDetails }}</p>
                        </div>
                    </div>
                </div>
            </template>
            <div v-else class="flex-1 flex items-center justify-center text-gray-400">
                Select an item from the sidebar to view details.
            </div>
        </div>

        <!-- Profile Modal -->
        <div v-if="isProfileModalOpen && activeChat"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
            <div
                class="bg-slate-950/98 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col md:flex-row h-[500px] backdrop-blur-xl">
                <!-- Left: Profile Details -->
                <div
                    class="w-full md:w-1/2 p-8 bg-slate-900/90 flex flex-col items-center justify-center text-center border-r border-white/10">
                    <div
                        class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl font-bold text-white mb-4 shadow-lg shadow-purple-500/30">
                        {{ chatDisplayName(activeChat.name).substring(0, 2).toUpperCase() }}
                    </div>
                    <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">{{ chatDisplayName(activeChat.name) }}</h3>
                    <p class="text-sm text-gray-500 mb-4">{{ activeChatDriver?.vehicle || activeChat.role || 'Logistic Partner' }}</p>

                    <div class="flex gap-2 mb-6">
                        <span
                            class="px-3 py-1 rounded-full text-xs font-bold border border-gray-200 dark:border-white/10"
                            :class="activeChat.status === 'Online' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
                            {{ activeChatDriver?.status || activeChat.status || 'Offline' }}
                        </span>
                        <span v-if="activeChat.muted"
                            class="px-3 py-1 rounded-full text-xs font-bold bg-yellow-50 text-yellow-600 border border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">notifications_off</span> Muted
                        </span>
                    </div>

                    <div class="w-full space-y-3 text-left">
                        <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                            <span class="text-gray-500">Phone</span>
                            <span class="font-mono text-gray-900 dark:text-white">{{ activeChat.phone || activeChatDriver?.phone || 'N/A' }}</span>
                        </div>
                        <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                            <span class="text-gray-500">Location</span>
                            <span class="text-gray-900 dark:text-white">{{ activeChatDriver?.location || 'N/A' }}</span>
                        </div>
                        <div class="flex justify-between text-sm py-2 border-b border-gray-200 dark:border-white/10">
                            <span class="text-gray-500">Current Job</span>
                            <span class="text-gray-900 dark:text-white truncate max-w-[160px]">{{ activeChatDriver?.currentJob || 'Unassigned' }}</span>
                        </div>
                    </div>
                </div>

                <!-- Right: Stats / Actions -->
                <div class="w-full md:w-1/2 p-8 flex flex-col">
                    <div class="flex justify-between items-center mb-6">
                        <h4 class="font-bold text-gray-900 dark:text-white">Performance Metrics</h4>
                        <button @click="isProfileModalOpen = false" class="text-gray-400 hover:text-gray-600"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>

                    <div class="space-y-4 mb-auto">
                        <div
                            class="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl border border-blue-100 dark:border-blue-500/20">
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase">Efficiency Score</span>
                                <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.efficiency != null ? activeChatDriver.efficiency + '%' : 'N/A' }}</span>
                            </div>
                            <div v-if="activeChatDriver?.efficiency != null" class="w-full h-1.5 bg-blue-200 dark:bg-blue-900/30 rounded-full overflow-hidden">
                                <div class="h-full bg-blue-500" :style="{ width: activeChatDriver.efficiency + '%' }"></div>
                            </div>
                        </div>
                        <div
                            class="bg-purple-50 dark:bg-purple-900/10 p-4 rounded-xl border border-purple-100 dark:border-purple-500/20">
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase">Driver Rating</span>
                                <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.rating != null ? activeChatDriver.rating + ' / 5' : 'N/A' }}</span>
                            </div>
                        </div>
                        <div
                            class="bg-green-50 dark:bg-green-900/10 p-4 rounded-xl border border-green-100 dark:border-green-500/20">
                            <div class="flex justify-between items-center">
                                <span class="text-xs font-bold text-green-600 dark:text-green-400 uppercase">Avg Speed</span>
                                <span class="text-xl font-black text-gray-900 dark:text-white">{{ activeChatDriver?.avgSpeed != null ? activeChatDriver.avgSpeed + ' km/h' : 'N/A' }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3 mt-6">
                        <button @click="handleMuteChat"
                            class="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-gray-100 rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2 border border-white/10">
                            <span class="material-symbols-outlined text-[18px]">{{ activeChat.muted ? 'notifications' :
                                'notifications_off' }}</span> {{ activeChat.muted ? 'Unmute' : 'Mute' }}
                        </button>
                        <button @click="isProfileModalOpen = false"
                            class="px-4 py-3 bg-primary hover:bg-primary/90 text-white rounded-xl font-bold text-sm transition-colors flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">chat</span> Message
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Modal -->
        <div v-if="isDeleteModalOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
            <div
                class="bg-slate-950/98 w-full max-w-sm rounded-2xl shadow-xl p-6 border border-white/10 text-center backdrop-blur-xl">
                <div
                    class="w-16 h-16 bg-red-100 dark:bg-red-900/20 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span class="material-symbols-outlined text-3xl">warning</span>
                </div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Delete Conversation?</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Are you sure you want to delete the chat with
                    <span class="font-bold text-gray-900 dark:text-white">{{ chatDisplayName(activeChat?.name) }}</span>? This action
                    cannot be
                    undone.
                </p>

                <div class="flex gap-3 justify-center">
                    <button @click="isDeleteModalOpen = false"
                        class="px-5 py-2.5 rounded-xl font-bold text-sm text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 transition-colors">Cancel</button>
                    <button @click="confirmDeleteChat"
                        class="px-5 py-2.5 rounded-xl font-bold text-sm text-white bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30 transition-colors">Delete
                        Chat</button>
                </div>
            </div>
        </div>

        <!-- Broadcast Modal -->
        <div v-if="isBroadcastModalOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
            <div
                class="bg-slate-950/98 w-full max-w-md rounded-2xl shadow-xl border border-white/10 overflow-hidden backdrop-blur-xl">
                <div
                    class="p-5 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 class="font-bold text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-purple-600">campaign</span> New System Broadcast
                    </h3>
                    <button @click="isBroadcastModalOpen = false"
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-5">
                    <div class="space-y-1.5">
                        <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Target Audience</label>
                        <select v-model="broadcastForm.audience"
                            class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all">
                            <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Personnel</option>
                            <option value="drivers" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Drivers (On-Duty)</option>
                            <option value="warehouses" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Warehouse Managers</option>
                        </select>
                    </div>
                    <div class="space-y-1.5">
                        <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Alert Type</label>
                        <select v-model="broadcastForm.type"
                            class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all">
                            <option value="info" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">General Information</option>
                            <option value="warning" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">System Warning</option>
                            <option value="emergency" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Emergency Recall / Halt</option>
                        </select>
                    </div>
                    <div class="space-y-1.5">
                        <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Message Details</label>
                        <textarea v-model="broadcastForm.message" rows="4" placeholder="Enter broadcast message here..."
                            class="w-full bg-slate-800 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-slate-400 outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20 shadow-sm transition-all resize-none"></textarea>
                    </div>
                </div>
                <div
                    class="p-5 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                    <button @click="isBroadcastModalOpen = false"
                        class="px-5 py-2.5 rounded-xl text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 font-bold text-sm transition-colors">Cancel</button>
                    <button @click="sendBroadcast"
                        class="px-6 py-2.5 rounded-xl font-bold text-sm text-white shadow-lg flex items-center gap-2 transition-all hover:scale-105"
                        :class="broadcastForm.type === 'emergency' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/30' : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-purple-500/30'">
                        <span class="material-symbols-outlined text-[18px]">send_time_extension</span> Deploy Alert
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import { storeToRefs } from 'pinia'

const store = useLogisticStore()
const authStore = useAuthStore()
const { filteredChats, filteredEscalations, escalations } = storeToRefs(store)

onMounted(() => {
    store.refresh().catch(() => {})
})

// Strip legacy "LM Driver: " prefix (for any old threads still on the backend)
function chatDisplayName(name) {
    if (!name) return ''
    return String(name).startsWith('LM Driver: ') ? String(name).slice('LM Driver: '.length) : String(name)
}

const activeTab = ref('chats')
const activeChatId = ref(null)
const activeTicketId = ref(null)
const searchQuery = ref('')
const messageInput = ref('')
const chatHistoryContainer = ref(null)
const ticketActionPending = ref(false)

// New Chat contact picker
const isNewChatOpen = ref(false)
const contactSearchQuery = ref('')
const newChatLoading = ref(false)

const filteredContactDrivers = computed(() => {
    const q = contactSearchQuery.value.toLowerCase()
    return store.drivers.filter((d) => !q || d.name?.toLowerCase().includes(q))
})

const filteredContactWMs = computed(() => {
    const q = contactSearchQuery.value.toLowerCase()
    return store.warehouseManagerUsers.filter((u) => !q || u.name?.toLowerCase().includes(q))
})

const startChatWith = async (contact, type) => {
    isNewChatOpen.value = false
    contactSearchQuery.value = ''
    newChatLoading.value = true
    try {
        let thread
        if (type === 'driver') {
            thread = await store.ensureManagerDriverThread(contact)
        } else {
            // For WMs find or create a thread by name
            const existing = store.chats.find((c) => c.name === contact.name)
            if (existing) {
                thread = existing
            } else {
                thread = await store.createChatThread(contact.name, contact.mobile || null, contact.hubId || null)
            }
        }
        activeTab.value = 'chats'
        activeChatId.value = thread.id
        await nextTick()
        scrollToBottom()
    } catch (e) {
        console.warn('[Communication] startChatWith failed:', e)
    } finally {
        newChatLoading.value = false
    }
}
const isMenuOpen = ref(false)
const menuButtonRef = ref(null)
const menuPosition = ref({ top: 0, right: 0 })

const toggleMenu = () => {
    if (!isMenuOpen.value && menuButtonRef.value) {
        const rect = menuButtonRef.value.getBoundingClientRect()
        menuPosition.value = {
            top: rect.bottom + 8,
            right: window.innerWidth - rect.right
        }
    }
    isMenuOpen.value = !isMenuOpen.value
}

const isProfileModalOpen = ref(false)
const isDeleteModalOpen = ref(false)
const isBroadcastModalOpen = ref(false)

const broadcastForm = ref({
    audience: 'all',
    type: 'info',
    message: ''
})

const activeChat = computed(() => {
    return activeChatId.value != null ? (filteredChats.value.find(c => c.id === activeChatId.value) ?? null) : null
})

const activeChatDriver = computed(() => {
    if (!activeChat.value) return null
    const name = chatDisplayName(activeChat.value.name)
    return store.drivers.find(d => d.name === name) || null
})

const activeTicket = computed(() => {
    return activeTicketId.value != null ? (filteredEscalations.value?.find(t => t.id === activeTicketId.value) ?? null) : null
})

const displayChats = computed(() => {
    if (activeTab.value !== 'chats') return []
    if (!searchQuery.value) return filteredChats.value
    return filteredChats.value.filter(c => c.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
})

const displayEscalations = computed(() => {
    if (activeTab.value !== 'escalations') return []
    if (!searchQuery.value) return filteredEscalations.value || []

    const query = searchQuery.value.toLowerCase()
    return (filteredEscalations.value || []).filter(t =>
        t.title.toLowerCase().includes(query) ||
        t.from.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query)
    )
})

const scrollToBottom = async () => {
    await nextTick()
    if (chatHistoryContainer.value) {
        chatHistoryContainer.value.scrollTop = chatHistoryContainer.value.scrollHeight
    }
}

const selectChat = (id) => {
    activeChatId.value = id
    scrollToBottom()
}

const sendMessage = async () => {
    const text = messageInput.value.trim()
    if (!text || !activeChat.value) return

    // Optimistic update for instant UI feedback
    activeChat.value.messages.push({
        id: Date.now(),
        text: text,
        sender: 'me',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    activeChat.value.lastMessage = text
    activeChat.value.time = 'Just now'
    messageInput.value = ''
    scrollToBottom()

    // Persist to backend
    try {
        await store.sendChatMessage(activeChat.value.id, text)
    } catch (e) {
        console.warn('[Communication] sendChatMessage failed:', e)
    }
}

// Watch active chat to scroll on change
watch(activeChatId, () => {
    scrollToBottom()
})

const handleViewProfile = () => {
    isMenuOpen.value = false
    isProfileModalOpen.value = true
}

const handleMuteChat = async () => {
    isMenuOpen.value = false
    if (activeChat.value) {
        const newMuted = !activeChat.value.muted
        activeChat.value.muted = newMuted // optimistic
        try {
            await store.muteChatThread(activeChat.value.id, newMuted)
        } catch (e) {
            console.warn('[Communication] muteChatThread failed:', e)
        }
    }
}

const handleDeleteChat = () => {
    isMenuOpen.value = false
    isDeleteModalOpen.value = true
}

const confirmDeleteChat = async () => {
    if (activeChat.value) {
        const deletedId = activeChat.value.id
        try {
            await store.deleteChatThread(deletedId)
        } catch (e) {
            console.warn('[Communication] deleteChatThread failed:', e)
            const idx = store.chats.findIndex(c => c.id === deletedId)
            if (idx !== -1) store.chats.splice(idx, 1)
        }
        activeChatId.value = store.chats.length > 0 ? store.chats[0].id : null
    }
    isDeleteModalOpen.value = false
}

import { resolveEscalationCenter } from '@/utils/aiApi'

function extractRestockRequestId(ticket) {
    const details = String(ticket?.actionDetails || '')
    const match = details.match(/\[ref:([0-9a-fA-F-]{36})\]/)
    return match?.[1] || null
}

function isRestockEscalation(ticket) {
    return Boolean(extractRestockRequestId(ticket)) && /restock/i.test(String(ticket?.title || ''))
}

async function resolveRestockEscalation(ticket, ticketStatus) {
    const requestId = extractRestockRequestId(ticket)
    if (!requestId) throw new Error('Restock request reference not found')

    const response = await fetch(apiUrl(`api/v1/inventory/restock-requests/${requestId}/status`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: ticketStatus === 'Approved' ? 'APPROVED' : 'REJECTED',
            manager_notes: ticketStatus === 'Approved'
                ? 'Approved by Logistics Manager via Communication Center'
                : 'Rejected by Logistics Manager via Communication Center',
            funding_source: 'APP_REVENUE',
        }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        const detail = String(error.detail || '')
        if (response.status === 400 && /already processed/i.test(detail)) {
            await resolveGenericLogisticsEscalation(ticket, 'Resolved')
            return
        }
        throw new Error(detail || 'Failed to update restock request')
    }
}

async function resolveGenericLogisticsEscalation(ticket, ticketStatus) {
    const response = await fetch(apiUrl(`api/v1/logistics/escalations/${ticket.id}`), {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: ticketStatus === 'Approved'
                ? 'APPROVED'
                : ticketStatus === 'Denied'
                    ? 'REJECTED'
                    : 'RESOLVED',
        }),
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Failed to update escalation')
    }
}

const resolveTicket = async (ticketStatus) => {
    const ticketId = activeTicketId.value
    const ticket = activeTicket.value
    if (!ticketId || !ticket || ticketActionPending.value) return

    ticketActionPending.value = true
    try {
        if (isRestockEscalation(ticket)) {
            await resolveRestockEscalation(ticket, ticketStatus)
        } else if (String(ticket.id).includes('-')) {
            await resolveGenericLogisticsEscalation(ticket, ticketStatus)
        } else {
            await resolveEscalationCenter(ticketId)
        }

        const remaining = (escalations.value || []).filter(t => t.id !== ticketId)
        escalations.value = remaining
        activeTicketId.value = remaining.length > 0 ? remaining[0].id : null
        store.refresh().catch(() => {})
    } catch (e) {
        console.error('Failed to resolve ticket:', e)
    } finally {
        ticketActionPending.value = false
    }
}

const broadcastSuccess = ref(false)
const broadcastError = ref(false)
const sendBroadcast = async () => {
    const { audience, type, message } = broadcastForm.value
    if (!message.trim()) return
    isBroadcastModalOpen.value = false
    try {
        await store.sendBroadcast({ audience, type, message })
        broadcastSuccess.value = true
        setTimeout(() => { broadcastSuccess.value = false }, 4000)

        const titleMap = { info: 'System Broadcast', warning: '⚠️ System Warning', emergency: '🚨 Emergency Alert' }
        const typeMap = { info: 'info', warning: 'warning', emergency: 'alert' }
        store.notifications.unshift({
            id: Date.now().toString(),
            title: `[Broadcast Sent] ${titleMap[type] ?? 'System Broadcast'}`,
            message: `Broadcast sent: ${message}`,
            time: new Date().toISOString(),
            read: false,
            type: typeMap[type] ?? 'info',
        })
    } catch (e) {
        broadcastError.value = true
        setTimeout(() => { broadcastError.value = false }, 4000)
        console.warn('[Communication] sendBroadcast failed:', e)
    }
    broadcastForm.value.message = ''
}
</script>
