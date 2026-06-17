<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Returns Processing (Warehouse)</h2>
            <div class="bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-1 flex gap-1">
                <button
                    :class="activeTab === 'damage_review' ? 'px-4 py-1.5 bg-blue-600 rounded text-white text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'damage_review'">
                    <span class="flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">photo_camera</span>
                        Damage Review
                        <span v-if="damageReviewQueue.length > 0" class="bg-red-500 text-white text-[9px] w-4 h-4 rounded-full flex items-center justify-center font-bold">{{ damageReviewQueue.length }}</span>
                    </span>
                </button>
                <button
                    :class="activeTab === 'processing' ? 'px-4 py-1.5 bg-primary rounded text-background-dark text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'processing'">Physical Inspection</button>
                <button
                    :class="activeTab === 'completed' ? 'px-4 py-1.5 bg-primary rounded text-background-dark text-sm font-bold shadow-lg' : 'px-4 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white text-sm transition-colors'"
                    @click="activeTab = 'completed'">Completed</button>
            </div>
        </div>

        <!-- Stats Row -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-blue-600 dark:text-blue-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ damageReviewQueue.length }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Damage Reviews Pending</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ processingItems.length }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Awaiting Physical Inspection</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-green-600 dark:text-green-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ completedItems.filter(i => i.disposition === 'restock').length }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Restocked Today</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-red-600 dark:text-red-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-red-600 dark:text-red-400">{{ completedItems.filter(i => i.disposition === 'claims').length }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Sent to Claims</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-gray-600 dark:text-gray-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-gray-600 dark:text-gray-400">{{ completedItems.filter(i => i.disposition === 'discard' || i.disposition === 'recycle').length }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Discarded / Recycled</div>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400">Loading returns data...</div>
        </div>

        <template v-else>

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

        <!-- ===== COMPLETED TAB ===== -->
        <div v-if="activeTab === 'completed'">
            <div class="glass-panel rounded-xl overflow-hidden">
                <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-100 dark:bg-black/20">
                    <h3 class="font-bold text-gray-900 dark:text-white">Completed Returns Log</h3>
                    <div class="flex gap-2">
                        <button v-for="f in ['All', 'restock', 'claims', 'discard', 'recycle']" :key="f"
                            @click="completedFilter = f === 'All' ? '' : f"
                            class="px-3 py-1 rounded text-xs font-bold transition-colors"
                            :class="(f === 'All' && !completedFilter) || completedFilter === f ? 'bg-primary/20 text-primary' : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                            {{ f === 'All' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1) }}
                        </button>
                    </div>
                </div>
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase">
                        <tr>
                            <th class="p-4">Item</th>
                            <th class="p-4">RMA</th>
                            <th class="p-4">Condition</th>
                            <th class="p-4">Disposition</th>
                            <th class="p-4">Photo</th>
                            <th class="p-4">Time</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="item in filteredCompleted" :key="item.id" class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                            <td class="p-4 text-gray-900 dark:text-white font-bold">{{ item.name }}</td>
                            <td class="p-4 font-mono text-gray-600 dark:text-gray-400 text-xs">{{ item.rma || '--' }}</td>
                            <td class="p-4">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="getConditionClass(item.condition)">{{ item.condition }}</span>
                            </td>
                            <td class="p-4">
                                <div class="flex items-center gap-2">
                                    <div class="w-6 h-6 rounded flex items-center justify-center" :class="getDispositionBg(item.disposition)">
                                        <span class="material-symbols-outlined text-[14px]" :class="getDispositionColor(item.disposition)">{{ getDispositionIcon(item.disposition) }}</span>
                                    </div>
                                    <span class="text-xs" :class="getDispositionColor(item.disposition)">{{ item.dispositionLabel }}</span>
                                </div>
                            </td>
                            <td class="p-4">
                                <button v-if="item.hasPhoto" @click="photoItem = item; showPhotoModal = true"
                                    class="text-blue-600 dark:text-blue-400 text-xs hover:underline cursor-pointer flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[14px]">photo_camera</span> Attached
                                </button>
                                <span v-else class="text-gray-600 text-xs">—</span>
                            </td>
                            <td class="p-4 text-gray-500 font-mono text-xs">{{ item.time }}</td>
                        </tr>
                        <tr v-if="filteredCompleted.length === 0">
                            <td colspan="6" class="p-8 text-center text-gray-500">No completed returns found.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        </template>

        <!-- Photo Modal -->
        <Teleport to="body">
            <div v-if="showPhotoModal && photoItem"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showPhotoModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Damage Photo — {{ photoItem.name }}</h3>
                        <button @click="showPhotoModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="w-full h-56 bg-gray-100 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10 flex flex-col items-center justify-center overflow-hidden">
                            <img v-if="photoItem?.photoUrl" :src="photoItem.photoUrl" alt="Damage photo" class="w-full h-full object-contain" />
                            <template v-else>
                                <span class="material-symbols-outlined text-5xl text-gray-400 dark:text-gray-500">image</span>
                                <div class="text-sm text-gray-500 mt-2">Damage photo captured during inspection</div>
                            </template>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">RMA</div>
                                <div class="font-mono text-sm text-gray-900 dark:text-white font-bold">{{ photoItem.rma }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Condition</div>
                                <div class="text-sm text-gray-900 dark:text-white font-bold">{{ photoItem.condition }}</div>
                            </div>
                        </div>
                        <button @click="showPhotoModal = false"
                            class="w-full bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white py-3 rounded-lg text-sm font-bold transition-colors">Close</button>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const openScanner = inject('openScanner')
const lastGlobalScan = inject('lastGlobalScan')

const activeTab = ref('damage_review')
const rmaId = ref('')
const itemCondition = ref('')
const conditionNotes = ref('')
const disposition = ref('')
const capturedPhoto = ref(null)  // Will hold actual photo data/blob
const toastMsg = ref('')
const completedFilter = ref('')
const showPhotoModal = ref(false)
const photoItem = ref(null)
const loading = ref(false)
const submitting = ref(false)
const submittingReview = ref(false)
const selectedOrderForReturn = ref(null)
const selectedGradingId = ref(null)   // set when editing an existing pending grading
const warehouseId = ref(null)

// Flow 2 (physical inspection) extra fields
const inspectionGenuineness = ref('')
const inspectionRecommendedOutcome = ref('')
const inspectionRemarks = ref('')

// Flow 1 (damage review) state
const damageReviewQueue = ref([])  // claims with status = 'Under Review' and flow_type = 'photo_review'
const selectedDamageReport = ref(null)
const reviewPhotoPreview = ref(null)
const damageReviewForm = ref({ severity: '', genuineness: '', recommendedSettlement: '', remarks: '' })

function selectDamageReport(claim) {
    selectedDamageReport.value = claim
    damageReviewForm.value = { severity: '', genuineness: '', recommendedSettlement: '', remarks: '' }
}

async function submitDamageReview() {
    if (!selectedDamageReport.value || submittingReview.value) return
    submittingReview.value = true
    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }
        // PATCH the damage report with WM assessment and set status to Claims Reviewed
        const reviewRes = await fetch(
            `http://localhost:8000/api/v1/damage-reports/${selectedDamageReport.value.id}/review`,
            {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    damage_severity: damageReviewForm.value.severity,
                    is_genuine: damageReviewForm.value.genuineness,
                    recommended_settlement: damageReviewForm.value.recommendedSettlement,
                    remarks: damageReviewForm.value.remarks,
                    new_status: 'Claims Reviewed',
                })
            }
        )
        if (!reviewRes.ok) throw new Error(`HTTP ${reviewRes.status}`)
        // Remove from local queue
        damageReviewQueue.value = damageReviewQueue.value.filter(c => c.id !== selectedDamageReport.value.id)
        selectedDamageReport.value = null
        damageReviewForm.value = { severity: '', genuineness: '', recommendedSettlement: '', remarks: '' }
        toastMsg.value = 'Damage review submitted to Logistics Manager.'
    } catch (e) {
        console.error('submitDamageReview error:', e)
        toastMsg.value = 'Failed to submit damage review.'
    } finally {
        submittingReview.value = false
        setTimeout(() => { toastMsg.value = '' }, 2500)
    }
}

