<template>
    <Transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100">
        <div v-if="showRaiseModal"
            class="fixed inset-0 z-[150] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            @click.self="showRaiseModal = false">
            <div class="w-full max-w-lg bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden">
                <div class="px-6 py-4 border-b border-gray-100 dark:border-white/10 flex items-center justify-between">
                    <h3 class="text-base font-bold text-gray-900 dark:text-white">Raise Case on Customer's Behalf</h3>
                    <button @click="showRaiseModal = false" class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500">
                        <span class="material-symbols-outlined text-[18px]">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4">
                    <!-- Duplicate Warning -->
                    <div v-if="duplicateWarning"
                        class="p-3 bg-yellow-50 dark:bg-yellow-500/10 border border-yellow-200 dark:border-yellow-500/20 rounded-xl text-xs text-yellow-800 dark:text-yellow-300 flex items-start gap-2">
                        <span class="material-symbols-outlined text-[16px] flex-shrink-0 mt-0.5">warning</span>
                        <span>A damage report already exists for this order: <strong>{{ duplicateWarning.reference_code }}</strong> ({{ duplicateWarning.status }}). Are you sure you want to create another?</span>
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Customer ID</label>
                        <input v-model="raiseForm.customer_id" type="text" placeholder="UUID of the customer..."
                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Order ID <span class="text-gray-400 font-normal">(optional)</span></label>
                        <input v-model="raiseForm.order_id" type="text" placeholder="UUID of the order..."
                            @blur="checkDuplicate"
                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition" />
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Flow Type</label>
                        <select v-model="raiseForm.flow_type" class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition">
                            <option value="photo_review">Photo Review</option>
                            <option value="pickup_inspection">Pickup Inspection</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">Description</label>
                        <textarea v-model="raiseForm.description" rows="3" placeholder="Describe the damage or issue..."
                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                    </div>
                    <div v-if="raiseError" class="text-sm text-red-600 dark:text-red-400">{{ raiseError }}</div>
                </div>
                <div class="px-6 py-4 border-t border-gray-100 dark:border-white/10 flex justify-end gap-2">
                    <button @click="showRaiseModal = false"
                        class="px-4 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                        Cancel
                    </button>
                    <button @click="submitRaiseCase" :disabled="raisingCase"
                        class="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg text-sm transition-colors disabled:opacity-50">
                        {{ raisingCase ? 'Creating…' : 'Create Report' }}
                    </button>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    checkDuplicate,
    duplicateWarning,
    raiseError,
    raiseForm,
    raisingCase,
    showRaiseModal,
    submitRaiseCase,
} = inject(reverseLogisticsPageKey)
</script>
