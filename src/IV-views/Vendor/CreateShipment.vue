<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Shipment Management</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Create new bookings or upload bulk shipments
                </p>
            </div>
        </div>

        <!-- Tabs -->
        <div class="flex gap-2 border-b border-gray-200 dark:border-white/10">
            <button @click="activeTab = 'new'"
                :class="activeTab === 'new' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">New Booking</button>
            <button @click="activeTab = 'bulk'"
                :class="activeTab === 'bulk' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">Bulk Editor</button>
            <button @click="activeTab = 'myshipments'"
                :class="activeTab === 'myshipments' ? 'border-blue-500 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
                class="px-4 py-2 border-b-2 font-medium text-sm transition-colors">My Shipments <span
                    class="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/20 text-blue-500">{{
                        store.shipments.length }}</span></button>
        </div>

        <!-- NEW BOOKING TAB -->
        <div v-if="activeTab === 'new'" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 space-y-6">
                    <!-- Category Selection -->
                    <div class="glass-panel p-6 rounded-xl">
                        <h3 class="text-base font-bold text-gray-900 dark:text-white mb-4">Shipment Category *</h3>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <label v-for="cat in categories" :key="cat.value"
                                :class="form.category === cat.value ? 'border-blue-500 bg-blue-500/10' : 'border-gray-200 dark:border-white/10 hover:border-blue-400'"
                                class="flex flex-col items-center p-4 rounded-xl border cursor-pointer transition-all">
                                <input type="radio" :value="cat.value" v-model="form.category" class="sr-only">
                                <span class="material-symbols-outlined text-3xl mb-2"
                                    :class="form.category === cat.value ? 'text-blue-500' : 'text-gray-400 dark:text-gray-500'">{{
                                        cat.icon }}</span>
                                <span class="text-sm font-medium"
                                    :class="form.category === cat.value ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'">{{
                                        cat.label }}</span>
                                <span class="text-xs text-gray-500 mt-1">{{ cat.desc }}</span>
                            </label>
                        </div>
                    </div>

                    <!-- Cargo Details -->
                    <div class="glass-panel p-6 rounded-xl space-y-4">
                        <h3
                            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
                            1. Cargo Details</h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Goods Description
                                    *</label>
                                <input v-model="form.description" type="text" placeholder="e.g. Electronic components"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div v-if="form.category !== 'b2c'">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">HSN/SAC
                                    Code</label>
                                <input v-model="form.hsnCode" type="text" placeholder="e.g. 8471"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div v-if="form.category === 'palletized'">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pallet Count
                                    *</label>
                                <input v-model.number="form.palletCount" @input="recalculate" type="number" min="1"
                                    placeholder="e.g. 12"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Total Weight (kg)
                                    *</label>
                                <input v-model.number="form.weight" @input="recalculate" type="number" min="1"
                                    placeholder="e.g. 4500"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Estimated Volume
                                    (m³)</label>
                                <input v-model.number="form.volume" type="number" min="0" step="0.01"
                                    placeholder="e.g. 12.5"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Declared Value
                                    (₹)</label>
                                <input v-model.number="form.declaredValue" type="number" placeholder="e.g. 50000"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Insurance
                                    Required</label>
                                <select v-model="form.insuranceRequired"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                    <option value="no" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">No</option>
                                    <option value="yes" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Yes ({{ rates.insurancePct ?? 3 }}% of value)</option>
                                </select>
                            </div>
                            <div class="sm:col-span-2">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Special
                                    Handling</label>
                                <div class="flex flex-wrap gap-3">
                                    <label v-for="h in handlingOptions" :key="h"
                                        class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors"
                                        :class="form.handling.includes(h) ? 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400'">
                                        <input type="checkbox" :value="h" v-model="form.handling" class="sr-only">
                                        <span class="text-sm">{{ h }}</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Route & Schedule -->
                    <div class="glass-panel p-6 rounded-xl space-y-4">
                        <h3
                            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
                            2. Route & Schedule</h3>

                        <!-- Pickup Toggle -->
                        <div class="flex gap-4 p-1 bg-gray-100 dark:bg-white/5 rounded-lg w-max">
                            <button @click="form.pickupType = 'hub'"
                                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
                                :class="form.pickupType === 'hub' ? 'bg-white dark:bg-gray-700 shadow text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
                                Hub Pickup
                            </button>
                            <button @click="form.pickupType = 'doorstep'"
                                class="px-3 py-1.5 text-sm font-medium rounded-md transition-all"
                                :class="form.pickupType === 'doorstep' ? 'bg-white dark:bg-gray-700 shadow text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'">
                                Shop/Doorstep Pickup
                            </button>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div v-if="form.pickupType === 'hub'">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                                    Drop-off Hub *
                                    <span class="text-gray-400 font-normal normal-case">(you bring goods here)</span>
                                </label>
                                <select v-model="form.pickupHub"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                    <option value="" disabled class="bg-white dark:bg-gray-800 text-gray-400">Select a warehouse...</option>
                                    <option v-for="w in store.warehouses" :key="w.id" :value="w.name"
                                        class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                                        {{ w.name }}
                                    </option>
                                </select>
                            </div>
                            <div v-else class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div class="sm:col-span-2">
                                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Address *</label>
                                    <button type="button" @click="openMapPicker('pickup')"
                                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-left flex items-center justify-between gap-2 hover:border-blue-500 transition-colors focus:outline-none focus:border-blue-500"
                                        :class="form.pickupAddress ? 'text-gray-900 dark:text-white' : 'text-gray-400'">
                                        <span class="truncate">{{ form.pickupAddress || 'Select your pickup location on map...' }}</span>
                                        <span class="material-symbols-outlined text-[20px] text-gray-400 flex-shrink-0">map</span>
                                    </button>
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup City
                                        *</label>
                                    <input v-model="form.pickupCity" type="text" placeholder="City name"
                                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Pincode
                                        *</label>
                                    <input v-model="form.pickupPincode" type="text" placeholder="e.g. 400001"
                                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                </div>
                            </div>

                            <div v-if="form.category === 'b2c'">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Customer Name
                                    *</label>
                                <input v-model="form.customerName" type="text" placeholder="John Doe"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div v-if="form.category === 'b2c'">
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Customer Phone
                                    *</label>
                                <input v-model="form.customerPhone" type="tel" placeholder="+91 0000000000"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination Address *</label>
                                <button type="button" @click="openMapPicker('destination')"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-left flex items-center justify-between gap-2 hover:border-blue-500 transition-colors focus:outline-none focus:border-blue-500"
                                    :class="form.destination ? 'text-gray-900 dark:text-white' : 'text-gray-400'">
                                    <span class="truncate">{{ form.destination || 'Select destination on map...' }}</span>
                                    <span class="material-symbols-outlined text-[20px] text-gray-400 flex-shrink-0">map</span>
                                </button>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Destination City
                                    *</label>
                                <input v-model="form.destinationCity" type="text" placeholder="City name"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pincode *</label>
                                <input v-model="form.pincode" type="text" placeholder="e.g. 400001"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Date
                                    *</label>
                                <input v-model="form.pickupDate" type="date"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Pickup Time
                                    Window</label>
                                <select v-model="form.timeWindow"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">08:00 AM - 12:00 PM</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">12:00 PM - 04:00 PM</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">04:00 PM - 08:00 PM</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Night (08 PM - 06 AM)</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Expected Delivery
                                    Date</label>
                                <input v-model="form.deliveryDate" type="date"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Priority</label>
                                <select v-model="form.priority"
                                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Standard</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Express</option>
                                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Urgent</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Service Options -->
                    <div class="glass-panel p-6 rounded-xl space-y-4">
                        <h3
                            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
                            3. Service Options</h3>
                        <div class="flex flex-col sm:flex-row gap-4">
                            <label
                                class="flex-1 flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors"
                                :class="form.packingRequired ? 'border-blue-500 bg-blue-500/5' : 'border-gray-200 dark:border-white/10 hover:border-blue-400'">
                                <input type="checkbox" v-model="form.packingRequired" @change="recalculate"
                                    class="sr-only">
                                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                                    :class="form.packingRequired ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-400'">
                                    <span class="material-symbols-outlined text-[20px]">inventory</span>
                                </div>
                                <div>
                                    <div class="font-medium text-sm text-gray-900 dark:text-white">Packing Service</div>
                                    <div class="text-xs text-gray-500">+₹{{ (rates.customerPackingFee ?? 200).toLocaleString() }} flat fee</div>
                                </div>
                            </label>
                            <label
                                class="flex-1 flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors"
                                :class="form.laborRequired ? 'border-purple-500 bg-purple-500/5' : 'border-gray-200 dark:border-white/10 hover:border-purple-400'">
                                <input type="checkbox" v-model="form.laborRequired" @change="recalculate"
                                    class="sr-only">
                                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                                    :class="form.laborRequired ? 'bg-purple-500 text-white' : 'bg-gray-100 dark:bg-white/5 text-gray-400'">
                                    <span class="material-symbols-outlined text-[20px]">groups</span>
                                </div>
                                <div>
                                    <div class="font-medium text-sm text-gray-900 dark:text-white">Labor Helpers</div>
                                    <div class="text-xs text-gray-500">+₹{{ (rates.customerLaborRate ?? 250).toLocaleString() }} per helper</div>
                                </div>
                            </label>
                        </div>
                        <div v-if="form.laborRequired" class="flex items-center gap-3">
                            <label class="text-xs text-gray-500 dark:text-gray-400">Number of helpers:</label>
                            <div class="flex items-center gap-2">
                                <button @click="form.laborCount = Math.max(1, form.laborCount - 1); recalculate()"
                                    class="w-7 h-7 rounded-full bg-gray-100 dark:bg-white/10 hover:bg-blue-500/20 text-gray-700 dark:text-white flex items-center justify-center font-bold transition-colors">-</button>
                                <span class="w-8 text-center font-bold text-gray-900 dark:text-white">{{ form.laborCount
                                    }}</span>
                                <button @click="form.laborCount = Math.min(8, form.laborCount + 1); recalculate()"
                                    class="w-7 h-7 rounded-full bg-gray-100 dark:bg-white/10 hover:bg-blue-500/20 text-gray-700 dark:text-white flex items-center justify-center font-bold transition-colors">+</button>
                            </div>
                        </div>
                    </div>

                    <!-- Payment -->
                    <div class="glass-panel p-6 rounded-xl space-y-4">
                        <h3
                            class="text-base font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-white/10 pb-2">
                            4. Payment Mode</h3>
                        <div class="flex flex-wrap gap-3">
                            <label v-for="mode in ['Invoice', 'COD', 'Full Payment']" :key="mode"
                                class="flex items-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition-colors"
                                :class="form.paymentMode === mode ? 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:border-green-400'">
                                <input type="radio" :value="mode" v-model="form.paymentMode" class="sr-only">
                                <span class="material-symbols-outlined text-[18px]">{{
                                    mode === 'COD' ? 'payments' : mode === 'Invoice' ? 'receipt' : 'credit_card'
                                    }}</span>
                                <span class="text-sm font-medium">{{ mode }}</span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Live Quotation Panel -->
                <div>
                    <div class="glass-panel p-5 rounded-xl lg:sticky lg:top-[5.5rem] z-10">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-400 text-[18px]">calculate</span>
                            Live Quotation
                        </h3>
                        <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20">
                            <span class="material-symbols-outlined text-blue-500 text-sm">route</span>
                            <span class="text-xs font-bold text-blue-700 dark:text-blue-400">{{ distanceKm }} km</span>
                            <span class="text-xs text-gray-500">(road distance · ₹{{ rates.perKmRate ?? 12 }}/km)</span>
                            <span v-if="distanceLoading" class="ml-auto text-xs text-gray-400 animate-pulse">calculating...</span>
                        </div>
                        <div class="space-y-2 mb-4">
                            <div class="flex justify-between text-xs"><span class="text-gray-500">Base
                                    Transport</span><span class="text-gray-900 dark:text-white">₹{{
                                        quote.baseTransport.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-xs"><span class="text-gray-500">Labor
                                    Charges</span><span class="text-gray-900 dark:text-white">₹{{
                                        quote.laborCharges.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-xs"><span class="text-gray-500">Packing
                                    Fee</span><span class="text-gray-900 dark:text-white">₹{{
                                        quote.packingFee.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-xs"><span class="text-gray-500">Insurance</span><span
                                    class="text-gray-900 dark:text-white">₹{{ quote.insurance.toLocaleString() }}</span>
                            </div>
                            <div
                                class="border-t border-gray-200 dark:border-white/10 pt-2 flex justify-between font-bold">
                                <span class="text-gray-700 dark:text-gray-200 text-sm">Total Estimate</span><span
                                    class="text-blue-500 text-lg">₹{{ quote.total.toLocaleString() }}</span>
                            </div>
                        </div>
                        <div v-if="!formValid" class="mb-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                            <div class="text-xs text-yellow-600 dark:text-yellow-400 font-medium">Required fields
                                missing</div>
                            <ul class="text-xs text-yellow-500 mt-1 list-disc list-inside">
                                <li v-for="e in validationErrors" :key="e">{{ e }}</li>
                            </ul>
                        </div>
                        <button @click="submitShipment" :disabled="!formValid"
                            class="w-full py-3 rounded-xl font-bold text-sm transition-all"
                            :class="formValid ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg' : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">Confirm
                            Shipment</button>
                        <button @click="saveDraft"
                            class="mt-2 w-full py-2.5 rounded-xl border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 text-sm font-medium transition-colors">Save
                            Draft</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- BULK EDITOR TAB -->
        <div v-if="activeTab === 'bulk'" class="space-y-6">
            <!-- Template Downloads -->
            <div class="glass-panel p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Download Templates</h3>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <button v-for="cat in categories" :key="cat.value" @click="downloadTemplate(cat.value)"
                        class="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-white/10 hover:border-blue-500 hover:bg-blue-500/5 transition-all">
                        <span class="material-symbols-outlined text-blue-500 text-2xl">{{ cat.icon }}</span>
                        <div class="flex-1 text-left">
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ cat.label }}</div>
                            <div class="text-xs text-gray-500">{{ cat.desc }}</div>
                        </div>
                        <span class="material-symbols-outlined text-gray-400">download</span>
                    </button>
                </div>
            </div>

            <!-- Sample Data Tables -->
            <div class="glass-panel p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Sample Data Preview</h3>
                <div class="space-y-4">
                    <div v-for="cat in categories" :key="cat.value"
                        class="border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden">
                        <div @click="toggleSample(cat.value)"
                            class="flex items-center justify-between p-4 bg-gray-50 dark:bg-white/5 cursor-pointer hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                            <div class="flex items-center gap-3">
                                <span class="material-symbols-outlined text-blue-500 text-xl">{{ cat.icon }}</span>
                                <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ cat.label }} Templates (5
                                    rows)</h4>
                            </div>
                            <span class="material-symbols-outlined text-gray-500 transition-transform duration-300"
                                :class="expandedSample === cat.value ? 'rotate-180' : ''">expand_more</span>
                        </div>

                        <div v-show="expandedSample === cat.value"
                            class="border-t border-gray-200 dark:border-white/10">
                            <div class="overflow-x-auto">
                                <table class="w-full text-xs border-collapse">
                                    <thead class="bg-gray-50 dark:bg-white/5">
                                        <tr>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                Order ID</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                Description</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                Pallets</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                Weight (kg)</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                From</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                To</th>
                                            <th
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-left font-medium text-gray-600 dark:text-gray-400">
                                                Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="i in 5" :key="i" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                                {{ cat.value.toUpperCase().substring(0, 3) }}_{{
                                                    String(i).padStart(3, '0') }}</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                                Sample {{ cat.label }} cargo {{ i }}</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                                {{ 5 + i }}</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white">
                                                {{ (200 + i * 50).toLocaleString() }}</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                                Mumbai Hub</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                                Delhi</td>
                                            <td
                                                class="px-3 py-2 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400">
                                                {{ new Date(2026, 2, 1 + i).toLocaleDateString('en-GB', {
                                                    day:
                                                        '2-digit', month: 'short'
                                                }) }}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm">Category Comparison (Bar)</h3>
                    <div class="h-64 w-full relative">
                        <BarChart :data="barChartData" :options="barChartOptions" />
                    </div>
                </div>
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-sm">Category Distribution (Doughnut)
                    </h3>
                    <div class="h-64 w-full relative">
                        <DoughnutChart :data="doughnutChartData" :options="doughnutChartOptions" />
                    </div>
                </div>
            </div>

            <!-- Upload History -->
            <div class="glass-panel p-6 rounded-xl">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-gray-900 dark:text-white">Upload History</h3>
                    <button @click="showUploadModal = true"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">upload_file</span>
                        New Upload
                    </button>
                </div>
                <div class="space-y-2">
                    <div v-for="upload in bulkUploads" :key="upload.id"
                        class="border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden">
                        <!-- Upload Row -->
                        <div @click="toggleUpload(upload.id)"
                            class="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer">
                            <span class="material-symbols-outlined text-gray-400"
                                :class="expandedUpload === upload.id ? 'rotate-90' : ''">chevron_right</span>
                            <div class="flex-1 grid grid-cols-5 items-center gap-4 text-sm">
                                <div>
                                    <div class="font-medium text-gray-900 dark:text-white">{{ upload.fileName }}</div>
                                    <div class="text-xs text-gray-500">{{ upload.date }}</div>
                                </div>
                                <div><span class="px-2 py-1 rounded text-xs font-bold"
                                        :class="upload.type === 'CSV' ? 'bg-green-100 text-green-700' : upload.type === 'XLSX' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'">{{
                                            upload.type }}</span></div>
                                <div class="text-gray-600 dark:text-gray-400">{{ upload.size }}</div>
                                <div class="text-gray-900 dark:text-white">{{ upload.entries.length }} entries</div>
                                <div class="text-blue-500 font-medium">₹{{
                                    upload.entries.reduce((s, e) => s + e.quotedPrice, 0).toLocaleString()}}</div>
                            </div>
                            <button @click.stop="deleteUpload(upload.id)"
                                class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors">
                                <span class="material-symbols-outlined text-[20px]">delete</span>
                            </button>
                        </div>
                        <!-- Expanded Entries -->
                        <div v-if="expandedUpload === upload.id" class="bg-gray-50 dark:bg-white/5 p-4 space-y-2">
                            <div v-for="entry in upload.entries" :key="entry.orderId"
                                class="bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
                                <!-- Entry Row -->
                                <div @click="toggleEntry(entry.orderId)"
                                    class="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer">
                                    <span class="material-symbols-outlined text-gray-400 text-[18px]"
                                        :class="expandedEntry === entry.orderId ? 'rotate-90' : ''">chevron_right</span>
                                    <div class="flex-1 grid grid-cols-6 items-center gap-3 text-xs">
                                        <div class="font-bold text-blue-600 dark:text-blue-400">{{ entry.orderId }}
                                        </div>
                                        <div class="col-span-2 text-gray-900 dark:text-white">{{ entry.description }}
                                        </div>
                                        <div class="text-gray-600 dark:text-gray-400">{{ entry.palletCount }} pallets
                                        </div>
                                        <div class="text-gray-600 dark:text-gray-400">{{ entry.weight }} kg</div>
                                        <div class="text-blue-500 font-bold">₹{{ entry.quotedPrice.toLocaleString() }}
                                        </div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button @click.stop="openEditModal(entry)"
                                            class="p-1.5 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400"><span
                                                class="material-symbols-outlined text-[18px]">edit</span></button>
                                        <button @click.stop="deleteEntry(upload.id, entry.orderId)"
                                            class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"><span
                                                class="material-symbols-outlined text-[18px]">delete</span></button>
                                    </div>
                                </div>
                                <!-- Expanded Entry Details -->
                                <div v-if="expandedEntry === entry.orderId"
                                    class="bg-gray-50 dark:bg-black/20 p-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs border-t border-gray-200 dark:border-white/10">
                                    <div><span class="text-gray-500">Category:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.category
                                            }}</span></div>
                                    <div><span class="text-gray-500">HSN Code:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.hsnCode || 'N/A'
                                            }}</span></div>
                                    <div><span class="text-gray-500">Value:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">₹{{
                                                entry.declaredValue.toLocaleString() }}</span></div>
                                    <div><span class="text-gray-500">Insurance:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.insuranceRequired
                                            }}</span></div>
                                    <div><span class="text-gray-500">Pickup Hub:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.pickupHub
                                            }}</span></div>
                                    <div><span class="text-gray-500">Destination:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.destinationCity
                                            }}</span></div>
                                    <div><span class="text-gray-500">Pincode:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.pincode }}</span>
                                    </div>
                                    <div><span class="text-gray-500">Pickup Date:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.pickupDate
                                            }}</span></div>
                                    <div><span class="text-gray-500">Priority:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.priority
                                            }}</span></div>
                                    <div><span class="text-gray-500">Payment:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.paymentMode
                                            }}</span></div>
                                    <div><span class="text-gray-500">Packing:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.packingRequired ?
                                                'Yes' : 'No' }}</span></div>
                                    <div><span class="text-gray-500">Labor:</span> <span
                                            class="text-gray-900 dark:text-white font-medium">{{ entry.laborRequired ?
                                                entry.laborCount + ' helpers' : 'No' }}</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- MY SHIPMENTS TAB -->
        <div v-if="activeTab === 'myshipments'" class="space-y-6">
            <!-- Filters -->
            <div class="glass-panel p-4 rounded-xl flex flex-col sm:flex-row gap-3 items-center">
                <div class="flex-1 relative">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input v-model="shipmentSearch" type="text" placeholder="Search by ID, destination, description..."
                        class="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                </div>
                <select v-model="shipmentStatusFilter"
                    class="px-4 py-2.5 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Status</option>
                    <option value="pending" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pending</option>
                    <option value="transit" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Transit</option>
                    <option value="delivery" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Out for Delivery</option>
                    <option value="delivered" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Delivered</option>
                    <option value="cancelled" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Cancelled</option>
                </select>
                <div class="text-xs text-gray-500">{{ filteredShipments.length }} of {{ store.shipments.length }}
                    shipments</div>
            </div>

            <!-- Shipments List -->
            <div class="space-y-2">
                <div v-if="filteredShipments.length === 0" class="glass-panel rounded-xl p-12 text-center">
                    <span
                        class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-6xl mb-3 block">inventory_2</span>
                    <div class="text-gray-500 dark:text-gray-400 text-sm">No shipments found</div>
                </div>

                <div v-for="ship in filteredShipments" :key="ship.id" class="glass-panel rounded-xl overflow-hidden">
                    <!-- Main Row -->
                    <div @click="expandedShipment = expandedShipment === ship.id ? null : ship.id"
                        class="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors">
                        <span class="material-symbols-outlined text-gray-400 transition-transform duration-300"
                            :class="expandedShipment === ship.id ? 'rotate-90' : ''">chevron_right</span>
                        <div class="flex-1 grid grid-cols-2 sm:grid-cols-6 items-center gap-3 text-sm">
                            <div>
                                <div class="font-bold text-blue-600 dark:text-blue-400">{{ ship.id }}</div>
                                <div class="text-[10px] text-gray-500">{{ ship.createdAt }}</div>
                            </div>
                            <div class="hidden sm:block text-gray-900 dark:text-white truncate">{{ ship.description ||
                                '—' }}</div>
                            <div class="hidden sm:block text-gray-600 dark:text-gray-400 truncate">{{ ship.destination
                                }}</div>
                            <div>
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase" :class="{
                                    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400': ship.statusKey === 'pending',
                                    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': ship.statusKey === 'transit',
                                    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400': ship.statusKey === 'delivery',
                                    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400': ship.statusKey === 'delivered',
                                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400': ship.statusKey === 'cancelled',
                                }">{{ ship.status }}</span>
                            </div>
                            <div class="hidden sm:block text-gray-500">{{ ship.weight }} kg</div>
                            <div class="text-blue-500 font-bold">₹{{ ship.amount?.toLocaleString() }}</div>
                        </div>
                        <div class="flex gap-1">
                            <button v-if="ship.statusKey === 'pending'" @click.stop="openShipmentEdit(ship)"
                                class="p-1.5 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400 transition-colors">
                                <span class="material-symbols-outlined text-[18px]">edit</span>
                            </button>
                            <button v-if="ship.statusKey === 'pending'" @click.stop="deleteShipment(ship.id)"
                                class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors">
                                <span class="material-symbols-outlined text-[18px]">delete</span>
                            </button>
                        </div>
                    </div>

                    <!-- Expanded Details -->
                    <div v-if="expandedShipment === ship.id"
                        class="bg-gray-50 dark:bg-black/20 border-t border-gray-200 dark:border-white/10 p-5">
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Category</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.category }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Origin</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.origin }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Destination</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.destination }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">ETA</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.eta }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Pallets</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.pallets || '—' }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Weight</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.weight }} kg</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Payment</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.paymentMode }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Amount</div>
                                <div class="text-blue-500 font-bold">₹{{ ship.amount?.toLocaleString() }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Packing</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.packingRequired ? 'Yes' :
                                    'No' }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Labor</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.laborRequired ?
                                    ship.laborCount + ' helpers' : 'No' }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Driver</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.driver || 'Not Assigned'
                                    }}</div>
                            </div>
                            <div class="space-y-0.5">
                                <div class="text-gray-500 uppercase font-bold text-[10px]">Vehicle</div>
                                <div class="text-gray-900 dark:text-white font-medium">{{ ship.vehicle || 'Not Assigned'
                                    }}</div>
                            </div>
                        </div>

                        <!-- Status Timeline -->
                        <div v-if="ship.statusHistory && ship.statusHistory.length"
                            class="mt-5 pt-4 border-t border-gray-200 dark:border-white/10">
                            <div class="text-[10px] uppercase font-bold text-gray-500 mb-3">Status Timeline</div>
                            <div class="flex flex-wrap gap-3">
                                <div v-for="(sh, si) in ship.statusHistory" :key="si" class="flex items-center gap-2">
                                    <div class="w-2 h-2 rounded-full"
                                        :class="si === ship.statusHistory.length - 1 ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'">
                                    </div>
                                    <div class="text-xs">
                                        <span class="font-bold text-gray-900 dark:text-white">{{ sh.status }}</span>
                                        <span class="text-gray-500 ml-1">{{ sh.time }}</span>
                                    </div>
                                    <span v-if="si < ship.statusHistory.length - 1"
                                        class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-[14px]">arrow_forward</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modals -->
        <Teleport to="body">
            <BaseModal :isOpen="showConfirmModal" title="Shipment Created"
                @close="showConfirmModal = false; resetForm()">
                <div class="text-center py-6">
                    <div
                        class="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-4">
                        <span
                            class="material-symbols-outlined text-green-600 dark:text-green-400 text-4xl">check_circle</span>
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">Booking Confirmed!</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">Your shipment has been created successfully
                    </p>
                    <div class="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-4">
                        <span class="text-xs text-gray-500 dark:text-gray-400">Order ID:</span>
                        <span class="text-sm font-bold text-blue-600 dark:text-blue-400">{{ confirmedOrderId }}</span>
                    </div>
                    <div class="flex gap-2 justify-center flex-wrap">
                        <button @click="openSlipWithData('bookingConfirmation', confirmedOrder, authStore.currentUser)" class="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-colors">
                            <span class="material-symbols-outlined text-[16px]">receipt_long</span> Booking Slip
                        </button>
                        <button @click="openSlipWithData('instantQuotation', confirmedOrder, authStore.currentUser)" class="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold transition-colors">
                            <span class="material-symbols-outlined text-[16px]">calculate</span> Quotation
                        </button>
                    </div>
                </div>
            </BaseModal>

            <!-- Razorpay Checkout for Full Payment -->
            <RazorpayCheckout
                v-model="showPayModal"
                :amount="pendingPayOrder ? pendingPayOrder.amount : 0"
                :order-id="pendingPayOrder?.id || ''"
                description="Full Payment for Shipment"
                :name="authStore.currentUser?.name || ''"
                :email="authStore.currentUser?.email || ''"
                :wallet-balance="store.walletBalance"
                @success="onRazorpaySuccess"
            />

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

            <BaseModal :isOpen="showUploadModal" title="Upload Bulk Shipments" @close="showUploadModal = false">
                <div class="py-6 space-y-4">
                    <div
                        class="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer">
                        <input type="file" accept=".csv,.xlsx,.json" class="hidden" id="bulkFileInput">
                        <label for="bulkFileInput" class="cursor-pointer">
                            <span
                                class="material-symbols-outlined text-gray-400 text-5xl mb-3 block">cloud_upload</span>
                            <div class="text-sm text-gray-600 dark:text-gray-400 mb-1">Click to upload or drag & drop
                            </div>
                            <div class="text-xs text-gray-500">CSV, XLSX, or JSON files</div>
                        </label>
                    </div>
                    <div class="flex gap-3">
                        <button @click="showUploadModal = false"
                            class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm">Upload</button>
                        <button @click="showUploadModal = false"
                            class="px-6 py-2.5 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg text-sm">Cancel</button>
                    </div>
                </div>
            </BaseModal>
        </Teleport>

        <!-- Map Picker -->
        <MapPicker
            v-if="showMapPicker"
            :isOpen="showMapPicker"
            :title="mapPickerTitle"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />
    </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount, defineAsyncComponent } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { fetchRoadDistanceKm } from '@/composables/useOsrmDistance'
