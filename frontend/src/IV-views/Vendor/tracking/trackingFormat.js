/**
 * Date, time, money and metric formatting for the vendor tracking screen.
 */

export function formatLogDate(iso) {
    if (!iso) return '—'
    try {
        const d = new Date(iso)
        const today = new Date()
        const diff = Math.floor((today - d) / 86400000)
        if (diff === 0) return 'Today'
        if (diff === 1) return 'Yesterday'
        return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
    } catch { return iso }
}

export function formatLogTime(iso) {
    if (!iso) return ''
    try { return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) }
    catch { return iso }
}

export function formatCurrencyAmount(value) {
    const amount = Number(value || 0)
    return amount.toLocaleString('en-IN', {
        minimumFractionDigits: amount % 1 === 0 ? 0 : 1,
        maximumFractionDigits: 2,
    })
}

export function formatMetricValue(value) {
    const numeric = Number(value || 0)
    return numeric.toLocaleString('en-IN', {
        minimumFractionDigits: numeric % 1 === 0 ? 0 : 1,
        maximumFractionDigits: 2,
    })
}
