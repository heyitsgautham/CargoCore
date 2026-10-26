// Manifest center helpers: which order items are packing assets, how they display,
// a fresh asset log, and trip status and time labels.
import { API_BASE_URL as API_BASE } from '@/config/api'

// ── SKU → display metadata (matches driver app) ────────────────────────────
export const PKG_DISPLAY_MAP = {
    'PKG-CARTON':        { name: 'Cardboard Boxes',      icon: 'inventory_2'  },
    'PKG-BUBBLE-WRAP':   { name: 'Bubble Wrap (rolls)',  icon: 'layers'       },
    'PKG-PLASTIC-CRATE': { name: 'Plastic Crates',       icon: 'cases'        },
    'PKG-BLANKET':       { name: 'Moving Blankets',      icon: 'king_bed'     },
    'PKG-WARDROBE-BOX':  { name: 'Wardrobe Boxes',       icon: 'checkroom'    },
    'PKG-TAPE':          { name: 'Tape Rolls',            icon: 'straighten'  },
}

export const PACKING_KEYWORDS = ['pack', 'wrap', 'box', 'carton', 'tape', 'blanket',
    'crate', 'film', 'pallet', 'protector', 'bag', 'bubble', 'foam', 'wardrobe']

export function isPackingItem(sku, name) {
    if (sku && sku.startsWith('PKG-')) return true
    if (!name) return false
    const lower = name.toLowerCase()
    return PACKING_KEYWORDS.some(kw => lower.includes(kw))
}

export function resolveDisplay(sku, nameFromApi) {
    if (sku && PKG_DISPLAY_MAP[sku]) return PKG_DISPLAY_MAP[sku]
    return { name: nameFromApi || sku || 'Item', icon: 'inventory_2' }
}

/** The packing items on an order, or an empty list when they cannot be loaded. */
export async function fetchTripPackingItems(tripId, token) {
    try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE}/api/v1/orders/${tripId}/items`, { headers })
        if (!res.ok) return []
        const items = await res.json()
        return (items || []).filter(i => isPackingItem(i.sku, i.name))
    } catch {
        return []
    }
}

export function buildLogFromOrderItems(orderItems) {
    return orderItems.map(i => {
        // Prefer the real inventory name returned from the API; fall back to display map then SKU
        const display = resolveDisplay(i.sku, i.name || i.sku)
        return {
            name: display.name,
            icon: display.icon,
            sku: i.sku || null,
            sentOut: i.quantity || 0,
            returned: 0,
        }
    })
}

export function freshLog() {
    // No hardcoded items — returns empty; callers should use fetchTripPackingItems instead
    return []
}

// ── Formatting helpers ─────────────────────────────────────────────────────
export function getStatusClass(status) {
    return {
        ASSIGNED:   'bg-blue-500/10 text-blue-500 border-blue-500/20',
        IN_TRANSIT: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        DELIVERED:  'bg-green-500/10 text-green-500 border-green-500/20',
    }[status] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'
}

export function formatStatus(status) {
    return {
        ASSIGNED:   'Assigned',
        IN_TRANSIT: 'In Transit',
        DELIVERED:  'Delivered',
        CONFIRMED:  'Confirmed',
    }[status] || status
}

export function formatTime(dateStr) {
    if (!dateStr) return '—'
    try {
        return new Date(dateStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
    } catch { return '—' }
}