import { useRates } from '@/composables/useRates'

const { openSlip, openSlipWithData } = useSlipPrinter()

const MapPicker = defineAsyncComponent(() => import('@/components/MapPicker.vue'))

let chartLibraryPromise = null
let chartsRegistered = false

function loadChartComponent(componentName) {
    if (!chartLibraryPromise) {
        chartLibraryPromise = Promise.all([
            import('chart.js'),
            import('vue-chartjs'),
        ]).then(([chartJs, vueChartJs]) => {
            if (!chartsRegistered) {
                chartJs.Chart.register(
                    chartJs.CategoryScale,
                    chartJs.LinearScale,
                    chartJs.BarElement,
                    chartJs.Title,
                    chartJs.Tooltip,
                    chartJs.Legend,
                    chartJs.ArcElement,
                )
                chartsRegistered = true
            }
            return vueChartJs
        })
    }

    return chartLibraryPromise.then((vueChartJs) => vueChartJs[componentName])
}

const BarChart = defineAsyncComponent(() => loadChartComponent('Bar'))
const DoughnutChart = defineAsyncComponent(() => loadChartComponent('Doughnut'))

const store = useVendorStore()
const authStore = useAuthStore()
const { rates } = useRates()
const confirmedOrder = ref(null)
const activeTab = ref('new')
const showConfirmModal = ref(false)
const showPayModal = ref(false)
const pendingPayOrder = ref(null)
const showEditModal = ref(false)
const showUploadModal = ref(false)
const confirmedOrderId = ref('')
const expandedUpload = ref(null)
const expandedEntry = ref(null)
const expandedShipment = ref(null)
const shipmentSearch = ref('')
const shipmentStatusFilter = ref('all')
const editingEntry = ref(null)
const isDark = ref(false)
const showSampleData = ref(false)
let themeObserver = null

