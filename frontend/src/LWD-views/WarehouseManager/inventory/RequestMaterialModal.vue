<template>
    <!-- Request New Material Modal -->
    <Teleport to="body">
        <div v-if="showRequestMaterialModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showRequestMaterialModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10 overflow-hidden">
                <!-- Header -->
                <div class="p-5 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-orange-50 dark:bg-orange-900/20">
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 rounded-xl bg-orange-500/15 flex items-center justify-center">
                            <span class="material-symbols-outlined text-orange-500 text-[20px]">add_shopping_cart</span>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-base">Packing Materials</h3>
                            <p class="text-[11px] text-gray-500">Add approved materials or request new ones</p>
                        </div>
                    </div>
                    <button @click="showRequestMaterialModal = false"
                        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>
                <!-- Body -->
                <div class="p-5 space-y-4">

                    <!-- Approved Materials Ready to Add -->
                    <div v-if="approvedMaterials.length > 0">
                        <p class="text-[10px] font-bold uppercase tracking-widest text-green-600 dark:text-green-400 mb-2 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">check_circle</span>
                            Ready to Add
                        </p>
                        <div class="space-y-2 mb-4">
                            <div v-for="req in approvedMaterials" :key="req.id"
                                class="flex items-center justify-between bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700/30 rounded-xl p-3">
                                <div>
                                    <span class="font-medium text-gray-900 dark:text-white">{{ req.material_name }}</span>
                                    <span class="text-xs text-gray-500 ml-2">₹{{ req.approved_rate }}/{{ req.unit }}</span>
                                </div>
                                <button @click="addApprovedMaterial(req)"
                                    class="bg-green-500 hover:bg-green-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium flex items-center gap-1 transition-colors">
                                    <span class="material-symbols-outlined text-[14px]">add</span>
                                    Add Stock
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Pending Requests -->
                    <div v-if="pendingMaterials.length > 0">
                        <p class="text-[10px] font-bold uppercase tracking-widest text-yellow-600 dark:text-yellow-400 mb-2 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">hourglass_empty</span>
                            Pending Approval
                        </p>
                        <div class="space-y-2 mb-4">
                            <div v-for="req in pendingMaterials" :key="req.id"
                                class="flex items-center justify-between bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700/30 rounded-xl p-3">
                                <span class="font-medium text-gray-900 dark:text-white">{{ req.material_name }}</span>
                                <span class="text-xs text-yellow-600 dark:text-yellow-400">Awaiting LM</span>
                            </div>
                        </div>
                    </div>

                    <!-- Divider if there are existing requests -->
                    <div v-if="myMaterialRequests.length > 0" class="relative">
                        <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-200 dark:border-white/10"></div></div>
                        <div class="relative flex justify-center"><span class="bg-white dark:bg-gray-900 px-3 text-xs text-gray-500">OR REQUEST NEW</span></div>
                    </div>

                    <!-- Request New Material Form -->
                    <div>
                        <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Material Name <span class="text-red-400">*</span></label>
                        <input type="text" v-model="materialRequestForm.name" placeholder="e.g. Foam Sheet, Pallet Wrap"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm" />
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Unit</label>
                            <select v-model="materialRequestForm.unit"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white text-sm">
                                <option value="pcs">pcs (pieces)</option>
                                <option value="m">m (meter)</option>
                                <option value="kg">kg</option>
                                <option value="roll">roll</option>
                                <option value="sheet">sheet</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Suggested Rate (₹)</label>
                            <input type="number" v-model.number="materialRequestForm.suggestedRate" placeholder="Optional"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white font-mono text-sm" />
                        </div>
                    </div>
                    <div>
                        <label class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5 block">Reason / Justification</label>
                        <textarea v-model="materialRequestForm.reason" rows="2" placeholder="Why is this material needed?"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl p-3 text-gray-900 dark:text-white text-sm resize-none"></textarea>
                    </div>
                    <div class="flex gap-3 pt-1">
                        <button @click="showRequestMaterialModal = false"
                            class="flex-1 py-3 rounded-xl border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 font-bold text-sm hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            Cancel
                        </button>
                        <button @click="submitMaterialRequest" :disabled="!materialRequestForm.name || submittingRequest"
                            class="flex-[2] py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50">
                            <span class="material-symbols-outlined text-[18px]">{{ submittingRequest ? 'hourglass_empty' : 'send' }}</span>
                            {{ submittingRequest ? 'Submitting...' : 'Request New' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inventoryPageKey } from './inventoryPageContext'

const {
    addApprovedMaterial,
    approvedMaterials,
    materialRequestForm,
    myMaterialRequests,
    pendingMaterials,
    showRequestMaterialModal,
    submitMaterialRequest,
    submittingRequest,
} = inject(inventoryPageKey)
</script>
