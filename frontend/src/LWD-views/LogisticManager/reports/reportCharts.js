// Chart.js data and options for the logistics reports, built from the store's
// transactions, hubs, returns and the backend's report metrics.

const PERSONAL_MOVE = /move|relocation|personal|individual/i
const RMA_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#9ca3af', '#8b5cf6']

/** Share of income from standard deliveries and personal moves, in percent. */
export function revenueStreamChart(transactions) {
    const income = transactions.filter(t => t.amount > 0)
    let data = [65, 35]
    if (income.length) {
        const personal = income.filter(t => PERSONAL_MOVE.test(t.desc || '')).reduce((s, t) => s + t.amount, 0)
        const standard = income.filter(t => !PERSONAL_MOVE.test(t.desc || '')).reduce((s, t) => s + t.amount, 0)
        const total = personal + standard || 1
        data = [Math.round(standard / total * 100), Math.round(personal / total * 100)]
    }
    return { labels: ['Standard Delivery', 'Personal Moves'], datasets: [{ backgroundColor: ['#3b82f6', '#8b5cf6'], data }] }
}

export function paymentReconChart(metrics) {
    const recon = metrics.payment_reconciliation
    return {
        labels: recon?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        datasets: [
            { label: 'Expected (Digital)', backgroundColor: '#34d399', data: recon?.expected_digital || [] },
            { label: 'Actual (Digital)', backgroundColor: '#059669', data: recon?.actual_digital || [] },
            { label: 'Expected (COD)', backgroundColor: '#fbbf24', data: recon?.expected_cod || [] },
            { label: 'Actual (COD)', backgroundColor: '#d97706', data: recon?.actual_cod || [] }
        ]
    }
}

export function fuelAuditChart(metrics) {
    const fuel = metrics.fuel_audit
    return {
        labels: fuel?.labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
            { label: 'Fuel Expense ($)', borderColor: '#ef4444', data: fuel?.fuel_expense || [], tension: 0.4 },
            { label: 'GPS Mileage (km/10)', borderColor: '#3b82f6', data: fuel?.gps_mileage || [], tension: 0.4, borderDash: [5, 5] }
        ]
    }
}

/** A sentence about the largest fuel expense when it is 40% above the average, else null. */
export function fuelAnomalyText(transactions) {
    const fuelTxs = transactions.filter(t => /fuel|petrol|gas/i.test(t.desc || '') && t.amount < 0)
    if (fuelTxs.length < 2) return null
    const amounts = fuelTxs.map(t => Math.abs(t.amount))
    const avg = amounts.reduce((s, a) => s + a, 0) / amounts.length
    const max = Math.max(...amounts)
    if (max <= avg * 1.4) return null
    const tx = fuelTxs.find(t => Math.abs(t.amount) === max)
    return `Transaction "${tx?.desc || 'Fuel Expense'}" on ${tx?.date || 'recent date'} was ₹${max.toLocaleString()} — ${Math.round((max / avg - 1) * 100)}% above fleet average.`
}

export function procurementCapitalChart(summary) {
    return {
        labels: ['Procurement (App Revenue)', 'Capital Invested'],
        datasets: [{
            backgroundColor: ['#f97316', '#3b82f6'],
            data: [summary?.procurement_expenses || 0, summary?.capital_invested || 0]
        }]
    }
}

export function workforceChart(metrics) {
    return {
        labels: metrics.workforce?.labels || ['In-Warehouse', 'On-Field', 'Off-Duty'],
        datasets: [{ backgroundColor: ['#f59e0b', '#10b981', '#9ca3af'], data: metrics.workforce?.values || [0, 0, 0] }]
    }
}

export function vendorLeadTimeChart(metrics) {
    return {
        labels: metrics.vendor_lead_time?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Avg Lead Time (Days)',
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            data: metrics.vendor_lead_time?.values || [],
            fill: true,
            tension: 0.4
        }]
    }
}

export function safetyIncidentChart(metrics) {
    return {
        labels: metrics.safety_incidents?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{ label: 'Safety Incidents', backgroundColor: '#ef4444', data: metrics.safety_incidents?.values || [], borderRadius: 4 }]
    }
}

