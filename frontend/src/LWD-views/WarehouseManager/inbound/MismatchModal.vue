<template>
    <!-- Mismatch Modal -->
    <Teleport to="body">
        <div v-if="showMismatchModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showMismatchModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Flag ASN Mismatch</h3>
                    <button @click="showMismatchModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">ASN ID</label>
                        <select v-model="mismatchForm.asnId"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option v-for="asn in asns" :key="asn.id" :value="asn.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ asn.id }} — {{
                                asn.supplier }}
                            </option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Mismatch Type</label>
                        <select v-model="mismatchForm.type"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Quantity difference</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Wrong SKU received</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Missing items</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Extra items</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Details</label>
                        <textarea v-model="mismatchForm.details" placeholder="Describe the mismatch..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm h-20 resize-none"></textarea>
                    </div>
                    <button @click="submitMismatch" :disabled="!mismatchForm.asnId"
                        class="w-full bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 font-bold py-3 rounded-lg transition-colors">
                        Submit Mismatch Report
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { asns, mismatchForm, showMismatchModal, submitMismatch } = inject(inboundPageKey)
</script>