// ── Map Picker ────────────────────────────────────────────────────────
const showMapPicker = ref(false)
const mapPickerType = ref('destination') // 'destination' | 'pickup'
const mapPickerTitle = computed(() =>
    mapPickerType.value === 'destination' ? 'Select Delivery Destination' : 'Select Pickup Location'
)
function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}
function handleMapSelect(data) {
    if (mapPickerType.value === 'destination') {
        form.destination = data.address
        form.destLat = data.lat
        form.destLng = data.lon
    } else {
        form.pickupAddress = data.address
        form.pickupLat = data.lat
        form.pickupLng = data.lon
    }
    showMapPicker.value = false
}

// Road distance via OSRM — recalculates quote whenever both coords are set
const distanceKm = ref(null)
const distanceLoading = ref(false)
const expandedSample = ref(null)

const categories = [
    { value: 'commercial', label: 'Commercial (B2B)', desc: 'Standard B2B shipments', icon: 'business' },
    { value: 'palletized', label: 'Palletized', desc: 'Pallet-based cargo', icon: 'inventory_2' },
    { value: 'b2c', label: 'B2C Shipment', desc: 'Direct to Customer', icon: 'person' },
]

const handlingOptions = ['Fragile', 'Cold Storage', 'Hazardous', 'Oversize', 'High Value']

