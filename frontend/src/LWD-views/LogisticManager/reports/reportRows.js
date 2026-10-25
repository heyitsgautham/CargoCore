// Attendance rules and the CSV rows each report tab exports.

/** Whether the user's last login falls on the given YYYY-MM-DD day. */
export function loggedInOn(user, day) {
    if (!user.lastLogin) return false
    return String(user.lastLogin).slice(0, 10) === day
}

export function attendanceCounts(users, day) {
    const present = users.filter(u => loggedInOn(u, day)).length
    const onLeave = users.filter(u => /leave|vacation/i.test(u.status || '')).length
    return {
        present,
        onLeave,
        unplanned: Math.max(0, users.length - present - onLeave),
        presentPct: users.length ? Math.round(present / users.length * 100) : 0,
    }
}

/** 20 days of annual leave, with days taken estimated from the user's status and id. */
export function userLeave(user) {
    const allowed = 20
    let taken = 0
    if (/leave|vacation/i.test(user.status || '')) {
        taken = 5
    } else {
        const code = (user.id || '').slice(-1).charCodeAt(0) || 0
        taken = code % 6
    }
    return { allowed, taken, balance: allowed - taken, extra: Math.max(0, taken - allowed) }
}

/** Header and rows for the tab's CSV export. A result of one row means nothing to export. */
export function exportRows(tab, store, day) {
    switch (tab) {
        case 'control_tower':
            return [
                ['Type', 'ID', 'Name', 'Status', 'Efficiency'],
                ...store.filteredDrivers.map(d => ['Driver', d.id, d.name, d.status, d.efficiency ?? '']),
                ...store.filteredVehicles.map(v => ['Vehicle', v.id || v.code, v.name || v.model || '', v.status, '']),
            ]
        case 'financials':
            return [
                ['ID', 'Type', 'Amount', 'Status', 'Date'],
                ...store.filteredTransactions.map(t => [t.id, t.type, t.amount, t.status, t.date || '']),
            ]
        case 'attendance':
            return [
                ['Name', 'Email', 'Status Today', 'Last Login'],
                ...store.filteredUsers.map(u => [u.name, u.email, loggedInOn(u, day) ? 'Present' : 'Absent', u.lastLogin || '']),
            ]
        case 'workforce':
            return [
                ['Name', 'Email', 'Role', 'Hub'],
                ...store.filteredUsers.map(u => [u.name, u.email, u.role || '', u.hubId || '']),
            ]
        case 'assets':
            return [
                ['ID', 'Name', 'Category', 'Quantity', 'Status'],
                ...store.filteredInventory.map(i => [i.id, i.name, i.category, i.quantity, i.status || '']),
            ]
        case 'returns':
            return [
                ['RMA ID', 'Customer', 'Order Ref', 'Reason', 'Condition', 'Status'],
                ...store.filteredReturns.map(r => [r.id, r.customer, r.orderId || '', r.reason, r.condition, r.status]),
            ]
        case 'security_audit':
            return [
                ['Timestamp', 'Admin User', 'Action', 'Target', 'Details', 'IP'],
                ...(store.filteredSecurityLogs || []).map(l => [l.time, l.actor, l.action, l.target, l.details, l.ip]),
            ]
        case 'reports_history':
            return [
                ['Report ID', 'Title', 'Date', 'Warehouse'],
                ...store.filteredReports.map(r => [r.id, r.title, r.date, store.activeWarehouseName || '']),
            ]
        default:
            return []
    }
}

export function toCsv(rows) {
    return rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
}

export function downloadCsv(filename, rows) {
    const blob = new Blob([toCsv(rows)], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}
