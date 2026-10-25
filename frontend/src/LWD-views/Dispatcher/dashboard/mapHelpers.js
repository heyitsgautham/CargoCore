/**
 * Map markers, colours, coordinate checks and distance helpers for the dispatcher dashboard map.
 */

import L from 'leaflet'

// Destination / delivery marker — stable orange location pin for route endpoints
export function getDestinationIcon() {
    const color = '#f97316'
    return L.divIcon({
        html: `<div style="background:${color};width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
            </svg>
        </div>`,
        className: 'custom-dest-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    })
}

// Driver marker — color-coded by status with truck SVG
export function getDriverIcon(statusColor) {
    // statusColor: 'bg-green-500' | 'bg-yellow-500' | 'bg-gray-500'
    let bg, border
    if (statusColor === 'bg-green-500') {
        bg = '#22c55e'; border = '#16a34a'
    } else if (statusColor === 'bg-yellow-500') {
        bg = '#eab308'; border = '#ca8a04'
    } else {
        bg = '#6b7280'; border = '#4b5563'
    }
    return L.divIcon({
        html: `<div style="background:${bg};width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid ${border};box-shadow:0 3px 10px rgba(0,0,0,0.4);">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white">
                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zm-.5 1.5 1.96 2.5H17V9.5h2.5zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
            </svg>
        </div>`,
        className: 'custom-driver-icon',
        iconSize: [34, 34],
        iconAnchor: [17, 17],
        popupAnchor: [0, -17],
    })
}

// Maps the raw status string from the tracking API to a Tailwind color token
export function getActiveDriverStatusColor(driver) {
    const s = (driver.status || '').toLowerCase()
    if (s === 'active' || s === 'on_route' || s === 'on route' || s === 'in-transit' || s === 'in_transit') return 'bg-green-500'
    if (s === 'idle' || s === 'on_break' || s === 'on break') return 'bg-yellow-500'
    return 'bg-gray-500'
}

export function hasValidCoordinate(value) {
    if (value === null || value === undefined || value === '') return false
    return Number.isFinite(Number(value))
}

export function getOrderDestinationLabel(order) {
    return order.deliveryAddr || `Order #${order.id} unloading point`
}

export function getOrderPickupLabel(order) {
    return order.pickupAddr || `Order #${order.id} pickup point`
}

export function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function isMapVisibleOrder(order) {
    return !['DELIVERED', 'CLOSED', 'CANCELLED'].includes(String(order?.status || '').toUpperCase())
}

export function getDriverSpeedKmph(driver) {
    const reported = Number(driver.avg_speed ?? driver.avgSpeed ?? 0)
    return Number.isFinite(reported) && reported > 0 ? Math.max(18, reported) : 24
}

// Zone color helper (inspired by Geofencing.vue)
export function getZoneColor(colorToken) {
    const colors = {
        blue: '#3b82f6',
        green: '#22c55e',
        red: '#ef4444',
        yellow: '#eab308',
        purple: '#a855f7',
        orange: '#f97316',
        teal: '#14b8a6',
        pink: '#ec4899',
    }
    return colors[colorToken] || colors.blue
}

// Priority color helper
export function getPriorityColor(priority) {
    if (priority === 'URGENT') return '#ef4444'
    if (priority === 'HIGH') return '#f97316'
    return '#3b82f6'
}

export function toCoordinatePair(lat, lng) {
    if (!hasValidCoordinate(lat) || !hasValidCoordinate(lng)) return null
    return [Number(lat), Number(lng)]
}

export function getDriverLocationLabel(driver) {
    if (driver.location) return driver.location
    if (hasValidCoordinate(driver.latitude) && hasValidCoordinate(driver.longitude)) {
        return `${Number(driver.latitude).toFixed(5)}, ${Number(driver.longitude).toFixed(5)}`
    }
    return 'Live location unavailable'
}

// Hub / Warehouse marker — indigo square with warehouse SVG
export const hubIcon = L.divIcon({
    html: `<div style="background:#4f46e5;width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M1 11v11h22V11L12 2 1 11zm20 9H3v-8.5l9-7 9 7V20zm-9-6H8v5h6v-5z"/>
        </svg>
    </div>`,
    className: 'custom-hub-icon',
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
})

export function getPickupIcon(priority) {
    const color = getPriorityColor(priority)
    return L.divIcon({
        html: `<div style="background:${color};width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.35);">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v9c0 1.1.9 2 2 2h1a3 3 0 0 0 6 0h4a3 3 0 0 0 6 0h1c1.1 0 2-.9 2-2v-3l-3-4zM6 18.5A1.5 1.5 0 1 1 6 15.5a1.5 1.5 0 0 1 0 3zm11 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM17 12V9.5h2.5l1.96 2.5H17z"/>
            </svg>
        </div>`,
        className: 'custom-pickup-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
    })
}