const form = reactive({
    category: 'commercial',
    description: '', hsnCode: '', palletCount: 1, weight: 100, volume: null, declaredValue: 0, insuranceRequired: 'no',
    customerName: '', customerPhone: '',
    pickupType: 'hub', pickupAddress: '', pickupCity: '', pickupPincode: '', pickupLat: null, pickupLng: null,
    handling: [], pickupHub: '', destination: '', destinationCity: '', pincode: '', destLat: null, destLng: null,
    pickupDate: '', deliveryDate: '', timeWindow: '08:00 AM - 12:00 PM', priority: 'Standard',
    packingRequired: false, laborRequired: false, laborCount: 1, paymentMode: 'Invoice',
})

watch(
    () => [form.pickupLat, form.pickupLng, form.destLat, form.destLng],
    async ([pLat, pLng, dLat, dLng]) => {
        if (!pLat || !pLng || !dLat || !dLng) { distanceKm.value = null; recalculate(); return }
        distanceLoading.value = true
        distanceKm.value = await fetchRoadDistanceKm(pLat, pLng, dLat, dLng)
        distanceLoading.value = false
        recalculate()
    }
)

const quote = ref({ baseTransport: 500, laborCharges: 0, packingFee: 0, insurance: 0, total: 500 })

const bulkUploads = ref([
    {
        id: 1, fileName: 'commercial_batch_01.csv', type: 'CSV', size: '45 KB', date: '28 Feb, 10:30 AM', entries: [
            { orderId: 'ORD_2026_001', date: '28-Feb-2026', category: 'Commercial', description: 'Electronics - Laptops', hsnCode: '8471', palletCount: 10, weight: 500, declaredValue: 125000, insuranceRequired: 'Yes', pickupHub: 'Mumbai Hub', destination: 'Tech Park', destinationCity: 'Bangalore', pincode: '560100', pickupDate: '2026-03-01', priority: 'Express', paymentMode: 'Invoice', packingRequired: true, laborRequired: true, laborCount: 2, quotedPrice: 8750 },
            { orderId: 'ORD_2026_002', date: '28-Feb-2026', category: 'Commercial', description: 'Office Furniture', hsnCode: '9403', palletCount: 8, weight: 400, declaredValue: 50000, insuranceRequired: 'No', pickupHub: 'Delhi Hub', destination: 'Business Center', destinationCity: 'Noida', pincode: '201301', pickupDate: '2026-03-02', priority: 'Standard', paymentMode: 'COD', packingRequired: false, laborRequired: false, laborCount: 1, quotedPrice: 4500 }
        ]
    },
    {
        id: 2, fileName: 'palletized_batch_15.xlsx', type: 'XLSX', size: '78 KB', date: '27 Feb, 03:45 PM', entries: [
            { orderId: 'ORD_2026_003', date: '27-Feb-2026', category: 'Palletized', description: 'FMCG Products', hsnCode: '2106', palletCount: 25, weight: 1200, declaredValue: 200000, insuranceRequired: 'Yes', pickupHub: 'Pune Hub', destination: 'Distribution Warehouse', destinationCity: 'Mumbai', pincode: '400001', pickupDate: '2026-03-03', priority: 'Standard', paymentMode: 'Invoice', packingRequired: true, laborRequired: true, laborCount: 4, quotedPrice: 18500 }
        ]
    },
    {
        id: 3, fileName: 'b2c_orders_08.json', type: 'JSON', size: '102 KB', date: '26 Feb, 09:15 AM', entries: [
            { orderId: 'ORD_2026_004', date: '26-Feb-2026', category: 'B2C', description: 'Home Appliances', hsnCode: '', palletCount: 0, weight: 35, declaredValue: 15000, insuranceRequired: 'Yes', pickupHub: 'Mumbai Hub', destination: 'Residential', destinationCity: 'Chennai', pincode: '600001', pickupDate: '2026-03-05', priority: 'Urgent', paymentMode: 'Full Payment', packingRequired: true, laborRequired: false, laborCount: 0, quotedPrice: 1200 },
            { orderId: 'ORD_2026_005', date: '26-Feb-2026', category: 'B2C', description: 'Fashion Apparels', hsnCode: '', palletCount: 0, weight: 12, declaredValue: 5000, insuranceRequired: 'No', pickupHub: 'Delhi Hub', destination: 'Home Address', destinationCity: 'Gurgaon', pincode: '122001', pickupDate: '2026-03-04', priority: 'Express', paymentMode: 'COD', packingRequired: false, laborRequired: false, laborCount: 0, quotedPrice: 450 }
        ]
    }
])

