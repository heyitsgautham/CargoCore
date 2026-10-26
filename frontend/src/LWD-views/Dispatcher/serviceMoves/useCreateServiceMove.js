// Creating a service move from the new move form, then assigning the chosen driver and vehicle.
import { parseApiError } from './serviceMoveRecords'
import { API_BASE_URL } from '@/config/api'

export function useCreateServiceMove({
    authHeaders,
    buildServiceMoveMeta,
    buildServiceTimeBlock,
    closeNewMoveModal,
    fetchServiceMoves,
    formError,
    formSuccess,
    loading,
    newMove,
    resetNewMoveForm,
    selectedVehicleOption,
    toast,
}) {
    async function createServiceMove() {
        if (!newMove.title || !newMove.pickup || !newMove.delivery) return

        loading.value = true
        formError.value = ''
        formSuccess.value = ''
        try {
            // Build scheduled timestamp
            const scheduledAt = newMove.scheduledDate && newMove.scheduledTime
                ? `${newMove.scheduledDate}T${newMove.scheduledTime}:00`
                : null

            // Create order payload
            const payload = {
                cargo_type: newMove.type,
                order_type: 'SERVICE_MOVE',
                pickup_addr: newMove.pickup,
                pickup_lat: newMove.pickupLat,
                pickup_lng: newMove.pickupLng,
                delivery_addr: newMove.delivery,
                delivery_lat: newMove.deliveryLat,
                delivery_lng: newMove.deliveryLng,
                vehicle_type: selectedVehicleOption.value?.code || selectedVehicleOption.value?.type || null,
                delivery_notes: buildServiceMoveMeta(),
                service_time_block: buildServiceTimeBlock(),
                scheduled_at: scheduledAt,
            }

            const res = await fetch(`${API_BASE_URL}/api/v1/orders`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(payload)
            })

            if (!res.ok) {
                const error = await res.json().catch(() => ({}))
                throw new Error(parseApiError(error, 'Failed to create service move'))
            }

            const createdOrder = await res.json()

            if (newMove.driverId && createdOrder.id) {
                const assignRes = await fetch(`${API_BASE_URL}/api/v1/orders/${createdOrder.id}/assign`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify({
                        driver_id: newMove.driverId,
                        vehicle_id: newMove.vehicleId || null,
                    }),
                })

                if (!assignRes.ok) {
                    const assignError = await assignRes.json().catch(() => ({}))
                    await fetchServiceMoves()
                    const partialMessage = parseApiError(assignError, 'Service move created, but assignment failed')
                    toast.warning(partialMessage)
                    resetNewMoveForm()
                    await closeNewMoveModal()
                    return
                }
            }

            await fetchServiceMoves()
            formSuccess.value = 'Service move created successfully.'
            toast.success('Service move created successfully.')
            resetNewMoveForm()
            await closeNewMoveModal()
        } catch (err) {
            console.error('Failed to create service move:', err)
            formError.value = err instanceof Error ? err.message : 'Failed to create service move'
            toast.error(formError.value)
        }
        loading.value = false
    }

    return { createServiceMove }
}
