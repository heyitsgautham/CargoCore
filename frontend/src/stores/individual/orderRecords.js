// Turns backend orders into the customer app's order records and links damage reports to them.
import { buildPodData } from '@/utils/pod'
import { normalizeBackendStatus, buildTransportLog } from './orderMapping'

export function useOrderRecords({ damageReports, orders, warehouses }) {
    function normalizeBackendOrder(order) {
        const status = normalizeBackendStatus(order.status)
        const warehouseSubstatus = order.warehouse_substatus || ''
        const warehouseId = order.warehouse_id ? String(order.warehouse_id) : null
        const warehouseName = order.warehouse_name
            || (warehouseId ? warehouses.value.find((warehouse) => warehouse.id === warehouseId)?.name : null)
            || null
        const warehouseAddress = order.warehouse_address
            || (warehouseId ? warehouses.value.find((warehouse) => warehouse.id === warehouseId)?.address : null)
            || null

        // Build transport log with warehouse operations
        const transportLog = buildTransportLog(order, status, warehouseSubstatus)

        return {
            id: order.tracking_code || String(order.id),
            backendId: order.id,
            trackingCode: order.tracking_code,
            status,
            rawStatus: order.status,
            warehouseId,
            warehouseName,
            warehouseAddress,
            warehouseSubstatus,
            moveType: String(order.order_type || '').toUpperCase() === 'INDIVIDUAL' ? 'house-shift' : 'small-package',
            cargoType: order.cargo_type || (String(order.order_type || '').toUpperCase() === 'INDIVIDUAL' ? 'Household Goods' : (order.order_type || 'Order')),
            pickup: order.pickup_addr,
            destination: order.delivery_addr,
            date: order.scheduled_at ? new Date(order.scheduled_at).toLocaleDateString('en-CA') : new Date(order.created_at).toLocaleDateString('en-CA'),
            timeWindow: order.scheduled_at ? new Date(order.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'TBD',
            laborCount: order.labor_count || 0,
            packingRequired: Number(order.packing_amount || 0) > 0,
            vehicleType: order.vehicle_type || String(order.order_type || 'move').toLowerCase(),
            cargoWeightKg: Number(order.cargo_weight_kg ?? order.weight ?? order.total_weight ?? 0),
            cargoVolumeM3: Number(order.cargo_volume_m3 ?? order.volume ?? order.total_volume ?? 0),
            materials: {},
            cost: {
                base: Number(order.base_amount || 0),
                labor: Number(order.labor_amount || 0),
                materials: Number(order.materials_amount || 0),
                packing: Number(order.packing_amount || 0),
                vehicle: Number(order.vehicle_amount || 0),
                platformFee: Number(order.platform_fee || 0),
                taxes: Number(order.tax_amount || 0),
                carryForward: Number(order.carry_forward_charge_amount || 0),
                total: Number(order.total_amount || 0),
            },
            driver: order.assigned_driver_name || order.driver || null,
            customerName: order.customer_name || null,
            customerPhone: order.customer_phone || null,
            eta: order.scheduled_at ? new Date(order.scheduled_at).toLocaleString() : 'TBD',
            progress: status === 'delivered' ? 100 : status === 'in-transit' ? 65 : status === 'dispatched' ? 40 : 0,
            paymentMode: order.payment_mode || 'Pending',
            paymentStatus: order.payment_status || (status === 'delivered' ? 'paid' : 'pending'),
            paidAmount: Number(order.paid_amount || 0),
            isDummyPayment: false,
            rating: null,
            feedback: '',
            customerRating: order.customer_rating ?? null,
            customerFeedback: order.customer_feedback ?? null,
            createdAt: order.created_at,
            deliveredAt: order.delivered_at || null,
            declaredValue: Number(order.declared_value || 0),
            serviceTimeBlock: order.service_time_block || 'TBD',
            dwellTime: { loading: 0, unloading: 0, total: 0 },
            beforeAfterPhotos: {},
            crewCheckin: null,
            transportLog,
            pod: status === 'delivered' ? buildPodData(order, {
                timestamp: order.delivered_at
                    ? new Date(order.delivered_at).toLocaleString()
                    : (order.created_at ? new Date(order.created_at).toLocaleString() : 'Delivered'),
                location: order.delivery_addr || '—',
                signedByFallback: 'Receiver',
            }) : null,
            cancellation: order.cancel_reason ? { reason: order.cancel_reason, fee: 0, date: new Date().toISOString() } : null,
            hasDamageReport: false,
            damageReportId: '',
            damageReportStatus: '',
            damageRefundAmount: null,
            damageCondition: null,
        }
    }

    function applyDamageReportsToOrders() {
        if (!orders.value.length) return

        const latestReportByOrderId = new Map()
        for (const report of damageReports.value) {
            const orderId = String(report.orderId || '')
            if (!orderId) continue

            const existing = latestReportByOrderId.get(orderId)
            if (!existing || new Date(report.createdAt || 0) > new Date(existing.createdAt || 0)) {
                latestReportByOrderId.set(orderId, report)
            }
        }

        orders.value = orders.value.map((order) => {
            const linkedReport = latestReportByOrderId.get(String(order.backendId || ''))
            if (!linkedReport) {
                return {
                    ...order,
                    hasDamageReport: false,
                    damageReportId: '',
                    damageReportStatus: '',
                    damageRefundAmount: null,
                    damageCondition: null,
                }
            }

            return {
                ...order,
                hasDamageReport: true,
                damageReportId: linkedReport.id,
                damageReportStatus: linkedReport.status || 'reported',
                damageRefundAmount: linkedReport.refundAmount ?? null,
                damageCondition: linkedReport.condition ?? null,
            }
        })
    }

    return { normalizeBackendOrder, applyDamageReportsToOrders }
}
