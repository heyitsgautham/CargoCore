<template>
    <Transition enter-active-class="transition-all duration-300" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition-all duration-200"
        leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="selected"
            class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-end"
            @click.self="selected = null">
            <div class="w-full max-w-2xl h-full bg-white dark:bg-gray-900 shadow-2xl overflow-y-auto flex flex-col">

                <!-- Drawer Header -->
                <div class="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-white/10 px-6 py-4 flex items-center justify-between z-10">
                    <div>
                        <span class="text-xs font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10 px-2 py-0.5 rounded">{{ selected.reference_code }}</span>
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white mt-1 truncate max-w-[24rem]">{{ selected.description }}</h3>
                    </div>
                    <button @click="selected = null"
                        class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Drawer Body: two-column layout -->
                <div class="flex-1 p-6 flex gap-6">

                    <!-- Left: main content -->
                    <div class="flex-1 space-y-6 min-w-0">

                        <!-- Badges -->
                        <div class="flex flex-wrap gap-2">
                            <span class="text-xs font-bold px-2.5 py-1 rounded-full" :class="statusStyle(selected.status)">{{ selected.status }}</span>
                            <span class="text-xs font-medium px-2.5 py-1 rounded-full" :class="flowStyle(selected.flow_type)">{{ flowLabel(selected.flow_type) }}</span>
                            <span v-if="selected.sentiment" class="text-xs font-medium px-2.5 py-1 rounded-full" :class="sentimentStyle(selected.sentiment)">{{ selected.sentiment }}</span>
                        </div>

                        <!-- Info Grid -->
                        <div class="grid grid-cols-2 gap-3">
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Customer</div>
                                <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ selected.customer_name }}</div>
                                <div class="text-xs text-gray-500">{{ selected.customer_email }}</div>
                            </div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Order</div>
                                <div class="text-sm font-semibold text-gray-900 dark:text-white font-mono">{{ selected.order_tracking_code || '—' }}</div>
                            </div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">Filed</div>
                                <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatFull(selected.created_at) }}</div>
                            </div>
                            <div v-if="selected.session_id" class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                <div class="text-[10px] text-gray-500 uppercase font-bold mb-1">AI Session</div>
                                <a class="text-xs text-purple-500 hover:underline truncate block" href="#">View Conversation</a>
                            </div>
                        </div>

                        <!-- Description -->
                        <div>
                            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Description</div>
                            <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ selected.description }}</div>
                        </div>

                        <!-- Photos -->
                        <div v-if="selected.photos && selected.photos.length > 0">
                            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Customer Photos</div>
                            <div class="grid grid-cols-3 gap-2">
                                <div v-for="(photo, idx) in selected.photos" :key="idx"
                                    class="aspect-square bg-gray-100 dark:bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-purple-500 transition-all"
                                    @click="zoomPhoto(photo)">
                                    <img :src="photo" class="w-full h-full object-cover" :alt="'Photo ' + (idx + 1)" loading="lazy" />
                                </div>
                            </div>
                        </div>
                        <div v-else-if="selected.photos !== undefined">
                            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Customer Photos</div>
                            <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-xs text-gray-400 text-center">No photos submitted</div>
                        </div>

                        <!-- Internal Notes -->
                        <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Internal Support Notes</div>
                            <textarea v-model="notesValue" rows="3" placeholder="Add internal notes (visible to WM and LM)..."
                                class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                            <button @click="saveNotes"
                                :disabled="savingNotes"
                                class="mt-2 px-4 py-2 bg-gray-800 dark:bg-white/10 hover:bg-gray-900 dark:hover:bg-white/20 text-white font-bold rounded-lg text-xs transition-colors disabled:opacity-50">
                                {{ savingNotes ? 'Saving…' : 'Save Notes' }}
                            </button>
                        </div>

                        <!-- Customer Communication Panel -->
                        <div class="border-t border-gray-100 dark:border-white/10 pt-5">
                            <div class="text-xs font-bold text-gray-500 uppercase mb-2">Message to Customer</div>
                            <!-- Sent message thread -->
                            <div v-if="selected.support_messages && selected.support_messages.length > 0"
                                class="mb-3 space-y-2 max-h-40 overflow-y-auto">
                                <div v-for="(msg, idx) in selected.support_messages" :key="idx"
                                    class="p-2.5 bg-purple-50 dark:bg-purple-500/10 rounded-lg border border-purple-100 dark:border-purple-500/20">
                                    <div class="text-xs font-semibold text-purple-700 dark:text-purple-400 mb-0.5">{{ msg.sent_by }}</div>
                                    <div class="text-sm text-gray-800 dark:text-gray-200">{{ msg.text }}</div>
                                    <div class="text-[10px] text-gray-400 mt-1">{{ formatFull(msg.sent_at) }}</div>
                                </div>
                            </div>
                            <textarea v-model="customerMessage" rows="2" placeholder="Type a message to send to the customer..."
                                class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                            <div v-if="sendMessageError" class="mt-1 text-xs text-red-600 dark:text-red-400">{{ sendMessageError }}</div>
                            <button @click="sendCustomerMessage"
                                :disabled="sendingMessage || !customerMessage.trim()"
                                class="mt-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold rounded-lg text-xs transition-colors flex items-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">send</span>
                                {{ sendingMessage ? 'Sending...' : 'Send' }}
                            </button>
                        </div>
                    </div>

                    <!-- Right: Customer History Sidebar -->
                    <div class="w-44 flex-shrink-0 space-y-3">
                        <div class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer History</div>
                        <div v-if="loadingHistory" class="text-xs text-gray-400">Loading…</div>
                        <template v-else-if="customerHistory">
                            <div v-for="item in customerHistoryCards" :key="item.label"
                                class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 text-center">
                                <div class="text-xl font-black" :class="item.color">{{ item.value }}</div>
                                <div class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 leading-tight">{{ item.label }}</div>
                            </div>
                            <div v-if="customerHistory.last_sentiment"
                                class="p-3 rounded-xl border text-center text-xs font-bold"
                                :class="sentimentStyle(customerHistory.last_sentiment)">
                                {{ customerHistory.last_sentiment }}
                            </div>
                        </template>
                        <div v-else class="text-xs text-gray-400">N/A</div>
                    </div>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    customerHistory,
    customerHistoryCards,
    customerMessage,
    flowLabel,
    flowStyle,
    formatFull,
    loadingHistory,
    notesValue,
    saveNotes,
    savingNotes,
    selected,
    sendCustomerMessage,
    sendMessageError,
    sendingMessage,
    sentimentStyle,
    statusStyle,
    zoomPhoto,
} = inject(reverseLogisticsPageKey)
</script>
