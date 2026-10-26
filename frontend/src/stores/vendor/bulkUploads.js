// Bulk order uploads and the orders they create.
import { API_BASE, getAuthHeaders } from './api'

export function useVendorBulkUploads({ bulkUploads }) {
    async function fetchBulkUploads() {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads`, {
            headers: getAuthHeaders(),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to load bulk uploads.')
        }

        bulkUploads.value = await response.json()
        return bulkUploads.value
    }

    async function createBulkOrders(rows) {
        const results = { created: 0, failed: 0 }
        for (const row of rows) {
            try {
                const declaredValue = Number(row.declared_value || row.declaredValue || 0)
                const weight = Number(row.weight_kg || row.weight || 0)
                const baseAmount = declaredValue > 0 ? Math.round(declaredValue * 0.02) : 850
                const packingAmount = Math.round(baseAmount * 0.1) || 100
                const total = baseAmount + packingAmount + Math.round((baseAmount + packingAmount) * 0.18)
                const res = await fetch(`${API_BASE}/orders`, {
                    method: 'POST',
                    headers: getAuthHeaders(true),
                    body: JSON.stringify({
                        order_type: 'VENDOR',
                        warehouse_id: null,
                        pickup_addr: row.pickup_address || row.pickupAddress || 'Origin Hub',
                        pickup_type: 'doorstep',
                        delivery_addr: row.delivery_address || row.deliveryAddress || row.destination || 'Destination',
                        cargo_type: row.cargo_type || row.item_description || 'Commercial Shipment',
                        vehicle_type: 'commercial',
                        priority: 'NORMAL',
                        labor_count: 0,
                        cargo_weight_kg: weight || null,
                        cargo_volume_m3: null,
                        base_amount: baseAmount,
                        vehicle_amount: 0,
                        labor_amount: 0,
                        materials_amount: 0,
                        packing_amount: packingAmount,
                        platform_fee: 0,
                        tax_amount: Math.round((baseAmount + packingAmount) * 0.18),
                        total_amount: total,
                        declared_value: declaredValue,
                        payment_mode: row.payment_mode || row.paymentMode || 'Invoice',
                        payment_status: 'pending',
                        service_time_block: null,
                        scheduled_at: null,
                        delivery_lat: null,
                        delivery_lng: null,
                    }),
                })
                if (res.ok) results.created++
                else results.failed++
            } catch {
                results.failed++
            }
        }
        return results
    }

    async function addBulkUpload(upload) {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads`, {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({
                filename: upload.filename || upload.fileName || 'upload.csv',
                file_size_kb: Math.round(Number(upload.fileSizeKb || 0)),
                orders: Number(upload.orders || 0),
                status: upload.status || 'Processed',
                errors: Number(upload.errors || 0),
                scheduled_for: upload.scheduledFor || null,
            }),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            const detail = errData.detail
            const msg = Array.isArray(detail)
                ? detail.map(e => e.msg || JSON.stringify(e)).join(', ')
                : (typeof detail === 'string' ? detail : 'Failed to save bulk upload.')
            throw new Error(msg)
        }

        await fetchBulkUploads()
    }

    async function updateBulkUpload(id, updates) {
        const response = await fetch(`${API_BASE}/vendor/bulk-uploads/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(true),
            body: JSON.stringify(updates),
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            throw new Error(errData.detail || 'Failed to update bulk upload.')
        }

        await fetchBulkUploads()
    }

    return { fetchBulkUploads, createBulkOrders, addBulkUpload, updateBulkUpload }
}
