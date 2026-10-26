import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { useFinanceSlips } from '@/LWD-views/LogisticManager/finance/useFinanceSlips'

const order = {
  tracking_code: 'QC-LOGI001',
  pickup_addr: 'Amazon FC, Newark',
  delivery_addr: 'Client DC, Boston',
  total_amount: 18630,
  customer_name: 'Mehta Home Retail',
}

function slips(tab = 'overview') {
  const openSlipWithData = vi.fn()
  const api = useFinanceSlips({
    activeTab: ref(tab),
    filteredTransactions: ref([{ id: 't0', relatedOrder: order }]),
    openSlipWithData,
  })
  return { ...api, openSlipWithData }
}

describe('finance ledger slips', () => {
  it('opens a booking confirmation for revenue linked to an order by its tracking code', async () => {
    const { downloadSlip, openSlipWithData } = slips()

    await downloadSlip({
      id: 't1',
      type: 'REVENUE_ONLINE',
      desc: 'Payment for QC-LOGI001',
      amount: 18630,
    })

    const [kind, payload, user] = openSlipWithData.mock.calls[0]
    expect(kind).toBe('bookingConfirmation')
    expect(payload).toMatchObject({ id: 'QC-LOGI001', origin: 'Amazon FC, Newark', amount: 18630 })
    expect(user.name).toBe('Mehta Home Retail')
  })

  it('falls back to a transaction slip when revenue has no matching order', async () => {
    const { downloadSlip, openSlipWithData } = slips()

    await downloadSlip({ id: 't2', type: 'EXPENSE_FUEL', desc: 'Diesel', amount: -900 })

    expect(openSlipWithData.mock.calls[0][0]).toBe('financeTransaction')
  })

  it('opens a salary slip on the payroll tabs instead of a shared slip', async () => {
    const { downloadSlip, openSlipWithData } = slips('staff')
    const open = vi.spyOn(window, 'open').mockReturnValue(null)
    vi.stubGlobal('URL', { ...URL, createObjectURL: () => 'blob:x', revokeObjectURL: () => {} })

    await downloadSlip({
      id: 't3',
      type: 'PAYROLL_RUN',
      name: 'Ravi',
      amount: -60000,
      date: 'Oct 26',
    })

    expect(openSlipWithData).not.toHaveBeenCalled()
    expect(open).toHaveBeenCalledWith('blob:x', '_blank')
  })

  it('names transaction types', () => {
    const { txTypeLabel } = slips()
    expect(txTypeLabel('REVENUE_COD')).toBe('COD Collection')
    expect(txTypeLabel('SOMETHING_NEW')).toBe('SOMETHING_NEW')
  })
})
