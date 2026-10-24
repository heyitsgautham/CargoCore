import { describe, expect, it } from 'vitest'
import { laborAssignmentReplacements } from '@/composables/slips/operationsSlips'
import { bookingConfirmationReplacements } from '@/composables/slips/orderSlips'

// Each map replaces the sample text baked into an HTML slip template with live data.

describe('bookingConfirmationReplacements', () => {
  it('fills customer, route and payment placeholders from the order', () => {
    const map = bookingConfirmationReplacements(
      {
        id: 'ORD-77',
        amount: 4000,
        paidAmount: 1000,
        origin: 'Koramangala',
        destination: 'Hebbal',
        laborCount: 3,
        vehicleType: 'Tempo',
        paymentMode: 'UPI',
      },
      { name: 'Asha', phone: '99999', email: 'asha@example.com' },
    )

    expect(map['CC-12345']).toBe('ORD-77')
    expect(map['Sarah Khan']).toBe('Asha')
    expect(map['123 Oak Street, Whitefield']).toBe('Koramangala')
    expect(map['₹4,500']).toBe('₹4,000')
    expect(map['₹1,350']).toBe('₹1,000')
    expect(map['₹3,150']).toBe('₹3,000')
    expect(map['Advance Paid (30%)']).toBe('Advance Paid (25%)')
    expect(map['4 skilled workers']).toBe('3 workers')
    expect(map['14 ft covered truck']).toBe('Tempo')
    expect(map['UPI / Online Transfer']).toBe('UPI')
  })

  it('never shows a negative balance and drops the advance percentage when nothing is paid', () => {
    const overpaid = bookingConfirmationReplacements({ amount: 100, paidAmount: 150 }, null)
    expect(overpaid['₹3,150']).toBe('₹0')

    const unpaid = bookingConfirmationReplacements({ amount: 100 }, null)
    expect(unpaid['Advance Paid (30%)']).toBe('Advance Paid')
    expect(unpaid['Sarah Khan']).toBe('—')
    expect(unpaid['4 skilled workers']).toBe('On-demand')
  })
})

describe('laborAssignmentReplacements', () => {
  it('builds the employee code and role from the staff record', () => {
    const map = laborAssignmentReplacements({
      id: 'abc123xyz',
      name: 'Kiran',
      orderId: 'ORD-9',
      role: 'Packer',
      task: 'Wrap fragile items',
      perf: 92,
      startTime: '10:00 AM',
    })

    expect(map['EMP-2541']).toBe('EMP-ABC123')
    expect(map['Rajesh Kumar']).toBe('Kiran')
    expect(map['TEAM LEAD']).toBe('PACKER')
    expect(map['8 Years']).toBe('92%')
    expect(map['09:00 AM - 05:00 PM']).toBe('10:00 AM — End of Shift')
    expect(map['456 Maple Avenue, Indiranagar']).toBe('Order: ORD-9')
  })

  it('uses safe defaults for a sparse staff record', () => {
    const map = laborAssignmentReplacements({ startTime: '--' })

    expect(map['EMP-2541']).toBe('EMP-TBD')
    expect(map['Rajesh Kumar']).toBe('Staff Member')
    expect(map['09:00 AM - 05:00 PM']).toBe('09:00 AM — End of Shift')
    expect(map['456 Maple Avenue, Indiranagar']).toBe('Order Location')
  })
})
