<template>
    <!-- ===== PHYSICAL INSPECTION TAB (Flow 2: pickup_inspection) ===== -->
    <div v-if="activeTab === 'processing'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Grading Station -->
        <div class="lg:col-span-2 glass-panel p-6 rounded-xl">
            <div class="flex justify-between items-center mb-6">
                <h3 class="font-bold text-gray-900 dark:text-white">Item Grading Station</h3>
                <span class="px-2 py-1 bg-green-500/20 text-green-600 dark:text-green-400 text-xs rounded border border-green-500/30 animate-pulse">Active</span>
            </div>

            <div class="flex gap-6">
                <!-- Damage Photo -->
                <div class="w-1/3 space-y-3">
                    <div @click="openScanner('camera')"
                        class="aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center border border-gray-100 dark:border-white/5 relative overflow-hidden group cursor-pointer hover:border-primary/50 transition-colors">
                        <div v-if="!capturedPhoto" class="flex flex-col items-center gap-2">
                            <span class="material-symbols-outlined text-5xl text-gray-600 group-hover:scale-110 transition-transform">photo_camera</span>
                            <div class="text-xs text-gray-500">Click to capture<br>damage photo</div>
                        </div>
                        <div v-else class="w-full h-full bg-gradient-to-br from-red-900/30 to-transparent flex items-center justify-center">
                            <span class="material-symbols-outlined text-4xl text-green-600 dark:text-green-400">check_circle</span>
                        </div>
                    </div>
                    <button @click="openScanner('camera')"
                        class="w-full py-2 text-xs font-bold rounded transition-colors"
                        :class="capturedPhoto ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400' : 'bg-primary/20 hover:bg-primary/30 text-primary'">
                        {{ capturedPhoto ? 'Retake Photo' : 'Capture Damage Photo' }}
                    </button>
                </div>

                <div class="flex-1 space-y-4">
                    <div class="relative">
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">RMA ID / Tracking #</label>
                        <input type="text" v-model="rmaId" placeholder="Scan barcode or select from queue..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 pr-10 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 font-mono">
                        <button @click="openScanner('scan')" class="absolute right-2 top-8 text-gray-500 dark:text-gray-400 hover:text-primary">
                            <span class="material-symbols-outlined">qr_code_scanner</span>
                        </button>
                    </div>

                    <!-- Order lookup result -->
                    <div v-if="selectedOrderForReturn" class="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                        <div class="text-xs text-primary font-bold mb-1">Order Found</div>
                        <div class="text-sm text-gray-900 dark:text-white font-bold">{{ selectedOrderForReturn.tracking_code }}</div>
                        <div class="text-xs text-gray-500">Type: {{ selectedOrderForReturn.order_type }} • Status: {{ selectedOrderForReturn.status }}</div>
                    </div>

                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Item Condition</label>
                        <select v-model="itemCondition"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Select condition...</option>
                            <option value="Like New" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Like New — No visible damage</option>
                            <option value="Minor Wear" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Minor Wear — Cosmetic only</option>
                            <option value="Damaged" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Damaged — Functional issue</option>
                            <option value="Broken" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Broken — Non-functional</option>
                        </select>
                    </div>

                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Condition Notes</label>
                        <textarea v-model="conditionNotes" placeholder="Describe the condition in detail..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm h-16 resize-none"></textarea>
                    </div>

                    <!-- Disposition Workflow -->
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Disposition Decision</label>
                        <div class="grid grid-cols-2 gap-3">
                            <button @click="disposition = 'restock'"
                                class="p-3 rounded-lg font-bold transition-all flex flex-col items-center gap-1 text-sm"
                                :class="disposition === 'restock' ? 'bg-green-500/30 border-2 border-green-500 text-green-600 dark:text-green-400' : 'bg-green-500/10 border border-green-500/20 hover:bg-green-500/20 text-green-600 dark:text-green-400'">
                                <span class="material-symbols-outlined">check_circle</span> Restock
                            </button>
                            <button @click="disposition = 'claims'"
                                class="p-3 rounded-lg font-bold transition-all flex flex-col items-center gap-1 text-sm"
                                :class="disposition === 'claims' ? 'bg-blue-500/30 border-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400'">
                                <span class="material-symbols-outlined">gavel</span> Send to Claims
                            </button>
                            <button @click="disposition = 'discard'"
                                class="p-3 rounded-lg font-bold transition-all flex flex-col items-center gap-1 text-sm"
                                :class="disposition === 'discard' ? 'bg-red-500/30 border-2 border-red-500 text-red-600 dark:text-red-400' : 'bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-600 dark:text-red-400'">
                                <span class="material-symbols-outlined">delete</span> Discard
                            </button>
                            <button @click="disposition = 'recycle'"
                                class="p-3 rounded-lg font-bold transition-all flex flex-col items-center gap-1 text-sm"
                                :class="disposition === 'recycle' ? 'bg-purple-500/30 border-2 border-purple-500 text-purple-600 dark:text-purple-400' : 'bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 text-purple-600 dark:text-purple-400'">
                                <span class="material-symbols-outlined">recycling</span> Recycle
                            </button>
                        </div>
                    </div>

                    <!-- Genuineness + Recommended Outcome for damage claims -->
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Claim Valid?</label>
                            <select v-model="inspectionGenuineness"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                <option value="" class="bg-white dark:bg-gray-800">Assess claim...</option>
                                <option :value="true" class="bg-white dark:bg-gray-800">Genuine</option>
                                <option :value="false" class="bg-white dark:bg-gray-800">Not Genuine</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Recommended Outcome</label>
                            <select v-model="inspectionRecommendedOutcome"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                <option value="" class="bg-white dark:bg-gray-800">Select...</option>
                                <option value="Full Refund" class="bg-white dark:bg-gray-800">Full Refund</option>
                                <option value="Partial Refund" class="bg-white dark:bg-gray-800">Partial Refund</option>
                                <option value="Reject Claim" class="bg-white dark:bg-gray-800">Reject Claim</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Remarks to LM</label>
                        <textarea v-model="inspectionRemarks" placeholder="Explain what WM found during physical inspection..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm h-20 resize-none"></textarea>
                    </div>

                    <div v-if="disposition === 'claims' || disposition === 'discard'"
                        class="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px]">info</span>
                        Requires Logistics Manager approval
                    </div>

                    <div v-if="itemCondition === 'Awaiting Pickup'" class="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-400 flex items-center gap-2">
                        <span class="material-symbols-outlined text-[16px]">local_shipping</span>
                        Item is still in transit — cannot grade until driver drops it off.
                    </div>
                    <button v-else @click="submitReturn"
                        class="w-full py-3 bg-primary hover:bg-primary-dark text-background-dark font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        :disabled="!rmaId || !itemCondition || !disposition || inspectionGenuineness === '' || !inspectionRecommendedOutcome || submitting">
                        <span v-if="submitting" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                        {{ submitting ? 'Submitting...' : 'Submit Return Decision' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Processing Queue — from real PACKED/ON_HOLD orders -->
        <div class="glass-panel rounded-xl overflow-hidden p-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Items Awaiting Grading</h3>
            <div class="space-y-3 max-h-[500px] overflow-y-auto">
                <div v-for="item in processingItems" :key="item.id"
                    class="p-3 rounded-lg border transition-colors cursor-pointer"
                    :class="item.prefill?.condition === 'Awaiting Pickup'
                        ? 'bg-blue-50/40 dark:bg-blue-500/5 border-blue-200 dark:border-blue-500/20 hover:border-blue-400/50 opacity-70'
                        : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5 hover:border-yellow-500/30'"
                    @click="selectItem(item)">
                    <div class="flex justify-between items-start">
                        <div>
                            <div class="text-gray-900 dark:text-white text-sm font-bold">{{ item.name }}</div>
                            <div class="text-xs text-gray-500 font-mono">{{ item.rma }}</div>
                        </div>
                        <span v-if="item.prefill?.condition === 'Awaiting Pickup'"
                            class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/20 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[10px]">local_shipping</span> IN TRANSIT
                        </span>
                        <span v-else class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border border-yellow-500/20">PENDING</span>
                    </div>
                    <div class="text-[10px] text-gray-500 mt-1">{{ item.reason }} • Received {{ item.time }}</div>
                </div>
                <div v-if="processingItems.length === 0" class="text-center text-gray-500 py-8">
                    <span class="material-symbols-outlined text-3xl opacity-50">check_circle</span>
                    <div class="text-sm mt-2">No items awaiting grading</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { returnsWarehousePageKey } from './returnsWarehousePageContext'

const {
    activeTab,
    capturedPhoto,
    conditionNotes,
    disposition,
    inspectionGenuineness,
    inspectionRecommendedOutcome,
    inspectionRemarks,
    itemCondition,
    openScanner,
    processingItems,
    rmaId,
    selectItem,
    selectedOrderForReturn,
    submitReturn,
    submitting,
} = inject(returnsWarehousePageKey)
</script>
