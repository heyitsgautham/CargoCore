// Labels for the tracking map and sidebar: the route legend, the stage names, the
// route summary line and the service checklist.
import { computed } from 'vue'

export function useRouteSummary({
    activeMove,
    destCoords,
    pickupCoords,
    pickupToDestCoords,
    warehouseCoords,
    warehouseToPickupCoords,
}) {
    function logColor(c) { return { green: '#22c55e', blue: '#3b82f6', amber: '#f59e0b', purple: '#a855f7', red: '#ef4444' }[c] || '#6b7280' }

    function isWarehouseEvent(event) {
        const warehouseEvents = ['labourer', 'picking', 'packing', 'quality check', 'dispatch', 'queued', 'on hold']
        return warehouseEvents.some(w => event.toLowerCase().includes(w))
    }

    const hasWarehouseRoutePoint = computed(() => Boolean(
        activeMove.value?.warehouseName
        || activeMove.value?.warehouseAddress
        || warehouseCoords.value
    ))

    const routeStageLabels = computed(() => {
        if (hasWarehouseRoutePoint.value) {
            return ['Warehouse', 'Pickup', 'Destination']
        }
        return ['Pickup', 'En Route', 'Destination']
    })

    const routeLegendItems = computed(() => {
        const items = []
        const delivered = activeMove.value?.status === 'delivered'
        const hasWarehouseLeg = hasWarehouseRoutePoint.value
            && (warehouseToPickupCoords.value.length > 0 || (warehouseCoords.value && pickupCoords.value))
        const hasDestinationLeg = pickupToDestCoords.value.length > 0 || (pickupCoords.value && destCoords.value)

        if (hasWarehouseLeg) {
            items.push({
                key: 'warehouse-pickup',
                label: 'Warehouse -> Pickup',
                color: '#f59e0b',
                dashed: !delivered,
                opacity: delivered ? 0.95 : 0.75,
            })
        }

        if (hasDestinationLeg) {
            items.push({
                key: 'pickup-destination',
                label: 'Pickup -> Destination',
                color: delivered ? '#10b981' : '#3b82f6',
                dashed: !delivered,
                opacity: delivered ? 0.95 : 0.8,
            })
        }

        return items
    })

    const routeBlueprintLabel = computed(() => {
        const order = activeMove.value
        if (!order) return ''

        const pickupLabel = order.pickup?.split(',')?.[0] || 'Pickup'
        const destLabel = order.destination?.split(',')?.[0] || 'Destination'
        const warehouseLabel = order.warehouseName || 'Warehouse'

        if (hasWarehouseRoutePoint.value) {
            return `${warehouseLabel} → ${pickupLabel} → ${destLabel}`
        }

        return `${pickupLabel} → ${destLabel}`
    })

    const serviceChecklist = computed(() => {
        const status = activeMove.value?.warehouseSubstatus || ''
        const orderStatus = activeMove.value?.status || ''
        const progress = activeMove.value?.progress ?? 0

        // Define status progression
        const statusOrder = ['AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED']
        const currentIdx = statusOrder.indexOf(status)

        return [
            { text: 'Order confirmed', done: progress >= 5 || orderStatus !== 'pending' },
            { text: 'Crew assigned', done: progress >= 10 || (activeMove.value?.laborCount > 0 && currentIdx >= 0) },
            { text: 'Picking completed', done: currentIdx >= statusOrder.indexOf('PICKED') || progress >= 30 },
            { text: 'Packing completed', done: currentIdx >= statusOrder.indexOf('PACKED') || progress >= 50 },
            { text: 'Quality verified', done: currentIdx >= statusOrder.indexOf('QC_PASSED') || progress >= 60 },
            { text: 'Shipment in transit', done: currentIdx >= statusOrder.indexOf('DISPATCHED') || progress >= 70 },
            { text: 'Delivery completed', done: orderStatus === 'delivered' || progress >= 100 },
        ]
    })

    return {
        logColor,
        isWarehouseEvent,
        routeStageLabels,
        routeLegendItems,
        routeBlueprintLabel,
        serviceChecklist,
    }
}
