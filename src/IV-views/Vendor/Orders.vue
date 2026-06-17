<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Order Management</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">View, manage, and take actions on all your shipment orders</p>
            </div>
            <router-link to="/vendor/create-shipment" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2 w-fit">
                <span class="material-symbols-outlined text-[16px]">add</span> New Order
            </router-link>
        </div>

        <!-- Summary Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-xs text-gray-500 mb-1">Total</div>
                <div class="text-xl font-bold text-gray-900 dark:text-white">{{ store.shipments.length }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-xs text-gray-500 mb-1">Pending</div>
                <div class="text-xl font-bold text-yellow-500">{{ store.pendingShipments.length }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-xs text-gray-500 mb-1">In Transit</div>
                <div class="text-xl font-bold text-blue-500">{{ inTransitCount }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-xs text-gray-500 mb-1">Delivered</div>
                <div class="text-xl font-bold text-green-500">{{ store.deliveredShipments.length }}</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-xs text-gray-500 mb-1">Cancelled</div>
                <div class="text-xl font-bold text-red-500">{{ cancelledCount }}</div>
            </div>
        </div>

        <!-- Filters -->
        <div class="glass-panel p-4 rounded-xl flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            <div class="relative flex-1">
                <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search order ID, origin, destination..."
                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <select v-model="statusFilter" class="text-sm bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none">
                <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Status</option>
                <option value="Pending" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pending</option>
                <option value="In Warehouse" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Warehouse</option>
                <option value="In Transit" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">In Transit</option>
                <option value="Delivered" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Delivered</option>
                <option value="Cancelled" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Cancelled</option>
            </select>
            <select v-model="categoryFilter" class="text-sm bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none">
                <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Categories</option>
                <option value="B2B" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">B2B</option>
                <option value="B2C" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">B2C</option>
                <option value="Pallets" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Pallets</option>
                <option value="Commercial" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Commercial</option>
            </select>
        </div>

        <!-- Orders Table -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm min-w-[900px]">
                    <thead class="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 uppercase text-[10px]">
                        <tr>
                            <th class="px-4 py-3">Order ID</th>
                            <th class="px-4 py-3">Route</th>
                            <th class="px-4 py-3">Category</th>
                            <th class="px-4 py-3">Weight</th>
                            <th class="px-4 py-3">ETA</th>
                            <th class="px-4 py-3">Status</th>
                            <th class="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-if="filteredOrders.length === 0">
                            <td colspan="7" class="px-4 py-8 text-center text-gray-400 text-sm">No orders found</td>
                        </tr>
                        <tr v-for="s in filteredOrders" :key="s.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="px-4 py-3 font-mono text-blue-500 text-xs font-bold">{{ s.id }}</td>
                            <td class="px-4 py-3">
                                <div class="text-xs text-gray-900 dark:text-white font-medium">{{ s.origin }}</div>
                                <div class="text-[10px] text-gray-500">→ {{ s.destination }}</div>
                            </td>
                            <td class="px-4 py-3">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-500">{{ s.category || 'B2B' }}</span>
                            </td>
                            <td class="px-4 py-3 text-gray-600 dark:text-gray-300 text-xs">{{ s.weight }}</td>
                            <td class="px-4 py-3 text-gray-600 dark:text-gray-300 text-xs">{{ s.eta }}</td>
                            <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="statusClass(s.status)">{{ s.status }}</span></td>
                            <td class="px-4 py-3 text-right">
                                <div class="flex items-center justify-end gap-1">
                                    <button @click="openDetail(s)" class="p-1.5 rounded-lg hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="View">
                                        <span class="material-symbols-outlined text-[16px]">visibility</span>
                                    </button>
                                    <button @click="openSlipWithData('bookingConfirmation', s, currentUser())" class="p-1.5 rounded-lg hover:bg-indigo-500/10 text-gray-400 hover:text-indigo-500 transition-colors" title="Booking Confirmation">
                                        <span class="material-symbols-outlined text-[16px]">receipt_long</span>
                                    </button>
                                    <button v-if="s.status === 'Delivered'" @click="openSlipWithData('finalTaxInvoice', s, currentUser())" class="p-1.5 rounded-lg hover:bg-green-500/10 text-gray-400 hover:text-green-500 transition-colors" title="Tax Invoice">
                                        <span class="material-symbols-outlined text-[16px]">request_quote</span>
                                    </button>
                                    <button v-if="s.status !== 'Delivered' && s.status !== 'Cancelled'" @click="openAddressModal(s)" class="p-1.5 rounded-lg hover:bg-yellow-500/10 text-gray-400 hover:text-yellow-500 transition-colors" title="Update Address">
                                        <span class="material-symbols-outlined text-[16px]">edit_location</span>
                                    </button>
                                    <button v-if="s.status !== 'Delivered' && s.status !== 'Cancelled'" @click="openRescheduleModal(s)" class="p-1.5 rounded-lg hover:bg-purple-500/10 text-gray-400 hover:text-purple-500 transition-colors" title="Reschedule">
                                        <span class="material-symbols-outlined text-[16px]">schedule</span>
                                    </button>
                                    <button v-if="s.status === 'Delivered'" @click="openDamageModal(s)" class="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors" title="Report Damage">
                                        <span class="material-symbols-outlined text-[16px]">report</span>
                                    </button>
                                    <button v-if="s.status === 'Delivered' && !s.customerRating" @click="openVendorRatingModal(s)" class="p-1.5 rounded-lg hover:bg-amber-500/10 text-gray-400 hover:text-amber-500 transition-colors" title="Rate Driver">
                                        <span class="material-symbols-outlined text-[16px]">star</span>
                                    </button>
                                    <span v-if="s.status === 'Delivered' && s.customerRating" class="p-1.5 text-amber-400 cursor-default" :title="`Rated ${s.customerRating}/5`">
                                        <span class="material-symbols-outlined text-[16px]">star</span>
                                    </span>
                                    <button v-if="s.status !== 'Delivered' && s.status !== 'Cancelled' && s.status !== 'In Transit'" @click="cancelOrder(s)" class="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors" title="Cancel">
                                        <span class="material-symbols-outlined text-[16px]">cancel</span>
                                    </button>
                                    <span v-if="s.status === 'In Transit'" class="p-1.5 text-amber-400 cursor-default" title="This order is already in progress. Please contact support to request changes or cancellation.">
                                        <span class="material-symbols-outlined text-[16px]">info</span>
                                    </span>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Order Detail Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="!!detailOrder" @close="detailOrder = null">
                <template #title>Order {{ detailOrder?.id }}</template>
                <div v-if="detailOrder" class="space-y-4">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Origin</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailOrder.origin }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Destination</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailOrder.destination }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Weight</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailOrder.weight }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">ETA</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailOrder.eta }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Status</div><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="statusClass(detailOrder.status)">{{ detailOrder.status }}</span></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Category</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailOrder.category || 'B2B' }}</div></div>
                        <div v-if="detailOrder.description" class="col-span-2 p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Description</div><div class="text-xs text-gray-700 dark:text-gray-300">{{ detailOrder.description }}</div></div>
                    </div>

                    <!-- Status Timeline -->
                    <div v-if="detailOrder.statusHistory?.length" class="border-t border-gray-200 dark:border-white/10 pt-3">
                        <div class="text-xs font-bold text-gray-900 dark:text-white mb-2">Status History</div>
                        <div class="space-y-2">
                            <div v-for="(h, i) in detailOrder.statusHistory" :key="i" class="flex items-center gap-3">
                                <div class="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0"></div>
                                <div class="flex-1 text-xs text-gray-600 dark:text-gray-300">{{ h.status }}</div>
                                <div class="text-[10px] text-gray-400">{{ h.time }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- PoD -->
                    <div v-if="detailOrder.pod" class="border-t border-gray-200 dark:border-white/10 pt-3">
                        <div class="text-xs font-bold text-gray-900 dark:text-white mb-2">Proof of Delivery</div>
                        <div class="flex items-center gap-3 p-3 bg-green-500/10 rounded-lg">
                            <span class="material-symbols-outlined text-green-500">verified</span>
                            <div>
                                <div class="text-xs font-bold text-green-600 dark:text-green-400">Delivered & Signed</div>
                                <div class="text-[10px] text-gray-500">{{ detailOrder.pod.signedBy }} • {{ detailOrder.pod.time }}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <template #footer>
                    <button @click="detailOrder = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    <button @click="openSlipWithData('bookingConfirmation', detailOrder, currentUser())" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[15px]">receipt_long</span> Booking Slip
                    </button>
                    <button v-if="detailOrder?.status === 'Delivered'" @click="openSlipWithData('proofOfDelivery', detailOrder, currentUser())" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[15px]">verified</span> PoD
                    </button>
                    <button v-if="detailOrder?.status === 'Delivered'" @click="openSlipWithData('finalTaxInvoice', detailOrder, currentUser())" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[15px]">request_quote</span> Invoice
                    </button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Address Update Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showAddressModal" @close="showAddressModal = false">
                <template #title>Update Delivery Address — {{ addressOrder?.id }}</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current Destination</label>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-700 dark:text-gray-300">{{ addressOrder?.destination }}</div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Address *</label>
                        <textarea v-model="newAddress" rows="3" placeholder="Enter new delivery address..." class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Reason</label>
                        <select v-model="addressReason" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Customer moved</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Incorrect address</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Area inaccessible</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Customer request</option>
                        </select>
                    </div>
                </div>
                <template #footer>
                    <button @click="showAddressModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitAddressUpdate" :disabled="!newAddress.trim()" class="px-4 py-2 bg-yellow-600 text-white rounded-lg text-sm font-bold hover:bg-yellow-700 transition-colors disabled:opacity-50">Update Address</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Reschedule Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showRescheduleModal" @close="showRescheduleModal = false">
                <template #title>Reschedule — {{ rescheduleOrder?.id }}</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current ETA</label>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-700 dark:text-gray-300">{{ rescheduleOrder?.eta }}</div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Date *</label>
                        <input v-model="newDate" type="date" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Reason</label>
                        <select v-model="rescheduleReason" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Customer not available</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Weather delay</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Vehicle breakdown</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Port delay</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Vendor request</option>
                        </select>
                    </div>
                </div>
                <template #footer>
                    <button @click="showRescheduleModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitReschedule" :disabled="!newDate" class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-bold hover:bg-purple-700 transition-colors disabled:opacity-50">Reschedule</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Damage Report Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showDamageModal" @close="showDamageModal = false">
                <template #title>Report Damage — {{ damageOrder?.id }}</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Severity *</label>
                        <div class="flex gap-2">
                            <label v-for="sev in ['Minor', 'Moderate', 'Severe']" :key="sev" class="flex-1 text-center px-3 py-2 rounded-lg border cursor-pointer text-xs font-bold transition-colors" :class="damageSeverity === sev ? severityBorderClass(sev) : 'border-gray-200 dark:border-white/10 text-gray-500'">
                                <input type="radio" :value="sev" v-model="damageSeverity" class="sr-only">{{ sev }}
                            </label>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description *</label>
                        <textarea v-model="damageDescription" rows="3" placeholder="Describe the damage..." class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                    <div class="p-3 bg-yellow-500/10 rounded-lg">
                        <div class="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">info</span>
                            A reverse logistics ticket will be auto-created for claims processing.
                        </div>
                    </div>
                </div>
                <template #footer>
                    <button @click="showDamageModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitDamageReport" :disabled="!damageDescription.trim()" class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 transition-colors disabled:opacity-50">Submit Report</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Driver Rating Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="vendorRatingModal.show" @close="vendorRatingModal.show = false">
                <template #title>Rate Your Driver</template>
                <div class="space-y-4 text-center">
                    <p class="text-sm text-gray-500 dark:text-gray-400">How was your experience? (optional)</p>
                    <div class="flex justify-center gap-2">
                        <span v-for="n in 5" :key="n"
                            @click="vendorRatingModal.selected = n"
                            @mouseenter="vendorRatingModal.hover = n"
                            @mouseleave="vendorRatingModal.hover = 0"
                            class="text-4xl cursor-pointer transition-colors select-none"
                            :class="(vendorRatingModal.hover || vendorRatingModal.selected) >= n ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
                    </div>
                    <textarea v-model="vendorRatingModal.feedback" rows="2" placeholder="Leave a comment (optional)"
                        class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-400/50 outline-none resize-none" />
                </div>
                <template #footer>
                    <div class="flex gap-3 w-full">
                        <button @click="submitVendorRating" :disabled="!vendorRatingModal.selected"
                            class="flex-1 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 text-sm font-bold disabled:opacity-40">Submit Rating</button>
                        <button @click="vendorRatingModal.show = false"
                            class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm">Skip</button>
                    </div>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlip, openSlipWithData } = useSlipPrinter()

