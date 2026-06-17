<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Inbound Shipments</h2>
            <div class="flex gap-2">
                <button @click="openInboundEstimator()" :disabled="loading || asns.length === 0"
                    class="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">model_training</span> AI Receive Plan
                </button>
                <button @click="showScheduleModal = true"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">calendar_today</span> Schedule Delivery
                </button>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-green-600 dark:text-green-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-green-600 dark:text-green-400">{{ arrivedCount }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Arrived Today</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-blue-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-blue-400">{{ inTransitCount }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">In Transit</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-red-600 dark:text-red-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-red-600 dark:text-red-400">{{ mismatchCount }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Mismatches Found</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div v-if="loading" class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 animate-pulse">--</div>
                <div v-else class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ damageCount }}</div>
                <div class="text-xs text-gray-600 dark:text-gray-400">Damage Reports</div>
            </div>
        </div>

        <!-- Loading overlay for table -->
        <div v-if="loading" class="glass-panel p-8 rounded-xl text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <div class="mt-2 text-gray-600 dark:text-gray-400 text-sm">Loading inbound shipments...</div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <!-- Dock Schedule -->
            <div class="glass-panel p-6 rounded-xl xl:col-span-1">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Dock Schedule (Today)</h3>
                <div class="space-y-3">
                    <div v-for="slot in dockSchedule" :key="slot.id" @click="selectedSlot = slot; showSlotDetail = true"
                        class="p-3 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 hover:border-white/20 rounded-lg cursor-pointer transition-all"
                        :class="slot.status === 'Completed' ? 'opacity-50' : ''">
                        <div class="flex justify-between items-center mb-1">
                            <span
                                :class="slot.status === 'Completed' ? 'text-gray-600 dark:text-gray-400' : 'text-primary'"
                                class="font-bold">{{ slot.time }}</span>
                            <span class="text-xs px-2 py-0.5 rounded font-bold" :class="slot.statusClass">{{ slot.status }}</span>
                        </div>
                        <div class="text-gray-900 dark:text-white text-sm">Supplier: {{ slot.supplier }}</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">{{ slot.dock }} • {{ slot.pallets }}
                            Pallets</div>
                    </div>
                </div>
            </div>

            <!-- Pending Receipt with Mismatch & Damage -->
            <div class="xl:col-span-3 glass-panel rounded-xl overflow-hidden">
                <div
                    class="p-4 border-b border-gray-100 dark:border-white/5 font-bold text-gray-900 dark:text-white flex flex-wrap gap-2 justify-between items-center">
                    <span>ASN Verification & Receiving</span>
                    <div class="flex gap-2">
                        <button @click="showMismatchModal = true"
                            class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">flag</span> Flag Mismatch
                        </button>
                        <button @click="showDamageModal = true"
                            class="bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-600 dark:text-yellow-400 px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">broken_image</span> Report Damage
                        </button>
                    </div>
                </div>
                <div class="overflow-x-auto">
                <table class="w-full text-left text-sm min-w-[700px]">
                    <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase text-[11px]">
                        <tr>
                            <th class="px-4 py-3">ASN ID</th>
                            <th class="px-4 py-3">Supplier</th>
                            <th class="px-4 py-3">Exp / Rcvd</th>
                            <th class="px-4 py-3">ETA</th>
                            <th class="px-4 py-3">Status</th>
                            <th class="px-4 py-3">Issues</th>
                            <th class="px-4 py-3">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-for="asn in asns" :key="asn.id"
                            class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-300">{{ asn.id }}</td>
                            <td class="px-4 py-3 text-gray-900 dark:text-white text-xs">{{ asn.supplier }}</td>
                            <td class="px-4 py-3 text-xs">
                                <span class="text-gray-600 dark:text-gray-400">{{ asn.expected }}</span>
                                <span class="text-gray-400 mx-1">/</span>
                                <span :class="asn.received !== asn.expected && asn.received > 0 ? 'text-red-500 font-bold' : 'text-gray-500'">
                                    {{ asn.received || '--' }}
                                </span>
                            </td>
                            <td class="px-4 py-3 text-xs text-gray-600 dark:text-gray-300 whitespace-nowrap">{{ asn.eta }}</td>
                            <td class="px-4 py-3">
                                <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="asn.statusClass">
                                    {{ asn.displayStatus }}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <div class="flex gap-1 flex-wrap">
                                    <span v-if="asn.mismatch"
                                        class="px-1.5 py-0.5 bg-red-500/20 text-red-600 dark:text-red-400 text-[9px] font-bold rounded border border-red-500/20">MISMATCH</span>
                                    <span v-if="asn.damaged"
                                        class="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 text-[9px] font-bold rounded border border-yellow-500/20">DAMAGED</span>
                                    <span v-if="!asn.mismatch && !asn.damaged" class="text-gray-500 text-xs">—</span>
                                </div>
                                <div v-if="asn.issueResolutionLabel" class="mt-1 text-[10px] text-gray-500 dark:text-gray-400">
                                    {{ asn.issueResolutionLabel }}
                                </div>
                                <div v-if="asn.issueStatus || asn.issueTicketReference" class="mt-1 flex gap-1 flex-wrap items-center">
                                    <span v-if="asn.issueStatus" class="px-1.5 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wider"
                                        :class="issueStatusClass(asn.issueStatus)">
                                        {{ formatIssueStatus(asn.issueStatus) }}
                                    </span>
                                    <span v-if="asn.issueTicketReference" class="text-[10px] text-gray-400">
                                        {{ asn.issueTicketReference }}
                                    </span>
                                </div>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <button @click="openInboundEstimator(asn.id)"
                                    class="bg-violet-500/15 hover:bg-violet-500/25 text-violet-600 dark:text-violet-300 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                                    AI Plan
                                </button>
                                <button v-if="showTakeBackAction(asn)" @click="generateTakeBack(asn)"
                                    class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                                    Generate Vendor Take-Back
                                </button>
                                <button v-if="asn.status === 'InTransit'" @click="markArrived(asn)"
                                    class="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-600 dark:text-indigo-300 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap mr-2">
                                    Mark Arrived
                                </button>
                                <button v-else-if="canStartInboundProcessing(asn)" @click="startReceiving(asn)"
                                    class="bg-primary/20 hover:bg-primary/30 text-primary px-3 py-1.5 rounded text-xs font-bold transition-colors">
                                    Start Receiving
                                </button>
                                <button v-else-if="canCompleteInboundProcessing(asn)" @click="completeReceiving(asn, { navigateToPicking: true })"
                                    class="bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 px-3 py-1.5 rounded text-xs font-bold transition-colors whitespace-nowrap">
                                    Complete & Move to Picking
                                </button>
                                <span v-else-if="asn.warehouseSubstatus === 'ON_HOLD'" class="text-red-500 text-xs font-bold">Vendor take-back generated</span>
                                <span v-else-if="showIssueHoldState(asn)" class="text-amber-500 text-xs font-bold">{{ asn.issueBlockingReason || 'Awaiting support/vendor decision' }}</span>
                                <span v-else-if="asn.status === 'Completed'" class="text-green-500 text-xs font-bold">Ready for next step</span>
                                <span v-else class="text-gray-500 text-xs">Awaiting arrival</span>
                            </td>
                        </tr>
                        <tr v-if="asns.length === 0">
                            <td colspan="7" class="p-8 text-center text-gray-500 text-sm">
                                No vendor inbound shipments are scheduled for this warehouse.
                            </td>
                        </tr>
                    </tbody>
                </table>
                </div>
            </div>
        </div>

        <!-- Slot Detail Modal -->
        <Teleport to="body">
            <div v-if="showSlotDetail && selectedSlot"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showSlotDetail = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Dock Slot Details</h3>
                        <button @click="showSlotDetail = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-3">
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Supplier</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.supplier }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Time</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.time }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Dock</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.dock }}</div>
                            </div>
                            <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                                <div class="text-xs text-gray-600 dark:text-gray-400">Pallets</div>
                                <div class="text-gray-900 dark:text-white font-bold">{{ selectedSlot.pallets }}</div>
                            </div>
                        </div>
                        <div class="bg-gray-50 dark:bg-white/5 p-3 rounded-lg">
                            <div class="text-xs text-gray-600 dark:text-gray-400">Status</div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="selectedSlot.statusClass">{{
                                selectedSlot.status }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

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

        <!-- Damage Modal -->
        <Teleport to="body">
            <div v-if="showDamageModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showDamageModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Report Shipment Damage</h3>
                        <button @click="showDamageModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">ASN ID</label>
                            <select v-model="damageForm.asnId"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option v-for="asn in asns" :key="asn.id" :value="asn.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ asn.id }} — {{
                                    asn.supplier }}
                                </option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damaged Items
                                Count</label>
                            <input type="number" v-model.number="damageForm.count" placeholder="0"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damage
                                Description</label>
                            <textarea v-model="damageForm.description" placeholder="Describe the damage..."
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm h-20 resize-none"></textarea>
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damage Camera Capture</label>
                            <div v-if="!damagePhoto" @click="openDamageCamera"
                                class="p-6 rounded-lg border-2 border-dashed text-center cursor-pointer transition-colors bg-gray-50 dark:bg-white/5 border-gray-300 dark:border-white/10 hover:border-primary/50 hover:bg-gray-100 dark:hover:bg-white/10">
                                <span class="material-symbols-outlined text-4xl text-gray-400 dark:text-gray-500">photo_camera</span>
                                <div class="text-sm mt-2 text-gray-600 dark:text-gray-400 font-medium">Open camera and capture damage photo</div>
                            </div>
                            <div v-else class="relative rounded-lg overflow-hidden border border-gray-200 dark:border-white/10">
                                <img :src="damagePhoto" class="w-full h-48 object-cover cursor-pointer" @click="viewImage(damagePhoto)" />
                                <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent pointer-events-none"></div>
                                <div class="absolute bottom-0 left-0 right-0 p-3 flex items-center justify-between">
                                    <div class="flex items-center gap-2 text-white text-xs font-bold">
                                        <span class="material-symbols-outlined text-[16px]">check_circle</span>
                                        Photo captured
                                    </div>
                                    <div class="flex gap-2">
                                        <button @click.stop="viewImage(damagePhoto)" class="px-3 py-1 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded text-xs font-bold transition-colors">
                                            View
                                        </button>
                                        <button @click.stop="retakeDamagePhoto" class="px-3 py-1 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded text-xs font-bold transition-colors">
                                            Retake
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <button @click="submitDamage" :disabled="!damageForm.asnId"
                            class="w-full bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-600 dark:text-yellow-400 font-bold py-3 rounded-lg transition-colors">
                            Submit Damage Report
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>

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

        <!-- Schedule Modal -->
        <Teleport to="body">
            <div v-if="showScheduleModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showScheduleModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg">Schedule Inbound
                            Delivery</h3>
                        <button @click="showScheduleModal = false"
                            class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                                class="material-symbols-outlined">close</span></button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Supplier
                                Name</label>
                            <input type="text" v-model="scheduleForm.supplier" placeholder="Supplier name"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Expected
                                    Qty</label>
                                <input type="number" v-model.number="scheduleForm.qty"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                            </div>
                            <div>
                                <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">ETA</label>
                                <input type="datetime-local" v-model="scheduleForm.eta"
                                    class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                            </div>
                        </div>
                        <button @click="scheduleDelivery" :disabled="!scheduleForm.supplier"
                            class="w-full bg-primary hover:bg-primary-dark text-background-dark font-bold py-3 rounded-lg transition-colors">Schedule
                            Delivery</button>
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

        <!-- Smart Scanner Modal for Camera -->
        <SmartScannerModal :is-open="isCameraOpen" :default-tab="'camera'" @close="isCameraOpen = false" @camera="handlePhotoCapture" />

        <!-- Image Viewer Modal -->
        <Teleport to="body">
            <div v-if="viewerImage" class="fixed inset-0 bg-black/90 backdrop-blur-sm z-[999] flex items-center justify-center p-4" @click="viewerImage = null">
                <button @click="viewerImage = null" class="absolute top-4 right-4 text-white hover:text-primary transition-colors">
                    <span class="material-symbols-outlined text-[32px]">close</span>
                </button>
                <div class="max-w-4xl max-h-[90vh] w-full" @click.stop>
                    <img :src="viewerImage" class="w-full h-full object-contain rounded-lg" />
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import SmartScannerModal from '@/components/SmartScannerModal.vue'
import { API_BASE_URL } from '@/config/api'

