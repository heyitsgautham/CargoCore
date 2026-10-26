import { ref } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useShipmentActions } from '@/IV-views/Vendor/tracking/useShipmentActions'

function setup(
  selected = { id: 'QC-1', backendId: 'o1', customerRating: 4, customerFeedback: 'Good' },
) {
  const store = {
    updateShipmentAddress: vi.fn().mockResolvedValue(),
    rescheduleShipment: vi.fn().mockResolvedValue(),
    cancelShipment: vi.fn().mockResolvedValue(),
    reportDamage: vi.fn().mockResolvedValue(),
    addTicket: vi.fn(),
    submitCustomerRating: vi.fn().mockResolvedValue({ success: true }),
  }
  const shipment = ref(selected)
  return { store, shipment, ...useShipmentActions(store, shipment) }
}

beforeEach(() => vi.useFakeTimers())
afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('vendor shipment actions', () => {
  it('updates the address and reschedules, then closes each dialog', async () => {
    const a = setup()
    a.newAddress.value = '  12 MG Road  '
    a.showAddressModal.value = true
    await a.updateAddress()
    expect(a.store.updateShipmentAddress).toHaveBeenCalledWith('QC-1', '12 MG Road')
    expect(a.showAddressModal.value).toBe(false)
    expect(document.body.textContent).toContain('Address updated successfully')

    a.newDate.value = '2026-11-02'
    await a.reschedule()
    expect(a.store.rescheduleShipment).toHaveBeenCalledWith(
      'QC-1',
      new Date('2026-11-02').toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
        year: 'numeric',
      }),
    )
  })

  it('ignores empty addresses, dates and damage descriptions', async () => {
    const a = setup()
    await a.updateAddress()
    await a.reschedule()
    await a.submitDamage()
    expect(a.store.updateShipmentAddress).not.toHaveBeenCalled()
    expect(a.store.rescheduleShipment).not.toHaveBeenCalled()
    expect(a.store.reportDamage).not.toHaveBeenCalled()
  })

  it('cancels only after the vendor confirms', async () => {
    const a = setup()
    vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true)
    await a.handleCancel()
    expect(a.store.cancelShipment).not.toHaveBeenCalled()
    await a.handleCancel()
    expect(a.store.cancelShipment).toHaveBeenCalledWith('QC-1')
  })

  it('reports damage and resets the form', async () => {
    const a = setup()
    a.damageForm.severity = 'High'
    a.damageForm.description = 'Crushed carton'
    await a.submitDamage()
    expect(a.store.reportDamage).toHaveBeenCalledWith('QC-1', {
      severity: 'High',
      description: 'Crushed carton',
      photos: [],
    })
    expect(a.damageForm).toMatchObject({ severity: 'Medium', description: '' })
  })

  it('opens the rating dialog with the earlier rating and submits a new one', async () => {
    const a = setup()
    a.openVendorRatingModal()
    expect(a.vendorRatingModal).toMatchObject({ show: true, selected: 4, feedback: 'Good' })

    a.vendorRatingModal.selected = 5
    a.vendorRatingModal.feedback = ''
    await a.submitVendorRating()
    expect(a.store.submitCustomerRating).toHaveBeenCalledWith('o1', 5, null)
    expect(a.vendorRatingModal.show).toBe(false)
  })

  it('raises a support ticket and keeps chat messages', () => {
    const a = setup()
    a.supportMessage.value = 'Where is my truck?'
    a.submitSupport()
    expect(a.store.addTicket).toHaveBeenCalledWith({
      subject: 'Support needed for QC-1',
      description: 'Where is my truck?',
      orderId: 'QC-1',
      priority: 'Medium',
    })

    a.newChatMessage.value = 'Please call'
    a.sendChatMessage()
    a.newChatMessage.value = '   '
    a.sendChatMessage()
    expect(a.chatMessages.value.map((m) => m.text)).toEqual(['Please call'])

    const file = { name: 'invoice.pdf' }
    const target = { files: [file], value: 'x' }
    a.handleFileUpload({ target })
    expect(a.chatMessages.value.at(-1).text).toContain('invoice.pdf')
    expect(target.value).toBe('')
  })
})
