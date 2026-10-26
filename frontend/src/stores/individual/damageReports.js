// Damage reports the customer files against delivered orders.
import { apiUrl } from '@/config/api'

export function useDamageReports({ applyDamageReportsToOrders, damageReports, damageReportsError, damageReportsLoading }) {
    async function fetchDamageReports() {
        damageReportsLoading.value = true
        damageReportsError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/damage-reports'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                damageReportsError.value = errData.detail || 'Failed to load damage reports.'
                return { success: false, message: damageReportsError.value }
            }

            const data = await response.json()
            damageReports.value = (data.reports || []).map((report) => ({
                id: report.id,
                orderId: report.order_id,
                description: report.description,
                photos: report.photos || [],
                flow_type: report.flow_type ?? null,
                status: report.status,
                qrCode: report.qr_code,
                createdAt: report.created_at,
                refundAmount: report.refund_amount ?? null,
                condition: report.condition ?? null,
            }))
            applyDamageReportsToOrders()
            return { success: true, data: damageReports.value }
        } catch (error) {
            damageReportsError.value = 'Error connecting to the server.'
            return { success: false, message: damageReportsError.value }
        } finally {
            damageReportsLoading.value = false
        }
    }

    async function reportDamageRemote(orderId, description, photos, resolutionType = 'photo_review') {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/damage-reports'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({
                    order_id: orderId,
                    description,
                    photos,
                    resolution_type: resolutionType,
                }),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit damage report.' }
            }

            await fetchDamageReports()
            return { success: true }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    return { fetchDamageReports, reportDamageRemote }
}