const authStore = useAuthStore()
const showMismatchModal = ref(false)
const showDamageModal = ref(false)
const showEstimatorModal = ref(false)
const showScheduleModal = ref(false)
const showSlotDetail = ref(false)
const selectedSlot = ref(null)
const toastMsg = ref('')
const isCameraOpen = ref(false)
const damagePhoto = ref(null)
const viewerImage = ref(null)
const loading = ref(false)
const estimatorLoading = ref(false)
const estimatorPlan = ref(null)
const inboundStats = ref({
    arrivedToday: 0,
    inTransit: 0,
    mismatchesFound: 0,
    damageReports: 0,
})

const mismatchForm = reactive({ asnId: '', type: 'Quantity difference', details: '' })
const damageForm = reactive({ asnId: '', count: 0, description: '', hasPhoto: false })
const estimatorForm = reactive({ asnId: '' })
const scheduleForm = reactive({ supplier: '', qty: 0, eta: '' })

const dockSchedule = ref([])
const asns = ref([])
const inboundStatusClassMap = {
    Arrived: 'bg-green-500/10 text-green-500 border-green-500/20',
    Scheduled: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    Receiving: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Completed: 'bg-green-500/10 text-green-500 border-green-500/20',
    InTransit: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    OnHold: 'bg-red-500/10 text-red-500 border-red-500/20',
}
const dockStatusClassMap = {
    Completed: 'bg-green-500/20 text-green-600 dark:text-green-400',
    Active: 'bg-blue-500/20 text-blue-500',
    Scheduled: 'bg-gray-500/20 text-gray-500',
}
const issueStatusClassMap = {
    new: 'bg-blue-500/10 text-blue-600 border-blue-500/20 dark:text-blue-300',
    in_progress: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-300',
    resolved: 'bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-300',
}
const riskClassMap = {
    Low: 'text-green-600 dark:text-green-400',
    Medium: 'text-yellow-600 dark:text-yellow-400',
    High: 'text-red-600 dark:text-red-400',
}
const inboundDisplayStatusClassMap = {
    'Ready for Picking': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    Picking: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Picked: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    Packing: 'bg-green-500/10 text-green-500 border-green-500/20',
    Packed: 'bg-green-500/10 text-green-500 border-green-500/20',
    'QC Passed': 'bg-green-500/10 text-green-500 border-green-500/20',
    'Ready for Dispatch': 'bg-green-500/10 text-green-500 border-green-500/20',
    'On Dock': 'bg-green-500/10 text-green-500 border-green-500/20',
    Dispatched: 'bg-green-500/10 text-green-500 border-green-500/20',
    'Vendor Take-Back': 'bg-red-500/10 text-red-500 border-red-500/20',
}
const PICKING_FLOW_SUBSTATUSES = new Set([
    'AWAITING_PICK',
    'PICKING',
    'PICKED',
    'PACKING',
    'PACKED',
    'QC_PASSED',
    'READY_FOR_DISPATCH',
    'ON_DOCK',
    'DISPATCHED',
])

