<template>
    <div class="min-h-[calc(100vh-8rem)] flex flex-col gap-6">

        <!-- Top Section -->
        <div class="flex flex-col md:flex-row gap-6 flex-1 min-h-[500px]">

            <!-- LEFT SIDEBAR -->
            <div class="w-full md:w-72 flex flex-col gap-6 shrink-0">
                <!-- Priority Support -->
                <div class="glass-panel p-5 rounded-xl flex flex-col items-center text-center justify-center">
                    <div class="w-14 h-14 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 mb-3">
                        <span class="material-symbols-outlined text-2xl">phone_in_talk</span>
                    </div>
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm">Priority Support</h3>
                    <p class="text-[10px] text-gray-400 mb-3">Dedicated line for enterprise partners.</p>
                    <div class="text-base font-bold text-gray-900 dark:text-white">+91 1800 999 0000</div>
                </div>

                <!-- Status Breakdown Chart -->
                <div class="glass-panel p-5 rounded-xl flex flex-col items-center justify-center relative min-h-[220px]">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 absolute top-5 left-5">Status Breakdown</h3>
                    <div class="w-full h-36 flex justify-center items-center mt-6">
                        <Doughnut :data="chartData" :options="chartOptions" />
                    </div>
                </div>

                <!-- Ticket Summary Stats -->
                <div class="glass-panel p-5 rounded-xl flex flex-col justify-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4">Ticket Summary</h3>
                    <div class="space-y-4 text-sm mt-2">
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between items-end">
                                <span class="text-gray-500 font-medium">Open</span>
                                <span class="font-bold text-yellow-500 text-lg">{{ openCount }}</span>
                            </div>
                            <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                                <div class="bg-yellow-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (openCount / store.tickets.length) * 100 : 0}%`"></div>
                            </div>
                        </div>
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between items-end">
                                <span class="text-gray-500 font-medium">In Progress</span>
                                <span class="font-bold text-blue-500 text-lg">{{ inProgressCount }}</span>
                            </div>
                            <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                                <div class="bg-blue-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (inProgressCount / store.tickets.length) * 100 : 0}%`"></div>
                            </div>
                        </div>
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between items-end">
                                <span class="text-gray-500 font-medium">Resolved</span>
                                <span class="font-bold text-green-500 text-lg">{{ resolvedCount }}</span>
                            </div>
                            <div class="w-full bg-gray-100 dark:bg-white/5 h-1.5 rounded-full overflow-hidden">
                                <div class="bg-green-500 h-full rounded-full" :style="`width: ${store.tickets.length ? (resolvedCount / store.tickets.length) * 100 : 0}%`"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- MAIN CONTENT -->
            <div class="flex-1 flex flex-col min-w-0 glass-panel rounded-xl overflow-hidden">

                <!-- Tabs -->
                <div class="flex border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 shrink-0">
                    <button @click="activeTab = 'tickets'"
                        class="flex items-center gap-2 px-5 py-3 text-sm font-bold transition-colors border-b-2 -mb-px"
                        :class="activeTab === 'tickets'
                            ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-transparent'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                        <span class="material-symbols-outlined text-[16px]">confirmation_number</span>
                        Support Tickets
                        <span class="ml-1 text-[10px] bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400 px-1.5 py-0.5 rounded-full font-bold">{{ store.tickets.length }}</span>
                    </button>
                    <button @click="switchToChat"
                        class="flex items-center gap-2 px-5 py-3 text-sm font-bold transition-colors border-b-2 -mb-px"
                        :class="activeTab === 'chat'
                            ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-transparent'
                            : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                        <span class="material-symbols-outlined text-[16px]">smart_toy</span>
                        AI Chat Support
                        <span v-if="unreadCount > 0"
                            class="ml-1 text-[10px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full font-bold animate-pulse">
                            {{ unreadCount }}
                        </span>
                    </button>
                </div>

                <!-- ── TICKETS TAB ── -->
                <div v-if="activeTab === 'tickets'" class="flex-1 flex flex-col overflow-hidden">
                    <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0">
                        <select v-model="statusFilter"
                            class="text-xs bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1 text-gray-700 dark:text-gray-300 focus:outline-none">
                            <option value="all" class="bg-white dark:bg-gray-800">All</option>
                            <option value="Open" class="bg-white dark:bg-gray-800">Open</option>
                            <option value="In Progress" class="bg-white dark:bg-gray-800">In Progress</option>
                            <option value="Resolved" class="bg-white dark:bg-gray-800">Resolved</option>
                        </select>
                        <button @click="openCreateModal"
                            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">add</span> Create Ticket
                        </button>
                    </div>

                    <div v-if="loadingTickets" class="flex-1 flex items-center justify-center text-gray-400 text-sm">
                        Loading tickets...
                    </div>
                    <div v-else class="flex-1 overflow-auto">
                        <table class="w-full text-left text-sm min-w-[600px]">
                            <thead class="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 uppercase text-[10px] sticky top-0">
                                <tr>
                                    <th class="px-4 py-3">Ticket</th>
                                    <th class="px-4 py-3">Subject</th>
                                    <th class="px-4 py-3">Created</th>
                                    <th class="px-4 py-3">Priority</th>
                                    <th class="px-4 py-3">Status</th>
                                    <th class="px-4 py-3 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                <tr v-if="filteredTickets.length === 0">
                                    <td colspan="6" class="px-4 py-8 text-center text-gray-400 text-sm">No tickets found</td>
                                </tr>
                                <tr v-for="t in filteredTickets" :key="t.id"
                                    class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                                    @click="openTicketDetail(t)">
                                    <td class="px-4 py-3 font-mono text-blue-500 text-xs font-bold">{{ t.id }}</td>
                                    <td class="px-4 py-3 text-gray-900 dark:text-white text-xs font-medium">{{ t.subject }}</td>
                                    <td class="px-4 py-3 text-gray-500 text-xs">{{ t.created }}</td>
                                    <td class="px-4 py-3">
                                        <span class="text-[10px] font-bold uppercase" :class="priorityClass(t.priority)">{{ t.priority }}</span>
                                    </td>
                                    <td class="px-4 py-3">
                                        <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="ticketStatusClass(t.status)">{{ t.status }}</span>
                                    </td>
                                    <td class="px-4 py-3 text-right" @click.stop>
                                        <button @click="openTicketDetail(t)"
                                            class="p-1 rounded hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="View Details">
                                              <span class="material-symbols-outlined text-[16px]">visibility</span>
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- ── AI CHAT TAB ── -->
                <div v-if="activeTab === 'chat'" class="flex-1 flex flex-col overflow-hidden">

                    <!-- Step 1: Shipment picker (shown until chat is started) -->
                    <div v-if="!chatStarted" class="flex-1 flex flex-col items-center justify-center gap-4 px-6 py-8 overflow-y-auto">
                        <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center shadow-lg">
                            <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
                        </div>
                        <div class="text-center">
                            <p class="font-bold text-gray-800 dark:text-white/80 text-sm">Start Support Chat</p>
                            <p class="text-gray-500 dark:text-white/40 text-xs mt-1 max-w-[260px]">
                                Select an active shipment for context, or start a general chat without one.
                            </p>
                        </div>
                        <div class="w-full max-w-sm space-y-2">
                            <div v-if="selectableShipments.length > 0">
                                <button
                                    v-for="s in selectableShipments"
                                    :key="s.backendId"
                                    @click="selectShipment(s)"
                                    class="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-blue-400/60 hover:bg-blue-50/50 dark:hover:bg-white/8 transition-all group text-left mb-2"
                                >
                                    <div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white font-mono">{{ s.id }}</div>
                                        <div class="text-[11px] text-gray-500 dark:text-white/40 mt-0.5">{{ s.origin }} → {{ s.destination }}</div>
                                    </div>
                                    <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                                        <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                                            :class="shipmentStatusBadge(s.statusKey)">{{ s.status }}</span>
                                        <span class="material-symbols-outlined text-gray-400 group-hover:text-blue-500 transition-colors text-[16px]">arrow_forward</span>
                                    </div>
                                </button>
                            </div>
                            <div v-else class="text-center text-xs text-gray-400 dark:text-white/30 py-3">
                                No active shipments found.
                            </div>
                            <!-- Chat without shipment -->
                            <div class="pt-2 border-t border-gray-200 dark:border-white/10">
                                <button
                                    @click="startWithoutShipment"
                                    class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-dashed border-gray-300 dark:border-white/15 bg-gray-50 dark:bg-white/5 hover:border-blue-400/60 hover:bg-blue-50/30 dark:hover:bg-white/8 transition-all text-sm text-gray-600 dark:text-gray-400 hover:text-blue-700 dark:hover:text-blue-400"
                                >
                                    <span class="material-symbols-outlined text-[18px]">chat</span>
                                    Chat without selecting a shipment
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Chat (shown once chat is started) -->
                    <template v-else-if="chatStarted">
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
                </div>
            </div>
        </div>

        <!-- FAQ -->
        <div class="glass-panel p-5 rounded-xl w-full shrink-0">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-blue-500">help</span> Frequently Asked Questions
            </h3>
            <div class="flex flex-col gap-3">
                <div v-for="(faq, idx) in faqList" :key="idx"
                    class="bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 overflow-hidden">
                    <button @click="toggleFaq(idx)"
                        class="w-full p-4 flex justify-between items-center text-left hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <span class="text-sm font-bold text-gray-800 dark:text-gray-200">{{ faq.q }}</span>
                        <span class="material-symbols-outlined text-gray-400 transition-transform duration-300"
                            :class="{ 'rotate-180': openFaq === idx }">expand_more</span>
                    </button>
                    <div v-show="openFaq === idx"
                        class="p-4 pt-0 text-xs text-gray-600 dark:text-gray-400 border-t border-gray-100 dark:border-white/5 mt-2 leading-relaxed">
                        {{ faq.a }}
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Ticket Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showCreateModal" @close="showCreateModal = false">
                <template #title>Create Support Ticket</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Subject *</label>
                        <input v-model="newTicket.subject" type="text" placeholder="Brief description of issue"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Priority</label>
                        <div class="flex gap-2">
                            <label v-for="p in ['Low', 'Medium', 'High']" :key="p"
                                class="flex-1 text-center px-3 py-2 rounded-lg border cursor-pointer text-xs font-bold transition-colors"
                                :class="newTicket.priority === p ? priorityBorderClass(p) : 'border-gray-200 dark:border-white/10 text-gray-500'">
                                <input type="radio" :value="p" v-model="newTicket.priority" class="sr-only">{{ p }}
                            </label>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Related Shipment (optional)</label>
                        <select v-model="newTicket.shipmentId"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            <option value="" class="bg-white dark:bg-gray-800">None</option>
                            <option v-for="s in store.shipments" :key="s.id" :value="s.backendId" class="bg-white dark:bg-gray-800">
                                {{ s.id }} — {{ s.origin }} → {{ s.destination }}
                            </option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description *</label>
                        <textarea v-model="newTicket.message" rows="4" placeholder="Provide details about your issue..."
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                </div>
                <template #footer>
                    <button @click="showCreateModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitTicket" :disabled="!newTicket.subject || !newTicket.message"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">
                        Submit Ticket
                    </button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Ticket Detail Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="!!detailTicket" @close="detailTicket = null">
                <template #title>{{ detailTicket?.id }} — {{ detailTicket?.subject }}</template>
                <div v-if="detailTicket" class="space-y-4">
                    <div class="flex gap-3 text-xs">
                        <span class="px-2 py-0.5 rounded font-bold" :class="ticketStatusClass(detailTicket.status)">{{ detailTicket.status }}</span>
                        <span class="font-bold uppercase" :class="priorityClass(detailTicket.priority)">{{ detailTicket.priority }}</span>
                        <span class="text-gray-400">{{ detailTicket.created }}</span>
                    </div>
                    <div class="space-y-3 max-h-64 overflow-y-auto pr-1">
                        <div v-for="(msg, idx) in detailTicket.replies" :key="idx"
                            class="p-3 rounded-lg text-xs"
                            :class="msg.from === 'You' ? 'bg-blue-500/10 ml-6' : 'bg-gray-100 dark:bg-white/5 mr-6'">
                            <div class="flex justify-between mb-1">
                                <span class="font-bold text-gray-900 dark:text-white">{{ msg.from }}</span>
                                <span class="text-gray-400 text-[10px]">{{ msg.time }}</span>
                            </div>
                            <p class="text-gray-600 dark:text-gray-300">{{ msg.message }}</p>
                        </div>
                    </div>
                    <div v-if="detailTicket.status !== 'Resolved'" class="flex gap-2">
                        <input v-model="replyText" type="text" placeholder="Type a reply..."
                            class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500"
                            @keyup.enter="sendReply">
                        <button @click="sendReply" :disabled="!replyText.trim()"
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">Send</button>
                    </div>
                </div>
                <template #footer>
                    <button @click="detailTicket = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    <button v-if="detailTicket?.status !== 'Resolved'"
                        @click="markResolved(detailTicket); detailTicket = null"
                        class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-bold hover:bg-green-700 transition-colors">
                        Mark Resolved
                    </button>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import BaseModal from '@/components/BaseModal.vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { sendChat, fetchConversation } from '@/utils/aiApi'

