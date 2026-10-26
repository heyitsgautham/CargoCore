// Booking a move: the quote, packing material SKUs, order creation and saved quotes.
import { apiUrl } from '@/config/api'
import { mapQuote, fallbackPackingSku } from './orderMapping'
import { localDateISO } from '@/utils/date'

export function useCustomerBooking({
    MATERIAL_SKU_MAP,
    assignmentPreview,
    fetchWalletBalance,
    normalizeBackendOrder,
    notifications,
    orders,
    payments,
    pendingTransportCharge,
    quotes,
    quotesError,
    quotesLoading,
    fetchDashboardSummary,
    fetchOrders,
    vehicleTypes,
    warehouses,
}) {
    async function fetchQuotes() {
        quotesLoading.value = true
        quotesError.value = ''

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/customer/quotes'), {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                quotesError.value = errData.detail || 'Failed to load quotes.'
                return { success: false, message: quotesError.value }
            }

            const data = await response.json()
            quotes.value = (data.quotes || []).map(mapQuote)
            return { success: true, data: quotes.value }
        } catch (error) {
            quotesError.value = 'Error connecting to the server.'
            return { success: false, message: quotesError.value }
        } finally {
            quotesLoading.value = false
        }
    }

    async function convertQuoteToOrderRemote(quoteId) {
        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl(`api/v1/customer/quotes/${quoteId}/convert`), {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                return { success: false, message: errData.detail || 'Failed to convert quote.' }
            }

            await fetchQuotes()
            await fetchOrders()
            const data = await response.json()
            return { success: true, data }
        } catch (error) {
            return { success: false, message: 'Error connecting to the server.' }
        }
    }

    function resolveMaterialSku(material = {}) {
        const explicitSku = String(material.sku || '').trim()
        if (explicitSku) return explicitSku

        const key = String(material.key || material.id || '').trim()
        if (MATERIAL_SKU_MAP[key]) return MATERIAL_SKU_MAP[key]

        return fallbackPackingSku(material.name || key)
    }

    async function createOrder(data) {
        const vehicle = vehicleTypes.value.find(v => v.key === data.vehicleType) || vehicleTypes.value[0]
        const totalAmount = Number(data.cost?.total || 0)
        const carryForwardChargeAmount = Number(data.carryForwardChargeAmount || 0)
        const payableBookingTotal = totalAmount + carryForwardChargeAmount
        const initialPaymentAmount = data.paymentMode === 'COD'
            ? 0
            : Math.min(Number(data.paymentAmount || 0), payableBookingTotal)
        const isWalletPayment = typeof (data.paymentMethod || '') === 'string' && (data.paymentMethod || '').toLowerCase().includes('wallet')

        // Prepare order data for backend API
        const orderPayload = {
            order_type: 'INDIVIDUAL',
            warehouse_id: data.warehouseId || null,
            pickup_addr: data.pickup || '',
            delivery_addr: data.destination || '',
            cargo_weight_kg: Number(data.packageWeight || data.cargoWeightKg || 0) || null,
            cargo_volume_m3: Number(data.cargoVolumeM3 || 0) || null,
            cargo_type: data.cargoType || null,
            vehicle_type: data.vehicleType || null,
            labor_count: data.laborCount || 0,
            base_amount: data.cost?.base || 0,
            vehicle_amount: data.cost?.vehicle || 0,
            labor_amount: data.cost?.labor || 0,
            materials_amount: data.cost?.materials || 0,
            packing_amount: data.cost?.packing || 0,
            platform_fee: data.cost?.platformFee || 0,
            tax_amount: data.cost?.taxes || 0,
            total_amount: totalAmount,
            payment_mode: data.paymentMode || null,
            payment_status: 'pending',
            initial_payment_amount: initialPaymentAmount,
            initial_payment_ref: data.paymentRef || null,
            initial_payment_mode: initialPaymentAmount > 0 ? (isWalletPayment ? 'WALLET' : 'ONLINE') : null,
            initial_payment_method: initialPaymentAmount > 0 ? (data.paymentMethod || 'Online') : null,
            service_time_block: data.moveType === 'small-package' ? '30 min' : '2-3 hours',
            scheduled_at: data.date ? new Date(data.date).toISOString() : null,
        }

        try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(apiUrl('api/v1/orders'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(orderPayload),
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `Server error ${response.status}: Failed to create order`)
            }

            const backendOrder = await response.json()
            const resolvedWarehouseId = backendOrder.warehouse_id ? String(backendOrder.warehouse_id) : (data.warehouseId || null)
            const resolvedWarehouse = resolvedWarehouseId
                ? warehouses.value.find((warehouse) => warehouse.id === resolvedWarehouseId)
                : null

            // Submit packing materials as OrderItems (so warehouse inventory deduction works during packing)
            // Prefer pre-resolved materialItems (sku + qty) passed directly from the booking form.
            // Only fall back to the old MATERIAL_SKU_MAP lookup when materialItems is not provided.
            const directItems = (data.materialItems || [])
                .map(i => ({ ...i, sku: resolveMaterialSku(i) }))
                .filter(i => i.sku && i.quantity > 0)

            let resolvedItems = null
            if (directItems.length > 0) {
                // Catalog-resolved: already have correct SKUs from the real WM inventory
                resolvedItems = directItems.map(i => ({ sku: i.sku, quantity: i.quantity, box_count: null, estimated_volume: null }))
            } else {
                // Legacy fallback: map old form.materials keys via MATERIAL_SKU_MAP
                const rawMaterialItems = Object.entries(data.materials || {})
                    .filter(([, qty]) => qty > 0)
                    .map(([key, qty]) => ({ key, qty, sku: resolveMaterialSku({ key }) }))
                    .filter(({ sku }) => sku)
                if (rawMaterialItems.length > 0) {
                    resolvedItems = rawMaterialItems.map(({ sku, qty }) => ({ sku, quantity: qty, box_count: null, estimated_volume: null }))
                }
            }

            if (resolvedItems && resolvedItems.length > 0) {
                try {
                    const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
                    const itemsRes = await fetch(apiUrl(`api/v1/orders/${backendOrder.id}/items`), {
                        method: 'POST',
                        headers,
                        body: JSON.stringify(resolvedItems),
                    })
                    if (!itemsRes.ok) {
                        const errBody = await itemsRes.json().catch(() => ({}))
                        console.error('Failed to attach packing material items:', itemsRes.status, errBody)
                    }
                } catch (itemErr) {
                    console.error('Could not attach packing material items to order:', itemErr)
                }
            }

            const normalizedOrder = normalizeBackendOrder({
                ...backendOrder,
                warehouse_name: resolvedWarehouse?.name || assignmentPreview.value?.warehouse_name || null,
                warehouse_address: resolvedWarehouse?.address || assignmentPreview.value?.warehouse_address || null,
            })
            if (Number(backendOrder.carry_forward_charge_amount || 0) > 0) {
                pendingTransportCharge.value = 0
            }

            // Add to local state immediately for instant UI feedback
            orders.value.unshift(normalizedOrder)

            if (initialPaymentAmount > 0) {
                payments.value.unshift({
                    id: data.paymentRef || (`PAY-${800 + payments.value.length + 1}`),
                    orderId: normalizedOrder.id,
                    amount: initialPaymentAmount,
                    mode: data.paymentMethod || 'Online',
                    status: 'completed',
                    date: new Date().toISOString(),
                    isDummy: false,
                })
            }

            // Add notification
            notifications.value.unshift({
                id: Date.now(),
                title: 'Order Created',
                message: `${normalizedOrder.trackingCode} booked — ${vehicle.name} assigned.`,
                time: 'Just now',
                read: false,
                icon: 'check_circle',
            })

            // Refresh dashboard summary so recent orders list is up to date
            fetchDashboardSummary()
            // Refresh wallet balance if paid via Cargo Core Wallet so UI reflects deduction
            if (isWalletPayment && initialPaymentAmount > 0) fetchWalletBalance()

            return normalizedOrder
        } catch (error) {
            console.error('Failed to create order:', error)
            // Re-throw so the UI (BookMove.vue) can show the real error to the user
            // instead of silently creating a local-only order that disappears on refresh
            throw error
        }
    }

    function addQuote(data) {
        const q = { id: `QT-${500 + quotes.value.length + 1}`, ...data, date: localDateISO(), status: 'active' }
        quotes.value.unshift(q)
        return q
    }

    async function convertQuoteToOrder(quoteId) {
        const q = quotes.value.find(q => q.id === quoteId)
        if (!q) return null
        q.status = 'converted'
        return await createOrder({
            cargoType: q.cargoType, pickup: q.from, destination: q.to,
            laborCount: q.laborCount, packingRequired: q.packing,
            materials: {}, cost: { base: Math.round(q.total * 0.45), labor: Math.round(q.total * 0.2), materials: Math.round(q.total * 0.1), packing: Math.round(q.total * 0.1), vehicle: Math.round(q.total * 0.15), total: q.total },
            date: localDateISO(), timeWindow: '10:00 AM - 12:00 PM',
            paymentMode: 'Full Payment', vehicleType: 'tempo',
        })
    }

    function calculateQuote(distance, laborCount, packingRequired, materialsCost, vehicleKey, ratesOverride = {}) {
        const individualDistanceRates = ratesOverride.individualDistanceRates || {}
        const perKmRates = {
            'mini-truck': individualDistanceRates.miniTruck ?? 18,
            'tempo': individualDistanceRates.tempo ?? 25,
            'lcv': individualDistanceRates.lcv ?? 35,
            'hcv': individualDistanceRates.hcv ?? 50,
        }
        const vehicle = vehicleTypes.value.find(v => v.key === vehicleKey) || vehicleTypes.value[0]
        const perKm = perKmRates[vehicleKey] || 25

        const bookingFee = ratesOverride.individualBookingFee ?? 300
        const laborRate = ratesOverride.individualLaborRate ?? 800
        const packingPct = (ratesOverride.individualPackingPct ?? 20) / 100
        const minimumCharge = ratesOverride.minimumCharge ?? 500

        const distCharge = Math.round(distance * perKm)                 // distance charge
        const base = Math.max(bookingFee + distCharge, minimumCharge)   // total base fare
        const labor = laborCount * laborRate
        const packing = packingRequired ? Math.round(base * packingPct) : 0
        const vehicleCost = Math.round(distCharge * (vehicle.priceMultiplier - 1) * 0.4)
        const matCost = materialsCost || 0
        const subtotal = base + labor + packing + vehicleCost + matCost
        const platformFee = 249
        const taxes = Math.round(subtotal * 0.18)
        return { base, labor, packing, materials: matCost, vehicle: vehicleCost, platformFee, taxes, total: subtotal + platformFee + taxes }
    }

    return {
        resolveMaterialSku,
        createOrder,
        calculateQuote,
        fetchQuotes,
        convertQuoteToOrderRemote,
        addQuote,
        convertQuoteToOrder,
     }
}