function getInboundDisplayStatus(status, warehouseSubstatus) {
    const substatus = (warehouseSubstatus || '').toUpperCase()
    const labelMap = {
        AWAITING_PICK: 'Ready for Picking',
        PICKING: 'Picking',
        PICKED: 'Picked',
        PACKING: 'Packing',
        PACKED: 'Packed',
        QC_PASSED: 'QC Passed',
        READY_FOR_DISPATCH: 'Ready for Dispatch',
        ON_DOCK: 'On Dock',
        DISPATCHED: 'Dispatched',
        ON_HOLD: 'Vendor Take-Back',
    }
    return labelMap[substatus] || status
}

function getInboundStatusClass(status, warehouseSubstatus) {
    const displayStatus = getInboundDisplayStatus(status, warehouseSubstatus)
    return inboundDisplayStatusClassMap[displayStatus]
        || inboundStatusClassMap[status]
        || inboundStatusClassMap.Scheduled
}

function isAsnInPickingFlow(asn) {
    return PICKING_FLOW_SUBSTATUSES.has((asn?.warehouseSubstatus || '').toUpperCase())
}

function authHeaders() {
    return {
        Authorization: `Bearer ${authStore.authToken}`,
        'Content-Type': 'application/json',
    }
}

function formatIssueStatus(status) {
    return {
        new: 'Support New',
        in_progress: 'Support Working',
        resolved: 'Support Resolved',
    }[(status || '').toLowerCase()] || 'Support Open'
}

