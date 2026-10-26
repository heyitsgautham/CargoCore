<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { communicationPageKey } from './communicationPageContext'

const { activeChat, chatDisplayName, confirmDeleteChat, isDeleteModalOpen } = inject(communicationPageKey)
</script>
