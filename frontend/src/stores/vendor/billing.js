// Wallet balance, top-ups and invoice payments.
import { API_BASE, clearLegacyWalletTopupOffset, getAuthHeaders } from './api'

export function useVendorBilling({
    dashboard,
    error,
    invoices,
    rebuildNotifications,
    walletBalance,
}) {
    async function fetchWalletBalance() {
        try {
            const res = await fetch(`${API_BASE}/vendor/wallet`, {
                headers: getAuthHeaders(),
            })
            if (res.ok) {
                const data = await res.json()
                walletBalance.value = Number(data.balance ?? 0)
                if (dashboard.value?.stats) {
                    dashboard.value.stats.credit_balance = walletBalance.value
                }
            }
        } catch (e) { /* silent */ }
    }

    async function payInvoice(id, amount, paymentMethod = 'Bank Transfer') {
        const invoice = invoices.value.find((item) => item.id === id)
        if (!invoice) return false

        // Optimistic update
        const nextPaid = Math.min(invoice.amount, invoice.paid + amount)
        const prevPaid = invoice.paid
        const prevStatus = invoice.status
        invoice.paid = nextPaid
        invoice.status = nextPaid >= invoice.amount ? 'Paid' : 'Partial'

        try {
            const res = await fetch(`${API_BASE}/vendor/invoices/${invoice.backendOrderId}/pay`, {
                method: 'POST',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ amount, payment_method: paymentMethod }),
            })
            if (!res.ok) {
                // Rollback on failure
                invoice.paid = prevPaid
                invoice.status = prevStatus
                return false
            }
            const updated = await res.json()
            invoice.paid = updated.paid ?? nextPaid
            invoice.status = updated.status ?? invoice.status
            rebuildNotifications()
            return true
        } catch {
            invoice.paid = prevPaid
            invoice.status = prevStatus
            return false
        }
    }

    function recordCODPayment(orderId, amount) {
        const invoice = invoices.value.find((item) => item.orderId === orderId)
        if (invoice) payInvoice(invoice.id, amount)
    }

    async function addFunds(amount) {
        if (amount <= 0) return false
        try {
            const res = await fetch(`${API_BASE}/vendor/wallet/top-up`, {
                method: 'POST',
                headers: getAuthHeaders(true),
                body: JSON.stringify({ amount }),
            })

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}))
                error.value = errData.detail || 'Failed to add funds.'
                return false
            }

            clearLegacyWalletTopupOffset()
            await fetchWalletBalance()
            if (dashboard.value?.stats) {
                dashboard.value.stats.credit_balance = walletBalance.value
            }
            return true
        } catch (err) {
            error.value = err?.message || 'Failed to add funds.'
            return false
        }
    }

    return { fetchWalletBalance, addFunds, payInvoice, recordCODPayment }
}
