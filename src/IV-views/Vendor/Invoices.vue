<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Invoices & Billing</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage payments, invoices, and billing history</p>
            </div>
            <div class="flex gap-3">
                <button @click="openSlipWithData('finalTaxInvoice', store.shipments.find(s => s.id === store.invoices[0]?.orderId), authStore.currentUser)"
                    :disabled="!store.invoices.length"
                    class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[16px]">request_quote</span> Tax Invoice
                </button>
                <button @click="exportReport" class="px-4 py-2 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[16px]">download</span> Export
                </button>
                <button @click="payAllDue" :disabled="store.totalUnpaid === 0" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                    <span class="material-symbols-outlined text-[16px]">payments</span> Pay All Due
                </button>
            </div>
        </div>

        <div class="glass-panel p-3 rounded-xl border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/10">
            <p class="text-xs text-amber-800 dark:text-amber-300 font-medium">
                Recurring auto-debit works only via wallet. Enable auto-debit in Recurring Schedules and keep enough wallet balance before the scheduled date/time.
            </p>
        </div>

        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-xl border-l-4 border-red-500">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase mb-1">Overdue</div>
                <div class="text-2xl font-bold text-red-500">₹{{ store.totalOverdue.toLocaleString() }}</div>
                <div class="text-xs text-red-400 mt-1">{{ store.overdueInvoices.length }} invoice(s)</div>
            </div>
            <div class="glass-panel p-5 rounded-xl border-l-4 border-blue-500">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase mb-1">Unpaid</div>
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ store.totalUnpaid }}</div>
                <div class="text-xs text-blue-400 mt-1">Pending settlement</div>
            </div>
            <div class="glass-panel p-5 rounded-xl border-l-4 border-green-500">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase mb-1">Paid This Month</div>
                <div class="text-2xl font-bold text-green-500">₹{{ store.totalPaidThisMonth.toLocaleString() }}</div>
                <div class="text-xs text-green-400 mt-1">Successful transactions</div>
            </div>
            <div class="glass-panel p-5 rounded-xl border-l-4 border-purple-500">
                <div class="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase mb-1">Credit Balance</div>
                <div class="text-2xl font-bold text-purple-500">₹{{ store.creditBalance.toLocaleString() }}</div>
                <div class="text-xs text-purple-400 mt-1">Available credit</div>
            </div>
        </div>

        <!-- Filters -->
        <div class="glass-panel p-4 rounded-xl flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            <div class="relative flex-1">
                <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search invoice ID, order ID..."
                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
            <select v-model="statusFilter" class="text-sm bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
                <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">All Status</option>
                <option value="Unpaid" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Unpaid</option>
                <option value="Overdue" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Overdue</option>
                <option value="Partial" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Partial</option>
                <option value="Paid" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Paid</option>
            </select>
        </div>

        <!-- Invoices Table -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm min-w-[700px]">
                    <thead class="bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 text-xs uppercase">
                        <tr>
                            <th class="px-5 py-3">Invoice #</th>
                            <th class="px-5 py-3">Order</th>
                            <th class="px-5 py-3">Date</th>
                            <th class="px-5 py-3">Due Date</th>
                            <th class="px-5 py-3 text-right">Amount</th>
                            <th class="px-5 py-3 text-right">Paid</th>
                            <th class="px-5 py-3">Status</th>
                            <th class="px-5 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-if="filteredInvoices.length === 0">
                            <td colspan="8" class="px-5 py-8 text-center text-gray-500 dark:text-gray-400">No invoices found</td>
                        </tr>
                        <tr v-for="inv in filteredInvoices" :key="inv.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="px-5 py-3 font-mono text-blue-500 text-xs font-bold">{{ inv.id }}</td>
                            <td class="px-5 py-3 text-gray-600 dark:text-gray-300 text-xs">{{ inv.orderId }}</td>
                            <td class="px-5 py-3 text-gray-500 dark:text-gray-400 text-xs">{{ inv.date }}</td>
                            <td class="px-5 py-3 text-xs" :class="inv.status === 'Overdue' ? 'text-red-500 font-bold' : 'text-gray-500 dark:text-gray-400'">{{ inv.dueDate }}</td>
                            <td class="px-5 py-3 text-right font-bold text-gray-900 dark:text-white text-xs">₹{{ inv.amount.toLocaleString() }}</td>
                            <td class="px-5 py-3 text-right text-xs" :class="inv.paid > 0 ? 'text-green-500 font-bold' : 'text-gray-400'">₹{{ inv.paid.toLocaleString() }}</td>
                            <td class="px-5 py-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="invoiceStatusClass(inv.status)">{{ inv.status }}</span></td>
                            <td class="px-5 py-3 text-right">
                                <div class="flex items-center justify-end gap-1">
                                    <button @click="viewInvoice(inv)" class="p-1.5 rounded-lg hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="View">
                                        <span class="material-symbols-outlined text-[16px]">visibility</span>
                                    </button>
                                    <button v-if="inv.status !== 'Paid'" @click="openPayModal(inv)" class="p-1.5 rounded-lg hover:bg-green-500/10 text-gray-400 hover:text-green-500 transition-colors" title="Pay">
                                        <span class="material-symbols-outlined text-[16px]">payments</span>
                                    </button>
                                    <button @click="openSlipWithData('finalTaxInvoice', store.shipments.find(s => s.id === inv.orderId), authStore.currentUser)" class="p-1.5 rounded-lg hover:bg-green-500/10 text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors" title="Download Invoice">
                                        <span class="material-symbols-outlined text-[16px]">request_quote</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Invoice Detail Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="!!viewingInvoice" @close="viewingInvoice = null">
                <template #title>Invoice {{ viewingInvoice?.id }}</template>
                <div v-if="viewingInvoice" class="space-y-4">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Order</div><div class="text-sm font-bold text-gray-900 dark:text-white">{{ viewingInvoice.orderId }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Status</div><span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="invoiceStatusClass(viewingInvoice.status)">{{ viewingInvoice.status }}</span></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Issue Date</div><div class="text-sm font-medium text-gray-900 dark:text-white">{{ viewingInvoice.date }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-xs text-gray-500 mb-1">Due Date</div><div class="text-sm font-medium text-gray-900 dark:text-white">{{ viewingInvoice.dueDate }}</div></div>
                    </div>
                    <div class="border-t border-gray-200 dark:border-white/10 pt-4 space-y-2">
                        <div class="flex justify-between text-sm"><span class="text-gray-500">Total Amount</span><span class="font-bold text-gray-900 dark:text-white">₹{{ viewingInvoice.amount.toLocaleString() }}</span></div>
                        <div class="flex justify-between text-sm"><span class="text-gray-500">Paid Amount</span><span class="font-bold text-green-500">₹{{ viewingInvoice.paid.toLocaleString() }}</span></div>
                        <div class="flex justify-between text-sm border-t border-gray-200 dark:border-white/10 pt-2"><span class="text-gray-500 font-bold">Balance Due</span><span class="font-bold text-red-500">₹{{ (viewingInvoice.amount - viewingInvoice.paid).toLocaleString() }}</span></div>
                    </div>
                </div>
                <template #footer>
                    <button @click="viewingInvoice = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    <button @click="openSlipWithData('finalTaxInvoice', store.shipments.find(s => s.id === viewingInvoice.orderId), authStore.currentUser)"
                        class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[15px]">request_quote</span> Download Invoice
                    </button>
                    <button v-if="viewingInvoice?.status !== 'Paid'" @click="openPayModal(viewingInvoice); viewingInvoice = null" class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-bold hover:bg-green-700 transition-colors">Make Payment</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Razorpay Checkout for Invoice Payment -->
        <RazorpayCheckout
            v-model="showPayModal"
            :amount="payingInvoice ? (payingInvoice.amount - payingInvoice.paid) : 0"
            :order-id="payingInvoice?.orderId || ''"
            :description="payingInvoice ? ('Invoice ' + payingInvoice.id) : ''"
            :name="authStore.currentUser?.name || ''"
            :email="authStore.currentUser?.email || ''"
            :wallet-balance="store.walletBalance"
            @success="onRazorpaySuccess"
        />
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlip, openSlipWithData } = useSlipPrinter()
const authStore = useAuthStore()

const store = useVendorStore()
const searchQuery = ref('')
const statusFilter = ref('all')
const viewingInvoice = ref(null)
const showPayModal = ref(false)
const payingInvoice = ref(null)

const filteredInvoices = computed(() => {
    let list = store.invoices
    if (statusFilter.value !== 'all') list = list.filter(i => i.status === statusFilter.value)
    if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(i => i.id.toLowerCase().includes(q) || i.orderId.toLowerCase().includes(q))
    }
    return list
})

