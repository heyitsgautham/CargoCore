// Printable slips for ledger rows: booking confirmations for revenue, salary slips for payroll,
// and a transaction slip for everything else.
import salarySlipTemplate from '../../../../html-slips/SalarySlip.html?raw'

export function useFinanceSlips({ activeTab, filteredTransactions, openSlipWithData }) {
    const TRACKING_CODE_REGEX = /\b([A-Z]{2,5}-[A-Z0-9]{4,})\b/i

    const extractTrackingCode = (value) => {
        const match = String(value || '').match(TRACKING_CODE_REGEX)
        return match?.[1]?.toUpperCase() || ''
    }

    const findRelatedOrder = (item) => {
        if (item.relatedOrder) return item.relatedOrder
        const metadata = item.metadataJson || {}
        const trackingCode = (
            item.desc === item.id
                ? item.desc
                : metadata.tracking_code || extractTrackingCode(item.desc) || extractTrackingCode(item.id)
        )
        if (!trackingCode) return null
        return filteredTransactions.value.find(tx => tx.relatedOrder?.tracking_code === trackingCode)?.relatedOrder || null
    }

    const isPayrollSlip = (item) => (
        activeTab.value === 'staff'
        || activeTab.value === 'drivers'
        || item.type === 'PAYROLL_RUN'
    )

    const isBookingSlip = (item) => ['REVENUE_ONLINE', 'REVENUE_COD', 'REVENUE_WALLET', 'COD'].includes(item.type)

    const buildBookingSlipPayload = (item) => {
        const order = findRelatedOrder(item)
        if (!order) return null

        return {
            order: {
                id: order.tracking_code || order.id,
                createdAt: order.created_at || item.date,
                eta: order.scheduled_at || order.created_at || item.date,
                serviceTimeBlock: order.service_time_block || 'Flexible',
                origin: order.pickup_addr || '—',
                destination: order.delivery_addr || '—',
                amount: Number(order.total_amount ?? Math.abs(item.amount || 0)),
                paidAmount: Number(order.paid_amount ?? Math.abs(item.amount || 0)),
                paymentMode: order.payment_mode || item.metadataJson?.payment_mode || txTypeLabel(item.type),
                laborCount: Number(order.labor_count || 0),
                vehicleType: order.vehicle_type || order.assigned_vehicle_code || 'Assigned vehicle',
            },
            user: {
                name: order.customer_name || 'Customer',
                phone: order.customer_phone || '—',
                email: order.customer_email || '—',
            },
        }
    }

    const financeSlipTitle = (item) => {
        if (item.type === 'EXPENSE_DRIVER') return 'Driver Shift Fee Slip'
        if (item.type === 'EXPENSE_FUEL' || item.type === 'FUEL_EXPENSE') return 'Fuel Expense Slip'
        if (item.type === 'REVENUE_RETURN_CHARGE') return 'Transport Charge Slip'
        if (item.type === 'REVENUE_REFUND' && item.desc?.toLowerCase().includes('damage')) return 'Damage Return Refund Slip'
        if (item.type === 'REVENUE_REFUND') return 'Refund / Reversal Slip'
        if (item.type === 'REVENUE_WALLET') return 'Wallet Booking Slip'
        if (item.type === 'DRIVER_CASHOUT') return 'Driver Cashout Slip'
        if (item.type === 'CAPITAL_INVESTMENT') return 'Capital Investment Slip'
        return 'Finance Transaction Slip'
    }

    const buildFinanceSlipPayload = (item) => {
        const metadata = item.metadataJson || {}
        const relatedOrder = findRelatedOrder(item)
        const trackingCode = relatedOrder?.tracking_code || metadata.tracking_code || extractTrackingCode(item.desc)
        const beneficiary = metadata.driver_name
            || relatedOrder?.customer_name
            || item.name
            || 'Cargo-Core Ledger'

        return {
            ...item,
            metadataJson: metadata,
            relatedOrder,
            slipTitle: financeSlipTitle(item),
            typeLabel: txTypeLabel(item.type),
            beneficiary,
            transactionCode: item.transactionCode || item.id,
            notes: trackingCode
                ? `${item.desc}. Linked reference: ${trackingCode}.`
                : `${item.desc}.`,
        }
    }

    const openSalarySlip = (item) => {
        const now = new Date()
        const period = now.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
        const paymentDate = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
        const shortDate = now.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

        const net = Math.round(Math.abs(item.amount || 0))
        const profTax = 200
        const tds = Math.round(net * 0.1)
        const totalDeductions = profTax + tds
        const gross = net + totalDeductions
        const basic = Math.round(gross * 0.70)
        const hra = Math.round(gross * 0.20)
        const transport = 2500
        const special = Math.max(0, gross - basic - hra - transport)

        const empId = (item.userId || item.id || '').slice(0, 6).toUpperCase()
        const name = item.name || 'Employee'
        const role = item.role || 'Staff'

        const html = salarySlipTemplate
            // meta & title
            .replace('Salary Slip – February 2026', `Salary Slip – ${period}`)
            .replace('For the month of February 2026', `For the month of ${period}`)
            // employee details
            .replace('Siddarth S', name)
            .replace('WM001', empId)
            .replace('Warehouse Manager', role)
            .replace('28 February 2026', paymentDate)
            // earnings
            .replace('42,000</td>', `${basic.toLocaleString('en-IN')}</td>`)
            .replace('12,000</td>', `${hra.toLocaleString('en-IN')}</td>`)
            .replace('2,500</td>', `${transport.toLocaleString('en-IN')}</td>`)
            .replace('3,500</td>', `${special.toLocaleString('en-IN')}</td>`)
            .replace('₹60,000</td>', `₹${gross.toLocaleString('en-IN')}</td>`)
            // deductions
            .replace('200</td>', `${profTax}</td>`)
            .replace('4,200</td>', `${tds.toLocaleString('en-IN')}</td>`)
            .replace('₹4,400</td>', `₹${totalDeductions.toLocaleString('en-IN')}</td>`)
            // net pay
            .replace('₹55,600</div>', `₹${net.toLocaleString('en-IN')}</div>`)
            // signature date
            .replace('28 Feb 2026', shortDate)

        const blob = new Blob([html], { type: 'text/html' })
        const url = URL.createObjectURL(blob)
        const win = window.open(url, '_blank')
        if (win) win.addEventListener('load', () => URL.revokeObjectURL(url))
    }

    const downloadSlip = async (item) => {
        if (isPayrollSlip(item)) {
            openSalarySlip(item)
            return
        }

        if (isBookingSlip(item)) {
            const bookingPayload = buildBookingSlipPayload(item)
            if (bookingPayload) {
                await openSlipWithData('bookingConfirmation', bookingPayload.order, bookingPayload.user)
                return
            }
        }

        await openSlipWithData('financeTransaction', buildFinanceSlipPayload(item))
    }

    const TX_TYPE_LABELS = {
        'REVENUE_ONLINE': 'Online Payment',
        'REVENUE_COD': 'COD Collection',
        'REVENUE_WALLET': 'Wallet Payment',
        'REVENUE_RETURN_CHARGE': 'Return Transport Charge',
        'REVENUE_REFUND': 'Refund / Reversal',
        'EXPENSE_BONUS': 'Performance Bonus',
        'EXPENSE_DRIVER': 'Driver Cost',
        'EXPENSE_LABOUR': 'Labour Cost',
        'EXPENSE_FUEL': 'Fuel',
        'FUEL_EXPENSE': 'Fuel Receipt',
        'EXPENSE_WAREHOUSE': 'Warehouse',
        'EXPENSE_PROCUREMENT': 'Procurement',
        'PAYROLL_RUN': 'Payroll',
        'DRIVER_CASHOUT': 'Driver Cashout',
        'CAPITAL_INVESTMENT': 'Capital Investment',
        'COD': 'COD Collection',
        'Expense': 'Expense',
        'Incoming': 'Income',
        'Payroll': 'Payroll',
    }
    const txTypeLabel = (type) => TX_TYPE_LABELS[type] || type

    return { downloadSlip, txTypeLabel }
}
