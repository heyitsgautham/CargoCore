// Rules behind the logistics manager's returns board: tabs, decision options, the
// status order, which claims need action, and the badge and hint for each status.

export const RETURN_TABS = [
    { id: 'All', label: 'All' },
    { id: 'Reported', label: 'Reported', dot: 'bg-yellow-500' },
    { id: 'Under Review', label: 'Under Review', dot: 'bg-blue-500' },
    { id: 'Claims Reviewed', label: 'Claims Reviewed', dot: 'bg-teal-500' },
    { id: 'Pickup Requested', label: 'Pickup Requested', dot: 'bg-orange-500' },
    { id: 'Pickup Approved', label: 'Pickup Approved', dot: 'bg-blue-500' },
    { id: 'Pickup Scheduled', label: 'Pickup Scheduled', dot: 'bg-blue-400' },
    { id: 'At Warehouse', label: 'At Warehouse', dot: 'bg-purple-500' },
    { id: 'Physically Inspected', label: 'Physically Inspected', dot: 'bg-teal-500' },
    { id: 'Approved', label: 'Approved', dot: 'bg-green-500' },
    { id: 'Rejected', label: 'Rejected', dot: 'bg-red-500' },
    { id: 'Refunded', label: 'Refunded', dot: 'bg-green-400' },
    { id: 'Closed', label: 'Closed', dot: 'bg-gray-400' },
]