export function shiftEfficiencyChart(metrics) {
    const shifts = metrics.shift_efficiency
    return {
        labels: shifts?.labels || ['Shift A', 'Shift B', 'Shift C'],
        datasets: [
            { label: 'Avg Efficiency (%)', backgroundColor: '#10b981', data: shifts?.efficiency || [] },
            { label: 'Overtime Hours', backgroundColor: '#f59e0b', data: shifts?.overtime || [] }
        ]
    }
}

export function dwellTimeChart(metrics) {
    return {
        labels: metrics.dwell_time?.labels || ['6am-9am', '9am-12pm', '12pm-3pm', '3pm-6pm', '6pm-9pm'],
        datasets: [{ label: 'Avg Dwell Time (Minutes)', backgroundColor: '#f97316', data: metrics.dwell_time?.values || [] }]
    }
}

export function rmaVsOrdersChart(metrics) {
    const rma = metrics.rma_vs_orders
    return {
        labels: rma?.labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
            { label: 'Total Orders', borderColor: '#3b82f6', data: rma?.orders || [], yAxisID: 'y' },
            { label: 'RMA Cases', borderColor: '#ef4444', data: rma?.rma || [], yAxisID: 'y1', borderDash: [5, 5] }
        ]
    }
}

/** Return reasons sorted into five buckets by keyword. */
export function rmaReasonBuckets(returns) {
    const buckets = { Damaged: 0, 'Wrong Item': 0, 'Late Delivery': 0, 'Changed Mind': 0, Other: 0 }
    for (const item of returns || []) {
        const reason = String(item.reason || '').toLowerCase()
        if (/(damage|damaged|broken|defect|defective|scrap|crack|cracked)/.test(reason)) buckets.Damaged += 1
        else if (/(wrong|incorrect|mismatch|different item|not what i ordered)/.test(reason)) buckets['Wrong Item'] += 1
        else if (/(late|delay|delayed|slow delivery|delivery issue)/.test(reason)) buckets['Late Delivery'] += 1
        else if (/(changed mind|no longer need|cancel|cancelled|cancelled order)/.test(reason)) buckets['Changed Mind'] += 1
        else if (reason) buckets.Other += 1
    }
    return buckets
}

/** The backend's RMA reason counts when it has any, else counts from the store's returns. */
export function rmaReasonsChart(metrics, returns) {
    const metricLabels = metrics.rma_reasons?.labels || []
    const metricValues = metrics.rma_reasons?.values || []
    const metricTotal = metricValues.reduce((sum, value) => sum + (Number(value) || 0), 0)

    if (metricLabels.length && metricValues.length && metricTotal > 0) {
        return { labels: metricLabels, datasets: [{ label: 'Issues Count', backgroundColor: RMA_COLORS, data: metricValues }] }
    }

    const entries = Object.entries(rmaReasonBuckets(returns)).filter(([, count]) => count > 0)
    return {
        labels: entries.length ? entries.map(([label]) => label) : ['Damaged', 'Wrong Item', 'Late Delivery', 'Changed Mind'],
        datasets: [{ label: 'Issues Count', backgroundColor: RMA_COLORS, data: entries.length ? entries.map(([, count]) => count) : [0, 0, 0, 0] }]
    }
}

export function slaChart(dashboardStats) {
    return {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'SLA Compliance (%)',
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            data: dashboardStats?.slaCompliance?.week || [92, 94, 88, 95, 90, 96, 98],
            fill: true,
            tension: 0.4
        }, {
            label: 'Target SLA',
            borderColor: '#ef4444',
            borderDash: [5, 5],
            data: [95, 95, 95, 95, 95, 95, 95],
            pointRadius: 0
        }]
    }
}

export function hubEfficiencyChart(hubs) {
    return {
        labels: hubs ? hubs.map(h => h.name) : ['North', 'South', 'West'],
        datasets: [{
            label: 'Hub Efficiency (%)',
            backgroundColor: hubs ? hubs.map(h => h.efficiency > 90 ? '#10b981' : h.efficiency > 80 ? '#f59e0b' : '#ef4444') : ['#10b981'],
            data: hubs ? hubs.map(h => h.efficiency) : [88, 92, 75]
        }]
    }
}

export const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 2000,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 100
    },
    plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true } }
    },
    scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(200, 200, 200, 0.1)' } },
        x: { grid: { display: false } }
    }
}

export const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        animateScale: true,
        animateRotate: true,
        duration: 2000,
        easing: 'easeOutBounce'
    },
    plugins: {
        legend: { position: 'right' }
    }
}
