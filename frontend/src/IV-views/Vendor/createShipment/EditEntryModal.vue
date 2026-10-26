<template>
    <!-- Custom Edit Modal with adjustable width -->
    <div v-if="showEditModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showEditModal = false"></div>
        <div
            class="relative w-full max-w-5xl bg-white dark:bg-card-dark rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            <div
                class="px-6 py-4 border-b border-gray-200 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">Edit Shipment Entry</h3>
                <button @click="showEditModal = false"
                    class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-white">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>

            <div class="p-6 overflow-y-auto">
                <div v-if="editingEntry" class="space-y-6">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <!-- Read-only Info -->
                        <div
                            class="col-span-1 md:col-span-2 bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl flex gap-6 border border-blue-100 dark:border-blue-500/20">
                            <div>
                                <div
                                    class="text-xs text-blue-600 dark:text-blue-400 font-bold uppercase tracking-wider mb-1">
                                    Order ID</div>
                                <div class="text-lg font-bold text-gray-900 dark:text-white">{{
                                    editingEntry.orderId }}</div>
                            </div>
                            <div>
                                <div
                                    class="text-xs text-blue-600 dark:text-blue-400 font-bold uppercase tracking-wider mb-1">
                                    Created</div>
                                <div class="text-lg font-bold text-gray-900 dark:text-white">{{
                                    editingEntry.date }}</div>
                            </div>
                        </div>

                        <!-- Form Fields -->
                        <div class="space-y-4">
                            <h4
                                class="text-sm font-bold text-gray-900 dark:text-warning border-b border-gray-100 dark:border-white/5 pb-2">
                                Basic Details</h4>
                            <div><label class="block text-xs font-medium text-gray-500 mb-1.5">Category</label>
                                <select v-model="editingEntry.category"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Commercial</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Palletized</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Bulk</option>
                                </select>
                            </div>
                            <div><label
                                    class="block text-xs font-medium text-gray-500 mb-1.5">Description</label>
                                <input v-model="editingEntry.description"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div><label class="block text-xs font-medium text-gray-500 mb-1.5">HSN
                                        Code</label>
                                    <input v-model="editingEntry.hsnCode"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label
                                        class="block text-xs font-medium text-gray-500 mb-1.5">Priority</label>
                                    <select v-model="editingEntry.priority"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Standard</option>
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Express</option>
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Urgent</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-4">
                            <h4
                                class="text-sm font-bold text-gray-900 dark:text-warning border-b border-gray-100 dark:border-white/5 pb-2">
                                Cargo Specs</h4>
                            <div class="grid grid-cols-2 gap-4">
                                <div><label
                                        class="block text-xs font-medium text-gray-500 mb-1.5">Pallets</label>
                                    <input v-model.number="editingEntry.palletCount" type="number"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label class="block text-xs font-medium text-gray-500 mb-1.5">Weight
                                        (kg)</label>
                                    <input v-model.number="editingEntry.weight" type="number"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label class="block text-xs font-medium text-gray-500 mb-1.5">Value
                                        (₹)</label>
                                    <input v-model.number="editingEntry.declaredValue" type="number"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label
                                        class="block text-xs font-medium text-gray-500 mb-1.5">Insurance</label>
                                    <select v-model="editingEntry.insuranceRequired"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                        <option value="No" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">No</option>
                                        <option value="Yes" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Yes</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-4">
                            <h4
                                class="text-sm font-bold text-gray-900 dark:text-warning border-b border-gray-100 dark:border-white/5 pb-2">
                                Route Details</h4>
                            <div><label class="block text-xs font-medium text-gray-500 mb-1.5">Pickup
                                    Hub</label>
                                <select v-model="editingEntry.pickupHub"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                    <option value="" disabled class="bg-white dark:bg-gray-800 text-gray-400">Select a warehouse...</option>
                                    <option v-for="w in store.warehouses" :key="w.id" :value="w.name"
                                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                                        {{ w.name }}
                                    </option>
                                </select>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div><label class="block text-xs font-medium text-gray-500 mb-1.5">City</label>
                                    <input v-model="editingEntry.destinationCity"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label
                                        class="block text-xs font-medium text-gray-500 mb-1.5">Pincode</label>
                                    <input v-model="editingEntry.pincode"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                            </div>
                        </div>

                        <div class="space-y-4">
                            <h4
                                class="text-sm font-bold text-gray-900 dark:text-warning border-b border-gray-100 dark:border-white/5 pb-2">
                                Services & Payment</h4>
                            <div class="grid grid-cols-2 gap-4">
                                <div><label class="block text-xs font-medium text-gray-500 mb-1.5">Pickup
                                        Date</label>
                                    <input v-model="editingEntry.pickupDate" type="date"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                </div>
                                <div><label
                                        class="block text-xs font-medium text-gray-500 mb-1.5">Payment</label>
                                    <select v-model="editingEntry.paymentMode"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Invoice</option>
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">COD</option>
                                        <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Full Payment</option>
                                    </select>
                                </div>
                            </div>
                            <div class="flex flex-wrap gap-4 pt-2">
                                <label
                                    class="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-blue-500 transition-colors">
                                    <input type="checkbox" v-model="editingEntry.packingRequired"
                                        class="rounded text-blue-600 focus:ring-offset-0">
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Packing
                                        Service</span>
                                </label>
                                <div
                                    class="flex items-center gap-2 p-3 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                                    <label class="flex items-center gap-2 cursor-pointer">
                                        <input type="checkbox" v-model="editingEntry.laborRequired"
                                            class="rounded text-purple-600 focus:ring-offset-0">
                                        <span
                                            class="text-sm font-medium text-gray-700 dark:text-gray-300">Labor</span>
                                    </label>
                                    <div v-if="editingEntry.laborRequired"
                                        class="flex items-center gap-2 ml-2 pl-2 border-l border-gray-300 dark:border-white/10">
                                        <button
                                            @click="editingEntry.laborCount = Math.max(1, (editingEntry.laborCount || 1) - 1)"
                                            class="w-6 h-6 rounded bg-gray-200 dark:bg-white/10 flex items-center justify-center hover:bg-gray-300">-</button>
                                        <span
                                            class="text-sm font-bold w-4 text-center text-gray-900 dark:text-white">{{
                                                editingEntry.laborCount }}</span>
                                        <button
                                            @click="editingEntry.laborCount = Math.min(10, (editingEntry.laborCount || 1) + 1)"
                                            class="w-6 h-6 rounded bg-gray-200 dark:bg-white/10 flex items-center justify-center hover:bg-gray-300">+</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="p-6 border-t border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 flex gap-3 justify-end">
                <button @click="showEditModal = false; editingEntry = null"
                    class="px-6 py-2.5 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/10 text-gray-700 dark:text-gray-300 font-bold rounded-xl text-sm hover:bg-gray-50 dark:hover:bg-white/10 transition-colors">Cancel</button>
                <button @click="saveEdit"
                    class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition-colors shadow-lg shadow-blue-500/30">Save
                    Changes</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const { editingEntry, saveEdit, showEditModal, store } = inject(createShipmentPageKey)
</script>
