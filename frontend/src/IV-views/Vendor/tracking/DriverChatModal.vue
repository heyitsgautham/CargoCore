<template>
    <!-- Driver Chat Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showChatModal" @close="showChatModal = false">
            <template #title>
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500">
                       <span class="material-symbols-outlined text-xs">person</span>
                    </div>
                    Chat with {{ selected?.driver?.split(' ')[0] || 'Driver' }}
                </div>
            </template>

            <div class="flex flex-col h-[400px] -mx-6 -mt-4 -mb-6 bg-gray-50 dark:bg-black/20">
                <!-- Chat Messages Area -->
                <div class="flex-1 overflow-y-auto p-4 space-y-4">
                    <!-- System Message -->
                    <div class="flex justify-center">
                        <span class="text-[10px] font-bold text-gray-400 bg-gray-200 dark:bg-white/5 px-3 py-1 rounded-full">
                            Shipment {{ selected?.id }} Dispatch Chat Start
                        </span>
                    </div>

                    <!-- Mock Driver Message -->
                    <div class="flex items-end gap-2">
                        <div class="w-8 h-8 rounded-full bg-blue-500/20 flex-shrink-0 flex items-center justify-center text-blue-500">
                            <span class="material-symbols-outlined text-sm">person</span>
                        </div>
                        <div class="bg-white dark:bg-card-dark border border-gray-100 dark:border-white/5 rounded-2xl rounded-bl-sm p-3 max-w-[80%] shadow-sm">
                            <p class="text-sm text-gray-800 dark:text-gray-200">Hi, I have picked up the shipment and am en route. Traffic is light so I should arrive close to the ETA.</p>
                            <div class="text-[9px] text-gray-400 mt-1 text-right">10:45 AM</div>
                        </div>
                    </div>

                    <!-- User Messages -->
                    <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex justify-end items-end gap-2">
                        <div class="bg-blue-600 rounded-2xl rounded-br-sm p-3 max-w-[80%] shadow-sm text-white">
                            <p class="text-sm">{{ msg.text }}</p>
                            <div class="text-[9px] text-blue-200 mt-1 flex justify-end items-center gap-1">
                                {{ msg.time }}
                                <span class="material-symbols-outlined text-[10px]">done_all</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Input Area -->
                <div class="p-3 bg-white dark:bg-card-dark border-t border-gray-200 dark:border-white/10">
                    <form @submit.prevent="sendChatMessage" class="flex items-center gap-2 relative">
                        <input type="file" ref="fileInput" class="hidden" @change="handleFileUpload" accept="image/*,.pdf,.doc,.docx" />
                        <button type="button" @click="$refs.fileInput.click()" class="p-2 text-gray-400 hover:text-blue-500 transition-colors tooltip-trigger relative group">
                            <span class="material-symbols-outlined text-[20px]">attach_file</span>
                            <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-30 font-bold pointer-events-none">Attach File</div>
                        </button>
                        <input v-model="newChatMessage" type="text" placeholder="Type your message..." 
                            class="flex-1 bg-gray-100 dark:bg-black/20 border border-transparent rounded-full px-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:bg-white dark:focus:bg-card-dark focus:border-blue-500 transition-all">
                        <button type="submit" :disabled="!newChatMessage.trim()"
                            class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                            <span class="material-symbols-outlined text-[18px]">send</span>
                        </button>
                    </form>
                </div>
            </div>

            <template #footer>
                <!-- Replacing default footer to ensure clean edge with the chat input box -->
                <span class="hidden"></span>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    chatMessages,
    handleFileUpload,
    newChatMessage,
    selected,
    sendChatMessage,
    showChatModal,
} = inject(vendorTrackingPageKey)
</script>