function issueStatusClass(status) {
    return issueStatusClassMap[(status || '').toLowerCase()] || issueStatusClassMap.new
}

function formatDateTime(value) {
    if (!value) return 'TBD'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return 'TBD'
    return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

// Fetch inbound shipments from backend
let inboundRefreshTimer = null
let inboundRefreshPending = false

async function fetchInboundShipments(options = {}) {
    const { silent = false } = options
    if (inboundRefreshPending) return
    inboundRefreshPending = true
    if (!silent) loading.value = true
    try {
        const warehouseId = authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            throw new Error('No warehouse assigned')
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/inbound`,
            { headers: authHeaders() }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to load inbound shipments')
        }
        const data = await res.json()
        inboundStats.value = {
            arrivedToday: data?.stats?.arrived_today || 0,
            inTransit: data?.stats?.in_transit || 0,
            mismatchesFound: data?.stats?.mismatches_found || 0,
            damageReports: data?.stats?.damage_reports || 0,
        }
        asns.value = (data?.shipments || []).map((shipment) => ({
            id: shipment.tracking_code || `ASN-${String(shipment.order_id).slice(0, 6).toUpperCase()}`,
            rawId: shipment.order_id,
            warehouseId,
            supplier: shipment.supplier_name,
            expected: shipment.expected_qty || 0,
            received: shipment.received_qty || 0,
            eta: formatDateTime(shipment.eta || shipment.scheduled_at || shipment.created_at),
            status: shipment.status || 'Scheduled',
            displayStatus: getInboundDisplayStatus(shipment.status, shipment.warehouse_substatus),
            statusClass: getInboundStatusClass(shipment.status, shipment.warehouse_substatus),
            warehouseSubstatus: shipment.warehouse_substatus || null,
            mismatch: Boolean(shipment.has_mismatch),
            mismatchDetails: shipment.mismatch_details || '',
            mismatchType: shipment.mismatch_type || '',
            damaged: Boolean(shipment.has_damage),
            damageCount: shipment.damage_count || 0,
            damageDescription: shipment.damage_description || '',
            issueType: shipment.issue_type || null,
            issueResolutionAction: shipment.issue_resolution_action || null,
            issueResolutionLabel: shipment.issue_resolution_label || null,
            issueStatus: shipment.issue_status || null,
            issueTicketId: shipment.issue_ticket_id || null,
            issueTicketReference: shipment.issue_ticket_reference || null,
            issueBlockingReason: shipment.issue_blocking_reason || '',
            canMoveToPicking: shipment.can_move_to_picking !== false,
            canGenerateTakeBack: Boolean(shipment.can_generate_take_back),
        })).filter((shipment) => !isAsnInPickingFlow(shipment))
        dockSchedule.value = (data?.dock_schedule || []).map((slot) => ({
            ...slot,
            statusClass: dockStatusClassMap[slot.status] || dockStatusClassMap.Scheduled,
        }))
        if (mismatchForm.asnId && !asns.value.some((asn) => asn.id === mismatchForm.asnId)) {
            mismatchForm.asnId = ''
        }
        if (damageForm.asnId && !asns.value.some((asn) => asn.id === damageForm.asnId)) {
            damageForm.asnId = ''
        }
        if (estimatorForm.asnId && !asns.value.some((asn) => asn.id === estimatorForm.asnId)) {
            estimatorForm.asnId = ''
            estimatorPlan.value = null
        }
    } catch (error) {
        console.error('Error fetching inbound shipments:', error)
        showToast(error.message || 'Unable to load inbound data from server')
    } finally {
        if (!silent) loading.value = false
        inboundRefreshPending = false
    }
}

function refreshInboundIfVisible() {
    if (document.visibilityState === 'visible') {
        fetchInboundShipments({ silent: true })
    }
}

onMounted(() => {
    fetchInboundShipments()
    window.addEventListener('focus', refreshInboundIfVisible)
    document.addEventListener('visibilitychange', refreshInboundIfVisible)
    inboundRefreshTimer = window.setInterval(() => {
        refreshInboundIfVisible()
    }, 15000)
})

onUnmounted(() => {
    window.removeEventListener('focus', refreshInboundIfVisible)
    document.removeEventListener('visibilitychange', refreshInboundIfVisible)
    if (inboundRefreshTimer) {
        window.clearInterval(inboundRefreshTimer)
        inboundRefreshTimer = null
    }
})

const arrivedCount = computed(() => inboundStats.value.arrivedToday)
const inTransitCount = computed(() => inboundStats.value.inTransit)
const mismatchCount = computed(() => inboundStats.value.mismatchesFound)
const damageCount = computed(() => inboundStats.value.damageReports)
const selectedEstimatorAsn = computed(() => asns.value.find((asn) => asn.id === estimatorForm.asnId) || null)
const estimatorPrimaryActionLabel = computed(() => {
    const selectedAsn = selectedEstimatorAsn.value
    if (!selectedAsn) return 'Close'
    if (selectedAsn.status === 'Receiving') return 'Complete & Move to Picking'
    if (selectedAsn.status === 'Arrived') return 'Start Receiving'
    return 'Schedule Delivery'
})

function showToast(msg) {
    toastMsg.value = msg
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

async function fetchInboundReceivePlan() {
    const selectedAsn = asns.value.find((asn) => asn.id === estimatorForm.asnId)
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!selectedAsn?.rawId || !warehouseId) {
        estimatorPlan.value = null
        return
    }

    estimatorLoading.value = true
    try {
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${selectedAsn.rawId}/ai-receive-plan`,
            { headers: authHeaders() }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to generate AI receive plan')
        }

        const data = await res.json()
        estimatorPlan.value = {
            asn: {
                id: data?.asn?.id || selectedAsn.id,
                supplier: data?.asn?.supplier || selectedAsn.supplier,
                status: data?.asn?.status || selectedAsn.status,
            },
            shipmentType: data?.asn?.shipment_type || 'Inbound transfer',
            materialProfile: data?.asn?.material_profile || 'General cargo',
            expectedUnits: data?.asn?.expected_units || selectedAsn.expected || 0,
            recurring: Boolean(data?.asn?.recurring),
            confidence: data?.confidence || 0,
            suggestedDock: data?.suggested_dock || 'Dock 1',
            workers: data?.workers || 2,
            totalMinutes: data?.total_minutes || 0,
            riskLevel: data?.risk_level || 'Low',
            riskClass: riskClassMap[data?.risk_level] || riskClassMap.Low,
            pallets: data?.pallet_load || 1,
            queueMinutes: data?.queue_minutes || 0,
            activeDockCount: data?.active_dock_count || 0,
            stagingZone: data?.staging_zone || 'Inbound Buffer A',
            nextAction: data?.next_action || 'Review this inbound before scheduling dock work.',
            reason: data?.reason || 'AI reasoning unavailable.',
            watchouts: Array.isArray(data?.watchouts) ? data.watchouts : [],
            summary: data?.summary || '',
            generatedBy: data?.generated_by || 'gemini',
        }
    } catch (error) {
        console.error(error)
        estimatorPlan.value = null
        showToast(error.message || 'Failed to generate AI receive plan')
    } finally {
        estimatorLoading.value = false
    }
}

