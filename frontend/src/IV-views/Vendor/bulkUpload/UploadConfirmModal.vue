<template>
    <BaseModal :isOpen="showConfirmModal" @close="cancelConfirmation">
        <template #title>Confirm Upload</template>
        <div class="space-y-5">
            <!-- File Summary -->
            <div
                class="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-4">
                <div class="flex items-center gap-3 mb-3">
                    <div class="p-2 bg-green-500/20 rounded-lg text-green-500">
                        <span class="material-symbols-outlined">description</span>
                    </div>
                    <div class="flex-1">
                        <div class="font-bold text-gray-900 dark:text-white text-sm">{{ pendingUpload.filename }}</div>
                        <div class="text-[10px] text-gray-500">{{ pendingUpload.fileSize }} KB • {{
                            pendingUpload.detectedRows }} shipments detected</div>
                    </div>
                    <span class="material-symbols-outlined text-green-500">verified</span>
                </div>
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div class="p-2 bg-white/50 dark:bg-black/20 rounded-lg">
                        <div class="text-lg font-bold text-gray-900 dark:text-white">{{ pendingUpload.detectedRows }}</div>
                        <div class="text-[10px] text-gray-500">Detected</div>
                    </div>
                    <div class="p-2 bg-white/50 dark:bg-black/20 rounded-lg">
                        <div class="text-lg font-bold text-green-500">{{ pendingUpload.validRows }}</div>
                        <div class="text-[10px] text-gray-500">Valid</div>
                    </div>
                    <div class="p-2 bg-white/50 dark:bg-black/20 rounded-lg">
                        <div class="text-lg font-bold"
                            :class="pendingUpload.warningRows > 0 ? 'text-yellow-500' : 'text-gray-400'">{{
                            pendingUpload.warningRows }}</div>
                        <div class="text-[10px] text-gray-500">Warnings</div>
                    </div>
                </div>
            </div>

            <!-- Live Quotation -->
            <div class="glass-panel rounded-xl p-4 border border-gray-200 dark:border-white/10">
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-blue-500 text-[18px]">calculate</span>
                    <h4 class="font-bold text-gray-900 dark:text-white text-sm">Live Quotation</h4>
                </div>
                <div class="space-y-2 mb-3">
                    <div class="flex justify-between text-xs">
                        <span class="text-gray-500">Base Transport ({{ pendingUpload.detectedRows }}
                            shipments)</span>
                        <span class="text-gray-900 dark:text-white font-medium">₹{{
                            uploadQuote.baseTransport.toLocaleString() }}</span>
                    </div>
                    <div class="flex justify-between text-xs">
                        <span class="text-gray-500">Handling & Packing</span>
                        <span class="text-gray-900 dark:text-white font-medium">₹{{
                            uploadQuote.handling.toLocaleString() }}</span>
                    </div>
                    <div class="flex justify-between text-xs">
                        <span class="text-gray-500">Insurance (estimated)</span>
                        <span class="text-gray-900 dark:text-white font-medium">₹{{
                            uploadQuote.insurance.toLocaleString() }}</span>
                    </div>
                    <div class="flex justify-between text-xs">
                        <span class="text-gray-500">GST (18%)</span>
                        <span class="text-gray-900 dark:text-white font-medium">₹{{
                            uploadQuote.gst.toLocaleString() }}</span>
                    </div>
                    <div class="border-t border-gray-200 dark:border-white/10 pt-2 flex justify-between">
                        <span class="text-sm font-bold text-gray-700 dark:text-gray-200">Total Estimate</span>
                        <span class="text-lg font-bold text-blue-500">₹{{ uploadQuote.total.toLocaleString() }}</span>
                    </div>
                </div>
                <div class="flex items-center gap-2 text-[10px] text-gray-400">
                    <span class="material-symbols-outlined text-[12px]">info</span>
                    Final amount may vary based on actual weight, distance, and service options.
                </div>
            </div>

            <!-- Confirmation Prompt -->
            <div class="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 flex items-start gap-2">
                <span class="material-symbols-outlined text-yellow-500 text-[18px] mt-0.5">help</span>
                <div>
                    <div class="text-sm font-bold text-gray-900 dark:text-white">Are you sure this file is
                        correct?</div>
                    <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">Review the summary above. Once
                        confirmed, shipments will be created and assigned to drivers.</p>
                </div>
            </div>

            <!-- Schedule Picker (conditionally shown) -->
            <div v-if="showSchedulePicker" class="space-y-2">
                <label class="block text-xs text-gray-500 dark:text-gray-400 font-bold">Schedule for Later</label>
                <div class="flex gap-3">
                    <input v-model="scheduleDate" type="date"
                        class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <input v-model="scheduleTime" type="time"
                        class="w-32 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
                <div class="flex justify-end gap-2 mt-2">
                    <button @click="showSchedulePicker = false"
                        class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">Cancel</button>
                    <button @click="confirmScheduleLater" :disabled="saving"
                        class="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                        {{ saving ? 'Scheduling...' : 'Confirm Schedule' }}
                    </button>
                </div>
            </div>
        </div>
        <template #footer>
            <div class="flex flex-wrap gap-2 w-full justify-center">
                <button @click="cancelConfirmation" :disabled="saving"
                    class="px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5
                    text-gray-600 bg-gray-100 border border-gray-200 hover:text-gray-800 hover:bg-gray-200
                    dark:text-gray-300 dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10 dark:hover:text-white
                    disabled:opacity-50 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[14px]">refresh</span> Modify / Re-upload
                </button>
                <button @click="showSchedulePicker = true" :disabled="saving"
                    class="px-4 py-2.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-lg text-sm font-bold hover:bg-purple-500/20 transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[14px]">schedule</span> Schedule Later
                </button>
                <button @click="confirmCreateNow" :disabled="saving"
                    class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5 disabled:opacity-60 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[14px]" :class="saving ? 'animate-spin' : ''">
                        {{ saving ? 'progress_activity' : 'rocket_launch' }}
                    </span>
                    {{ saving ? 'Creating...' : 'Create Shipments Now' }}
                </button>
            </div>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { bulkUploadPageKey } from './bulkUploadPageContext'

const {
    cancelConfirmation,
    confirmCreateNow,
    confirmScheduleLater,
    pendingUpload,
    saving,
    scheduleDate,
    scheduleTime,
    showConfirmModal,
    showSchedulePicker,
    uploadQuote,
} = inject(bulkUploadPageKey)
</script>
