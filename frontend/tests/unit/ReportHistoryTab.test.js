import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { reportsPageKey } from '@/LWD-views/LogisticManager/reports/reportsPageContext'

vi.mock('vue-chartjs', () => ({ Bar: { template: '<div />' }, Line: { template: '<div />' } }))

const { default: ReportHistoryTab } =
  await import('@/LWD-views/LogisticManager/reports/ReportHistoryTab.vue')

describe('Report history tab', () => {
  it('names each report card after its own hub and offers a CSV', () => {
    const downloadReport = vi.fn()
    const wrapper = mount(ReportHistoryTab, {
      global: {
        provide: {
          [reportsPageKey]: {
            activeTab: 'reports_history',
            analyticsHubData: {},
            analyticsSLAData: {},
            chartOptions: {},
            downloadReport,
            store: {
              activeWarehouseName: 'All Warehouses',
              hubs: [{ id: 'wh-1', name: 'North-East Hub' }],
              filteredReports: [
                {
                  id: 'R-1',
                  hubId: 'wh-1',
                  title: 'Weekly SLA',
                  date: 'Oct 20',
                  icon: 'summarize',
                  color: 'blue',
                },
                {
                  id: 'R-2',
                  hubId: 'gone',
                  title: 'Old',
                  date: 'Oct 1',
                  icon: 'summarize',
                  color: 'blue',
                },
              ],
            },
          },
        },
      },
    })

    expect(wrapper.text()).toContain('Date: Oct 20 • North-East Hub')
    expect(wrapper.text()).toContain('Date: Oct 1 • All Warehouses')
    expect(wrapper.text()).toContain('Download CSV')

    wrapper.find('button').trigger('click')
    expect(downloadReport).toHaveBeenCalledWith('R-1')
  })
})