async function openInboundEstimator(asnId = '') {
    if (!asns.value.length) {
        showToast('No inbound ASN available for receive planning yet')
        return
    }
    estimatorForm.asnId = asnId || estimatorForm.asnId || asns.value.find((item) => item.status !== 'Completed')?.id || asns.value[0].id
    showEstimatorModal.value = true
    await fetchInboundReceivePlan()
}

async function handleEstimatorPrimaryAction() {
    const selectedAsn = selectedEstimatorAsn.value
    if (!selectedAsn) {
        showEstimatorModal.value = false
        return
    }
    if (selectedAsn.status === 'Receiving') {
        await completeReceiving(selectedAsn)
        return
    }
    if (selectedAsn.status === 'Arrived') {
        startReceiving(selectedAsn)
        return
    }
    openScheduleFromEstimator()
}

function startReceiving(asn) {
    asn.status = 'Receiving'
    asn.displayStatus = 'Receiving'
    asn.statusClass = inboundStatusClassMap.Receiving
    showToast(`Started receiving ${asn.id}`)
}

async function completeReceiving(asn) {
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot complete receiving')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/receive-inbound`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to complete receiving')
        }
        showToast(`${asn.id} received — moved to picking queue`)
        await fetchInboundShipments()
        showEstimatorModal.value = false
    } catch (e) {
        console.error(e)
        showToast(e.message || 'Failed to complete receiving')
    }
}

