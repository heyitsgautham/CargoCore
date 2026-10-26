// Pending and active orders, order detail, clusters and assignment.
import { authenticatedJsonRequest } from '@/config/api'
import { isDispatcherVisiblePendingOrder } from './orderMetrics'
import { API_BASE, authHeaders } from './api'

export function useDispatchOrders({
    activeOrders,
    activeOrdersLoading,
    mapOrder,
    ordersLoading,
    pendingOrders,
}) {
    async function fetchOrders() {
        ordersLoading.value = true
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders?status_filter=CONFIRMED&page_size=100`, {
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) {
                const data = await res.json()
                const items = Array.isArray(data) ? data : (data.items || data.orders || [])
                pendingOrders.value = items
                    .filter(isDispatcherVisiblePendingOrder)
                    .map(mapOrder)
            }
        } catch (_) {
        } finally {
            ordersLoading.value = false
        }
    }

    async function fetchActiveOrders() {
        activeOrdersLoading.value = true
        try {
            // Fetch ASSIGNED, IN_TRANSIT, and DELIVERED orders for the Order Status view
            // (driver load counting uses only ASSIGNED + IN_TRANSIT, but the UI needs DELIVERED too)
            const [aRes, tRes, dRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
                fetch(`${API_BASE}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
                fetch(`${API_BASE}/api/v1/orders?status_filter=DELIVERED&page_size=100`, { headers: { 'Content-Type': 'application/json', ...authHeaders() } }),
            ])
            const assigned = aRes.ok ? (await aRes.json()) : []
            const inTransit = tRes.ok ? (await tRes.json()) : []
            const delivered = dRes.ok ? (await dRes.json()) : []
            const assignedItems = Array.isArray(assigned) ? assigned : (assigned.items || [])
            const inTransitItems = Array.isArray(inTransit) ? inTransit : (inTransit.items || [])
            const deliveredItems = Array.isArray(delivered) ? delivered : (delivered.items || [])
            activeOrders.value = [...assignedItems, ...inTransitItems, ...deliveredItems].map(o => mapOrder(o))
        } catch (_) {
        } finally {
            activeOrdersLoading.value = false
        }
    }

    async function fetchOrderDetail(orderId) {
        const data = await authenticatedJsonRequest(`api/v1/orders/${orderId}`, {
            headers: { ...authHeaders() },
        })
        return mapOrder(data)
    }

    async function fetchClusters(radiusKm = 5.0) {
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders/cluster?radius_km=${radiusKm}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
            })
            if (res.ok) return await res.json()
            return { clusters: [], unbatched: [], total_orders: 0, estimated_miles_saved_pct: 0, avg_efficiency_pct: 0 }
        } catch (_) {
            return { clusters: [], unbatched: [], total_orders: 0, estimated_miles_saved_pct: 0, avg_efficiency_pct: 0 }
        }
    }

    async function assignOrder(orderId, driverId, vehicleId = null) {
        const body = { driver_id: driverId }
        if (vehicleId) body.vehicle_id = vehicleId
        try {
            const res = await fetch(`${API_BASE}/api/v1/orders/${orderId}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeaders() },
                body: JSON.stringify(body),
            })
            if (res.ok) {
                await fetchOrders()
                await fetchActiveOrders()
            }
            return res.ok
        } catch (_) {
            return false
        }
    }

    async function batchAssignOrders(assignments) {
        const res = await fetch(`${API_BASE}/api/v1/orders/batch-assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ assignments }),
        })
        if (!res.ok) throw new Error('Batch assign failed')
        await fetchOrders()
        return await res.json()
    }

    return {
        fetchOrders,
        fetchActiveOrders,
        fetchOrderDetail,
        fetchClusters,
        assignOrder,
        batchAssignOrders,
     }
}
