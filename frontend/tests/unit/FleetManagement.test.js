import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { stubFetch } from '../helpers/fetchRouter'

// The map is not under test, and vue-leaflet loads Leaflet's ESM build lazily, which jsdom cannot run.
vi.mock('@vue-leaflet/vue-leaflet', () => {
  const stub = { template: '<div><slot /></div>' }
  return { LMap: stub, LTileLayer: stub, LMarker: stub, LPopup: stub }
})

const { default: FleetManagement } = await import('@/LWD-views/LogisticManager/FleetManagement.vue')

const bootstrap = {
  hubs: [{ id: 'wh-1', name: 'North Hub', status: 'Active' }],
  drivers: [
    {
      id: 'd1',
      hub_id: 'wh-1',
      name: 'Ravi Kumar',
      status: 'Active',
      vehicle: 'TRK-992',
      efficiency: 90,
    },
    {
      id: 'd2',
      hub_id: 'wh-1',
      name: 'Meena Das',
      status: 'Active',
      vehicle: 'VAN-104',
      efficiency: 80,
    },
  ],
  vehicles: [
    {
      id: 'v1',
      hub_id: 'wh-1',
      code: 'TRK-992',
      type: 'Heavy Truck',
      model: 'Volvo FH16',
      status: 'Active',
      driver: 'Ravi Kumar',
      mileage: 1,
    },
  ],
}

class FakeSocket {
  static OPEN = 1
  readyState = 0
  close() {}
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('auth_token', 'tok')
  setActivePinia(createPinia())
  vi.stubGlobal('WebSocket', FakeSocket)
  stubFetch([
    ['GET', '/logistics/bootstrap', bootstrap],
    ['GET', '/finance/summary', {}],
    ['GET', '/tracking/drivers', []],
  ])
})

async function mountFleet() {
  const wrapper = mount(FleetManagement, {
    global: {
      stubs: { Teleport: true },
    },
  })
  await flushPromises()
  return wrapper
}

function tab(wrapper, label) {
  return wrapper.findAll('button').find((b) => b.text() === label)
}

describe('Fleet management', () => {
  it('lists the roster on the drivers tab and switches to the vehicles tab', async () => {
    const wrapper = await mountFleet()

    expect(wrapper.text()).toContain('Driver Roster & Performance')
    expect(wrapper.text()).toContain('Meena Das')

    await tab(wrapper, 'Fleet Vehicles').trigger('click')
    expect(wrapper.text()).not.toContain('Driver Roster & Performance')
    expect(wrapper.text()).toContain('Volvo FH16')
    wrapper.unmount()
  })

  it('filters the roster with the search box', async () => {
    const wrapper = await mountFleet()
    const roster = () => wrapper.find('.glass-panel.h-\\[500px\\]').text()

    await wrapper.find('input[placeholder="Search Active Drivers..."]').setValue('meena')

    expect(roster()).toContain('Meena Das')
    expect(roster()).not.toContain('Ravi Kumar')
    wrapper.unmount()
  })
})
