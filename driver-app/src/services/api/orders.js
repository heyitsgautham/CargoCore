// Assigned orders, trip intelligence, delivery proof, packing returns and ratings.
import { authHeaders, extractErrorMessage, fetchWithAuth, fetchWithNetworkHelp } from './client.js'

export async function getAssignedOrders() {
    const fetchByStatus = async (statusFilter) => {
        const res = await fetchWithNetworkHelp(
            `/api/v1/orders?status_filter=${statusFilter}&page_size=100`,
            { headers: { 'Content-Type': 'application/json', ...authHeaders() } }
        )
        if (!res.ok) return []
        const payload = await res.json()
        return Array.isArray(payload) ? payload : (payload.items || [])
    }

    try {
        const [assigned, inTransit] = await Promise.all([
            fetchByStatus('ASSIGNED'),
            fetchByStatus('IN_TRANSIT'),
        ])
        return [...assigned, ...inTransit]
    } catch (err) {
        console.error('Failed to fetch assigned orders', err)
        return []
    }
}

export async function getCompletedOrders() {
    try {
        const res = await fetchWithNetworkHelp(
            `/api/v1/orders?status_filter=DELIVERED&page_size=50`,
            { headers: { 'Content-Type': 'application/json', ...authHeaders() } }
        )
        if (!res.ok) return []
        const payload = await res.json()
        return Array.isArray(payload) ? payload : (payload.items || [])
    } catch {
        return []
    }
}

export async function getTripIntelligence(orderId) {
    const res = await fetchWithAuth(`/api/v1/orders/${orderId}/trip-intelligence`, {
        headers: { 'Content-Type': 'application/json' },
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to load trip intelligence' }))
        throw new Error(extractErrorMessage(error, 'Failed to load trip intelligence'))
    }
    return await res.json()
}

export async function reportTripDeviation(orderId, payload) {
    const res = await fetchWithAuth(`/api/v1/orders/${orderId}/trip-intelligence/deviation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to report deviation' }))
        throw new Error(extractErrorMessage(error, 'Failed to report deviation'))
    }
    return await res.json()
}

export async function completeReturn(orderId) {
    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/complete-return`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
    })
    if (!res.ok) throw new Error('Failed to complete return order')
    return await res.json()
}

export async function updateOrderStatus(orderId, status, notes = null) {
    const body = { next_status: status }
    if (notes) body.notes = notes

    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(body)
    })

    if (!res.ok) throw new Error('Failed to update order status')
    return await res.json()
}

export async function sendDeliveryOtp(orderId, forceResend = false) {
    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/delivery-otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ force_resend: forceResend }),
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to send delivery OTP' }))
        throw new Error(extractErrorMessage(error, 'Failed to send delivery OTP'))
    }
    return await res.json()
}

export async function uploadProofOfDelivery(orderId, imagesBase64 = [], signature = null, otpCode = null, customerName = null, notes = null) {
    const body = {
        otp_code: otpCode,
        images_data: imagesBase64,
        signature_data: signature,
        customer_name: customerName,
        notes,
    }

    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/proof-of-delivery`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(body)
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to upload proof of delivery' }))
        throw new Error(extractErrorMessage(error, 'Failed to upload proof of delivery'))
    }
    return await res.json()
}

export async function getOrderItems(orderId) {
    try {
        const res = await fetchWithAuth(`/api/v1/orders/${orderId}/items`)
        if (!res.ok) return []
        return await res.json()
    } catch {
        return []
    }
}

export async function submitPackingReturn(orderId, payload) {
    try {
        const res = await fetchWithAuth(`/api/v1/orders/${orderId}/packing-return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        return res.ok
    } catch {
        return false
    }
}

export async function submitHouseShiftSignoff(orderId, signatureData, customerName = null, notes = null) {
    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/house-shift-signoff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
            signature_data: signatureData,
            customer_name: customerName,
            notes,
        })
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to submit house-shift sign-off' }))
        throw new Error(extractErrorMessage(error, 'Failed to submit house-shift sign-off'))
    }
    return await res.json()
}

export async function submitJobRating(orderId, rating, feedback = null) {
    const res = await fetchWithNetworkHelp(`/api/v1/orders/${orderId}/job-rating`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ rating, feedback })
    })

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to submit job rating' }))
        throw new Error(extractErrorMessage(error, 'Failed to submit job rating'))
    }
    return await res.json()
}
