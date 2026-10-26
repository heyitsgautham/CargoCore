<template>
    <!-- Confirmation Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showConfirmModal" @close="showConfirmModal = false">
            <template #title>{{ moveType === 'house-shift' ? 'Booking Confirmed! 🎉' : 'Pickup Scheduled! 📦'
                }}</template>
            <div class="space-y-4">
                <div class="text-center py-4">
                    <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"
                        :class="moveType === 'house-shift' ? 'bg-green-500/20 text-green-500' : 'bg-blue-500/20 text-blue-500'">
                        <span class="material-symbols-outlined text-3xl">task_alt</span>
                    </div>
                    <p class="text-gray-700 dark:text-gray-300">
                        {{ moveType === 'house-shift' ? 'Your move has been booked!'
                        : 'Auto-pickup scheduled!' }}</p>
                    <div class="text-2xl font-mono font-bold mt-2"
                        :class="moveType === 'house-shift' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                        {{ confirmedOrderId }}</div>
                </div>
                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Type</div>
                        <div class="font-medium text-gray-900 dark:text-white">
                            {{ moveType === 'house-shift' ? form.cargoType : 'Small Package' }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">Total</div>
                        <div class="font-bold"
                            :class="moveType === 'house-shift' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                            ₹{{ bookingTotal.toLocaleString() }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">
                            {{ moveType === 'house-shift' ? 'Vehicle' : 'Est. Delivery' }}</div>
                        <div class="font-medium text-gray-900 dark:text-white">
                            {{ moveType === 'house-shift' ? selectedVehicle?.name : estimatedDelivery }}</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                        <div class="text-xs text-gray-500 mb-1">{{ moveType === 'house-shift' ? 'Helpers' : 'Weight'
                            }}
                        </div>
                        <div class="font-medium text-gray-900 dark:text-white">{{ moveType === 'house-shift' ?
                            form.laborCount : pkg.weight + ' kg' }}</div>
                    </div>
                </div>
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm">
                    <div class="text-xs text-gray-500 mb-1">Assigned Hub</div>
                    <div class="font-medium text-gray-900 dark:text-white">
                        {{ confirmedOrder?.warehouseName || routingPreview?.warehouse_name || 'Pending assignment' }}
                    </div>
                </div>
                <!-- Dummy text removed -->
            </div>
            <template #footer>
                <div class="flex gap-3 w-full flex-wrap">
                    <button @click="openSlipWithData('bookingConfirmation', confirmedOrder, authStore.currentUser)"
                        class="flex-1 py-2 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-1.5 hover:bg-indigo-500/20">
                        <span class="material-symbols-outlined text-sm">receipt_long</span> Booking Slip
                    </button>
                    <router-link to="/individual/orders"
                        class="flex-1 py-2 rounded-lg hover:opacity-90 transition text-sm font-bold text-center text-white"
                        :class="moveType === 'house-shift' ? 'bg-green-600' : 'bg-blue-600'">View Orders</router-link>
                    <button @click="showConfirmModal = false"
                        class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm font-medium">Close</button>
                </div>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { bookMovePageKey } from './bookMovePageContext'

const {
    authStore,
    bookingTotal,
    confirmedOrder,
    confirmedOrderId,
    estimatedDelivery,
    form,
    moveType,
    openSlipWithData,
    pkg,
    routingPreview,
    selectedVehicle,
    showConfirmModal,
} = inject(bookMovePageKey)
</script>
