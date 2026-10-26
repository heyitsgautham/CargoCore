// Packing material records: icons, the per-hub issuance log cache in localStorage,
// log normalisation and merging, and matching order item SKUs to stock.

const MAX_CACHED_ISSUANCE_LOGS = 200

// Emoji map by category/name
export function getEmoji(name = '', category = '') {
    const n = (name + category).toLowerCase()
    if (n.includes('box') || n.includes('carton')) return '📦'
    if (n.includes('bubble') || n.includes('wrap')) return '🫧'
    if (n.includes('tape') || n.includes('adhesive')) return '🔖'
    if (n.includes('blanket') || n.includes('pad')) return '🛡️'
    if (n.includes('crate') || n.includes('plastic')) return '📥'
    if (n.includes('stretch') || n.includes('film')) return '🔄'
    if (n.includes('label') || n.includes('sheet')) return '🏷️'
    if (n.includes('dolly') || n.includes('cart')) return '🛒'
    if (n.includes('corner') || n.includes('protector')) return '📐'
    if (n.includes('bag')) return '🛍️'
    if (n.includes('pallet')) return '🪵'
    return '📦'
}

export function issuanceLogStorageKey(warehouseId) {
    return `warehouse-material-issuance-log:${warehouseId || 'unassigned'}`
}

export function readCachedIssuanceLogs(warehouseId) {
    if (typeof window === 'undefined') return []

    try {
        const raw = window.localStorage.getItem(issuanceLogStorageKey(warehouseId))
        const parsed = raw ? JSON.parse(raw) : []
        return Array.isArray(parsed) ? parsed : []
    } catch {
        return []
    }
}

export function writeCachedIssuanceLogs(warehouseId, logs) {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(
        issuanceLogStorageKey(warehouseId),
        JSON.stringify((logs || []).slice(0, MAX_CACHED_ISSUANCE_LOGS))
    )
}

export function formatIssuanceTime(createdAt) {
    const date = createdAt ? new Date(createdAt) : new Date()
    if (Number.isNaN(date.getTime())) return ''
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

export function normalizeIssuanceLog(log = {}) {
    const movementType = (log.movement_type || log.type || '').toUpperCase()
    const type = movementType === 'RESERVED' || log.type === 'reserved' ? 'reserved' : 'issued'
    // PACK movements are auto-deductions triggered by complete_packing; label them clearly
    const isPack = movementType === 'PACK'
    const createdAt = log.created_at || log.createdAt || new Date().toISOString()
    const orderId = log.reference_order_tracking || log.orderId || (
        typeof log.reference_order_id === 'string' ? log.reference_order_id.slice(0, 8) : null
    ) || 'N/A'
    const material = log.item_name || log.material || 'Item'
    const qty = Number(log.quantity ?? log.qty ?? 0)
    const issuedTo = log.issuedTo || log.performed_by_name || log.performedByName || 'System'

    const displayStatus = isPack ? 'Auto-Packed' : (type === 'issued' ? 'Issued' : 'Reserved')
    const displayStatusClass = isPack
        ? 'bg-blue-500/10 text-blue-500 border-blue-500/20'
        : (type === 'issued' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20')

    return {
        id: String(log.id || `${type}-${orderId}-${material}-${qty}-${createdAt}`),
        orderId,
        material,
        qty,
        issuedTo: isPack ? 'System (Packing)' : issuedTo,
        time: formatIssuanceTime(createdAt),
        createdAt,
        status: displayStatus,
        statusClass: displayStatusClass,
        type: isPack ? 'issued' : type,  // PACK shows in "Issued" tab
    }
}

export function mergeIssuanceLogs(...logGroups) {
    const merged = new Map()

    for (const group of logGroups) {
        for (const log of group || []) {
            const normalized = normalizeIssuanceLog(log)
            const existing = merged.get(normalized.id)

            if (existing) {
                merged.set(normalized.id, {
                    ...existing,
                    ...normalized,
                    issuedTo: normalized.issuedTo || existing.issuedTo,
                })
                continue
            }

            merged.set(normalized.id, normalized)
        }
    }

    return [...merged.values()].sort((left, right) => {
        const leftTime = Date.parse(left.createdAt || '') || 0
        const rightTime = Date.parse(right.createdAt || '') || 0
        return rightTime - leftTime
    })
}

export function normalizeSku(value = '') {
    return String(value || '').trim().toUpperCase()
}

export function inventoryIdTokenFromSku(sku = '') {
    return normalizeSku(sku).replace(/^PKG-/, '')
}

export function keywordsForSku(sku = '') {
    const normalized = normalizeSku(sku)
    const keywordMap = {
        'PKG-CARTON': ['carton', 'box'],
        'PKG-BUBBLE-WRAP': ['bubble', 'wrap'],
        'PKG-PLASTIC-CRATE': ['crate', 'plastic'],
        'PKG-BLANKET': ['blanket', 'pad'],
        'PKG-WARDROBE-BOX': ['wardrobe', 'box'],
        'PKG-TAPE': ['tape'],
        'PKG-BOX': ['box', 'carton'],
        'FOAM-SHEET': ['foam', 'sheet'],
        'PKG-FOAM-SHEET': ['foam', 'sheet'],
    }
    const tokens = normalized
        .replace(/^PKG-/, '')
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .filter(token => token.length > 2)
    const phrase = normalized.replace(/^PKG-/, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
    return [...new Set([...(keywordMap[normalized] || []), ...tokens, phrase].filter(Boolean))]
}
