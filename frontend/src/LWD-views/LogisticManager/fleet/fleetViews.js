// Pure filters, groupings and summaries behind the fleet management tabs.

function matches(query, ...values) {
    return !query || values.some((value) => String(value || '').toLowerCase().includes(query))
}

export function searchDrivers(drivers, query, isSuspended) {
    const q = query.toLowerCase()
    return drivers
        .filter(d =>
            !q ||
            d.name.toLowerCase().includes(q) ||
            String(d.vehicle || '').toLowerCase().includes(q) ||
            String(d.currentJob || '').toLowerCase().includes(q) ||
            String(d.status || '').toLowerCase().includes(q)
        )
        .map(d => ({ ...d, dispatcherSuspended: isSuspended(d) }))
}

export function searchTopDrivers(drivers, query, isSuspended) {
    const q = query.toLowerCase()
    return drivers
        .filter(d => !q || d.name.toLowerCase().includes(q))
        .map(d => ({ ...d, dispatcherSuspended: isSuspended(d) }))
}

export function searchVehicles(vehicles, query) {
    const q = query.toLowerCase()
    return vehicles.filter(v =>
        !q ||
        String(v.code || v.id || '').toLowerCase().includes(q) ||
        v.type.toLowerCase().includes(q) ||
        v.model.toLowerCase().includes(q) ||
        v.driver.toLowerCase().includes(q) ||
        v.status.toLowerCase().includes(q)
    )
}

export function searchMaintenance(items, query) {
    const q = query.toLowerCase()
    return items.filter(m => matches(q, m.id, m.issue, m.status))
}

/** Logs of one type at the selected hub, matching the query in any field. */
export function searchLogs(logs, query, activeWarehouse) {
    const q = query.toLowerCase()
    return (logs || []).filter(l =>
        (activeWarehouse === 'all' || l.hubId === activeWarehouse) &&
        (!q || Object.values(l).some(val => String(val).toLowerCase().includes(q)))
    )
}

function completion(logs, status) {
    const done = logs.filter(l => (Array.isArray(status) ? status.includes(l.status) : l.status === status)).length
    return { done, pct: logs.length ? Math.round((done / logs.length) * 100) : 0 }
}

function averageCost(totalCost, logs) {
    return `₹${logs.length ? (totalCost / logs.length).toFixed(0) : 0}`
}

/** The summary card for the selected log type: two tiles, a progress trend and the total cost. */
export function computeLogStats(logType, logs) {
    const totalCost = logs.reduce((sum, log) => sum + (log.cost || 0), 0)

    if (logType === 'Fuel Logs') {
        const totalVolume = logs.reduce((sum, log) => sum + (log.gallons || 0), 0)
        const avgPrice = totalVolume > 0 ? (totalCost / totalVolume).toFixed(2) : 0
        const { done, pct } = completion(logs, ['Completed', 'Verified'])
        return {
            title: 'Fuel Consumption',
            icon: 'local_gas_station',
            color: 'orange',
            tiles: [
                { label: 'Avg Price/Gal', value: `₹${avgPrice}` },
                { label: 'Total Volume', value: `${totalVolume.toLocaleString()} L` }
            ],
            trend: { label: 'Verified Logs', value: `${done} / ${logs.length}`, target: `${logs.length}`, pct },
            totalCost
        }
    }
    if (logType === 'Service Logs') {
        const { done, pct } = completion(logs, 'Completed')
        return {
            title: 'Service Metrics',
            icon: 'car_repair',
            color: 'blue',
            tiles: [
                { label: 'Total Services', value: logs.length },
                { label: 'Avg Cost', value: averageCost(totalCost, logs) }
            ],
            trend: { label: 'Completion Rate', value: `${done} / ${logs.length}`, target: `${logs.length}`, pct },
            totalCost
        }
    }
    if (logType === 'Maintenance Logs') {
        const { done, pct } = completion(logs, 'Resolved')
        return {
            title: 'Maintenance Costs',
            icon: 'build',
            color: 'red',
            tiles: [
                { label: 'Active Repairs', value: logs.filter(l => l.status !== 'Resolved').length },
                { label: 'Avg Repair Cost', value: averageCost(totalCost, logs) }
            ],
            trend: { label: 'Resolved', value: `${done} / ${logs.length}`, target: `${logs.length}`, pct },
            totalCost
        }
    }
    const { done, pct } = completion(logs, 'Completed')
    return {
        title: 'Fleet Hygiene',
        icon: 'cleaning_services',
        color: 'teal',
        tiles: [
            { label: 'Total Washes', value: logs.length },
            { label: 'Avg Wash Cost', value: averageCost(totalCost, logs) }
        ],
        trend: { label: 'Completed', value: `${done} / ${logs.length}`, target: `${logs.length}`, pct },
        totalCost
    }
}

