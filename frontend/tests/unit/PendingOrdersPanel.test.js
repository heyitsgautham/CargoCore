import { describe, expect, it, vi } from 'vitest'
import { reactive, ref } from 'vue'
import { mount } from '@vue/test-utils'
import PendingOrdersPanel from '@/LWD-views/Dispatcher/clustering/PendingOrdersPanel.vue'
import { clusteringPageKey } from '@/LWD-views/Dispatcher/clustering/clusteringPageContext'

function mountPanel() {
  const ctx = {
    assigningId: ref(null),
    availableDrivers: ref([{ id: 'd1', name: 'Ravi' }]),
    availableVehicles: ref([{ id: 'v1', licensePlate: 'TX-118-PQ' }]),
    canAssignOrder: () => true,
    manualAssign: vi.fn(),
    needsDispatcherVehicle: () => true,
    orderDriverPick: reactive({}),
    orderVehiclePick: reactive({}),
    priorityClass: () => '',
    recommendedVehicleLabel: () => 'TX-118-PQ',
    unassignedOrders: ref([
      { id: 'o1', trackingCode: 'QC-1', priority: 'NORMAL', pickupAddr: 'A', deliveryAddr: 'B' },
    ]),
    vehicleLabel: (v) => v.licensePlate,
  }
  const wrapper = mount(PendingOrdersPanel, { global: { provide: { [clusteringPageKey]: ctx } } })
  return { wrapper, ctx }
}

describe('order clustering manual assignment', () => {
  it('shows each select placeholder before anything is picked', () => {
    const { wrapper } = mountPanel()
    const [vehicle, driver] = wrapper.findAll('select')
    expect(vehicle.element.selectedIndex).toBe(0)
    expect(vehicle.element.options[0].text).toBe('AI vehicle: TX-118-PQ')
    expect(driver.element.selectedIndex).toBe(0)
    expect(driver.element.options[0].text).toBe('Select Driver')
  })

  it('records the picked driver and vehicle and assigns with them', async () => {
    const { wrapper, ctx } = mountPanel()
    const [vehicle, driver] = wrapper.findAll('select')
    await vehicle.setValue('v1')
    await driver.setValue('d1')
    expect(ctx.orderVehiclePick.o1).toBe('v1')
    expect(ctx.orderDriverPick.o1).toBe('d1')
    await wrapper.find('button').trigger('click')
    expect(ctx.manualAssign).toHaveBeenCalledWith(expect.objectContaining({ id: 'o1' }))
  })
})