async function fetchDamageReviewQueue() {
    if (!authStore.authToken) return
    try {
        const headers = { 'Authorization': `Bearer ${authStore.authToken}` }
        const res = await fetch(
            `http://localhost:8000/api/v1/damage-reports?status=Reported&flow_type=photo_review&page_size=50`,
            { headers }
        )
        if (res.ok) {
            const data = await res.json()
            damageReviewQueue.value = data.items || data || []
        } else {
            console.warn(`Damage review queue fetch failed: HTTP ${res.status}`)
        }
    } catch (e) {
        console.error('fetchDamageReviewQueue error:', e)
    }
}
let refreshTimer = null

// Real data from API
const inboundReturns = ref([])       // ON_HOLD orders = items awaiting inspection
const pendingGradings = ref([])      // Pending (created but not completed) return gradings
const completedItems = ref([])       // Completed return gradings from API

// Listen for global scans
watch(lastGlobalScan, (newVal) => {
    if (newVal) {
        if (newVal === 'captured_image_data_mock' || newVal.startsWith('data:image')) {
            // Captured photo data
            capturedPhoto.value = newVal
        } else {
            rmaId.value = newVal
            const found = processingItems.value.find(p => p.rma === newVal)
            if (found) {
                selectItem(found)
                toastMsg.value = `Loaded RMA ${newVal} details.`
                setTimeout(() => { toastMsg.value = '' }, 2500)
            } else {
                selectedOrderForReturn.value = null
                selectedGradingId.value = null
            }
        }
        lastGlobalScan.value = null
    }
})

function resolveWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id || null
}

async function fetchWarehouseId() {
    try {
        await authStore.ensureWarehouseContext()

        const resolvedWarehouseId = resolveWarehouseId()
        if (resolvedWarehouseId) {
            warehouseId.value = resolvedWarehouseId
            return
        }

        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }
        const response = await fetch('http://localhost:8000/api/v1/warehouses?page=1&page_size=100', { headers })
        if (!response.ok) return

        const data = await response.json()
        const warehouses = data.items || data || []
        const profile = authStore.currentUser || {}
        const linkedWarehouse = warehouses.find(warehouse =>
            warehouse.id === profile.warehouse_id || warehouse.manager_id === profile.id
        ) || null

        warehouseId.value = linkedWarehouse?.id || null
    } catch (error) {
        console.error('Error fetching warehouse ID:', error)
    }
}

function mapGradingToCompleted(g) {
    return {
        id: g.id,
        name: g.order_tracking || g.rma_code || 'Unknown',
        rma: g.rma_code,
        condition: g.item_condition,
        disposition: g.disposition,
        dispositionLabel: getDispositionLabel(g.disposition),
        hasPhoto: !!g.damage_photo_url,
        photoUrl: g.damage_photo_url,
        time: g.graded_at
            ? new Date(g.graded_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
            : '--',
    }
}

async function fetchReturns({ silent = false } = {}) {
    if (!authStore.authToken) return

    if (!silent) {
        loading.value = true
    }
    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        // ON_HOLD orders are NOT reliable as return indicators — returns are tracked via
        // the return gradings API exclusively. Keep inboundReturns empty.
        inboundReturns.value = []

        if (warehouseId.value) {
            // Fetch pending return gradings (created but not yet completed)
            const pendingRes = await fetch(
                `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns?status_filter=pending&page_size=50`,
                { headers }
            )
            if (pendingRes.ok) {
                const data = await pendingRes.json()
                pendingGradings.value = data.items || []
            }

            // Fetch completed return gradings (status_filter is the correct param name)
            const completedRes = await fetch(
                `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns?status_filter=completed&page_size=50`,
                { headers }
            )
            if (completedRes.ok) {
                const completedData = await completedRes.json()
                completedItems.value = (completedData.items || []).map(mapGradingToCompleted)
            }
        }
    } catch (error) {
        console.error('Error fetching returns:', error)
    } finally {
        if (!silent) {
            loading.value = false
        }
    }
}

async function refreshReturnsContext() {
    await fetchWarehouseId()
    await fetchDamageReviewQueue()
    if (!warehouseId.value) {
        pendingGradings.value = []
        completedItems.value = []
        inboundReturns.value = []
        return
    }
    await fetchReturns()
}

function handleVisibilityRefresh() {
    if (document.visibilityState === 'visible') {
        refreshReturnsContext()
    }
}

function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(() => {
        if (document.visibilityState === 'visible') {
            fetchReturns({ silent: true })
        }
    }, 15000)
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
    }
}

function getDispositionLabel(d) {
    const labels = { restock: 'Restocked', claims: 'Sent to Claims', discard: 'Discarded', recycle: 'Recycled' }
    return labels[d] || d
}

