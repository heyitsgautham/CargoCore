// Formatting and input rules for the user and role management page.

/** Users shown under the selected tab. */
export function filterUsersByTab(users, tab) {
    if (tab === 'All Users') return users
    return users.filter(u => {
        if (tab === 'Vendor Requests') return isVendorRequest(u)
        if (tab === 'Managers') return u.role.includes('Manager')
        if (tab === 'Dispatchers') return u.role.includes('Dispatcher')
        if (tab === 'Drivers') return u.role.includes('Driver')
        if (tab === 'Support') return u.role.includes('Support')
        return true
    })
}

export const getInitials = (name) => {
    if (!name) return '?'
    return name.split(' ').slice(0, 2).map(w => w[0]?.toUpperCase()).join('')
}

export const avatarGradient = (name) => {
    const colors = [
        'linear-gradient(135deg,#667eea,#764ba2)',
        'linear-gradient(135deg,#f093fb,#f5576c)',
        'linear-gradient(135deg,#4facfe,#00f2fe)',
        'linear-gradient(135deg,#43e97b,#38f9d7)',
        'linear-gradient(135deg,#fa709a,#fee140)',
        'linear-gradient(135deg,#a18cd1,#fbc2eb)',
        'linear-gradient(135deg,#ffecd2,#fcb69f)',
        'linear-gradient(135deg,#ff9a9e,#fecfef)',
    ]
    const idx = (name || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % colors.length
    return colors[idx]
}

export const formatLastLogin = (dateStr) => {
    if (!dateStr) return 'Never'
    try {
        return new Date(dateStr).toLocaleString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        })
    } catch {
        return dateStr
    }
}

export const isVendorRequest = (user) => user.role === 'Vendor' && user.approvalStatus === 'PENDING'

export const formatApprovalStatus = (status) => {
    if (!status) return 'Approved'
    return status.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase())
}

export const approvalBadgeClass = (status) => {
    if (status === 'PENDING') return 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300 border-amber-200 dark:border-amber-500/20'
    if (status === 'REJECTED') return 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-300 border-red-200 dark:border-red-500/20'
    return 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/20'
}

export const formatSubmittedAt = (dateStr) => {
    if (!dateStr) return 'New request'
    try {
        return new Date(dateStr).toLocaleString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        })
    } catch {
        return dateStr
    }
}

const ROLE_BY_MODE = { 'create': 'Warehouse Manager', 'create-support': 'Customer Support', 'create-driver': 'Driver' }

/** A blank account form for the create mode, or null for modes that edit an existing user. */
export function emptyStaffForm(mode, hubId) {
    if (!ROLE_BY_MODE[mode]) return null
    return {
        role: ROLE_BY_MODE[mode],
        status: 'Active',
        hubId,
        username: '',
        password: '',
        mobileVerified: false,
        emailVerified: false,
    }
}

/**
 * Tidy a typed value: Aadhaar in 4-digit groups, phones as +91 numbers, PAN and IFSC
 * upper case, and bank accounts as digits only.
 */
export function normalizeFieldValue(key, value) {
    let val = value
    if (key === 'aadharCard') {
        val = val.replace(/\D/g, '').substring(0, 12)
        val = val.replace(/(\d{4})(?=\d)/g, '$1-')
    } else if (key === 'mobile' || key === 'emergencyContact') {
        let digits = val.replace(/[^\d+]/g, '')
        if (digits.length > 0 && !digits.startsWith('+')) {
            digits = '+91 ' + digits
        }
        if (digits.startsWith('+91') && digits.length > 3 && digits[3] !== ' ') {
            digits = '+91 ' + digits.substring(3)
        }
        val = digits.substring(0, 14)
    } else if (key === 'panCard') {
        val = val.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().substring(0, 10)
    } else if (key === 'ifscCode') {
        val = val.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().substring(0, 11)
    } else if (key === 'bankAccount') {
        val = val.replace(/\D/g, '').substring(0, 18)
    }
    return val
}