ChartJS.register(ArcElement, Tooltip, Legend)

const store = useVendorStore()
const SESSION_KEY = 'support_session_vendor'

// ── Tabs ──────────────────────────────────────────────────────────────────────
const activeTab = ref('tickets')

// ── Tickets ───────────────────────────────────────────────────────────────────
const statusFilter = ref('all')
const showCreateModal = ref(false)
const detailTicket = ref(null)
const replyText = ref('')
const openFaq = ref(null)
const loadingTickets = ref(false)

const faqList = [
    { q: 'How to bulk upload shipments?', a: 'Navigate to the "Bulk Upload" page. Download our CSV template, fill it out with your shipment details, and upload it back. The grid will auto-populate for review before final submission.' },
    { q: 'Where do I find my invoice & billing cycles?', a: 'Invoices are generated bi-weekly. You can access them under the Invoices section in your portal or request priority copies via Support.' },
    { q: 'Is there an API Integration guide available?', a: 'Yes. Enterprise partners have access to our RESTful API. Please contact priority support to receive your API keys and the latest swagger documentation link.' },
    { q: 'What is the damage claim process?', a: 'Open the specific shipment from your Tracking dashboard and use the "Report Issue" action button. Attach photos for faster resolution.' },
    { q: 'Can I set up recurring scheduled shipments?', a: 'Absolutely. Go to "Recurring Orders" to template a route and define a frequency schedule (e.g., Every Monday at 9AM).' },
]