// Build processing queue: pending gradings first, then ON_HOLD orders not yet assigned a grading
const processingItems = computed(() => {
    const fromGradings = pendingGradings.value.map(g => ({
        id: `grading-${g.id}`,
        gradingId: g.id,
        orderId: g.order_id,
        name: g.order_tracking || g.rma_code,
        rma: g.rma_code,
        reason: g.condition_notes || 'Returned by customer',
        time: g.created_at
            ? new Date(g.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
            : '--',
        rawOrder: { id: g.order_id, tracking_code: g.order_tracking },
        // Pre-fill fields if grading already has partial data
        prefill: {
            condition: g.item_condition,
            notes: g.condition_notes,
            disposition: g.disposition,
            genuineness: g.is_genuine,
            recommendedOutcome: g.recommended_outcome,
            remarks: g.inspection_remarks,
        },
    }))

    // Only show ON_HOLD orders that don't already have a pending grading
    const gradedOrderIds = new Set(pendingGradings.value.map(g => g.order_id).filter(Boolean))
    const fromOrders = inboundReturns.value
        .filter(order => !gradedOrderIds.has(order.id))
        .map(order => ({
            id: `order-${order.id}`,
            gradingId: null,
            orderId: order.id,
            name: order.tracking_code || `Order #${order.id?.slice(0, 8)}`,
            rma: `RMA-${order.tracking_code || order.id?.slice(0, 6).toUpperCase()}`,
            reason: order.notes || order.hold_reason || 'Returned by customer',
            time: order.updated_at
                ? new Date(order.updated_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
                : '--',
            rawOrder: order,
            prefill: null,
        }))

    return [...fromGradings, ...fromOrders]
})

const filteredCompleted = computed(() => {
    if (!completedFilter.value) return completedItems.value
    return completedItems.value.filter(i => i.disposition === completedFilter.value)
})

function getConditionClass(c) {
    if (c === 'Like New') return 'bg-green-500/20 text-green-600 dark:text-green-400'
    if (c === 'Minor Wear') return 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'
    if (c === 'Damaged') return 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
    return 'bg-red-500/20 text-red-600 dark:text-red-400'
}

function getDispositionBg(d) {
    if (d === 'restock') return 'bg-green-500/20'
    if (d === 'claims') return 'bg-blue-500/20'
    if (d === 'discard') return 'bg-red-500/20'
    return 'bg-purple-500/20'
}

function getDispositionColor(d) {
    if (d === 'restock') return 'text-green-500'
    if (d === 'claims') return 'text-blue-500'
    if (d === 'discard') return 'text-red-500'
    return 'text-purple-500'
}

function getDispositionIcon(d) {
    if (d === 'restock') return 'check'
    if (d === 'claims') return 'gavel'
    if (d === 'discard') return 'close'
    return 'recycling'
}

function selectItem(item) {
    rmaId.value = item.rma
    selectedOrderForReturn.value = item.rawOrder
    selectedGradingId.value = item.gradingId || null
    if (item.prefill) {
        itemCondition.value = item.prefill.condition || ''
        conditionNotes.value = item.prefill.notes || ''
        disposition.value = item.prefill.disposition || ''
        inspectionGenuineness.value = typeof item.prefill.genuineness === 'boolean' ? item.prefill.genuineness : ''
        inspectionRecommendedOutcome.value = item.prefill.recommendedOutcome || ''
        inspectionRemarks.value = item.prefill.remarks || ''
    } else {
        itemCondition.value = ''
        conditionNotes.value = ''
        disposition.value = ''
        inspectionGenuineness.value = ''
        inspectionRecommendedOutcome.value = ''
        inspectionRemarks.value = ''
    }
}

async function submitReturn() {
    if (!warehouseId.value) {
        toastMsg.value = 'No warehouse selected'
        setTimeout(() => { toastMsg.value = '' }, 2500)
        return
    }

    submitting.value = true
    const labels = { restock: 'Restocked', claims: 'Sent to Claims', discard: 'Discarded', recycle: 'Recycled' }

    try {
        const headers = {
            'Authorization': `Bearer ${authStore.authToken}`,
            'Content-Type': 'application/json'
        }

        let gradingId = selectedGradingId.value

        if (gradingId) {
            // Existing pending grading — update it first, then complete
            await fetch(
                `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}`,
                {
                    method: 'PUT',
                    headers,
                    body: JSON.stringify({
                        item_condition: itemCondition.value,
                        condition_notes: conditionNotes.value || null,
                        disposition: disposition.value,
                        is_genuine: inspectionGenuineness.value !== '' ? inspectionGenuineness.value : null,
                        recommended_outcome: inspectionRecommendedOutcome.value || null,
                        inspection_remarks: inspectionRemarks.value || null,
                    })
                }
            )
        } else {
            // New grading — create it
            const response = await fetch(
                `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns`,
                {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        rma_code: rmaId.value,
                        order_id: selectedOrderForReturn.value?.id || null,
                        item_condition: itemCondition.value,
                        condition_notes: conditionNotes.value || null,
                        disposition: disposition.value,
                        is_genuine: inspectionGenuineness.value !== '' ? inspectionGenuineness.value : null,
                        recommended_outcome: inspectionRecommendedOutcome.value || null,
                        inspection_remarks: inspectionRemarks.value || null,
                    })
                }
            )
            if (!response.ok) throw new Error(`HTTP ${response.status}`)
            const grading = await response.json()
            gradingId = grading.id
        }

        // Upload photo if captured
        if (capturedPhoto.value && gradingId) {
            await uploadDamagePhoto(gradingId, capturedPhoto.value)
        }

        // Mark as completed — this is what moves it to the "Completed" tab
        const completeRes = await fetch(
            `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}/complete`,
            { method: 'POST', headers }
        )
        if (!completeRes.ok) throw new Error(`Complete failed: HTTP ${completeRes.status}`)
        const completed = await completeRes.json()

        // Add to completed list immediately
        completedItems.value.unshift(mapGradingToCompleted(completed))

        // Remove from processing queue
        const gradingIdx = pendingGradings.value.findIndex(g => g.id === selectedGradingId.value)
        if (gradingIdx !== -1) pendingGradings.value.splice(gradingIdx, 1)
        const orderIdx = inboundReturns.value.findIndex(o =>
            rmaId.value.includes(o.tracking_code) || rmaId.value.includes(o.id?.slice(0, 6))
        )
        if (orderIdx !== -1) inboundReturns.value.splice(orderIdx, 1)

        toastMsg.value = `Return ${rmaId.value} — ${labels[disposition.value]}`

        // Reset form
        capturedPhoto.value = null
        rmaId.value = ''
        itemCondition.value = ''
        conditionNotes.value = ''
        disposition.value = ''
        inspectionGenuineness.value = ''
        inspectionRecommendedOutcome.value = ''
        inspectionRemarks.value = ''
        selectedOrderForReturn.value = null
        selectedGradingId.value = null

    } catch (error) {
        console.error('Error submitting return:', error)
        toastMsg.value = 'Failed to submit return grading'
    } finally {
        submitting.value = false
        setTimeout(() => { toastMsg.value = '' }, 2500)
    }
}