const store = useVendorStore()
const authStore = useAuthStore()

function currentUser() {
  return authStore.currentUser || {}
}
const searchQuery = ref('')
const statusFilter = ref('all')
const categoryFilter = ref('all')

const detailOrder = ref(null)
const showAddressModal = ref(false)
const addressOrder = ref(null)
const newAddress = ref('')
const addressReason = ref('Customer request')

const showRescheduleModal = ref(false)
const rescheduleOrder = ref(null)
const newDate = ref('')
const rescheduleReason = ref('Customer not available')

const showDamageModal = ref(false)
const damageOrder = ref(null)
const damageSeverity = ref('Moderate')
const damageDescription = ref('')

const inTransitCount = computed(() => store.shipments.filter(s => s.status === 'In Transit').length)
const cancelledCount = computed(() => store.shipments.filter(s => s.status === 'Cancelled').length)

const filteredOrders = computed(() => {
    let list = store.shipments
    if (statusFilter.value !== 'all') list = list.filter(s => s.status === statusFilter.value)
    if (categoryFilter.value !== 'all') list = list.filter(s => (s.category || 'B2B') === categoryFilter.value)
    if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(s => s.id.toLowerCase().includes(q) || s.origin.toLowerCase().includes(q) || s.destination.toLowerCase().includes(q))
    }
    return list
})