const barChartData = computed(() => ({
    labels: ['Commercial', 'Palletized', 'B2C'],
    datasets: [{ label: 'Shipment Count', data: [2, 1, 2], backgroundColor: ['#3B82F6', '#10B981', '#8B5CF6'] }]
}))

const barChartOptions = computed(() => ({
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { ticks: { color: isDark.value ? '#9ca3af' : '#374151' }, grid: { color: isDark.value ? 'rgba(255,255,255,0.07)' : 'rgba(107,114,128,0.15)' } }, x: { ticks: { color: isDark.value ? '#9ca3af' : '#374151' }, grid: { display: false } } }
}))

const doughnutChartData = computed(() => ({
    labels: ['Commercial', 'Palletized', 'B2C'],
    datasets: [{ data: [2, 1, 2], backgroundColor: ['#3B82F6', '#10B981', '#8B5CF6'] }]
}))

const doughnutChartOptions = computed(() => ({
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'bottom', labels: { color: isDark.value ? '#9ca3af' : '#374151', padding: 15 } } }
}))

function recalculate() {
    const r = rates.value
    const km = distanceKm.value || 0
    const distCharge = Math.round(km * (r.perKmRate ?? 12))
    let base = (r.baseBookingFee ?? 220) + (form.weight || 0) * 0.5 + distCharge
    if (form.category === 'palletized') {
        base += (form.palletCount || 0) * 15
    }
    if (form.pickupType === 'doorstep') {
        base += 150 // Pickup charge
    }
    if (form.priority === 'Express') {
        base *= (r.expressMultiplier ?? 1.5)
    } else if (form.priority === 'Urgent') {
        base *= (r.dynamic?.emergency ?? r.expressMultiplier ?? 1.5)
    }
    base = Math.max(base, r.minimumCharge ?? 500)
    let labor = form.laborRequired ? form.laborCount * (r.customerLaborRate ?? 250) : 0
    let packing = form.packingRequired ? (r.customerPackingFee ?? 200) : 0
    let insurance = form.insuranceRequired === 'yes' && form.declaredValue ? (form.declaredValue * ((r.insurancePct ?? 3) / 100)) : 0
    quote.value = { baseTransport: Math.round(base), laborCharges: labor, packingFee: packing, insurance: Math.round(insurance), distanceKm: km, total: Math.round(base + labor + packing + insurance) }
}