const newTicket = ref({ subject: '', priority: 'Medium', shipmentId: '', message: '' })

const filteredTickets = computed(() => {
    if (statusFilter.value === 'all') return store.tickets
    return store.tickets.filter(t => t.status === statusFilter.value)
})

const openCount = computed(() => store.tickets.filter(t => t.status === 'Open').length)
const inProgressCount = computed(() => store.tickets.filter(t => t.status === 'In Progress').length)
const resolvedCount = computed(() => store.tickets.filter(t => t.status === 'Resolved').length)

const chartData = computed(() => ({
    labels: ['Open', 'In Progress', 'Resolved'],
    datasets: [{
        data: [openCount.value, inProgressCount.value, resolvedCount.value],
        backgroundColor: ['#EAB308', '#3B82F6', '#22C55E'],
        borderWidth: 0,
        hoverOffset: 4,
    }],
}))

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 12,
            titleFont: { size: 13, family: "'Inter', sans-serif" },
            bodyFont: { size: 12, family: "'Inter', sans-serif" },
            boxPadding: 6,
        },
    },
}

const toggleFaq = (idx) => { openFaq.value = openFaq.value === idx ? null : idx }

function priorityClass(p) {
    return { High: 'text-red-500', Medium: 'text-yellow-500', Low: 'text-green-500' }[p] || 'text-gray-500'
}