const statusClass = s => ({
    Pending: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    'In Warehouse': 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
    'In Transit': 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    Delivered: 'bg-green-500/20 text-green-600 dark:text-green-400',
    Cancelled: 'bg-red-500/20 text-red-600 dark:text-red-400',
}[s] || 'bg-gray-500/20 text-gray-500')

const severityBorderClass = sev => ({
    Minor: 'border-yellow-500 bg-yellow-500/10 text-yellow-600',
    Moderate: 'border-orange-500 bg-orange-500/10 text-orange-600',
    Severe: 'border-red-500 bg-red-500/10 text-red-600',
}[sev])

function openDetail(s) { detailOrder.value = s }

function openAddressModal(s) {
    addressOrder.value = s
    newAddress.value = ''
    addressReason.value = 'Customer request'
    showAddressModal.value = true
}

async function submitAddressUpdate() {
    if (!newAddress.value.trim() || !addressOrder.value) return
    await store.updateShipmentAddress(addressOrder.value.id, newAddress.value.trim())
    showAddressModal.value = false
    showToast('Address updated')
}

function openRescheduleModal(s) {
    rescheduleOrder.value = s
    newDate.value = ''
    rescheduleReason.value = 'Customer not available'
    showRescheduleModal.value = true
}

async function submitReschedule() {
    if (!newDate.value || !rescheduleOrder.value) return
    await store.rescheduleShipment(rescheduleOrder.value.id, newDate.value)
    showRescheduleModal.value = false
    showToast('Shipment rescheduled')
}