watch(
    () => [
        rates.value,
        distanceKm.value,
        form.category,
        form.weight,
        form.palletCount,
        form.pickupType,
        form.priority,
        form.packingRequired,
        form.laborRequired,
        form.laborCount,
        form.declaredValue,
        form.insuranceRequired,
    ],
    () => recalculate(),
    { deep: true, immediate: true }
)

const validationErrors = computed(() => {
    const e = []
    if (!form.description) e.push('Goods description required')

    if (form.category === 'palletized') {
        if (!form.palletCount || form.palletCount < 1) e.push('Pallet count required')
    }

    if (form.category === 'b2c') {
        if (!form.customerName) e.push('Customer name required')
        if (!form.customerPhone) e.push('Customer phone required')
    }

    if (form.pickupType === 'doorstep') {
        if (!form.pickupAddress) e.push('Pickup address required')
        if (!form.pickupCity) e.push('Pickup city required')
        if (!form.pickupPincode) e.push('Pickup pincode required')
    }

    if (!form.weight || form.weight < 1) e.push('Weight required')
    if (!form.destination) e.push('Destination required')
    if (!form.destinationCity) e.push('Destination city required')
    if (!form.pincode) e.push('Pincode required')
    if (!form.pickupDate) e.push('Pickup date required')
    return e
})
const formValid = computed(() => validationErrors.value.length === 0)