function priorityBorderClass(p) {
    return {
        High: 'border-red-500 bg-red-500/10 text-red-500',
        Medium: 'border-yellow-500 bg-yellow-500/10 text-yellow-500',
        Low: 'border-green-500 bg-green-500/10 text-green-500',
    }[p]
}

function ticketStatusClass(s) {
    return {
        Open: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
        'In Progress': 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
        Resolved: 'bg-green-500/20 text-green-600 dark:text-green-400',
    }[s] || 'bg-gray-500/20 text-gray-500'
}

function openCreateModal() {
    newTicket.value = { subject: '', priority: 'Medium', shipmentId: '', message: '' }
    showCreateModal.value = true
}

async function submitTicket() {
    if (!newTicket.value.subject || !newTicket.value.message) return
    await store.addTicket({
        subject: newTicket.value.subject,
        priority: newTicket.value.priority,
        shipmentId: newTicket.value.shipmentId || null,
        message: newTicket.value.message,
    })
    showCreateModal.value = false
    showToast('Ticket created successfully')
}

function openTicketDetail(t) {
    detailTicket.value = t
    replyText.value = ''
}

async function sendReply() {
    if (!replyText.value.trim() || !detailTicket.value) return
    const ticketId = detailTicket.value.id
    await store.replyTicket(ticketId, replyText.value.trim())
    replyText.value = ''
    const updated = store.tickets.find(t => t.id === ticketId)
    if (updated) detailTicket.value = updated
}