function canStartInboundProcessing(asn) {
    return asn.status === 'Arrived' && (asn.canMoveToPicking || (!asn.mismatch && !asn.damaged))
}

function canCompleteInboundProcessing(asn) {
    return asn.status === 'Receiving' && (asn.canMoveToPicking || (!asn.mismatch && !asn.damaged))
}

function showIssueHoldState(asn) {
    return (asn.mismatch || asn.damaged) && !asn.canMoveToPicking && !asn.canGenerateTakeBack
}

function showTakeBackAction(asn) {
    return asn.canGenerateTakeBack && asn.warehouseSubstatus !== 'ON_HOLD'
}

async function generateTakeBack(asn) {
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot generate take-back')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/generate-take-back`,
            {
                method: 'POST',
                headers: authHeaders(),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to generate vendor take-back')
        }
        showToast(`Vendor take-back generated for ${asn.id}`)
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to generate vendor take-back')
    }
}

async function markArrived(asn) {
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        if (!warehouseId) {
            showToast('No warehouse assigned - cannot mark arrival')
            return
        }
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/mark-arrived`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json',
                },
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to mark arrival')
        }
        showToast(`${asn.id} marked as arrived`)
        await fetchInboundShipments()
    } catch (e) {
        console.error(e)
        showToast(e.message || 'Failed to mark arrival')
    }
}

async function submitMismatch() {
    const asn = asns.value.find(a => a.id === mismatchForm.asnId)
    if (!asn?.rawId) {
        showToast('Select a valid ASN first')
        return
    }
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/report-mismatch`,
            {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    mismatch_type: mismatchForm.type,
                    details: mismatchForm.details || null,
                }),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to report mismatch')
        }
        showMismatchModal.value = false
        mismatchForm.details = ''
        showToast(`Mismatch flagged for ${mismatchForm.asnId}`)
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to report mismatch')
    }
}

