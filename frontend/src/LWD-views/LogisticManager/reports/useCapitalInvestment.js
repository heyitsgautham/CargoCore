// Logging an offline capital investment from the finances tab.
import { ref } from 'vue'
import { apiUrl } from '@/config/api'

export function useCapitalInvestment({ store, authStore, showNotification }) {
    const investmentModalOpen = ref(false)
    const investmentSubmitting = ref(false)
    const investmentForm = ref({
        amount: '',
        description: '',
        funding_source: 'OFFLINE_CAPITAL',
        investment_date: new Date().toISOString().slice(0, 10),
    })

    const submitInvestment = async () => {
        if (!investmentForm.value.amount || !investmentForm.value.description) {
            showNotification('Amount and Description are required', 'error')
            return
        }
        investmentSubmitting.value = true
        try {
            const res = await fetch(apiUrl('api/v1/logistics/capital-investment'), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(investmentForm.value)
            })
            if (res.ok) {
                showNotification(`Capital Investment of ₹${investmentForm.value.amount.toLocaleString()} logged!`, 'success')
                investmentModalOpen.value = false
                investmentForm.value = { amount: '', description: '', funding_source: 'OFFLINE_CAPITAL', investment_date: new Date().toISOString().slice(0, 10) }
                store.refresh()
            } else {
                showNotification('Failed to log investment', 'error')
            }
        } catch(e) {
            console.error(e)
            showNotification('Error logging investment', 'error')
        } finally {
            investmentSubmitting.value = false
        }
    }

    return { investmentModalOpen, investmentSubmitting, investmentForm, submitInvestment }
}