const invoiceStatusClass = s => ({
    Unpaid: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    Overdue: 'bg-red-500/20 text-red-600 dark:text-red-400',
    Partial: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    Paid: 'bg-green-500/20 text-green-600 dark:text-green-400',
}[s] || 'bg-gray-500/20 text-gray-500')

function viewInvoice(inv) {
    viewingInvoice.value = inv
}

function openPayModal(inv) {
    payingInvoice.value = inv
    showPayModal.value = true
    showToast('Tip: For next recurring run, enable Wallet Auto-Debit in Recurring Schedules and keep sufficient wallet balance.', 'warning')
}

async function onRazorpaySuccess({ payment_id, method, amount }) {
    if (!payingInvoice.value) return
    const ok = await store.payInvoice(payingInvoice.value.id, amount, method)
    payingInvoice.value = null
    showToast(ok ? `Payment of ₹${amount.toLocaleString()} recorded! (${payment_id})` : 'Payment failed — please try again')
}

async function payAllDue() {
    if (!confirm('Pay all outstanding invoices?')) return
    const unpaid = store.invoices.filter(i => i.status !== 'Paid')
    await Promise.all(unpaid.map(inv => store.payInvoice(inv.id, inv.amount - inv.paid, 'Bank Transfer')))
    showToast('All invoices settled')
}

function downloadInvoice(inv) {
    openSlipWithData('finalTaxInvoice', store.shipments.find(s => s.id === inv.orderId), authStore.currentUser)
}

function exportReport() {
    const rows = [
        ['Invoice #', 'Order ID', 'Date', 'Due Date', 'Amount', 'Paid', 'Balance', 'Status'],
        ...filteredInvoices.value.map(inv => [
            inv.id,
            inv.orderId,
            inv.date,
            inv.dueDate,
            inv.amount,
            inv.paid,
            inv.amount - inv.paid,
            inv.status,
        ])
    ]
    downloadCsv(`invoices_${new Date().toISOString().slice(0, 10)}.csv`, rows)
}

function downloadCsv(filename, rows) {
    const csv = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    const cls = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-amber-600',
    }[type] || 'bg-green-500'
    t.className = `fixed right-4 bottom-4 z-[9999] ${cls} text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

</script>
