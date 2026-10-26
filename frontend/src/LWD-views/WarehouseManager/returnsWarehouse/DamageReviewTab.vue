<template>
    <!-- ===== DAMAGE REVIEW TAB (Flow 1: photo_review) ===== -->
    <div v-if="activeTab === 'damage_review'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Review Form -->
        <div class="lg:col-span-2 glass-panel p-6 rounded-xl">
            <div class="flex justify-between items-center mb-5">
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white">Damage Review / Claims Review</h3>
                    <p class="text-xs text-gray-500 mt-0.5">Review customer-submitted photos and provide your assessment to the Logistics Manager.</p>
                </div>
                <span class="px-2 py-1 bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs rounded border border-blue-500/30 animate-pulse">Photo Review</span>
            </div>

            <div v-if="!selectedDamageReport" class="flex flex-col items-center justify-center py-12 text-gray-400 opacity-60">
                <span class="material-symbols-outlined text-5xl mb-2">photo_library</span>
                <p class="text-sm">Select a claim from the queue to begin review</p>
            </div>

            <div v-else class="space-y-4">
                <!-- Claim info -->
                <div class="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                    <div class="flex items-center justify-between mb-1">
                        <span class="font-mono font-bold text-blue-600 dark:text-blue-400 text-sm">{{ selectedDamageReport.id }}</span>
                        <span class="text-xs text-gray-500">Order: {{ selectedDamageReport.orderId }}</span>
                    </div>
                    <p class="text-sm text-gray-700 dark:text-gray-300 italic">"{{ selectedDamageReport.description }}"</p>
                </div>

                <!-- Customer photos -->
                <div v-if="selectedDamageReport.images?.length > 0">
                    <label class="text-xs text-gray-500 mb-2 block font-bold uppercase tracking-wide">Customer Photos ({{ selectedDamageReport.images.length }})</label>
                    <div class="flex gap-2 flex-wrap">
                        <button v-for="(img, i) in selectedDamageReport.images" :key="i"
                            @click="reviewPhotoPreview = img"
                            class="w-20 h-20 rounded-lg overflow-hidden border border-gray-200 dark:border-white/10 bg-gray-100 dark:bg-white/5 hover:border-blue-400 transition-colors">
                            <img :src="img" class="w-full h-full object-cover" />
                        </button>
                    </div>
                </div>
                <div v-else class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl text-xs text-gray-500 flex items-center gap-2">
                    <span class="material-symbols-outlined text-[16px]">hide_image</span> No photos attached by customer.
                </div>

                <!-- WM assessment fields -->
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block font-bold uppercase">Damage Severity</label>
                        <select v-model="damageReviewForm.severity"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500/50 text-sm">
                            <option value="" class="bg-white dark:bg-gray-800">Select severity...</option>
                            <option value="Minor" class="bg-white dark:bg-gray-800">Minor — Small cosmetic damage</option>
                            <option value="Moderate" class="bg-white dark:bg-gray-800">Moderate — Functional issue possible</option>
                            <option value="Severe" class="bg-white dark:bg-gray-800">Severe — Major damage / non-functional</option>
                            <option value="Cannot Determine" class="bg-white dark:bg-gray-800">Cannot Determine from photos</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block font-bold uppercase">Claim Genuineness</label>
                        <select v-model="damageReviewForm.genuineness"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500/50 text-sm">
                            <option value="" class="bg-white dark:bg-gray-800">Assess claim...</option>
                            <option :value="true" class="bg-white dark:bg-gray-800">Looks Genuine</option>
                            <option :value="false" class="bg-white dark:bg-gray-800">Looks Suspicious</option>
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block font-bold uppercase">Recommended Settlement</label>
                        <select v-model="damageReviewForm.recommendedSettlement"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500/50 text-sm">
                            <option value="" class="bg-white dark:bg-gray-800">Select recommendation...</option>
                            <option value="Full Refund" class="bg-white dark:bg-gray-800">Full Refund</option>
                            <option value="Partial Refund" class="bg-white dark:bg-gray-800">Partial Refund</option>
                            <option value="Reject Claim" class="bg-white dark:bg-gray-800">Reject Claim</option>
                            <option value="Need More Evidence" class="bg-white dark:bg-gray-800">Need More Evidence</option>
                        </select>
                    </div>
                    <div class="col-span-2">
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block font-bold uppercase">Remarks to LM</label>
                        <textarea v-model="damageReviewForm.remarks" rows="3" placeholder="Add remarks, observations, or instructions for the LM..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-blue-500/50 text-sm resize-none"></textarea>
                    </div>
                </div>

                <button @click="submitDamageReview"
                    :disabled="!damageReviewForm.severity || damageReviewForm.genuineness === '' || !damageReviewForm.recommendedSettlement || submittingReview"
                    class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    <span v-if="submittingReview" class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                    {{ submittingReview ? 'Submitting Review...' : 'Submit Damage Review to LM' }}
                </button>
            </div>
        </div>

        <!-- Damage Review Queue -->
        <div class="glass-panel rounded-xl overflow-hidden p-6">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4">Claims Review Queue</h3>
            <div class="space-y-3 max-h-[600px] overflow-y-auto">
                <div v-for="claim in damageReviewQueue" :key="claim.id"
                    class="p-3 rounded-lg border cursor-pointer transition-colors"
                    :class="selectedDamageReport?.id === claim.id
                        ? 'bg-blue-50 dark:bg-blue-500/10 border-blue-300 dark:border-blue-500/40'
                        : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5 hover:border-blue-400/40'"
                    @click="selectDamageReport(claim)">
                    <div class="flex justify-between items-start">
                        <div class="font-mono font-bold text-blue-600 dark:text-blue-400 text-xs">{{ claim.id }}</div>
                        <span v-if="claim.images?.length > 0" class="text-[9px] font-bold text-blue-500 bg-blue-50 dark:bg-blue-500/10 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                            <span class="material-symbols-outlined text-[10px]">photo_library</span> {{ claim.images.length }}
                        </span>
                    </div>
                    <div class="text-xs text-gray-500 mt-0.5">{{ claim.customer }}</div>
                    <div class="text-xs text-gray-700 dark:text-gray-300 mt-1 line-clamp-1 italic">"{{ claim.description }}"</div>
                </div>
                <div v-if="damageReviewQueue.length === 0" class="text-center text-gray-500 py-8">
                    <span class="material-symbols-outlined text-3xl opacity-50">check_circle</span>
                    <div class="text-sm mt-2">No damage reviews pending</div>
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
    damageReviewForm,
    damageReviewQueue,
    reviewPhotoPreview,
    selectDamageReport,
    selectedDamageReport,
    submitDamageReview,
    submittingReview,
} = inject(returnsWarehousePageKey)
</script>
