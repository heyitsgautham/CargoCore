// The trend chart under the logistics dashboard: SLA, revenue or orders for the week or month,
// drawn point by point.

const SERIES = {
    sla: { stat: 'slaCompliance', label: 'SLA Compliance (%)', bg: 'rgba(56, 189, 248, 0.1)', border: 'rgb(56, 189, 248)' },
    revenue: { stat: 'revenue', label: 'Revenue ($)', bg: 'rgba(16, 185, 129, 0.1)', border: 'rgb(16, 185, 129)' },
    orders: { stat: 'orders', label: 'Order Volume', bg: 'rgba(168, 85, 247, 0.1)', border: 'rgb(168, 85, 247)' },
}

export function trendChartData(dashboardStats, tab, period) {
    const series = SERIES[tab]
    const data = series ? (dashboardStats[series.stat][period] || []) : []
    const labels = period === 'week'
        ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        : Array.from({ length: data.length }, (_, i) => i + 1)
    return {
        labels,
        datasets: [
            {
                label: series?.label || '',
                backgroundColor: series?.bg,
                borderColor: series?.border,
                borderWidth: 2,
                pointBackgroundColor: series?.border,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: series?.border,
                fill: true,
                tension: 0.4,
                data,
            }
        ]
    }
}

// Progressive animation: each point appears in turn over about a second.
const totalDuration = 1000
const delayBetweenPoints = totalDuration / 30 // Max points is ~30 for month
const previousY = (ctx) => ctx.index === 0 ? ctx.chart.scales.y.getPixelForValue(100) : ctx.chart.getDatasetMeta(ctx.datasetIndex).data[ctx.index - 1].getProps(['y'], true).y

const animationConfig = {
    x: {
        type: 'number',
        easing: 'linear',
        duration: delayBetweenPoints,
        from: NaN, // the point is initially skipped
        delay(ctx) {
            if (ctx.type !== 'data' || ctx.xStarted) {
                return 0
            }
            ctx.xStarted = true
            return ctx.index * delayBetweenPoints
        }
    },
    y: {
        type: 'number',
        easing: 'linear',
        duration: delayBetweenPoints,
        from: previousY,
        delay(ctx) {
            if (ctx.type !== 'data' || ctx.yStarted) {
                return 0
            }
            ctx.yStarted = true
            return ctx.index * delayBetweenPoints
        }
    }
}

/** The tooltip text for one point: a percentage, a dollar amount or a plain count. */
export function trendTooltipLabel(tab, datasetLabel, y) {
    let label = datasetLabel ? `${datasetLabel}: ` : ''
    if (tab === 'sla') label += y + '%'
    else if (tab === 'revenue') label += '$' + y.toLocaleString()
    else label += y.toLocaleString()
    return label
}

export function trendChartOptions(tab) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: animationConfig,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: (context) => trendTooltipLabel(tab, context.dataset.label || '', context.parsed.y),
                }
            }
        },
        scales: {
            y: {
                min: tab === 'sla' ? 70 : 0,
                max: tab === 'sla' ? 100 : undefined,
                grid: {
                    color: 'rgba(156, 163, 175, 0.1)',
                    drawBorder: false,
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false,
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    }
}
