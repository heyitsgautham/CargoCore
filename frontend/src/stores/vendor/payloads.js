/**
 * Turn vendor shipment and invoice payloads from the API into the rows the vendor screens render.
 */

import { buildPodData } from '@/utils/pod'
import {
    parseStatusKey,
    formatStatusLabel,
    statusProgress,
    safeDateLabel,
    safeDateTimeLabel,
    routeSummary,
    isRecurringShipment,
} from './shipmentFormat'

export function normalizeShipment(raw) {
    const statusKey = parseStatusKey(raw.status_key || raw.status)
    const trackingCode = raw.tracking_code || String(raw.id)
    const pickup = raw.pickup_addr || 'Origin'
    const delivery = raw.delivery_addr || 'Destination'
    const amount = Number(raw.amount ?? raw.cost?.total ?? 0)
    const delivered = statusKey === 'delivered'
    const isRecurring = isRecurringShipment(raw)
    const driverName = raw.assigned_driver_name || raw.driver_name || raw.driver?.name || null
    const driverPhone = raw.assigned_driver_phone || raw.driver_phone || raw.driver?.phone || null
    const assignedVehicleCode = raw.assigned_vehicle_code || raw.vehicle_code || null

    return {
        id: trackingCode,
        backendId: raw.id,
        trackingCode,
        origin: pickup,
        destination: delivery,
        route: routeSummary(pickup, delivery),
        status: raw.status_label || formatStatusLabel(statusKey),
        statusKey,
        eta: raw.eta_label || safeDateLabel(raw.scheduled_at, safeDateLabel(raw.created_at)),
        amount,
        pallets: 0,
        weight: Number(raw.cargo_weight_kg ?? raw.weight ?? raw.total_weight ?? 0),
        volume: Number(raw.cargo_volume_m3 ?? raw.volume ?? raw.total_volume ?? 0),
        category: raw.cargo_type || 'Commercial',
        paymentMode: raw.payment_mode || 'Invoice',
        paymentStatus: raw.payment_status || 'pending',
        driver: driverName,
        driverPhone,
        customerName: raw.customer_name || null,
        customerPhone: raw.customer_phone || null,
        vehicle: assignedVehicleCode || raw.vehicle_type || null,
        progress: Number(raw.progress ?? statusProgress(statusKey)),
        deliveredAt: raw.delivered_at || null,
        pod: delivered ? buildPodData(raw, {
            timestamp: safeDateTimeLabel(raw.delivered_at || raw.scheduled_at || raw.created_at),
            location: delivery,
            signedByFallback: 'Receiver',
        }) : null,
        originAddress: pickup,
        destinationAddress: delivery,
        driverLat: raw.driver_lat || raw.driverLat || null,
        driverLng: raw.driver_lng || raw.driverLng || null,
        description: raw.cargo_type || '',
        packingRequired: Number(raw.cost?.packing || 0) > 0,
        laborRequired: Number(raw.labor_count || 0) > 0,
        laborCount: Number(raw.labor_count || 0),
        isRecurring,
        createdAt: safeDateTimeLabel(raw.created_at),
        statusHistory: (raw.status_history || []).map((item) => ({
            status: item.status,
            time: item.time,
        })),
        autoDebitNote: raw.auto_debit_note || null,
        paidAmount: Number(raw.paid_amount || 0),
        customerRating: raw.customer_rating ?? null,
        customerFeedback: raw.customer_feedback ?? null,
        declaredValue: Number(raw.declared_value || 0),
        cost: {
            base: Number(raw.cost?.base || 0),
            vehicle: Number(raw.cost?.vehicle || 0),
            labor: Number(raw.cost?.labor || 0),
            materials: Number(raw.cost?.materials || 0),
            packing: Number(raw.cost?.packing || 0),
            platformFee: Number(raw.cost?.platform_fee || 0),
            taxes: Number(raw.cost?.taxes || 0),
            total: amount,
        },
    }
}

export function normalizeInvoice(raw) {
    return {
        id: raw.id,
        orderId: raw.tracking_code,
        backendOrderId: raw.order_id,
        date: raw.date,
        dueDate: raw.due_date,
        amount: Number(raw.amount || 0),
        paid: Number(raw.paid || 0),
        status: raw.status || 'Unpaid',
    }
}