async function markResolved(t) {
    await store.resolveTicket(t.id)
    showToast(`Ticket ${t.id} resolved`)
}

function showToast(msg) {
    const el = document.createElement('div')
    el.className = 'fixed right-4 bottom-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    el.textContent = msg
    document.body.appendChild(el)
    setTimeout(() => el.remove(), 3000)
}

// ── AI Chat ───────────────────────────────────────────────────────────────────
const chatMessages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const chatContainer = ref(null)
const sessionId = ref(null)
const unreadCount = ref(0)
const humanHandoffLocked = ref(false)
const selectedShipment = ref(null)
const chatStarted = ref(false)
let lastLoadedAt = null
let pollTimer = null

// Shipments eligible for support chat (not delivered / cancelled)
const selectableShipments = computed(() =>
    store.shipments.filter(s => !['delivered', 'cancelled'].includes(s.statusKey))
)

function shipmentStatusBadge(statusKey) {
    return {
        pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300',
        warehouse: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300',
        transit: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
        delivery: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300',
    }[statusKey] || 'bg-gray-100 text-gray-600 dark:bg-white/10 dark:text-gray-300'
}

function saveSession() {
    if (chatStarted.value) {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({
            shipmentId: selectedShipment.value?.backendId ?? null,
            sessionId: sessionId.value,
        }))
    }
}

async function restoreSession() {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return false
    try {
        const saved = JSON.parse(raw)
        if (saved === null || typeof saved !== 'object') return false

        if (saved.shipmentId) {
            if (!store.shipments.length) {
                try { await store.fetchShipments() } catch { /* ignore */ }
            }
            const shipment = store.shipments.find(s => s.backendId === saved.shipmentId)
            if (!shipment) { sessionStorage.removeItem(SESSION_KEY); return false }
            selectedShipment.value = shipment
        } else {
            selectedShipment.value = null
        }

        chatStarted.value = true

        if (!saved.sessionId) return true

        sessionId.value = saved.sessionId
        try {
            const data = await fetchConversation(saved.sessionId)
            const hist = Array.isArray(data?.messages) ? data.messages : []
            if (hist.length > 0) {
                chatMessages.value = hist.map((m, i) => mapServerMsg(m, i))
                lastLoadedAt = hist[hist.length - 1].created_at
            }
            if (data?.human_handoff_locked || hist.some(m => m.intent === 'support_session_closed')) {
                humanHandoffLocked.value = true
            }
            startPolling()
        } catch { /* ignore — start fresh */ }
        await scrollToBottom()
        return true
    } catch {
        sessionStorage.removeItem(SESSION_KEY)
        return false
    }
}

function selectShipment(shipment) {
    selectedShipment.value = shipment
    chatStarted.value = true
    sessionId.value = null
    chatMessages.value = []
    humanHandoffLocked.value = false
    lastLoadedAt = null
    saveSession()
}

function startWithoutShipment() {
    selectedShipment.value = null
    chatStarted.value = true
    sessionId.value = null
    chatMessages.value = []
    humanHandoffLocked.value = false
    lastLoadedAt = null
    saveSession()
}

const quickChips = [
    'Show my pending shipments',
    'Do I have overdue invoices?',
    'What is my wallet balance?',
    'Talk to a human agent',
]

const SUPPORT_PREFIX_RE = /^\[Support — ([^\]]+)\]\s*/

function formatText(raw) {
    return String(raw)
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n/g, '<br>')
}

function nowTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function mapServerMsg(m, idx) {
    // Manager-closed session message
    if (m.intent === 'support_session_closed') {
        humanHandoffLocked.value = true
        return {
            id: `h-${m.created_at}-${idx}`,
            role: 'closed',
            text: formatText(m.message || 'Human support session has been closed.'),
            time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            createdAt: m.created_at,
        }
    }
    // agent_reply / support_message = actual human agent replied → orange Human Support bubble
    // handover = bot escalation notice → regular AI bubble
    if (['support_message', 'agent_reply'].includes(m.intent)) {
        return {
            id: `h-${m.created_at}-${idx}`,
            role: 'support',
            intent: m.intent,
            text: formatText((m.message || '').replace(SUPPORT_PREFIX_RE, '')),
            time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            createdAt: m.created_at,
        }
    }
    return {
        id: `h-${m.created_at}-${idx}`,
        role: m.role === 'user' ? 'user' : 'ai',
        intent: m.intent || null,
        text: formatText(m.message || ''),
        time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        createdAt: m.created_at,
    }
}

