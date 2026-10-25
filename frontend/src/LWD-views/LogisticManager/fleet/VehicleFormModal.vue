<template>
    <!-- Add/Edit Vehicle Modal -->
    <Teleport to="body">
        <div v-if="isVehicleModalOpen"
            class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            @click.self="closeVehicleModal">
            <div :class="vehicleModalMode === 'add' ? 'max-w-[800px]' : 'max-w-md'"
                class="lm-vehicle-modal bg-slate-950/98 w-full rounded-2xl shadow-2xl border border-white/10 overflow-hidden flex flex-col max-h-[90vh] backdrop-blur-xl">
                <div
                    class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 class="text-lg font-bold text-white">{{ vehicleModalMode === 'add' ? `Add
                        New Vehicle` : `Edit Vehicle` }}</h3>
                    <button @click="closeVehicleModal"
                        class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="p-6 overflow-y-auto bg-slate-950/95 text-slate-200" :class="vehicleModalMode === 'add' ? 'grid grid-cols-1 md:grid-cols-2 gap-8' : 'space-y-4'">
                    <!-- Left Column: Vehicle Details -->
                    <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vehicle
                                ID</label>
                            <input v-model="vehicleFormData.id" :disabled="vehicleModalMode === 'edit'"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 disabled:opacity-50">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">License
                                Plate</label>
                            <input v-model="vehicleFormData.licensePlate"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type /
                            Model</label>
                        <input v-model="vehicleFormData.model" placeholder="e.g. Ford Transit (2022)"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                    </div>

                    <div v-if="vehicleModalMode === 'add'">
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hub
                            Assignment</label>
                        <div class="relative">
                            <select v-model="vehicleFormData.hubId"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Global (All Warehouses)</option>
                                <option v-for="h in store.hubs" :key="h.id" :value="h.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ h.name }}</option>
                            </select>
                        </div>
                    </div>

                    </div> <!-- End Left Column -->

                    <!-- Right Column: Required Documentation Section -->
                    <div v-if="vehicleModalMode === 'add'" class="space-y-6 bg-slate-900/70 p-5 rounded-2xl border border-white/10">
                        <h4 class="text-xs font-bold text-slate-300 uppercase tracking-wider">Required Documents</h4>

                        <!-- Insurance Policy -->
                        <div class="space-y-3">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-gray-400 text-sm">verified_user</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">Insurance Policy</p>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-medium text-slate-300 mb-1">Expiry Date</label>
                                    <input type="date" v-model="vehicleFormData.insuranceExpiry" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-slate-300 mb-1">Policy Document</label>
                                    <label class="w-full flex items-center justify-center gap-2 cursor-pointer bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg px-3 py-2 text-xs font-bold text-primary transition-colors h-[38px]">
                                        <span class="material-symbols-outlined text-[16px]">cloud_upload</span>
                                        <span class="truncate">{{ vehicleFormData.insuranceFileName || 'Upload PDF/IMG' }}</span>
                                        <input type="file" class="hidden" accept="image/*,.pdf" @change="e => handleVehicleDocUpload(e, 'insurance')">
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Vehicle Registration -->
                        <div class="space-y-3">
                            <div class="flex items-center gap-2">
                                <span class="material-symbols-outlined text-gray-400 text-sm">assignment</span>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">Vehicle Registration</p>
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-medium text-slate-300 mb-1">Expiry Date</label>
                                    <input type="date" v-model="vehicleFormData.registrationExpiry" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-slate-300 mb-1">Registration Document</label>
                                    <label class="w-full flex items-center justify-center gap-2 cursor-pointer bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg px-3 py-2 text-xs font-bold text-primary transition-colors h-[38px]">
                                        <span class="material-symbols-outlined text-[16px]">cloud_upload</span>
                                        <span class="truncate">{{ vehicleFormData.registrationFileName || 'Upload PDF/IMG' }}</span>
                                        <input type="file" class="hidden" accept="image/*,.pdf" @change="e => handleVehicleDocUpload(e, 'registration')">
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    class="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/90">
                    <button @click="closeVehicleModal"
                        class="px-4 py-2 rounded-lg font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 dark:bg-white/10 dark:border-white/10 dark:text-gray-200 dark:hover:bg-white/15 transition-colors shadow-sm">Cancel</button>
                    <button @click="submitVehicle" :disabled="isSubmitting"
                        class="px-4 py-2 rounded-lg font-medium text-white flex items-center justify-center gap-2 min-w-[120px] bg-primary hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-75 disabled:cursor-not-allowed">
                        <span v-if="isSubmitting" class="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin"></span>
                        <span>{{ vehicleModalMode === 'add' ? (isSubmitting ? 'Uploading...' : 'Add Vehicle') : 'Save Changes' }}</span>
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    closeVehicleModal,
    handleVehicleDocUpload,
    isSubmitting,
    isVehicleModalOpen,
    store,
    submitVehicle,
    vehicleFormData,
    vehicleModalMode,
} = inject(fleetPageKey)
</script>

<style scoped src="./fleetModal.css"></style>
