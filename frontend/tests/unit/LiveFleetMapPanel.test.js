import { describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import { mount } from '@vue/test-utils'

// Leaflet needs a real layout engine, so the map is a stub that records its props.
const mapProps = []
vi.mock('@vue-leaflet/vue-leaflet', () => {
  const passthrough = (name) =>
    defineComponent({
      name,
      setup:
        (_, { slots }) =>
        () =>
          h('div', slots.default?.()),
    })
  return {
    LMap: defineComponent({
      name: 'LMap',
      inheritAttrs: false,
      setup(_, { attrs, slots }) {
        mapProps.push(attrs)
        return () => h('div', { class: 'l-map' }, slots.default?.())
      },
    }),
    LMarker: passthrough('LMarker'),
    LPopup: passthrough('LPopup'),
    LTileLayer: passthrough('LTileLayer'),
  }
})

const { default: LiveFleetMapPanel } =
  await import('@/LWD-views/LogisticManager/dashboard/LiveFleetMapPanel.vue')
const { lmDashboardPageKey } =
  await import('@/LWD-views/LogisticManager/dashboard/lmDashboardPageContext')

function mountPanel() {
  const ctx = {
    fleetLoading: ref(false),
    fleetMap: ref(null),
    fleetMapCenter: ref([12.97, 77.59]),
    fleetMapZoom: ref(11),
    getDriverIcon: () => null,
    liveDrivers: ref([]),
    mapZoomIn: vi.fn(),
    mapZoomOut: vi.fn(),
    onMapReady: vi.fn(),
    wsConnected: ref(true),
  }
  const wrapper = mount(LiveFleetMapPanel, { global: { provide: { [lmDashboardPageKey]: ctx } } })
  return { wrapper, ctx }
}

describe('logistics dashboard fleet map', () => {
  it("hides Leaflet's own zoom control, which sat under the LIVE FLEET VIEW badge", () => {
    mountPanel()
    expect(mapProps.at(-1).options).toMatchObject({ zoomControl: false })
  })

  it('zooms with the panel buttons instead', async () => {
    const { wrapper, ctx } = mountPanel()
    const [zoomIn, zoomOut] = wrapper.findAll('button')
    await zoomIn.trigger('click')
    await zoomOut.trigger('click')
    expect(ctx.mapZoomIn).toHaveBeenCalledOnce()
    expect(ctx.mapZoomOut).toHaveBeenCalledOnce()
  })
})