const scrollToBottom = async () => {
    await nextTick()
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

async function pollHistory() {
    if (!sessionId.value || isTyping.value) return
    try {
        const { messages: hist } = await fetchConversation(sessionId.value)
        if (!hist?.length) return
        const newHist = lastLoadedAt ? hist.filter(m => m.created_at > lastLoadedAt) : []
        if (!newHist.length) return
        const offset = hist.length - newHist.length
        const newMsgs = newHist.map((m, i) => mapServerMsg(m, offset + i))
        chatMessages.value.push(...newMsgs)
        lastLoadedAt = hist[hist.length - 1].created_at
        const supportCount = newMsgs.filter(m => m.role === 'support').length
        if (activeTab.value !== 'chat' && supportCount > 0) unreadCount.value += supportCount
        if (activeTab.value === 'chat') await scrollToBottom()
    } catch { /* ignore transient poll errors */ }
}

function startPolling() {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = setInterval(pollHistory, 8_000)
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

function switchToChat() {
    activeTab.value = 'chat'
    unreadCount.value = 0
}

async function handleSend() {
    const text = userInput.value.trim()
    if (!text || isTyping.value) return
    userInput.value = ''
    chatMessages.value.push({ id: `u-${Date.now()}`, role: 'user', text, time: nowTime() })
    isTyping.value = true
    await scrollToBottom()
    try {
        const res = await sendChat(text, sessionId.value, {
            context: 'support_chat',
            ...(selectedShipment.value ? { orderId: selectedShipment.value.backendId } : {}),
        })
        if (res.session_id) {
            sessionId.value = res.session_id
            saveSession()
            if (!lastLoadedAt) {
                lastLoadedAt = new Date().toISOString()
                startPolling()
            } else {
                lastLoadedAt = new Date().toISOString()
            }
        }

        if (res.human_handoff_locked) humanHandoffLocked.value = true

        if (res.intent === 'support_session_closed') {
            humanHandoffLocked.value = true
            chatMessages.value.push({
                id: `closed-${Date.now()}`,
                role: 'closed',
                text: formatText(res.message || 'Human support session has been closed.'),
                time: nowTime(),
            })
        } else if (res.intent === 'agent_waiting') {
            // Human agent has taken over — show a quiet status pill, not an AI bubble
            chatMessages.value.push({
                id: `status-${Date.now()}`,
                role: 'status',
                text: res.message || 'Your message has been sent to the support agent.',
                time: nowTime(),
            })
        } else {
            // handover = bot escalation notice → regular AI bubble
            // agent_reply / support_message = actual human agent → orange Human Support bubble
            const msgText = res.message || "I'm here to help!"
            chatMessages.value.push({
                id: `ai-${Date.now()}`,
                role: ['agent_reply', 'support_message'].includes(res.intent) ? 'support' : 'ai',
                intent: res.intent || null,
                text: formatText(msgText),
                time: nowTime(),
            })
        }
    } catch (err) {
        chatMessages.value.push({
            id: `err-${Date.now()}`,
            role: 'ai',
            text: `<span class="text-red-400">⚠ ${err.message || 'Something went wrong. Please try again.'}</span>`,
            time: nowTime(),
        })
    } finally {
        isTyping.value = false
        await scrollToBottom()
    }
}

function sendChip(chip) {
    userInput.value = chip
    handleSend()
}

function startNewChat() {
    stopPolling()
    sessionStorage.removeItem(SESSION_KEY)
    chatMessages.value = []
    sessionId.value = null
    lastLoadedAt = null
    unreadCount.value = 0
    humanHandoffLocked.value = false
    selectedShipment.value = null
    chatStarted.value = false
}

onMounted(async () => {
    loadingTickets.value = true
    try { await store.fetchTickets() } catch { /* ignore */ } finally { loadingTickets.value = false }
    // Restore any previous chat session (survives page refresh via sessionStorage)
    await restoreSession()
    // If no saved session, still pre-load shipments for the picker
    if (!store.shipments.length) {
        try { await store.fetchShipments() } catch { /* ignore */ }
    }
})

onUnmounted(() => {
    stopPolling()
    // sessionStorage is intentionally kept so refresh restores the session.
    // User must click the "+" / new-chat button to fully reset.
})
</script>
