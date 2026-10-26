// Labels and colours for return conditions and dispositions on the warehouse returns screen.

export function getDispositionLabel(d) {
    const labels = { restock: 'Restocked', claims: 'Sent to Claims', discard: 'Discarded', recycle: 'Recycled' }
    return labels[d] || d
}

export function getConditionClass(c) {
    if (c === 'Like New') return 'bg-green-500/20 text-green-600 dark:text-green-400'
    if (c === 'Minor Wear') return 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'
    if (c === 'Damaged') return 'bg-orange-500/20 text-orange-600 dark:text-orange-400'
    return 'bg-red-500/20 text-red-600 dark:text-red-400'
}

export function getDispositionBg(d) {
    if (d === 'restock') return 'bg-green-500/20'
    if (d === 'claims') return 'bg-blue-500/20'
    if (d === 'discard') return 'bg-red-500/20'
    return 'bg-purple-500/20'
}

export function getDispositionColor(d) {
    if (d === 'restock') return 'text-green-500'
    if (d === 'claims') return 'text-blue-500'
    if (d === 'discard') return 'text-red-500'
    return 'text-purple-500'
}

export function getDispositionIcon(d) {
    if (d === 'restock') return 'check'
    if (d === 'claims') return 'gavel'
    if (d === 'discard') return 'close'
    return 'recycling'
}