const filteredShipments = computed(() => {
    let list = store.shipments
    if (shipmentStatusFilter.value !== 'all') {
        list = list.filter(s => s.statusKey === shipmentStatusFilter.value)
    }
    if (shipmentSearch.value.trim()) {
        const q = shipmentSearch.value.toLowerCase()
        list = list.filter(s => s.id.toLowerCase().includes(q) || s.destination.toLowerCase().includes(q) || (s.description || '').toLowerCase().includes(q))
    }
    return list
})

async function submitShipment() {
    if (!formValid.value) return
    const s = await store.createShipment({ ...form, quotedPrice: quote.value.total, quoteBreakdown: { ...quote.value } })
    confirmedOrderId.value = s.id
    confirmedOrder.value = s
    if (form.paymentMode === 'Full Payment') {
        pendingPayOrder.value = s
        showPayModal.value = true
    } else {
        showConfirmModal.value = true
    }
}

async function onRazorpaySuccess({ payment_id, method, amount }) {
    showPayModal.value = false
    if (pendingPayOrder.value) {
        const invoice = store.invoices.find(inv => inv.orderId === pendingPayOrder.value.id)
        if (invoice) {
            await store.payInvoice(invoice.id, amount, method)
        }
        pendingPayOrder.value = null
    }
    showConfirmModal.value = true
}

