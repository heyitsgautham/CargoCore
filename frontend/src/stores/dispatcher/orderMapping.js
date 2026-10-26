// Turns backend orders into dispatcher board records with driver and vehicle names.
import { buildPodData } from '@/utils/pod'
import { parseCoordinate, resolveCargoWeight, resolveCargoVolume } from './orderMetrics'

export function useDispatchOrderMapping({
    LOADING_STATUSES,
    READY_STATUSES,
    _vehicles,
    ls,
}) {
    function resolveDriverName(driverId) {
        if (!driverId) return null
        const id = String(driverId)
        // Check filtered drivers first, then all drivers from logistic store
        const driver = ls.filteredDrivers.find(d => d.id === id)
        return driver ? driver.name : null
    }

    function resolveVehicleCode(vehicleId, driverIdFallback = null) {
        // Combined vehicle pool: dispatcher's directly-fetched list first, then logistic store.
        // Read _vehicles directly; the store's filteredVehicles depends on hub selection.
        const localVehicles = _vehicles.value.map(v => ({
            id: String(v.id),
            code: v.code || '',
            licensePlate: v.license_plate || v.licensePlate || '',
            model: v.model || '',
            driverId: v.assigned_driver_id ? String(v.assigned_driver_id) : null,
        }))
        const allVehicles = localVehicles.length > 0 ? [...localVehicles, ...ls.filteredVehicles] : ls.filteredVehicles

        // 1. Try by vehicleId directly
        if (vehicleId) {
            const id = String(vehicleId)
            const vehicle = allVehicles.find(v => v.id === id)
            if (vehicle) return vehicle.licensePlate || vehicle.code || vehicle.model || null
        }
        // 2. Fall back to finding the vehicle assigned to this driver
        //    (vehicles table has assigned_driver_id, not the orders table)
        if (driverIdFallback) {
            const driverId = String(driverIdFallback)
            const vehicle = allVehicles.find(v =>
                v.driverId && String(v.driverId) === driverId
            )
            if (vehicle) return vehicle.licensePlate || vehicle.code || vehicle.model || null
        }
        return null
    }

    function mapOrder(o) {
        const substatus = o.warehouse_substatus || ''
        const isEscalated = o.escalated === true || String(o.escalation_status || '').toUpperCase() === 'OPEN'
        const weight = resolveCargoWeight(o)
        const volume = resolveCargoVolume(o)
        // Prefer server-resolved names, fall back to local store lookup
        const driverName = o.assigned_driver_name || resolveDriverName(o.assigned_driver_id)
        // assigned_vehicle_code doesn't exist in DB; look up by vehicle_id then by driver assignment
        const vehicleCode = resolveVehicleCode(o.assigned_vehicle_id, o.assigned_driver_id)
        const deliveryAddr =
            o.unloading_addr ||
            o.unloading_address ||
            o.destination ||
            o.delivery_addr ||
            ''
        const deliveryLat = parseCoordinate(
            o.delivery_lat ??
            o.destination_lat ??
            o.unloading_lat ??
            o.drop_lat ??
            o.dest_lat ??
            o.destLat ??
            o.destinationLat
        )
        const deliveryLng = parseCoordinate(
            o.delivery_lng ??
            o.destination_lng ??
            o.unloading_lng ??
            o.drop_lng ??
            o.dest_lng ??
            o.destLng ??
            o.destinationLng
        )
        const pickupLat = parseCoordinate(
            o.pickup_lat ??
            o.origin_lat ??
            o.loading_lat ??
            o.source_lat ??
            o.pickupLat ??
            o.originLat
        )
        const pickupLng = parseCoordinate(
            o.pickup_lng ??
            o.origin_lng ??
            o.loading_lng ??
            o.source_lng ??
            o.pickupLng ??
            o.originLng
        )
        const podTimeLabel = o.delivered_at
            ? new Date(o.delivered_at).toLocaleString()
            : (o.created_at ? new Date(o.created_at).toLocaleString() : 'Delivered')
        const pod = o.status === 'DELIVERED'
            ? buildPodData(o, {
                timestamp: podTimeLabel,
                location: deliveryAddr || '—',
                signedByFallback: 'Receiver',
            })
            : null
        return {
            id: String(o.id || ''),
            trackingCode: o.tracking_code || '',
            displayId: o.tracking_code || String(o.id || '').slice(0, 8).toUpperCase(),
            warehouse: o.pickup_addr || o.warehouse_id || 'Hub',
            weight: weight ?? 0,
            hasWeight: weight !== null,
            volume: volume ?? 0,
            hasVolume: volume !== null,
            laborCount: o.labor_count || 0,
            priority: o.priority || 'NORMAL',
            deadline: o.scheduled_at || o.delivery_deadline || '',
            specialInstructions: o.notes || o.special_instructions || '',
            feasibility: o.feasibility || 'unchecked',
            failReason: o.fail_reason || '',
            selected: false,
            // warehouse readiness
            warehouseSubstatus: substatus,
            readyForDispatch: READY_STATUSES.includes(substatus),
            loadingInProgress: LOADING_STATUSES.includes(substatus),
            // for OrderStatusControl
            status: o.status || 'CONFIRMED',
            statusLabel: o.status || 'Confirmed',
            driver: driverName || (o.assigned_driver_id ? 'Driver ' + String(o.assigned_driver_id).slice(0, 6) : 'Unassigned'),
            driverId: o.assigned_driver_id ? String(o.assigned_driver_id) : null,
            vehicle: vehicleCode || (o.assigned_vehicle_id ? 'Vehicle ' + String(o.assigned_vehicle_id).slice(0, 6) : '—'),
            vehicleId: o.assigned_vehicle_id ? String(o.assigned_vehicle_id) : null,
            eta: o.scheduled_at || '—',
            etaOverdue: false,
            slaStatus: isEscalated ? 'ESCALATED' : 'On Track',
            slaClass: isEscalated ? 'bg-red-500/20 text-red-400' : 'text-green-400',
            lastUpdated: o.delivered_at || o.arrived_at || o.scheduled_at || o.created_at || '—',
            type: o.order_type || o.cargo_type || 'Standard',
            hub: o.pickup_addr || '',
            cargoType: o.cargo_type || '',
            vehicleType: o.vehicle_type || '',
            totalAmount: o.total_amount || 0,
            packingAmount: o.packing_amount || 0,
            warehouseId: o.warehouse_id || null,
            customerName: o.customer_name || null,
            customerPhone: o.customer_phone || null,
            createdAt: o.created_at || null,
            deliveredAt: o.delivered_at || null,
            deliveryNotes: o.delivery_notes || null,
            packingReturnData: o.packing_return_data || null,
            escalated: isEscalated,
            escalationId: o.escalation_id ? String(o.escalation_id) : null,
            escalationStatus: o.escalation_status || null,
            pod,
            // Map coordinates for visualization
            pickupAddr: o.pickup_addr || '',
            pickupLat,
            pickupLng,
            deliveryAddr,
            deliveryLat,
            deliveryLng,
        }
    }

    return { mapOrder }
}
