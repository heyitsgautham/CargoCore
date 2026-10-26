<template>
    <!-- AI Receive Plan Modal -->
    <Teleport to="body">
        <div v-if="showEstimatorModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showEstimatorModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-3xl border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">AI Receive Plan</h3>
                        <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            Estimates dock load, unloading time, crew need, and exception risk for vendor inbound.
                        </p>
                    </div>
                    <button @click="showEstimatorModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div v-if="estimatorLoading" class="p-8 text-center">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
                    <div class="mt-3 text-sm text-gray-600 dark:text-gray-400">Gemini is preparing the inbound receive plan...</div>
                </div>

                <div v-else-if="estimatorPlan" class="p-6 space-y-5 overflow-y-auto">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Select inbound ASN</label>
                        <select v-model="estimatorForm.asnId" @change="fetchInboundReceivePlan"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-violet-500/50">
                            <option v-for="asn in asns" :key="asn.id" :value="asn.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                                {{ asn.id }} — {{ asn.supplier }} — {{ asn.status }}
                            </option>
                        </select>
                    </div>

                    <div class="rounded-xl border border-violet-500/20 bg-violet-500/10 p-4">
                        <div class="flex flex-wrap gap-3 items-start justify-between">
                            <div>
                                <div class="text-xs uppercase tracking-wide text-violet-700 dark:text-violet-300">Planned For</div>
                                <div class="text-lg font-bold text-gray-900 dark:text-white">{{ estimatorPlan.asn.id }}</div>
                                <div class="text-sm text-gray-600 dark:text-gray-300">{{ estimatorPlan.asn.supplier }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {{ estimatorPlan.shipmentType }} · {{ estimatorPlan.generatedBy === 'gemini' ? 'Real AI' : 'Fallback logic' }}
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Confidence</div>
                                <div class="text-2xl font-bold text-violet-700 dark:text-violet-300">{{ estimatorPlan.confidence }}%</div>
                            </div>
                        </div>
                        <div class="mt-3 h-2 rounded-full bg-white/40 dark:bg-white/10 overflow-hidden">
                            <div class="h-full bg-violet-500 rounded-full transition-all"
                                :style="`width: ${estimatorPlan.confidence}%`"></div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Type Of Order</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.shipmentType }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {{ estimatorPlan.recurring ? 'Generated from recurring vendor schedule.' : 'One-time inbound vendor order.' }}
                            </div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Material Profile</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.materialProfile }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ estimatorPlan.expectedUnits }} expected units in this shipment.</div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Suggested Dock</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.suggestedDock }}</div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Crew Needed</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.workers }} staff</div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Receive Time</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.totalMinutes }} min</div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Risk Level</div>
                            <div class="text-lg font-bold mt-1" :class="estimatorPlan.riskClass">{{ estimatorPlan.riskLevel }}</div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Pallet Load</div>
                            <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.pallets }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Based on expected quantity and vendor flow.</div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Queue Delay</div>
                            <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.queueMinutes }} min</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ estimatorPlan.activeDockCount }} dock slot(s) still active today.</div>
                        </div>
                        <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10">
                            <div class="text-xs text-gray-500 dark:text-gray-400 uppercase">Putaway Zone</div>
                            <div class="text-lg font-bold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.stagingZone }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">Best staging area before stock update.</div>
                        </div>
                    </div>

                    <div class="rounded-xl bg-gray-50 dark:bg-white/5 p-4 border border-gray-200 dark:border-white/10 space-y-3">
                        <div>
                            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">AI Summary</div>
                            <div class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ estimatorPlan.summary }}</div>
                        </div>
                        <div>
                            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">AI Recommendation</div>
                            <div class="text-sm font-semibold text-gray-900 dark:text-white mt-1">{{ estimatorPlan.nextAction }}</div>
                        </div>
                        <div>
                            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Why this plan</div>
                            <div class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ estimatorPlan.reason }}</div>
                        </div>
                        <div>
                            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Watchouts</div>
                            <div class="flex flex-wrap gap-2 mt-2">
                                <span v-for="item in estimatorPlan.watchouts" :key="item"
                                    class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-gray-200 dark:bg-white/10 text-gray-700 dark:text-gray-200">
                                    {{ item }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div v-else class="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
                    No AI receive plan available for this ASN yet.
                </div>

                <div class="p-6 border-t border-gray-100 dark:border-white/5 flex justify-end gap-3">
                    <button @click="showEstimatorModal = false"
                        class="px-4 py-2 rounded-lg border border-gray-200 dark:border-white/10 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                        Close
                    </button>
                    <button @click="handleEstimatorPrimaryAction"
                        class="px-4 py-2 rounded-lg bg-primary hover:bg-primary-dark text-background-dark font-bold transition-colors">
                        {{ estimatorPrimaryActionLabel }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const {
    asns,
    estimatorForm,
    estimatorLoading,
    estimatorPlan,
    estimatorPrimaryActionLabel,
    fetchInboundReceivePlan,
    handleEstimatorPrimaryAction,
    showEstimatorModal,
} = inject(inboundPageKey)
</script>
