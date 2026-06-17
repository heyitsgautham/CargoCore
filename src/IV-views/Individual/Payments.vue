<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Payments</h2>
            <div class="flex gap-3">
                <div class="glass-panel px-4 py-2 rounded-lg text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">Total Paid</div>
                    <div class="text-lg font-bold text-green-600 dark:text-green-400">₹{{ totalPaid.toLocaleString() }}
                    </div>
                </div>
                <div class="glass-panel px-4 py-2 rounded-lg text-center">
                    <div class="text-xs text-gray-500 dark:text-gray-400">Pending</div>
                    <div class="text-lg font-bold text-amber-500">₹{{ pendingAmount.toLocaleString() }}</div>
                </div>
            </div>
        </div>

        <!-- Payment History -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 sm:p-5 border-b border-gray-200 dark:border-white/5">
                <h3 class="font-bold text-gray-900 dark:text-white">Payment History</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr
                            class="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-white/5">
                            <th class="py-3 px-5 font-medium">Payment ID</th>
                            <th class="py-3 px-5 font-medium">Order</th>
                            <th class="py-3 px-5 font-medium hidden sm:table-cell">Mode</th>
                            <th class="py-3 px-5 font-medium">Amount</th>
                            <th class="py-3 px-5 font-medium">Status</th>
                            <th class="py-3 px-5 font-medium text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="p in store.payments" :key="p.id"
                            class="border-b border-gray-100 dark:border-white/5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="py-3 px-5 font-mono font-bold text-gray-700 dark:text-gray-300">{{ p.id }}</td>
                            <td class="py-3 px-5 font-mono text-green-600 dark:text-green-400 font-bold">{{ p.orderId }}
                            </td>
                            <td class="py-3 px-5 text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                                <span class="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-white/10">{{
                                    p.mode }}</span>
                            </td>
                            <td class="py-3 px-5 font-bold text-gray-900 dark:text-white font-mono">₹{{
                                p.amount.toLocaleString() }}</td>
                            <td class="py-3 px-5">
                                <span
                                    class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400">
                                    {{ p.status }}
                                </span>
                            </td>
                            <td class="py-3 px-5 text-right">
                                <button @click="viewDetail(p)"
                                    class="text-green-600 dark:text-green-400 text-xs font-bold hover:underline">View</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Pending Payments -->
        <div v-if="pendingPayments.length > 0" class="glass-panel p-4 sm:p-5 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-amber-500">pending</span> Pending Payments
            </h3>
            <div class="space-y-3">
                <div v-for="order in pendingPayments" :key="order.id"
                    class="flex items-center justify-between p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                    <div>
                        <span class="font-mono font-bold text-gray-900 dark:text-white">{{ order.id }}</span>
                        <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">₹{{
                            order.cost.total.toLocaleString() }}</span>
                    </div>
                    <button @click="initiatePayment(order)"
                        class="px-4 py-1.5 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors">Pay
                        Now</button>
                </div>
            </div>
        </div>

        <!-- Payment Detail Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="detailModal.show" @close="detailModal.show = false">
                <template #title>Payment Details</template>
                <div class="space-y-4" v-if="detailModal.payment">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500">Payment ID</div>
                            <div class="font-mono font-bold text-sm text-gray-900 dark:text-white">{{
                                detailModal.payment.id }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500">Order</div>
                            <div class="font-mono font-bold text-sm text-green-600 dark:text-green-400">{{
                                detailModal.payment.orderId
                            }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500">Amount</div>
                            <div class="font-bold text-sm text-gray-900 dark:text-white">₹{{
                                detailModal.payment.amount.toLocaleString()
                            }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500">Mode</div>
                            <div class="font-medium text-sm text-gray-900 dark:text-white">{{ detailModal.payment.mode
                            }}</div>
                        </div>
                    </div>
                    <button @click="openSlipWithData('finalTaxInvoice', store.orders.find(o => o.id === detailModal.payment.orderId), authStore.currentUser)"
                        class="w-full py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-2">
                        <span class="material-symbols-outlined text-sm">download</span> Download Invoice
                    </button>
                </div>
                <template #footer>
                    <button @click="detailModal.show = false"
                        class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Close</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Razorpay Checkout -->
        <RazorpayCheckout
            v-model="showPaymentModal"
            :amount="selectedOrder ? selectedOrder.cost.total : 0"
            :order-id="selectedOrder ? selectedOrder.id : ''"
            :description="selectedOrder ? ('Order ' + selectedOrder.id) : ''"
            :name="authStore.currentUser?.name || ''"
            :email="authStore.currentUser?.email || ''"
            :wallet-balance="store.walletBalance"
            @success="onRazorpaySuccess"
        />


        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl bg-green-600 text-white border border-green-500 max-w-sm">
                    <span class="material-symbols-outlined">check_circle</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import BaseModal from '@/components/BaseModal.vue'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'

const store = useIndividualStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()

const totalPaid = computed(() => store.paymentsSummary?.total_paid ?? store.payments.filter(p => p.status === 'completed').reduce((s, p) => s + p.amount, 0))
const pendingAmount = computed(() => store.paymentsSummary?.pending_amount ?? store.orders.filter(o => o.paymentStatus === 'pending').reduce((s, o) => s + o.cost.total, 0))
const pendingPayments = computed(() => store.orders.filter(o => o.paymentStatus === 'pending'))

const detailModal = reactive({ show: false, payment: null })
function viewDetail(p) { detailModal.payment = p; detailModal.show = true }

const showPaymentModal = ref(false)
const isProcessingPayment = ref(false)
const selectedOrder = ref(null)

function initiatePayment(order) {
    selectedOrder.value = order
    showPaymentModal.value = true
}

function onRazorpaySuccess({ payment_id, method, amount }) {
    showPaymentModal.value = false
    store.makePayment(selectedOrder.value.id, amount, method, false, payment_id)
    showToast(`₹${amount.toLocaleString()} paid via ${method}! (${payment_id})`)
    selectedOrder.value = null
}

const toast = reactive({ show: false, message: '' })
function showToast(msg) { toast.show = true; toast.message = msg; setTimeout(() => { toast.show = false }, 3000) }

onMounted(async () => {
    await Promise.all([
        store.fetchOrders(),
        store.fetchPaymentsSummary(),
    ])
})
</script>
