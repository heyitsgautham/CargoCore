<template>
    <!-- Issue to Order Modal -->
    <Teleport to="body">
        <div v-if="showIssueModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showIssueModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-2xl border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Issue Materials to Order</h3>
                    <button @click="closeIssueModal" class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4 overflow-y-auto flex-1">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Select Order</label>
                        <select v-model="issueForm.orderId" @change="onOrderSelected"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option value="">Select a picking order...</option>
                            <option v-for="o in ordersAvailableForIssuance" :key="o.id" :value="o.tracking_code">
                                {{ o.tracking_code }} — {{ getEffectiveWarehouseSubstatus(o, getWarehouseId()) || o.status }}
                            </option>
                            <option v-if="ordersAvailableForIssuance.length === 0" disabled value="">
                                No orders pending material issuance
                            </option>
                        </select>
                    </div>

                    <!-- Order Details & Requirements -->
                    <div v-if="selectedOrderDetails" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-500/30 rounded-lg p-4 space-y-3">
                        <div class="flex items-start justify-between">
                            <div>
                                <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-1">Order Details</h4>
                                <div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                    <div><span class="font-semibold">Tracking:</span> {{ selectedOrderDetails.tracking_code }}</div>
                                    <div><span class="font-semibold">Status:</span> {{ selectedOrderDetails.status }}</div>
                                    <div v-if="selectedOrderDetails.customer_name" class="capitalize">
                                        <span class="font-semibold">Customer:</span> {{ selectedOrderDetails.customer_name }}
                                    </div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-gray-500 dark:text-gray-400">Estimated Items</div>
                                <div class="text-2xl font-bold text-primary">{{ selectedOrderDetails.estimated_items || '—' }}</div>
                            </div>
                        </div>

                        <!-- Recommended Materials -->
                        <div v-if="recommendedMaterials.length > 0" class="pt-2 border-t border-blue-200 dark:border-blue-500/20">
                            <div class="text-xs font-bold text-blue-600 dark:text-blue-400 mb-2 flex items-center gap-1">
                                <span class="material-symbols-outlined text-sm">lightbulb</span>
                                Recommended Packing Materials
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <div v-for="rec in recommendedMaterials" :key="rec.id"
                                    class="text-xs bg-white dark:bg-gray-800/50 rounded p-2 flex items-center justify-between">
                                    <span class="text-gray-900 dark:text-white">{{ rec.emoji }} {{ rec.name }}</span>
                                    <span class="font-bold text-primary">{{ rec.suggestedQty }} {{ rec.unit }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Material Selection -->
                    <div v-if="issueForm.orderId">
                        <div class="flex items-center justify-between mb-2">
                            <label class="text-xs text-gray-600 dark:text-gray-400 block">Select Materials to Issue</label>
                            <button v-if="recommendedMaterials.length > 0" @click="applyRecommendedQuantities"
                                class="text-xs bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1 rounded-lg font-semibold transition-colors">
                                Apply Recommended
                            </button>
                        </div>
                        <div class="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto p-1">
                            <div v-for="item in packingItems" :key="item.id"
                                class="bg-gray-50 dark:bg-white/5 border rounded-lg p-3 transition-colors"
                                :class="issueForm.items[item.id] > 0 ? 'border-primary/50 bg-primary/5' : 'border-gray-200 dark:border-white/10'">
                                <div class="flex items-center gap-2 mb-2">
                                    <span class="text-2xl">{{ item.emoji }}</span>
                                    <div class="flex-1">
                                        <div class="text-xs font-bold text-gray-900 dark:text-white">{{ item.name }}</div>
                                        <div class="text-[10px] text-gray-500">Available: {{ item.stock }} {{ item.unit }}</div>
                                    </div>
                                </div>
                                <div class="relative">
                                    <input type="number" min="0" :max="item.stock" placeholder="0"
                                        v-model.number="issueForm.items[item.id]"
                                        class="w-full bg-white dark:bg-black/40 border rounded-lg p-2 text-gray-900 dark:text-white text-sm text-center font-bold focus:outline-none focus:border-primary/50"
                                        :class="issueForm.items[item.id] > item.stock ? 'border-red-500' : 'border-gray-200 dark:border-white/10'" />
                                    <div v-if="issueForm.items[item.id] > item.stock" class="text-[10px] text-red-500 mt-1 text-center font-semibold">
                                        ⚠ Exceeds stock
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-else class="text-center py-8 text-gray-500 text-sm">
                        <span class="material-symbols-outlined text-4xl mb-2 opacity-30">inbox</span>
                        <p>Select an order to see recommended materials</p>
                    </div>

                    <div v-if="issueForm.orderId">
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-2">
                            <span>Issue To (Driver / Laborer)</span>
                            <span class="text-[10px] text-green-500 font-semibold">{{ issuableLabourers.length }} selectable</span>
                        </label>
                        <select v-model="issueForm.issuedToLabourerId"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option value="">Select staff...</option>
                            <option v-for="l in issuableLabourers" :key="l.id" :value="String(l.id)">
                                {{ l.name || l.full_name }} ({{ labourerIssueLabel(l) }})
                            </option>
                        </select>
                        <div v-if="issuableLabourers.length === 0" class="text-xs text-orange-500 mt-1 flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm">warning</span>
                            No workers currently selectable. All staff are assigned to other orders or off duty.
                        </div>
                    </div>
                </div>

                <div class="p-6 border-t border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-black/20">
                    <button @click="submitIssue"
                        class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        :disabled="!canSubmitIssue || issuingMaterials">
                        <span v-if="issuingMaterials" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                        {{ issuingMaterials ? 'Issuing...' : 'Issue Materials' }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { getEffectiveWarehouseSubstatus } from '@/utils/warehouseOrderState'
import { packingMaterialsPageKey } from './packingMaterialsPageContext'

const {
    applyRecommendedQuantities,
    canSubmitIssue,
    closeIssueModal,
    getWarehouseId,
    issuableLabourers,
    issueForm,
    issuingMaterials,
    labourerIssueLabel,
    onOrderSelected,
    ordersAvailableForIssuance,
    packingItems,
    recommendedMaterials,
    selectedOrderDetails,
    showIssueModal,
    submitIssue,
} = inject(packingMaterialsPageKey)
</script>
