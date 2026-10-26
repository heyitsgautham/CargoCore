<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">My Orders</h2>
            <div class="flex items-center gap-3 w-full sm:w-auto">
                <div class="relative flex-1 sm:flex-none">
                    <span
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-lg">search</span>
                    <input v-model="search" type="text" placeholder="Search orders..."
                        class="w-full sm:w-64 pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 outline-none text-sm" />
                </div>
                <select v-model="statusFilter"
                    class="px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-green-500/50 outline-none">
                    <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All</option>
                    <option value="pending" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pending</option>
                    <option value="dispatched" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Dispatched</option>
                    <option value="in-transit" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Transit</option>
                    <option value="delivered" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Delivered</option>
                    <option value="cancelled" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Cancelled</option>
                </select>
            </div>
        </div>

        <div class="space-y-4">
            <div v-for="order in filteredOrders" :key="order.id"
                class="glass-panel rounded-xl overflow-hidden transition-all duration-300"
                :class="expandedOrder === order.id ? 'ring-1 ring-green-500/30' : ''">

                <!-- Header -->
                <div class="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                    @click="expandedOrder = expandedOrder === order.id ? null : order.id">
                    <div class="flex items-center gap-4 w-full sm:w-auto">
                        <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                            :class="statusBg(order.status)">
                            <span class="material-symbols-outlined text-xl">{{ statusIcon(order.status) }}</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="font-mono font-bold text-green-600 dark:text-green-400 text-sm">{{ order.id
                                    }}</span>
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                    :class="statusBadge(order.status)">{{ order.status.replace('-', ' ') }}</span>
                                <span v-if="order.hasDamageReport" class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                    :class="damageStatusBadge(order.damageReportStatus)">
                                    {{ damageStatusLabel(order.damageReportStatus) }}
                                </span>
                                <span v-if="order.moveType === 'small-package'"
                                    class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400">Package</span>
                            </div>
                            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{{ order.cargoType }}
                                · {{ order.vehicleType?.toUpperCase() || '' }} · {{ order.date }}</div>
                        </div>
                    </div>
                    <div class="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                        <span class="text-lg font-bold text-gray-900 dark:text-white font-mono">₹{{
                            order.cost.total.toLocaleString() }}</span>
                        <span class="material-symbols-outlined text-gray-400 transition-transform duration-300"
                            :class="expandedOrder === order.id ? 'rotate-180' : ''">expand_more</span>
                    </div>
                </div>

                <!-- Expanded -->
                <transition enter-active-class="transition-all duration-300 ease-out"
                    enter-from-class="max-h-0 opacity-0" enter-to-class="max-h-[2000px] opacity-100"
                    leave-active-class="transition-all duration-200 ease-in"
                    leave-from-class="max-h-[2000px] opacity-100" leave-to-class="max-h-0 opacity-0">
                    <div v-if="expandedOrder === order.id" class="overflow-hidden">
                        <div class="border-t border-gray-200 dark:border-white/5 p-4 sm:p-5 space-y-5">

                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div class="flex items-start gap-3"><span
                                            class="material-symbols-outlined text-green-500 mt-0.5">trip_origin</span>
                                        <div>
                                            <div class="text-xs text-gray-500">Pickup</div>
                                            <div class="text-sm font-medium text-gray-900 dark:text-white">{{
                                                order.pickup }}</div>
                                        </div>
                                    </div>
                                    <div class="flex items-start gap-3"><span
                                            class="material-symbols-outlined text-red-500 mt-0.5">location_on</span>
                                        <div>
                                            <div class="text-xs text-gray-500">Destination</div>
                                            <div class="text-sm font-medium text-gray-900 dark:text-white">{{
                                                order.destination }}</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                                        <div class="text-xs text-gray-500">Vehicle</div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white uppercase">{{ order.vehicleType || 'N/A' }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                                        <div class="text-xs text-gray-500">Helpers</div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white">{{ order.laborCount }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                                        <div class="text-xs text-gray-500">Payment</div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white">{{ order.paymentMode }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-center">
                                        <div class="text-xs text-gray-500">Amount</div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white">₹{{ order.cost.total.toLocaleString() }}</div>
                                    </div>
                                </div>
                                <div v-if="order.cancellation"
                                    class="p-3 bg-red-50 dark:bg-red-500/5 border border-red-200 dark:border-red-500/20 rounded-lg text-sm">
                                    <div class="text-red-600 dark:text-red-400 font-bold">{{ order.cancellation.reason }}</div>
                                </div>

                                <div v-if="order.hasDamageReport"
                                    class="p-3 bg-red-50 dark:bg-red-500/5 border border-red-200 dark:border-red-500/20 rounded-lg text-sm space-y-2">
                                    <div class="flex items-center justify-between gap-3 flex-wrap">
                                        <div class="font-bold text-red-700 dark:text-red-400 flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[18px]">report</span>
                                            Damage Report {{ order.damageReportId }}
                                        </div>
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                            :class="damageStatusBadge(order.damageReportStatus)">
                                            {{ damageStatusLabel(order.damageReportStatus) }}
                                        </span>
                                    </div>
                                    <div v-if="order.damageCondition" class="text-xs text-gray-600 dark:text-gray-300">
                                        Condition: <span class="font-bold">{{ order.damageCondition }}</span>
                                    </div>
                                    <div v-if="order.damageRefundAmount && order.damageRefundAmount > 0" class="text-xs text-green-700 dark:text-green-400 font-bold">
                                        Refund: ₹{{ order.damageRefundAmount.toLocaleString() }}
                                    </div>
                                    <router-link to="/individual/damage-report"
                                        class="inline-flex items-center gap-1.5 text-xs font-bold text-red-600 dark:text-red-400 hover:underline">
                                        <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                                        View Damage Report
                                    </router-link>
                                </div>

                            <!-- Actions -->
                            <div class="flex flex-wrap gap-2 pt-2 border-t border-gray-200 dark:border-white/5">
                                <router-link v-if="['in-transit', 'dispatched', 'delivered'].includes(order.status)"
                                    :to="'/individual/tracking?orderId=' + order.id"
                                    class="px-4 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-sm">{{ order.status === 'delivered' ? 'route' : 'gps_fixed' }}</span>
                                    {{ order.status === 'delivered' ? 'Route Blueprint' : 'Track' }}
                                </router-link>
                                <button v-if="order.status === 'pending'" @click="showRescheduleModal(order)"
                                    class="px-4 py-2 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-sm">schedule</span> Reschedule
                                </button>
                                <button v-if="order.status === 'pending' || order.status === 'dispatched'"
                                    @click="showCancelModal(order)"
                                    class="px-4 py-2 bg-red-600 text-white text-sm font-bold rounded-lg hover:bg-red-700 transition-colors flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-sm">cancel</span> Cancel Order
                                </button>
                                <div v-if="order.status === 'in-transit'"
                                    class="px-4 py-2 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs rounded-lg flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-sm">info</span>
                                    This order is already in progress. Please contact support to request changes or cancellation.
                                </div>
                                <router-link v-if="order.status === 'delivered'" to="/individual/damage-report"
                                    class="px-4 py-2 bg-red-500/10 text-red-600 dark:text-red-400 text-sm font-bold rounded-lg hover:bg-red-500/20 transition-colors flex items-center gap-1.5">
                                    <span class="material-symbols-outlined text-sm">report</span> Report Damage
                                </router-link>
                            </div>

                            <!-- Order Documents -->
                            <div class="pt-4 border-t border-gray-200 dark:border-white/5">
                                <div class="flex items-center gap-2 mb-3">
                                    <span class="material-symbols-outlined text-gray-400 text-[18px]">folder_open</span>
                                    <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest">Order Documents</span>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">

                                    <!-- Booking Slip -->
                                    <div class="flex flex-col gap-3 p-4 rounded-xl border border-indigo-100 dark:border-indigo-500/20 bg-gradient-to-br from-indigo-50/60 to-white dark:from-indigo-500/5 dark:to-transparent hover:border-indigo-200 dark:hover:border-indigo-400/30 transition-all">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-500/20 flex items-center justify-center shrink-0">
                                                <span class="material-symbols-outlined text-indigo-600 dark:text-indigo-400 text-[22px]">receipt_long</span>
                                            </div>
                                            <div>
                                                <div class="text-sm font-bold text-gray-800 dark:text-white leading-tight">Booking Slip</div>
                                                <div class="text-[11px] text-gray-400 mt-0.5">Confirmation document</div>
                                            </div>
                                        </div>
                                        <div class="flex gap-2">
                                            <button @click="openSlipWithData('bookingConfirmation', order, authStore.currentUser)"
                                                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95 transition-all">
                                                <span class="material-symbols-outlined text-[15px]">download</span> Download
                                            </button>
                                            <button @click="printSlipWithData('bookingConfirmation', order, authStore.currentUser)"
                                                title="Print"
                                                class="flex items-center justify-center px-3 py-2 rounded-lg text-xs font-bold bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-400 hover:bg-indigo-200 dark:hover:bg-indigo-500/30 active:scale-95 transition-all">
                                                <span class="material-symbols-outlined text-[15px]">print</span>
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Proof of Delivery -->
                                    <div class="flex flex-col gap-3 p-4 rounded-xl transition-all"
                                        :class="order.status === 'delivered'
                                            ? 'border border-green-100 dark:border-green-500/20 bg-gradient-to-br from-green-50/60 to-white dark:from-green-500/5 dark:to-transparent hover:border-green-200 dark:hover:border-green-400/30'
                                            : 'border border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02] opacity-50'">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                                                :class="order.status === 'delivered' ? 'bg-green-100 dark:bg-green-500/20' : 'bg-gray-100 dark:bg-white/5'">
                                                <span class="material-symbols-outlined text-[22px]"
                                                    :class="order.status === 'delivered' ? 'text-green-600 dark:text-green-400' : 'text-gray-400'">verified</span>
                                            </div>
                                            <div>
                                                <div class="text-sm font-bold text-gray-800 dark:text-white leading-tight">Proof of Delivery</div>
                                                <div class="text-[11px] mt-0.5" :class="order.status === 'delivered' ? 'text-gray-400' : 'text-gray-400'">
                                                    {{ order.status === 'delivered' ? 'Delivery confirmed' : 'Available after delivery' }}
                                                </div>
                                            </div>
                                        </div>
                                        <div class="flex gap-2">
                                            <button @click="openSlipWithData('proofOfDelivery', order, authStore.currentUser)"
                                                :disabled="order.status !== 'delivered'"
                                                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold transition-all active:scale-95"
                                                :class="order.status === 'delivered' ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                                <span class="material-symbols-outlined text-[15px]">download</span> Download
                                            </button>
                                            <button @click="printSlipWithData('proofOfDelivery', order, authStore.currentUser)"
                                                :disabled="order.status !== 'delivered'"
                                                title="Print"
                                                class="flex items-center justify-center px-3 py-2 rounded-lg text-xs font-bold transition-all active:scale-95"
                                                :class="order.status === 'delivered' ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-500/30' : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                                <span class="material-symbols-outlined text-[15px]">print</span>
                                            </button>
                                        </div>
                                    </div>

                                    <!-- Tax Invoice -->
                                    <div class="flex flex-col gap-3 p-4 rounded-xl transition-all"
                                        :class="order.status === 'delivered'
                                            ? 'border border-blue-100 dark:border-blue-500/20 bg-gradient-to-br from-blue-50/60 to-white dark:from-blue-500/5 dark:to-transparent hover:border-blue-200 dark:hover:border-blue-400/30'
                                            : 'border border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-white/[0.02] opacity-50'">
                                        <div class="flex items-center gap-3">
                                            <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                                                :class="order.status === 'delivered' ? 'bg-blue-100 dark:bg-blue-500/20' : 'bg-gray-100 dark:bg-white/5'">
                                                <span class="material-symbols-outlined text-[22px]"
                                                    :class="order.status === 'delivered' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'">request_quote</span>
                                            </div>
                                            <div>
                                                <div class="text-sm font-bold text-gray-800 dark:text-white leading-tight">Tax Invoice</div>
                                                <div class="text-[11px] mt-0.5" :class="order.status === 'delivered' ? 'text-gray-400' : 'text-gray-400'">
                                                    {{ order.status === 'delivered' ? 'Official tax document' : 'Available after delivery' }}
                                                </div>
                                            </div>
                                        </div>
                                        <div class="flex gap-2">
                                            <button @click="openSlipWithData('finalTaxInvoice', order, authStore.currentUser)"
                                                :disabled="order.status !== 'delivered'"
                                                class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold transition-all active:scale-95"
                                                :class="order.status === 'delivered' ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                                <span class="material-symbols-outlined text-[15px]">download</span> Download
                                            </button>
                                            <button @click="printSlipWithData('finalTaxInvoice', order, authStore.currentUser)"
                                                :disabled="order.status !== 'delivered'"
                                                title="Print"
                                                class="flex items-center justify-center px-3 py-2 rounded-lg text-xs font-bold transition-all active:scale-95"
                                                :class="order.status === 'delivered' ? 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-500/30' : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                                <span class="material-symbols-outlined text-[15px]">print</span>
                                            </button>
                                        </div>
                                    </div>

                                </div>
                            </div>
                            <!-- Driver Rating (optional, delivered orders only) -->
                            <div v-if="order.status === 'delivered'" class="pt-2 border-t border-gray-200 dark:border-white/5">
                                <div v-if="order.customerRating" class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                    <span class="font-medium">Your rating:</span>
                                    <span v-for="n in 5" :key="n" class="text-base" :class="n <= order.customerRating ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
                                    <span v-if="order.customerFeedback" class="text-xs italic truncate max-w-[160px]">"{{ order.customerFeedback }}"</span>
                                </div>
                                <div v-else class="flex flex-wrap items-center gap-2">
                                    <span class="text-xs text-gray-500 dark:text-gray-400">Rate driver (optional):</span>
                                    <span v-for="n in 5" :key="n"
                                        @click="openRatingModal(order, n)"
                                        class="text-xl cursor-pointer transition-colors"
                                        :class="(ratingHover[order.backendId] || 0) >= n ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'"
                                        @mouseenter="ratingHover[order.backendId] = n"
                                        @mouseleave="ratingHover[order.backendId] = 0">★</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </transition>
            </div>
        </div>

        <div v-if="filteredOrders.length === 0" class="text-center py-16 text-gray-500 dark:text-gray-400">
            <span class="material-symbols-outlined text-5xl mb-2 block">receipt_long</span>
            <p class="font-medium">No orders found.</p>
        </div>

        <!-- Cancel Confirmation Modal -->
        <Teleport to="body">
            <CancelOrderModal />
        </Teleport>

        <!-- Reschedule Modal -->
        <Teleport to="body">
            <RescheduleModal />
        </Teleport>

        <!-- Driver Rating Modal -->
        <Teleport to="body">
            <DriverRatingModal />
        </Teleport>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl max-w-sm"
                    :class="toast.type === 'error' ? 'bg-red-600 text-white border border-red-500' : 'bg-green-600 text-white border border-green-500'">
                    <span class="material-symbols-outlined">{{ toast.type === 'error' ? 'error' : 'check_circle'
                        }}</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import CancelOrderModal from './orders/CancelOrderModal.vue'
import RescheduleModal from './orders/RescheduleModal.vue'
import DriverRatingModal from './orders/DriverRatingModal.vue'
import { individualOrdersPageKey } from './orders/individualOrdersPageContext'
import { ref, computed, reactive, onMounted, watch, provide } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const store = useIndividualStore()
const authStore = useAuthStore()
const { openSlipWithData, printSlipWithData } = useSlipPrinter()
const search = ref('')
const statusFilter = ref('all')
const expandedOrder = ref(null)
const ratingHover = ref({})

const filteredOrders = computed(() => {
    return store.orders.filter(o => {
        const s = !search.value || o.id.toLowerCase().includes(search.value.toLowerCase()) || o.cargoType.toLowerCase().includes(search.value.toLowerCase())
        const f = statusFilter.value === 'all' || o.status === statusFilter.value
        return s && f
    })
})

onMounted(() => {
    Promise.all([
        store.fetchOrders(),
        store.fetchDamageReports(),
    ])
})

watch(statusFilter, () => {
    store.fetchOrders(statusFilter.value)
})

function statusIcon(st) { return { 'delivered': 'check_circle', 'in-transit': 'local_shipping', 'dispatched': 'person_pin_circle', 'pending': 'schedule', 'cancelled': 'cancel' }[st] || 'package_2' }
function statusBg(st) { return { 'delivered': 'bg-green-500/20 text-green-500', 'in-transit': 'bg-blue-500/20 text-blue-500', 'dispatched': 'bg-purple-500/20 text-purple-500', 'pending': 'bg-amber-500/20 text-amber-500', 'cancelled': 'bg-red-500/20 text-red-500' }[st] || '' }
function statusBadge(st) { return { 'delivered': 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', 'in-transit': 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', 'dispatched': 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400', 'pending': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', 'cancelled': 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400' }[st] || '' }
function damageStatusLabel(st) { return { reported: 'Damage Reported', inspected: 'Under Review', resolved: 'Resolved', rejected: 'Rejected' }[String(st || '').toLowerCase()] || 'Damage Reported' }
function damageStatusBadge(st) { return { reported: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400', inspected: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400', resolved: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400', rejected: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400' }[String(st || '').toLowerCase()] || 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400' }

// Driver Rating
const ratingModal = reactive({ show: false, order: null, selected: 0, hover: 0, feedback: '' })
function openRatingModal(order, initialStar = 0) {
    Object.assign(ratingModal, { show: true, order, selected: initialStar, hover: 0, feedback: '' })
}
async function submitRatingModal() {
    if (!ratingModal.selected || !ratingModal.order?.backendId) return
    const result = await store.submitCustomerRating(ratingModal.order.backendId, ratingModal.selected, ratingModal.feedback || null)
    ratingModal.show = false
    if (result.success) {
        showToast('Thanks for rating your driver!', 'success')
    } else {
        showToast(result.message || 'Failed to submit rating.', 'error')
    }
}

// Cancel
const cancelModal = reactive({ show: false, order: null })
const estimatedCancelFee = computed(() => {
    if (!cancelModal.order) return 0
    if (cancelModal.order.status === 'pending') return 0
    if (cancelModal.order.progress < 30) return Math.round(cancelModal.order.cost.total * 0.10)
    return Math.round(cancelModal.order.cost.total * 0.25)
})
const estimatedWalletRefund = computed(() => {
    if (!cancelModal.order) return 0
    const paid = cancelModal.order.cost?.paid ?? cancelModal.order.cost?.total ?? 0
    return Math.max(paid - estimatedCancelFee.value, 0)
})
function showCancelModal(order) { cancelModal.order = order; cancelModal.show = true }
async function doCancel() {
    const result = await store.cancelOrderRemote(cancelModal.order.id)
    cancelModal.show = false
    if (!result.success) {
        showToast(result.message || 'Failed to cancel order.', 'error')
        return
    }
    const fee = result.order?.cancellation?.fee || 0
    const refund = result.walletRefund ?? 0
    if (refund > 0) {
        showToast(`Cancelled. ₹${refund.toLocaleString()} refunded to your wallet.`, 'success')
    } else {
        showToast(fee > 0 ? `Cancelled. Fee: ₹${fee.toLocaleString()}` : 'Cancelled — no fee.', fee > 0 ? 'error' : 'success')
    }
}

// Reschedule
const rescheduleModal = reactive({ show: false, order: null, date: '', time: '09:00 AM - 12:00 PM' })
function showRescheduleModal(order) { Object.assign(rescheduleModal, { show: true, order, date: '', time: '09:00 AM - 12:00 PM' }) }
async function doReschedule() {
    const { id } = rescheduleModal.order
    const { date, time } = rescheduleModal
    rescheduleModal.show = false
    const result = await store.rescheduleOrderRemote(id, date, time)
    if (result.success) {
        showToast('Rescheduled successfully!', 'success')
    } else {
        showToast(result.message || 'Failed to reschedule. Please try again.', 'error')
    }
}

const toast = reactive({ show: false, message: '', type: 'success' })
function showToast(msg, type = 'success') { toast.show = true; toast.message = msg; toast.type = type; setTimeout(() => { toast.show = false }, 3000) }

provide(individualOrdersPageKey, {
    cancelModal,
    doCancel,
    doReschedule,
    estimatedCancelFee,
    estimatedWalletRefund,
    ratingModal,
    rescheduleModal,
    submitRatingModal,
})
</script>