/** Vehicle documents at the selected hub that match the query, keyed by vehicle id. */
export function groupVehicleDocs(docs, activeWarehouse, query) {
    let filtered = activeWarehouse !== 'all' ? docs.filter(d => d.hubId === activeWarehouse) : docs
    if (query) {
        const q = query.toLowerCase()
        filtered = filtered.filter(d =>
            d.vehicleId.toLowerCase().includes(q) ||
            d.type.toLowerCase().includes(q) ||
            d.status.toLowerCase().includes(q)
        )
    }
    const groups = {}
    filtered.forEach(doc => {
        if (!groups[doc.vehicleId]) groups[doc.vehicleId] = []
        groups[doc.vehicleId].push(doc)
    })
    return groups
}

/** Driver documents at the selected hub that match the query, one group per driver. */
export function groupDriverDocs(docs, activeWarehouse, query) {
    let filtered = activeWarehouse !== 'all' ? docs.filter(d => d.hubId === activeWarehouse) : docs
    if (query) {
        const q = query.toLowerCase()
        filtered = filtered.filter(d =>
            d.driver.toLowerCase().includes(q) ||
            d.type.toLowerCase().includes(q) ||
            d.licenseNo.toLowerCase().includes(q) ||
            d.status.toLowerCase().includes(q)
        )
    }
    const groups = {}
    filtered.forEach(doc => {
        if (!groups[doc.driverId]) groups[doc.driverId] = { id: doc.driverId, name: doc.driver, docs: [] }
        groups[doc.driverId].docs.push(doc)
    })
    return Object.values(groups)
}

/** Service and repair history of one vehicle from the fleet logs, with its total cost. */
export function vehicleServiceHistory(fleetLogs, vehicleId) {
    const history = [
        ...(fleetLogs['Service Logs'] || []).filter(item => item.vehicleId === vehicleId).map(item => ({
            id: item.id,
            service: item.service,
            date: item.date,
            type: 'Routine',
            cost: item.cost,
        })),
        ...(fleetLogs['Maintenance Logs'] || []).filter(item => item.vehicleId === vehicleId).map(item => ({
            id: item.id,
            service: item.issue,
            date: item.date,
            type: 'Repair',
            cost: item.cost,
        })),
    ]
    return { history, total: history.reduce((sum, item) => sum + item.cost, 0) }
}

/** The repair cost shown on a maintenance alert, or an em dash when no log has one. */
export function maintenanceCostLabel(vehicles, fleetLogs, vehicleId) {
    const vehicle = vehicles.find(v => v.id === vehicleId)
    if (!vehicle) return '—'
    const log = (fleetLogs['Maintenance Logs'] || []).find(l => l.vehicleId === vehicle.code)
    return log?.cost != null ? `₹${log.cost.toLocaleString()}` : '—'
}

/** CSV text of the fleet maintenance report, one row per vehicle. */
export function maintenanceReportCsv(vehicles, hubs) {
    const rows = [
        ['Vehicle ID', 'License Plate', 'Type', 'Model', 'Year', 'Driver', 'Status', 'Warehouse', 'Fuel Efficiency', 'Current Location'],
        ...vehicles.map(v => [
            v.code || v.id, v.licensePlate || '—', v.type || '—', v.model || '—', v.year || '—',
            v.driver || '—', v.status || '—',
            hubs.find(h => h.id === v.hubId)?.name || 'Main Hub',
            v.fuelEfficiency || '—', v.currentLocation || '—'
        ])
    ]
    return rows.map(r => r.map(c => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
}
