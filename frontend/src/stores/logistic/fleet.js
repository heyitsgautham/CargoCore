/**
 * Drivers and vehicles: status changes, new vehicles and drivers, and messages to drivers.
 */

import { apiRequest, authHeaders } from './api'
import {
    normalizeDriverLoginId,
    normalizeDriverPin,
} from './mappers'

export function useLogisticFleet({ drivers, vehicles, refresh }) {
    async function sendMessageToDriver(driverId, text) {
        const driver = drivers.value.find((item) => item.id === String(driverId))
        if (!driver) return
        driver.chatHistory.push({
            id: Date.now(),
            text,
            sender: 'dispatch',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        })
    }

    async function updateDriverStatus(driverId, newStatus) {
        try {
            await apiRequest(`/logistics/drivers/${driverId}`, {
                method: 'PUT',
                headers: authHeaders(),
                body: JSON.stringify({ status: newStatus }),
            })
            await refresh()
        } catch (e) {
            // Fallback to local update if API fails
            const driver = drivers.value.find((item) => item.id === String(driverId))
            if (driver) driver.status = newStatus
        }
    }

    async function updateVehicle(vehicleId, fields) {
        await apiRequest(`/logistics/vehicles/${vehicleId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(fields),
        })
        await refresh()
    }

    async function addVehicle(vehicleData) {
        try {
            await apiRequest('/logistics/vehicles', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    code: vehicleData.id,
                    vehicle_type: vehicleData.type,
                    warehouse_id: vehicleData.hubId && vehicleData.hubId !== 'all' ? vehicleData.hubId : null,
                    assigned_driver_id: vehicleData.driverId || null,
                    model: vehicleData.model,
                    year: vehicleData.year || new Date().getFullYear(),
                    license_plate: vehicleData.licensePlate,
                    status: vehicleData.status || 'Active',
                    fuel_efficiency: vehicleData.fuelEfficiency || 'Pending Calibration',
                    mileage: vehicleData.mileage || 0,
                    maintenance_issue: vehicleData.issue || null,
                }),
            })
            await refresh()
        } catch (e) {
            console.warn("Backend /vehicles not implemented, mocking local state", e)
            vehicles.value.push({
                id: vehicleData.id,
                hubId: vehicleData.hubId && vehicleData.hubId !== 'all' ? String(vehicleData.hubId) : null,
                type: vehicleData.type,
                code: vehicleData.id,
                model: vehicleData.model,
                year: vehicleData.year || new Date().getFullYear(),
                licensePlate: vehicleData.licensePlate,
                status: 'Active',
                driver: vehicleData.driver || 'Unassigned',
                fuelEfficiency: '10.5 mpg',
                mileage: '0 mi',
                nextService: '3 Months',
                issue: 'None'
            })
        }
    }

    async function updateVehicleStatus(vehicleId, newStatus) {
        await apiRequest(`/logistics/vehicles/${vehicleId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ status: newStatus }),
        })
        await refresh()
    }

    async function addDriver(driverData) {
        const driverId = normalizeDriverLoginId(driverData.driver_id || driverData.username, driverData.email)
        const driverPin = normalizeDriverPin(driverData.pin || driverData.password)
        await apiRequest('/logistics/drivers', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: driverData.name,
                email: driverData.email,
                phone: driverData.phone || null,
                warehouse_id: driverData.warehouse_id && driverData.warehouse_id !== 'all' ? driverData.warehouse_id : null,
                status: driverData.status || 'Active',
                current_location: driverData.current_location || null,
                driver_id: driverId || null,
                pin: driverPin,
            }),
        })
        await refresh()
    }

    return { sendMessageToDriver, updateDriverStatus, updateVehicle, addVehicle, updateVehicleStatus, addDriver }
}
