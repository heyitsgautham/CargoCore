// Wallet balance, pending transport charges and top-ups.
import { apiUrl } from '@/config/api'

export function useCustomerWallet({ pendingTransportCharge, walletBalance }) {
    async function addFunds(amount) {
        const topUpAmount = Number(amount || 0)
        if (!(topUpAmount > 0)) return false

        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/wallet/top-up'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ amount: topUpAmount }),
            })

            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.detail || 'Failed to top up wallet')
            }

            const data = await res.json()
            walletBalance.value = Number(data.balance ?? walletBalance.value + topUpAmount)
            return true
        } catch (error) {
            console.error('Failed to add wallet funds:', error)
            return false
        }
    }

    async function fetchWalletBalance() {
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(apiUrl('api/v1/customer/wallet'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })
            if (res.ok) {
                const data = await res.json()
                walletBalance.value = data.balance ?? 0
                pendingTransportCharge.value = data.pending_transport_charge ?? 0
            }
        } catch (e) { /* silent */ }
    }

    return { addFunds, fetchWalletBalance }
}
