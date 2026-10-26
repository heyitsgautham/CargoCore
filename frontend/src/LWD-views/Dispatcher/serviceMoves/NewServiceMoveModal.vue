<template>
    <!-- New Service Move Modal -->
    <Teleport to="body">
    <div v-if="showNewMove" class="fixed inset-0 bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4" @click.self="closeNewMoveModal">
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 shadow-2xl border border-primary/20 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
            <div class="flex items-center justify-between mb-5">
                <h3 class="text-xl font-bold text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">add_circle</span>
                    Create New Service Move
                </h3>
                <button @click="closeNewMoveModal" class="text-gray-400 hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div v-if="formError" class="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {{ formError }}
            </div>
            <div v-else-if="formSuccess" class="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                {{ formSuccess }}
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">Move Title *</label>
                    <input v-model="newMove.title" type="text" placeholder="e.g., Johnson Family House Shift"
                        class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                </div>

                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">Service Type *</label>
                    <select v-model="newMove.type" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                        <option value="House Shift" class="bg-gray-900">🏠 House Shift</option>
                        <option value="Office Shift" class="bg-gray-900">🏢 Office Shift</option>
                        <option value="Warehouse Transfer" class="bg-gray-900">🏭 Warehouse Transfer</option>
                        <option value="Warehouse Supply Pickup" class="bg-gray-900">📦 Warehouse Supply Pickup</option>
                        <option value="Equipment Transfer" class="bg-gray-900">🛠️ Equipment Transfer</option>
                        <option value="Manual Service" class="bg-gray-900">🧰 Manual Service</option>
                    </select>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">Pickup Location *</label>
                        <div class="relative">
                            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-green-400 text-[18px]">trip_origin</span>
                            <button type="button" @click="openMapPicker('pickup')"
                                class="w-full pl-10 pr-3 py-2.5 rounded-lg border border-gray-700 hover:border-primary/50 focus:border-primary bg-black/40 text-left text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors flex items-center justify-between">
                                <span :class="newMove.pickup ? '' : 'text-gray-500'">{{ newMove.pickup || 'Select pickup on map' }}</span>
                                <span class="material-symbols-outlined text-[18px] text-gray-400">map</span>
                            </button>
                        </div>
                        <div class="mt-1 flex items-center justify-between gap-2 text-[11px] text-gray-400">
                            <span class="truncate">
                                {{ newMove.pickupLat !== null && newMove.pickupLng !== null
                                    ? `${Number(newMove.pickupLat).toFixed(5)}, ${Number(newMove.pickupLng).toFixed(5)}`
                                    : 'Search or click on the map' }}
                            </span>
                            <button v-if="assignedHub?.address" type="button" @click="useAssignedHub('pickup')" class="shrink-0 text-primary hover:text-yellow-300 transition-colors">
                                Use assigned hub
                            </button>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">Delivery Location *</label>
                        <div class="relative">
                            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-400 text-[18px]">location_on</span>
                            <button type="button" @click="openMapPicker('delivery')"
                                class="w-full pl-10 pr-3 py-2.5 rounded-lg border border-gray-700 hover:border-primary/50 focus:border-primary bg-black/40 text-left text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors flex items-center justify-between">
                                <span :class="newMove.delivery ? '' : 'text-gray-500'">{{ newMove.delivery || 'Select delivery on map' }}</span>
                                <span class="material-symbols-outlined text-[18px] text-gray-400">map</span>
                            </button>
                        </div>
                        <div class="mt-1 flex items-center justify-between gap-2 text-[11px] text-gray-400">
                            <span class="truncate">
                                {{ newMove.deliveryLat !== null && newMove.deliveryLng !== null
                                    ? `${Number(newMove.deliveryLat).toFixed(5)}, ${Number(newMove.deliveryLng).toFixed(5)}`
                                    : 'Search or click on the map' }}
                            </span>
                            <button v-if="assignedHub?.address" type="button" @click="useAssignedHub('delivery')" class="shrink-0 text-primary hover:text-yellow-300 transition-colors">
                                Use assigned hub
                            </button>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">📅 Scheduled Date</label>
                        <input v-model="newMove.scheduledDate" type="date"
                            class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">⏰ Scheduled Time</label>
                        <input v-model="newMove.scheduledTime" type="time"
                            class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">🚚 Assign Vehicle</label>
                    <select v-model="newMove.vehicleId" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                        <option value="" class="bg-gray-900">-- Select Vehicle --</option>
                        <option v-for="vehicle in realVehicleOptions" :key="vehicle.id" :value="vehicle.id" class="bg-gray-900">
                            {{ vehicle.label }}
                        </option>
                    </select>
                    <div v-if="realVehicleOptions.length === 0" class="mt-1 text-xs text-yellow-400">
                        ⚠️ No direct-dispatch vehicles available right now.
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">👤 Assign Driver</label>
                    <select v-model="newMove.driverId" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                        <option value="" class="bg-gray-900">-- Select Driver --</option>
                        <option v-for="driver in availableDrivers" :key="driver.id" :value="driver.id" class="bg-gray-900">
                            {{ driver.name }} ({{ driver.status }}){{ driver.vehicle ? ' · ' + driver.vehicle : '' }}
                        </option>
                    </select>
                    <div v-if="availableDrivers.length === 0" class="mt-1 text-xs text-yellow-400">
                        ⚠️ No available drivers ready for direct dispatch
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">⏱️ Estimated Duration (hours)</label>
                    <input v-model="newMove.estimatedDuration" type="number" min="1" max="24" placeholder="4"
                        class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                </div>

                <div>
                    <label class="block text-xs font-medium text-primary mb-1.5">📝 Special Notes</label>
                    <textarea v-model="newMove.notes" rows="2" placeholder="Any special instructions or requirements..."
                        class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors resize-none"></textarea>
                </div>
            </div>
            <div class="flex gap-3 mt-6">
                <button @click="createServiceMove" :disabled="!newMove.title || !newMove.pickup || !newMove.delivery || loading"
                    class="flex-1 bg-gradient-to-r from-primary to-yellow-400 hover:from-yellow-400 hover:to-primary text-black font-bold py-3 rounded-lg text-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg">
                    <span v-if="loading" class="flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                        Creating...
                    </span>
                    <span v-else class="flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">check_circle</span>
                        Create Move
                    </span>
                </button>
                <button @click="closeNewMoveModal" class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 rounded-lg text-sm transition-colors">
                    Cancel
                </button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const {
    assignedHub,
    availableDrivers,
    closeNewMoveModal,
    createServiceMove,
    formError,
    formSuccess,
    loading,
    newMove,
    openMapPicker,
    realVehicleOptions,
    showNewMove,
    useAssignedHub,
} = inject(serviceMovesPageKey)
</script>