async function submitDamage() {
    const asn = asns.value.find(a => a.id === damageForm.asnId)
    if (!asn?.rawId) {
        showToast('Select a valid ASN first')
        return
    }
    if (!damageForm.count || damageForm.count < 1) {
        showToast('Enter damaged item count')
        return
    }
    if (!damageForm.description.trim()) {
        showToast('Enter damage description')
        return
    }
    try {
        const warehouseId = asn.warehouseId || authStore.currentUser?.warehouse_id
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/orders/${asn.rawId}/report-damage`,
            {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    damaged_count: damageForm.count,
                    description: damageForm.description.trim(),
                    photo_url: damagePhoto.value || null,
                }),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to report damage')
        }
        showDamageModal.value = false
        damageForm.description = ''
        damageForm.count = 0
        damageForm.hasPhoto = false
        damagePhoto.value = null
        showToast(`Damage report submitted for ${damageForm.asnId}`)
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to report damage')
    }
}

function openDamageCamera() {
    isCameraOpen.value = true
}

function handlePhotoCapture(photoData) {
    damagePhoto.value = typeof photoData === 'string' ? photoData : (photoData?.preview || null)
    damageForm.hasPhoto = true
}

function retakeDamagePhoto() {
    damagePhoto.value = null
    damageForm.hasPhoto = false
    isCameraOpen.value = true
}

function viewImage(imageSrc) {
    viewerImage.value = imageSrc
}

function openScheduleFromEstimator() {
    const selectedAsn = asns.value.find((asn) => asn.id === estimatorForm.asnId)
    if (selectedAsn) {
        scheduleForm.supplier = selectedAsn.supplier
        scheduleForm.qty = selectedAsn.expected || 0
    }
    showEstimatorModal.value = false
    showScheduleModal.value = true
}

async function scheduleDelivery() {
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!warehouseId) {
        showToast('No warehouse assigned')
        return
    }
    const scheduledAt = scheduleForm.eta ? new Date(scheduleForm.eta) : null
    if (!scheduleForm.supplier.trim()) {
        showToast('Enter supplier name')
        return
    }
    if (!scheduleForm.qty || scheduleForm.qty < 1) {
        showToast('Enter expected quantity')
        return
    }
    if (!scheduledAt || Number.isNaN(scheduledAt.getTime())) {
        showToast('Choose a valid delivery time')
        return
    }
    try {
        const res = await fetch(
            `${API_BASE_URL}/api/v1/warehouses/${warehouseId}/operations/inbound/schedule`,
            {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    supplier_name: scheduleForm.supplier.trim(),
                    expected_qty: scheduleForm.qty,
                    scheduled_at: scheduledAt.toISOString(),
                }),
            }
        )
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}))
            throw new Error(errorData.detail || 'Failed to schedule delivery')
        }
        showScheduleModal.value = false
        scheduleForm.supplier = ''
        scheduleForm.qty = 0
        scheduleForm.eta = ''
        showToast('Delivery scheduled successfully')
        await fetchInboundShipments()
    } catch (error) {
        console.error(error)
        showToast(error.message || 'Failed to schedule delivery')
    }
}
</script>
