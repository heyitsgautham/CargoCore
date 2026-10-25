/**
 * Pure mapping and normalisation helpers for the logistics manager store.
 * They turn backend payloads into the shapes the dashboard views render.
 */

// Older builds kept every new account's password or PIN here in plain text.
export const LEGACY_CREDENTIAL_CACHE_KEY = 'logistic_manager_created_credentials'

export const asArray = (value) => Array.isArray(value) ? value : []
export const asStringId = (value, fallback = 'all') => value == null ? fallback : String(value)
export const asWarehouseId = (value) => {
    if (value == null) return null
    const normalized = String(value)
    return normalized && normalized.toLowerCase() !== 'all' ? normalized : null
}
export const financeScopeFor = (warehouseId) => warehouseId && warehouseId !== 'all' ? String(warehouseId) : 'all'

export function normalizeReturnStatus(status) {
    if (status === 'Inspected') return 'Physically Inspected'
    return status
}

export function deriveReturnFlowType(item) {
    const explicit = item.flow_type || item.flowType || null
    if (explicit) return explicit

    const status = normalizeReturnStatus(item.status || '')
    if (['Under Review', 'Claims Reviewed'].includes(status)) {
        return 'photo_review'
    }
    if (
        ['Pickup Requested', 'Pickup Approved', 'Pickup Rejected', 'Pickup Scheduled', 'Collected', 'At Warehouse', 'Physically Inspected'].includes(status) ||
        item.wm_disposition ||
        item.wm_graded_at ||
        item.wm_grader_name
    ) {
        return 'pickup_inspection'
    }
    return null
}

export function mapReturnRecord(item) {
    const flowType = deriveReturnFlowType(item)
    return {
        id: asStringId(item.id),
        hubId: asWarehouseId(item.hub_id),
        orderId: item.order_id ? String(item.order_id) : '',
        customer: item.customer,
        reason: item.reason,
        condition: item.condition,
        status: normalizeReturnStatus(item.status),
        flow_type: flowType,
        originalPrice: item.original_price,
        refundAmount: item.refund_amount,
        images: item.images || [],
        referenceCode: item.reference_code,
        walletCredited: item.wallet_credited ?? false,
        wmDisposition: item.wm_disposition || null,
        wmGenuineness: typeof item.wm_is_genuine === 'boolean' ? item.wm_is_genuine : undefined,
        wmRecommendedSettlement: item.wm_recommended_outcome || null,
        wmRemarks: item.wm_inspection_remarks || null,
        wmActualCondition: flowType === 'pickup_inspection' ? item.condition || null : null,
        wmDamageSeverity: flowType === 'photo_review' ? item.condition || null : null,
        wmGradedAt: item.wm_graded_at || null,
        wmGraderName: item.wm_grader_name || null,
        transportChargeAmount: Number(item.transport_charge_amount || 0),
        transportChargeWalletCollected: Number(item.transport_charge_wallet_collected || 0),
        transportChargePendingAmount: Number(item.transport_charge_pending_amount || 0),
        transportChargeStatus: item.transport_charge_status || null,
        transportChargeAppliedAt: item.transport_charge_applied_at || null,
        isUrgent: item.is_urgent ?? false,
        urgentReason: item.urgent_reason || null,
    }
}

/** Delete the plain-text credential store an older build left in localStorage. */
export function purgeLegacyCredentialCache() {
    try {
        localStorage.removeItem(LEGACY_CREDENTIAL_CACHE_KEY)
    } catch {
        // Storage can be unavailable in private windows; there is nothing to clear then.
    }
}

export function roleLabel(role) {
    if (role === 'LOGISTIC_MANAGER') return 'Logistic Manager'
    if (role === 'WAREHOUSE_MANAGER') return 'Warehouse Manager'
    if (role === 'DISPATCHER') return 'Dispatcher'
    if (role === 'DRIVER') return 'Driver'
    if (role === 'AI_AGENT' || role === 'AI_SUPPORT' || role === 'CUSTOMER_SUPPORT') return 'Customer Support'
    if (role === 'VENDOR') return 'Vendor'
    return role || 'User'
}

export function roleApiValue(role) {
    const normalized = String(role || 'DRIVER')
        .trim()
        .replace(/\s+/g, '_')
        .replace(/-/g, '_')
        .toUpperCase()

    if (normalized === 'CUSTOMER_SUPPORT' || normalized === 'AI_SUPPORT') {
        return 'AI_AGENT'
    }

    return normalized
}

export function normalizeDriverLoginId(value, fallbackEmail = '') {
    const raw = String(value || '').trim()
    if (raw) return raw
    const emailPrefix = String(fallbackEmail || '').split('@')[0]?.trim()
    return emailPrefix || ''
}

export function normalizeDriverPin(value) {
    const raw = String(value || '').trim()
    return /^\d{4}$/.test(raw) ? raw : '1234'
}