function openDamageModal(s) {
    damageOrder.value = s
    damageSeverity.value = 'Moderate'
    damageDescription.value = ''
    showDamageModal.value = true
}

async function submitDamageReport() {
    if (!damageDescription.value.trim() || !damageOrder.value) return
    await store.reportDamage({ shipmentId: damageOrder.value.id, severity: damageSeverity.value, description: damageDescription.value.trim() })
    showDamageModal.value = false
    showToast('Damage reported — reverse logistics ticket created')
}

async function cancelOrder(s) {
    if (!confirm(`Cancel order ${s.id}?\n\nIf you already paid online, the amount will be refunded to your wallet.`)) return
    const result = await store.cancelShipment(s.id)
    if (!result.success) {
        showToast(result.message || `Failed to cancel ${s.id}`, 'error')
        return
    }
    const refund = result.walletRefund ?? 0
    showToast(refund > 0 ? `Order ${s.id} cancelled. ₹${refund.toLocaleString()} refunded to wallet.` : `Order ${s.id} cancelled.`)
}

// Driver Rating
const vendorRatingModal = reactive({ show: false, order: null, selected: 0, hover: 0, feedback: '' })
function openVendorRatingModal(s) {
    Object.assign(vendorRatingModal, { show: true, order: s, selected: 0, hover: 0, feedback: '' })
}
async function submitVendorRating() {
    if (!vendorRatingModal.selected || !vendorRatingModal.order?.backendId) return
    const result = await store.submitCustomerRating(vendorRatingModal.order.backendId, vendorRatingModal.selected, vendorRatingModal.feedback || null)
    vendorRatingModal.show = false
    showToast(result.success ? 'Thanks for rating your driver!' : (result.message || 'Failed to submit rating.'), result.success ? 'success' : 'error')
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    const bg = type === 'error' ? 'bg-red-500' : 'bg-green-500'
    t.className = `fixed right-4 bottom-4 z-[9999] ${bg} text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

</script>
