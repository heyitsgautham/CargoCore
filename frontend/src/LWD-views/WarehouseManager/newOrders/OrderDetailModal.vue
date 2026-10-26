<template>
    <div v-if="showDetailModal && selectedOrder"
        class="fixed inset-0 w-screen h-screen z-[9999] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
        @click.self="showDetailModal = false">
        <div
            class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto border border-gray-200 dark:border-white/10">
            <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">Order {{ selectedOrder.tracking_code }}</h3>
                <button @click="showDetailModal = false"
                    class="text-gray-500 hover:text-gray-900 dark:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6 space-y-6">
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Order Type</div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.order_type }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Cargo Type
                        </div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.cargo_type || 'Move order' }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Service Window
                        </div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ selectedOrder.service_time_block || 'TBD' }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Scheduled Time
                        </div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ formatDate(selectedOrder.scheduled_at) }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Total Value
                        </div>
                        <div class="text-gray-900 dark:text-white font-bold">{{ formatCurrency(selectedOrder.total_amount) }}</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Pickup Address</div>
                        <div class="text-gray-900 dark:text-white text-sm leading-6">{{ selectedOrder.pickup_addr || 'Not available' }}</div>
                    </div>
                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                        <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-1">Delivery Address</div>
                        <div class="text-gray-900 dark:text-white text-sm leading-6">{{ selectedOrder.delivery_addr || 'Not available' }}</div>
                    </div>
                </div>

                <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-lg">
                    <div class="text-xs text-gray-600 dark:text-gray-400 uppercase mb-3">Item Manifest</div>
                    <div v-if="selectedOrder.items?.length" class="space-y-2">
                        <div v-for="item in selectedOrder.items" :key="item.id"
                            class="flex items-center justify-between rounded-lg border border-gray-200 dark:border-white/10 px-3 py-2">
                            <div>
                                <div class="font-medium text-gray-900 dark:text-white">{{ item.sku }}</div>
                                <div class="text-xs text-gray-500">Boxes: {{ item.box_count ?? 0 }} • Volume: {{ item.estimated_volume ?? 0 }}</div>
                            </div>
                            <div class="text-sm font-bold text-gray-900 dark:text-white">{{ item.quantity }}</div>
                        </div>
                    </div>
                    <div v-else class="text-sm text-gray-500 dark:text-gray-400 leading-6">
                        No item-level list was captured for this booking. Warehouse and dispatcher can currently see only order-level details unless items are added later through the order items API.
                    </div>
                </div>

                <div class="flex gap-3">
                    <button v-if="selectedOrder.status === 'DRAFT' || needsWarehouseAcceptance(selectedOrder)"
                        @click="acceptOrder(selectedOrder); showDetailModal = false"
                        class="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 py-3 rounded-lg font-bold transition-colors">
                        <span
                            class="material-symbols-outlined text-[18px] align-middle mr-1">check_circle</span>
                        {{ selectedOrder.status === 'DRAFT' ? 'Validate Order' : 'Accept Order' }}
                    </button>
                    <button @click="escalateOrder(selectedOrder)"
                        class="bg-red-500/20 hover:bg-red-500/30 text-red-600 dark:text-red-400 py-3 px-6 rounded-lg font-bold transition-colors">
                        <span
                            class="material-symbols-outlined text-[18px] align-middle mr-1">arrow_upward</span>
                        Escalate
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { newOrdersPageKey } from './newOrdersPageContext'

const {
    acceptOrder,
    escalateOrder,
    formatCurrency,
    formatDate,
    needsWarehouseAcceptance,
    selectedOrder,
    showDetailModal,
} = inject(newOrdersPageKey)
</script>
