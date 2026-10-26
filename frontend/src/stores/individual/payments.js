// Payment history and paying for an order.
import { apiUrl } from '@/config/api'

export function useCustomerPayments({
    orders,
    payments,
    paymentsError,
    paymentsLoading,
    paymentsSummary,
    updateOrder,
}) {
    async function fetchPaymentsSummary() {
        paymentsLoading.value = true
        paymentsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/payments'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                paymentsError.value = errData.detail || 'Failed to load payments.'
                return { success: false, message: paymentsError.value }
            }

            const data = await response.json()
            paymentsSummary.value = data
            payments.value = (data.records || []).map((record) => ({
                id: record.id,
                orderId: record.tracking_code,
                amount: record.amount,
                mode: record.mode,
                status: record.status,
                date: record.created_at,
                isDummy: false,
            }))
            return { success: true, data }
        } catch (error) {
            paymentsError.value = 'Error connecting to the server.'
            return { success: false, message: paymentsError.value }
        } finally {
            paymentsLoading.value = false
        }
    }

    async function makePayment(orderId, amount, mode, isDummy = false, paymentRef = null) {
        const p = {
            id: `PAY-${800 + payments.value.length + 1}`, orderId, amount, mode,
            status: isDummy ? 'simulated' : 'completed',
            date: new Date().toISOString(), isDummy,
        }
        payments.value.unshift(p)
        updateOrder(orderId, { paymentStatus: isDummy ? 'simulated' : 'paid', paymentMode: mode, isDummyPayment: isDummy })

        // Persist to backend if real payment (not simulated)
        if (!isDummy) {
            const order = orders.value.find(o => o.id === orderId || o.trackingCode === orderId)
            const backendId = order?.backendId
            if (backendId) {
                try {
                    const token = localStorage.getItem('auth_token')
                    const isWalletPayment = typeof mode === 'string' && mode.toLowerCase().includes('wallet')
                    if (isWalletPayment) {
                        await fetch(apiUrl(`api/v1/orders/${backendId}/wallet-pay`), {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                            body: JSON.stringify({ amount }),
                        })
                    } else {
                        await fetch(apiUrl(`api/v1/orders/${backendId}/pay`), {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                            body: JSON.stringify({
                                payment_ref: paymentRef,
                                payment_mode: 'ONLINE',
                                payment_method: mode,
                                amount,
                            }),
                        })
                    }
                } catch (e) {
                    console.warn('[makePayment] Backend /pay call failed (non-fatal):', e)
                }
            }
        }
        return p
    }

    return { fetchPaymentsSummary, makePayment }
}
