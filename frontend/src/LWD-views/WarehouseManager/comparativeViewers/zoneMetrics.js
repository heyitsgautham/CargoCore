// Zone metric helpers for the Comparative Viewers page.
// zoneMetricsCache maps a zone id to { latest, series } from the warehouse metrics API,
// and the floor store supplies the sections and racks used for rack counts.

export function useZoneMetrics(zoneMetricsCache, store) {
    const getZoneMetricValue = (zoneId, metricKey) => {
        const cache = zoneMetricsCache.value[zoneId]
        if (!cache) return null  // not fetched yet
        const metrics = cache.latest
        if (!metrics) return null  // fetched but empty
        const fieldMap = {
            'orders_processed': metrics.orders_processed,
            'picking_accuracy': metrics.picking_accuracy_pct,
            'active_pickers': metrics.active_pickers,
            'capacity_used': metrics.capacity_used_pct,
            'throughput': metrics.throughput_items_per_hour,
        }
        const val = fieldMap[metricKey]
        return (val !== undefined && val !== null) ? Math.round(val) : null
    }

    // Compute trend: percentage change vs previous record in series
    const getMetricTrend = (zoneId, metricKey) => {
        const cache = zoneMetricsCache.value[zoneId]
        const series = cache?.series
        if (!series || series.length < 2) return null
        const apiFieldMap = {
            'orders_processed': 'orders_processed',
            'picking_accuracy': 'picking_accuracy_pct',
            'active_pickers': 'active_pickers',
            'capacity_used': 'capacity_used_pct',
            'throughput': 'throughput_items_per_hour',
        }
        const field = apiFieldMap[metricKey]
        if (!field) return null
        const latest = series[series.length - 1]?.[field]
        const prev = series[series.length - 2]?.[field]
        if (latest == null || prev == null || prev === 0) return null
        return Math.round(((latest - prev) / prev) * 100)
    }

    // Compute total rack count for a zone from the store's floor plan
    const getZoneRackCount = (zoneId) => {
        const groupSections = store.sections.filter(s => s.groupId === zoneId)
        if (!groupSections.length) return 0
        return store.racks.filter(r => groupSections.some(s => s.id === r.sectionId)).length
    }

    // Capacity percentage for a zone (from API or zone.value string)
    const getCapacityPct = (zone) => {
        const cached = zoneMetricsCache.value[zone.id]
        if (cached?.latest?.capacity_used_pct != null) {
            return Math.round(cached.latest.capacity_used_pct)
        }
        if (zone.value === 'Full') return 100
        const parsed = parseInt(zone.value)
        return isNaN(parsed) ? '–' : parsed
    }

    // Used rack count derived from capacity % and total racks
    const getUsedRacks = (zone) => {
        const total = getZoneRackCount(zone.id)
        if (!total) return '–'
        const pct = getCapacityPct(zone)
        if (pct === '–') return '–'
        return Math.round((pct / 100) * total) + ' Racks'
    }

    // Staffing status based on actual active_pickers
    const getStaffingStatus = (zoneId) => {
        const cache = zoneMetricsCache.value[zoneId]
        const pickers = cache?.latest?.active_pickers
        if (pickers == null) return { label: '–', color: 'text-gray-400 dark:text-gray-500' }
        if (pickers >= 10) return { label: 'Optimal', color: 'text-green-500' }
        if (pickers >= 5) return { label: 'Moderate', color: 'text-yellow-500' }
        return { label: 'Low Staff', color: 'text-red-500' }
    }

    // Chart — uses real time-series; null when no data
    const getLineChartData = (zoneId, label, color = 'blue') => {
        const cache = zoneMetricsCache.value[zoneId]
        const series = cache?.series || []
        if (!series.length) return null

        const fieldKey = label === 'Throughput' ? 'throughput_items_per_hour'
            : label === 'Stock' ? 'capacity_used_pct'
            : 'orders_processed'
        const slice = series.slice(-7)
        return {
            labels: slice.map(m => {
                const d = new Date(m.metric_date)
                return d.toLocaleDateString('en-US', { weekday: 'short' })
            }),
            datasets: [{
                label,
                data: slice.map(m => Math.round(m[fieldKey] ?? 0)),
                borderColor: color === 'purple' ? '#8b5cf6' : color === 'green' ? '#10b981' : '#3b82f6',
                backgroundColor: color === 'purple' ? 'rgba(139, 92, 246, 0.1)' : color === 'green' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 2
            }]
        }
    }

    // Labor doughnut — based on real active_pickers; null when no data
    const getLaborData = (zoneId) => {
        const pickers = zoneMetricsCache.value[zoneId]?.latest?.active_pickers
        if (pickers == null || pickers === 0) return null
        const pickerCount = Math.round(pickers * 0.6) || 1
        const stowerCount = Math.round(pickers * 0.25) || 1
        const qaCount = Math.max(pickers - pickerCount - stowerCount, 0)
        return {
            labels: ['Pickers', 'Stowers', 'QA'],
            datasets: [{
                data: [pickerCount, stowerCount, qaCount],
                backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981'],
                borderWidth: 0
            }]
        }
    }

    return {
        getZoneMetricValue,
        getMetricTrend,
        getZoneRackCount,
        getCapacityPct,
        getUsedRacks,
        getStaffingStatus,
        getLineChartData,
        getLaborData,
    }
}

export const miniChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
    },
    scales: {
        x: {
            display: true,
            grid: { display: false },
            ticks: { font: { size: 10 } }
        },
        y: {
            display: true,
            ticks: { font: { size: 10 } }
        }
    }
}