function saveDraft() {
    const tooltip = document.createElement('div')
    tooltip.className = 'fixed bottom-4 right-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    tooltip.textContent = 'Draft saved locally'
    document.body.appendChild(tooltip)
    setTimeout(() => tooltip.remove(), 2500)
}

function resetForm() {
    Object.assign(form, {
        category: 'commercial', description: '', hsnCode: '', palletCount: 1, weight: 100, volume: null, declaredValue: 0, insuranceRequired: 'no', customerName: '', customerPhone: '',
        pickupType: 'hub', pickupAddress: '', pickupCity: '', pickupPincode: '',
        handling: [], pickupHub: store.warehouses[0]?.name || '', destination: '', destinationCity: '', pincode: '', pickupDate: '', deliveryDate: '', timeWindow: '08:00 AM - 12:00 PM', priority: 'Standard', packingRequired: false, laborRequired: false, laborCount: 1, paymentMode: 'Invoice'
    })
    recalculate()
}

const CSV_TEMPLATES = {
    commercial: {
        filename: 'commercial_b2b_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,cargo_type,weight_kg,pallets,declared_value,payment_mode',
            'ORD-001,Mumbai Warehouse MIDC Andheri,Delhi Central Hub Okhla,Electronics,500,5,50000,Invoice',
            'ORD-002,Pune Factory Pimpri,Bangalore Depot Whitefield,Machinery,1200,12,120000,Prepaid',
        ]
    },
    palletized: {
        filename: 'palletized_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,pallets,weight_kg,pallet_type,declared_value,payment_mode',
            'ORD-001,Pune Factory Pimpri,Bangalore Depot Whitefield,10,2000,Standard EUR,100000,Invoice',
            'ORD-002,Chennai Port Trust,Hyderabad JNPC Hub,4,800,Heat-Treated,40000,Prepaid',
        ]
    },
    b2c: {
        filename: 'b2c_shipment_template.csv',
        rows: [
            'reference_id,customer_name,customer_phone,pickup_address,delivery_address,item_description,weight_kg,declared_value',
            'ORD-001,Rahul Sharma,9876543210,Seller Hub Mumbai,123 Main St Bangalore,Smart TV 55 inch,12,25000',
            'ORD-002,Priya Patel,9123456789,Retail Store Ahmedabad,Plot 45 Surat,Home Appliances Set,35,15000',
        ]
    }
}

function downloadTemplate(category) {
    const t = CSV_TEMPLATES[category]
    if (!t) return
    const content = t.rows.join('\r\n') + '\r\n'
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = t.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

function toggleSample(category) {
    expandedSample.value = expandedSample.value === category ? null : category
}

function toggleUpload(id) {
    expandedUpload.value = expandedUpload.value === id ? null : id
    expandedEntry.value = null
}

function toggleEntry(orderId) {
    expandedEntry.value = expandedEntry.value === orderId ? null : orderId
}

function openEditModal(entry) {
    editingEntry.value = JSON.parse(JSON.stringify(entry))
    showEditModal.value = true
}

function saveEdit() {
    const upload = bulkUploads.value.find(u => u.entries.some(e => e.orderId === editingEntry.value.orderId))
    if (upload) {
        const idx = upload.entries.findIndex(e => e.orderId === editingEntry.value.orderId)
        if (idx !== -1) upload.entries[idx] = editingEntry.value
    }
    showEditModal.value = false
    editingEntry.value = null
}

function deleteUpload(id) {
    if (!confirm('Delete this upload and all its entries?')) return
    bulkUploads.value = bulkUploads.value.filter(u => u.id !== id)
}

function openShipmentEdit(ship) {
    editingEntry.value = JSON.parse(JSON.stringify({
        orderId: ship.id,
        date: ship.createdAt,
        category: ship.category,
        description: ship.description,
        hsnCode: '',
        palletCount: ship.pallets,
        weight: ship.weight,
        declaredValue: ship.amount,
        insuranceRequired: 'No',
        pickupHub: ship.origin,
        destinationCity: ship.destination,
        pincode: '',
        pickupDate: '',
        priority: 'Standard',
        paymentMode: ship.paymentMode,
        packingRequired: ship.packingRequired,
        laborRequired: ship.laborRequired,
        laborCount: ship.laborCount,
        _isStoreShipment: true,
    }))
    showEditModal.value = true
}

function deleteShipment(id) {
    if (!confirm('Delete this shipment? This cannot be undone.')) return
    store.shipments.splice(store.shipments.findIndex(s => s.id === id), 1)
    const tooltip = document.createElement('div')
    tooltip.className = 'fixed top-4 right-4 z-[9999] bg-red-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    tooltip.textContent = `Shipment ${id} deleted`
    document.body.appendChild(tooltip)
    setTimeout(() => tooltip.remove(), 2500)
}

function deleteEntry(uploadId, orderId) {
    if (!confirm('Delete this entry?')) return
    const upload = bulkUploads.value.find(u => u.id === uploadId)
    if (upload) upload.entries = upload.entries.filter(e => e.orderId !== orderId)
}

// Auto-select first warehouse once loaded
watch(() => store.warehouses, (list) => {
    if (!form.pickupHub && list.length) form.pickupHub = list[0].name
}, { immediate: true })

onMounted(async () => {
    if (typeof document !== 'undefined') {
        isDark.value = document.documentElement.classList.contains('dark')
    }

    if (typeof document !== 'undefined' && typeof MutationObserver !== 'undefined') {
        themeObserver = new MutationObserver(() => {
            isDark.value = document.documentElement.classList.contains('dark')
        })
        themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    }

    // Always re-fetch warehouses when page loads so new hubs are visible immediately
    await store.fetchWarehouses()
})

onBeforeUnmount(() => {
    themeObserver?.disconnect()
    themeObserver = null
})

recalculate()
</script>