export const PHOTO_REVIEW_DECISIONS = [
    { value: 'Full Refund', label: 'Full Refund', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Partial Refund', label: 'Partial Refund', activeClass: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300' },
    { value: 'Reject Claim', label: 'Reject Claim', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
    { value: 'Need More Evidence', label: 'Keep Pending / Need More Evidence', activeClass: 'bg-blue-500/20 border-blue-500/40 text-blue-300' },
]

export const PICKUP_DECISIONS = [
    { value: 'Approve Pickup', label: 'Approve Pickup', desc: 'Forward to dispatcher to assign driver and vehicle.', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Reject Pickup Request', label: 'Reject Pickup Request', desc: 'Decline the pickup — notify customer with reason.', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
    { value: 'Ask for More Evidence', label: 'Ask for More Evidence', desc: 'Request additional photos or information before deciding.', activeClass: 'bg-blue-500/20 border-blue-500/40 text-blue-300' },
]

export const FINAL_DECISIONS = [
    { value: 'Full Refund', label: 'Full Refund — Claim valid, waive charges', activeClass: 'bg-green-500/20 border-green-500/40 text-green-300' },
    { value: 'Partial Refund', label: 'Partial Refund — Deduct reasonable transport/handling charge', activeClass: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300' },
    { value: 'Reject Claim', label: 'Reject Claim — Pickup/transport charge may apply', activeClass: 'bg-red-500/20 border-red-500/40 text-red-300' },
]

const STATUS_ORDER = [
    'Reported', 'Under Review', 'Claims Reviewed',
    'Pickup Requested', 'Pickup Approved', 'Pickup Rejected', 'Pickup Scheduled',
    'Collected', 'At Warehouse', 'Physically Inspected',
    'Approved', 'Partially Approved', 'Rejected', 'Refunded', 'Closed'
]

const RESOLVED = ['Approved', 'Partially Approved', 'Rejected', 'Refunded', 'Closed', 'Pickup Rejected']

/** Counts for the stat cards. */
export function returnStats(returns) {
    return {
        reported: returns.filter(r => !r.status || r.status === 'Reported').length,
        photoReview: returns.filter(r => r.flow_type === 'photo_review').length,
        pickupInspection: returns.filter(r => r.flow_type === 'pickup_inspection').length,
        awaitingLM: returns.filter(r =>
            r.status === 'Claims Reviewed' ||
            r.status === 'Physically Inspected' ||
            (r.flow_type === 'pickup_inspection' && ['Reported', 'Pickup Requested'].includes(r.status || 'Reported'))
        ).length,
        refundValue: returns
            .filter(r => ['Approved', 'Partially Approved', 'Refunded'].includes(r.status))
            .reduce((sum, r) => sum + (r.refundAmount || 0), 0),
    }
}

/** Claims in the selected tab, in workflow order, matching the search on id, order or customer. */
export function filterClaims(returns, activeStatus, searchQuery) {
    let list = returns
    if (activeStatus !== 'All') {
        list = activeStatus === 'Reported'
            ? list.filter(r => !r.status || r.status === 'Reported')
            : list.filter(r => r.status === activeStatus)
    }
    list = [...list].sort((a, b) => STATUS_ORDER.indexOf(a.status || 'Reported') - STATUS_ORDER.indexOf(b.status || 'Reported'))
    if (searchQuery) {
        const q = searchQuery.toLowerCase()
        list = list.filter(r =>
            String(r.id || '').toLowerCase().includes(q) ||
            String(r.orderId || '').toLowerCase().includes(q) ||
            String(r.customer || '').toLowerCase().includes(q)
        )
    }
    return list
}

/** Whether the manager has to act on the claim now. */
export function needsManagerAction(rma) {
    const s = rma.status || 'Reported'
    if (rma.flow_type === 'photo_review') return s === 'Reported' || s === 'Claims Reviewed'
    if (rma.flow_type === 'pickup_inspection') return s === 'Reported' || s === 'Pickup Requested' || s === 'Physically Inspected'
    return false
}

/** Whether someone else (warehouse, dispatcher or driver) is working on the claim. */
export function isInProgress(rma) {
    const s = rma.status || 'Reported'
    if (rma.flow_type === 'photo_review') return s === 'Under Review'
    if (rma.flow_type === 'pickup_inspection') return ['Pickup Approved', 'Pickup Scheduled', 'Collected', 'At Warehouse'].includes(s)
    return false
}

export function isResolved(rma) {
    return RESOLVED.includes(rma.status)
}

export const getRowAccentClass = (rma) => {
    if (needsManagerAction(rma)) return 'border-l-orange-500'
    if (RESOLVED.includes(rma.status || 'Reported')) return 'border-l-gray-400/30'
    return 'border-l-blue-500/60'
}

export function decisionTitle(rma) {
    if (!rma) return 'Review Claim'
    if (rma.flow_type === 'photo_review') return 'Damage Review Decision'
    if (['Reported', 'Pickup Requested'].includes(rma.status || 'Reported')) return 'Pickup Approval Decision'
    return 'Final Inspection Decision'
}

export const getStatusClass = (status) => {
    switch (status) {
        case 'Reported': return 'bg-yellow-50 border-yellow-200 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20'
        case 'Under Review': return 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
        case 'Claims Reviewed': return 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
        case 'Pickup Requested': return 'bg-orange-50 border-orange-200 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/20'
        case 'Pickup Approved': return 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20'
        case 'Pickup Rejected': return 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
        case 'Pickup Scheduled': return 'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-500/10 dark:text-blue-300 dark:border-blue-500/20'
        case 'Collected': return 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400 dark:border-indigo-500/20'
        case 'At Warehouse': return 'bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400 dark:border-purple-500/20'
        case 'Physically Inspected': return 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20'
        case 'Approved': return 'bg-green-50 border-green-200 text-green-700 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20'
        case 'Partially Approved': return 'bg-lime-50 border-lime-200 text-lime-700 dark:bg-lime-500/10 dark:text-lime-400 dark:border-lime-500/20'
        case 'Rejected': return 'bg-red-50 border-red-200 text-red-700 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'
        case 'Refunded': return 'bg-green-50 border-green-300 text-green-700 dark:bg-green-500/10 dark:text-green-300 dark:border-green-500/30'
        case 'Closed': return 'bg-gray-50 border-gray-200 text-gray-600 dark:bg-gray-500/10 dark:text-gray-400 dark:border-gray-500/20'
        default: return 'bg-yellow-50 border-yellow-200 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/20'
    }
}

export const getStatusHint = (status, flowType) => {
    switch (status) {
        case 'Reported': return flowType === 'photo_review' ? 'Awaiting LM — forward to WM' : 'Awaiting LM pickup decision'
        case 'Under Review': return 'WM is reviewing claim'
        case 'Claims Reviewed': return 'LM decision needed'
        case 'Pickup Requested': return 'LM to approve/reject'
        case 'Pickup Approved': return 'Awaiting dispatcher'
        case 'Pickup Rejected': return 'Pickup declined'
        case 'Pickup Scheduled': return 'Driver en route'
        case 'Collected': return 'Parcel picked up'
        case 'At Warehouse': return 'Awaiting WM inspection'
        case 'Physically Inspected': return 'LM final decision needed'
        case 'Approved': return 'Refund approved'
        case 'Partially Approved': return 'Partial refund approved'
        case 'Rejected': return 'Claim rejected'
        case 'Refunded': return 'Refund issued'
        case 'Closed': return 'Case closed'
        default: return 'Awaiting review'
    }
}

export const getStatusHintClass = (status) => {
    switch (status) {
        case 'Claims Reviewed':
        case 'Physically Inspected': return 'text-teal-600 dark:text-teal-400'
        case 'Pickup Requested': return 'text-orange-600 dark:text-orange-400'
        case 'Pickup Approved':
        case 'Pickup Scheduled': return 'text-blue-600 dark:text-blue-400'
        case 'Pickup Rejected':
        case 'Rejected': return 'text-red-600 dark:text-red-400'
        case 'At Warehouse':
        case 'Collected': return 'text-purple-600 dark:text-purple-400'
        case 'Approved': return 'text-green-600 dark:text-green-400'
        case 'Partially Approved': return 'text-lime-600 dark:text-lime-400'
        case 'Refunded': return 'text-green-500 dark:text-green-300'
        case 'Closed': return 'text-gray-400'
        default: return 'text-yellow-600 dark:text-yellow-400'
    }
}

export const formatDateTime = (value) => {
    if (!value) return '—'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return parsed.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}
