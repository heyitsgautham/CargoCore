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

describe('uploading a document', () => {
  it('builds the request only when vehicle, type and file are all present', async () => {
    const { buildDocumentPayload } =
      await import('@/LWD-views/LogisticManager/fleet/useDocumentUpload')
    const form = {
      entityId: 'v1',
      docType: 'Insurance Policy',
      expiryDate: '2027-06-30',
      fileBase64: 'data:application/pdf;base64,AAAA',
    }

    expect(buildDocumentPayload('VEHICLE', form, 'wh-1')).toEqual({
      entity_type: 'VEHICLE',
      entity_id: 'v1',
      hub_id: 'wh-1',
      doc_type: 'Insurance Policy',
      document_url: 'data:application/pdf;base64,AAAA',
      expiry_date: new Date('2027-06-30').toISOString(),
    })
    expect(buildDocumentPayload('DRIVER', { ...form, expiryDate: '' }, 'all')).toMatchObject({
      hub_id: null,
      expiry_date: null,
    })
    expect(buildDocumentPayload('VEHICLE', { ...form, fileBase64: null }, 'all')).toBeNull()
  })

  it('opens from the vehicle documents tab and posts the chosen document', async () => {
    const router = stubFetch([
      ['GET', '/logistics/bootstrap', bootstrap],
      ['GET', '/finance/summary', {}],
      ['GET', '/tracking/drivers', []],
      ['POST', '/logistics/documents', { id: 'doc-1' }],
    ])
    const wrapper = await mountFleet()

    await tab(wrapper, 'Vehicle Documents').trigger('click')
    expect(wrapper.find('#upload-document-title').exists()).toBe(false)
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('Upload Doc'))
      .trigger('click')

    expect(wrapper.find('#upload-document-title').text()).toBe('Upload Vehicle Document')
    const submit = () => wrapper.findAll('[role=dialog] button').at(-1)
    expect(submit().attributes('disabled')).toBeDefined()

    await wrapper.find('#upload-entity').setValue('v1')
    await wrapper.find('#upload-doc-type').setValue('Vehicle Registration')
    const file = new File(['%PDF'], 'rc.pdf', { type: 'application/pdf' })
    const input = wrapper.find('[role=dialog] input[type=file]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await vi.waitFor(() => expect(submit().attributes('disabled')).toBeUndefined())

    await submit().trigger('click')
    await flushPromises()

    const posted = router.calls.find(
      (c) => c.method === 'POST' && c.url.includes('/logistics/documents'),
    )
    expect(posted.body).toMatchObject({
      entity_type: 'VEHICLE',
      entity_id: 'v1',
      doc_type: 'Vehicle Registration',
    })
    expect(posted.body.document_url.startsWith('data:application/pdf')).toBe(true)
    expect(wrapper.find('#upload-document-title').exists()).toBe(false)
    wrapper.unmount()
  })
})
