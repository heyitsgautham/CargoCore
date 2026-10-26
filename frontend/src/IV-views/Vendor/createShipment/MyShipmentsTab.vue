<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const {
    activeTab,
    deleteShipment,
    expandedShipment,
    filteredShipments,
    openShipmentEdit,
    shipmentSearch,
    shipmentStatusFilter,
    store,
} = inject(createShipmentPageKey)
</script>