async function uploadDamagePhoto(gradingId, photoData) {
    try {
        // Convert base64/data URL to blob if needed
        let blob
        if (typeof photoData === 'string' && photoData.startsWith('data:')) {
            const res = await fetch(photoData)
            blob = await res.blob()
        } else if (photoData instanceof Blob) {
            blob = photoData
        } else {
            // Mock photo - skip upload
            return
        }

        const formData = new FormData()
        formData.append('file', blob, 'damage_photo.jpg')

        const response = await fetch(
            `http://localhost:8000/api/v1/warehouses/${warehouseId.value}/operations/returns/${gradingId}/photo`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                },
                body: formData
            }
        )

        if (!response.ok) {
            console.warn('Failed to upload photo:', response.status)
        }
    } catch (error) {
        console.error('Error uploading damage photo:', error)
    }
}

watch(
    () => [authStore.currentWarehouse?.id, authStore.currentUser?.warehouse_id],
    async ([currentWarehouseId, currentUserWarehouseId], [prevCurrentWarehouseId, prevCurrentUserWarehouseId]) => {
        if (
            currentWarehouseId === prevCurrentWarehouseId
            && currentUserWarehouseId === prevCurrentUserWarehouseId
        ) {
            return
        }
        await refreshReturnsContext()
    }
)

onMounted(async () => {
    await refreshReturnsContext()
    startAutoRefresh()
    window.addEventListener('focus', refreshReturnsContext)
    document.addEventListener('visibilitychange', handleVisibilityRefresh)
})

onUnmounted(() => {
    stopAutoRefresh()
    window.removeEventListener('focus', refreshReturnsContext)
    document.removeEventListener('visibilitychange', handleVisibilityRefresh)
})
</script>
