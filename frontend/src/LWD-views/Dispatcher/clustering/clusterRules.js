// Labels and checks for the order clustering panels.
import { orderAllowsDirectVehicleSelection } from '../dispatchRules'

export function priorityClass(priority) {
    const p = (priority || 'NORMAL').toUpperCase()
    if (p === 'URGENT') return 'bg-red-500/20 text-red-400'
    if (p === 'HIGH') return 'bg-orange-500/20 text-orange-400'
    if (p === 'LOW') return 'bg-gray-500/20 text-gray-400'
    return 'bg-blue-500/20 text-blue-400'
}

export function needsDispatcherVehicle(order) {
    return !!order && !order.vehicleId && orderAllowsDirectVehicleSelection(order)
}

export function vehicleLabel(vehicle) {
    return vehicle?.licensePlate || vehicle?.code || vehicle?.model || 'Vehicle'
}
