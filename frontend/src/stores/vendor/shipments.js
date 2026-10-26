// Booking, changing, cancelling and rating the vendor's shipments, and the hubs they ship from.
import { normalizeShipment } from './payloads'
import { safeDateLabel, safeDateTimeLabel } from './shipmentFormat'
import { API_BASE, getAuthHeaders } from './api'

export function useVendorShipments({
    assignmentPreview,
    assignmentPreviewError,
    damageReports,
    fetchWalletBalance,
    notifications,
    rates,
    rebuildNotifications,
    refreshVendorData,
    shipments,
    warehouses,
}) {
    async function fetchWarehouses() {
        try {
            const res = await fetch(`${API_BASE}/warehouses`, {
                headers: getAuthHeaders(),
            })
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                console.warn('[vendorStore] fetchWarehouses failed:', res.status, err.detail || '')
                return
            }
            const data = await res.json()
            warehouses.value = (Array.isArray(data) ? data : data.items || [])
                .filter((warehouse) => warehouse?.is_active !== false)
                .map(w => ({
                    id: String(w.id),
                    name: w.name,
                    address: w.address || w.location || '',
                    lat: w.lat ?? null,
                    lng: w.lng ?? null,
                }))
        } catch (e) {
            console.warn('[vendorStore] fetchWarehouses error:', e)
        }
    }

    async function fetchOrderAssignmentPreview(warehouseId = null) {
        try {
            const query = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''
            const response = await fetch(`${API_BASE}/orders/assignment-preview${query}`, {
                headers: getAuthHeaders(),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || 'Failed to resolve assignment preview')
            }

            const data = await response.json()
            assignmentPreviewError.value = ''
            assignmentPreview.value = {
                ...data,
                warehouse_id: String(data.warehouse_id),
            }
            return assignmentPreview.value
        } catch (error) {
            console.warn('[vendorStore] fetchOrderAssignmentPreview failed:', error)
            assignmentPreview.value = null
            assignmentPreviewError.value = error?.message || 'Failed to resolve assignment preview'
            return null
        }
    }

    async function fetchShipments() {
        const response = await fetch(`${API_BASE}/vendor/shipments`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load shipments.')
        }

        const data = await response.json()
        shipments.value = (data.shipments || []).map(normalizeShipment)
        rebuildNotifications()
        return data
    }

    async function fetchDamageReports() {
        const response = await fetch(`${API_BASE}/vendor/damage-reports`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load damage reports.')
        }

        const data = await response.json()
        damageReports.value = (data.reports || []).map((report) => ({
            id: report.id,
            orderId: report.order_id,
            description: report.description,
            severity: 'Medium',
            photos: report.photos || [],
            status: report.status,
            createdAt: report.created_at,
            resolution: null,
        }))
        return data
    }

    async function createShipment(data) {
        const selectedWarehouse = data.pickupType === 'hub'
            ? warehouses.value.find((warehouse) => warehouse.name === data.pickupHub) || null
            : null
        if (data.pickupType === 'hub' && data.pickupHub && !selectedWarehouse) {
            throw new Error('Selected hub is not available right now. Please choose another active warehouse.')
        }
        const pickupAddr = data.pickupType === 'doorstep'
            ? [data.pickupAddress, data.pickupCity, data.pickupPincode].filter(Boolean).join(', ')
            : data.pickupHub || 'Origin Hub'

        const deliveryAddr = [data.destination, data.destinationCity, data.pincode].filter(Boolean).join(', ')
        const scheduledAt = data.pickupDate ? new Date(data.pickupDate).toISOString() : null
        const quote = data.quoteBreakdown || {}
        const total = Number(quote.total ?? data.quotedPrice ?? 0)
        const materialsAmount = 0
        const packingAmount = Number(
            quote.packingFee
            ?? (data.packingRequired ? (rates.value.customerPackingFee ?? 200) : 0)
        )
        const laborAmount = Number(
            quote.laborCharges
            ?? (data.laborRequired ? Number(data.laborCount || 0) * (rates.value.customerLaborRate ?? 250) : 0)
        )
        const baseAmount = Math.max(total - packingAmount - laborAmount, 0)

        const priorityMap = { 'Urgent': 'URGENT', 'Express': 'HIGH', 'Standard': 'NORMAL' }
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                order_type: 'VENDOR',
                warehouse_id: selectedWarehouse?.id || null,
                pickup_addr: pickupAddr,
                pickup_type: data.pickupType || 'hub',
                delivery_addr: deliveryAddr,
                cargo_type: data.description || data.category || 'Commercial Shipment',
                vehicle_type: data.category || 'commercial',
                priority: priorityMap[data.priority] || 'NORMAL',
                labor_count: Number(data.laborCount || 0),
                cargo_weight_kg: Number(data.weight || 0) || null,
                cargo_volume_m3: Number(data.volume || 0) || null,
                base_amount: baseAmount,
                vehicle_amount: 0,
                labor_amount: laborAmount,
                materials_amount: materialsAmount,
                packing_amount: packingAmount,
                platform_fee: 0,
                tax_amount: 0,
                total_amount: total,
                declared_value: Number(data.declaredValue || 0),
                payment_mode: data.paymentMode || 'Invoice',
                payment_status: 'pending',
                service_time_block: data.timeWindow || null,
                scheduled_at: scheduledAt,
                delivery_lat: data.destLat || null,
                delivery_lng: data.destLng || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to create shipment.')
        }

        await refreshVendorData()
        const created = await response.json()
        const normalized = shipments.value.find((shipment) => shipment.backendId === created.id) || normalizeShipment({
            ...created,
            amount: created.total_amount,
            status_label: 'Pending',
            status_key: 'pending',
            progress: 15,
            eta_label: safeDateLabel(created.scheduled_at, safeDateLabel(created.created_at)),
            cost: {
                base: created.base_amount,
                vehicle: created.vehicle_amount,
                labor: created.labor_amount,
                materials: created.materials_amount,
                packing: created.packing_amount,
                platform_fee: created.platform_fee,
                taxes: created.tax_amount,
                total: created.total_amount,
            },
            status_history: [{ status: 'Created', time: safeDateTimeLabel(created.created_at) }],
        })

        notifications.value.unshift({
            id: `created-${normalized.id}-${Date.now()}`,
            title: 'Shipment Created',
            message: `${normalized.id} created successfully.`,
            time: 'Just now',
            read: false,
            type: 'success',
        })
        return normalized
    }

    async function updateShipmentAddress(id, newAddress) {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return false

        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ delivery_addr: newAddress }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update shipment address.')
        }

        await refreshVendorData()
        return true
    }

    async function rescheduleShipment(id, newDate) {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return false

        const parsed = new Date(newDate)
        const scheduledAt = Number.isNaN(parsed.getTime()) ? null : parsed.toISOString()
        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ scheduled_at: scheduledAt }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to reschedule shipment.')
        }

        await refreshVendorData()
        return true
    }

    async function cancelShipment(id, reason = 'Cancelled by vendor') {
        const shipment = shipments.value.find((item) => item.id === id || item.backendId === id)
        if (!shipment?.backendId) return { success: false, message: 'Shipment not found.' }

        const response = await fetch(`${API_BASE}/orders/${shipment.backendId}/cancel`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({ reason }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            return { success: false, message: errData.detail || 'Failed to cancel shipment.' }
        }

        const updated = await response.json()
        await refreshVendorData()
        // Refresh wallet so balance reflects the refund immediately
        await fetchWalletBalance()
        return {
            success: true,
            walletRefund: updated.wallet_refund_amount ?? 0,
        }
    }

    async function reportDamage(orderIdOrPayload, reportPayload) {
        const orderId = typeof orderIdOrPayload === 'object' ? orderIdOrPayload.shipmentId : orderIdOrPayload
        const payload = typeof orderIdOrPayload === 'object' ? orderIdOrPayload : reportPayload

        const shipment = shipments.value.find((item) => item.id === orderId || item.backendId === orderId)
        const response = await fetch(`${API_BASE}/vendor/damage-reports`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                order_id: shipment?.backendId || '',
                description: payload?.description || '',
                photos: payload?.photos || [],
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to submit damage report.')
        }

        await fetchDamageReports()
        return true
    }

    function calculateQuote(pallets, weight, laborCount, packingRequired, materials) {
        const base = pallets * 120 + weight * 0.08
        const labor = laborCount * 250
        const packing = packingRequired ? 200 : 0
        const materialsTotal = materials ? materials.reduce((sum, material) => sum + material.qty * material.unitPrice, 0) : 0
        const total = base + labor + packing + materialsTotal
        return {
            baseTransport: Math.round(base),
            laborCharges: labor,
            packingFee: packing,
            materialsCost: Math.round(materialsTotal),
            total: Math.round(total),
        }
    }

    async function submitCustomerRating(backendId, rating, feedback = null) {
        try {
            const response = await fetch(`${API_BASE}/orders/${backendId}/customer-rating`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ rating, feedback }),
            })
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to submit rating.' }
            }
            const updated = await response.json()
            const idx = shipments.value.findIndex(s => s.backendId === backendId)
            if (idx !== -1) {
                shipments.value[idx].customerRating = updated.customer_rating
                shipments.value[idx].customerFeedback = updated.customer_feedback
            }
            return { success: true }
        } catch {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    return {
        fetchWarehouses,
        fetchOrderAssignmentPreview,
        fetchShipments,
        createShipment,
        updateShipmentAddress,
        rescheduleShipment,
        cancelShipment,
        reportDamage,
        fetchDamageReports,
        submitCustomerRating,
        calculateQuote,
     }
}
