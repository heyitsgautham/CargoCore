import { describe, expect, it } from 'vitest'
import { mapBootstrap } from '@/stores/logistic/bootstrapMapping'

const identityUser = (user) => ({ id: String(user.id), name: user.name })

describe('logistics bootstrap mapping', () => {
  it('fills every store field with an empty value for an empty payload', () => {
    const mapped = mapBootstrap({}, identityUser)
    expect(mapped.hubs).toEqual([])
    expect(mapped.financeSummary).toEqual({})
    expect(mapped.creditBalance).toBe(0)
    expect(mapped.dashboardStats.ordersToday).toBe(0)
    expect(Object.keys(mapped)).toHaveLength(32)
  })

  it('maps snake_case API rows to the camelCase shapes views read', () => {
    const mapped = mapBootstrap(
      {
        dashboard_stats: { orders_today: 4, sla_week: [90, 95] },
        hubs: [{ id: 7, name: 'South Hub', status: 'Archived', hub_code: 'HUB-01' }],
        drivers: [{ id: 'd1', hub_id: 7, name: 'Ravi', avatar_color: 'bg-red-600', rating: '4.5' }],
        top_drivers: [{ id: 'd1', name: 'Ravi', trips: 3 }],
        transactions: [
          { id: 1, hub_id: 7, amount: 500, transaction_type: 'REVENUE_ONLINE' },
          { id: 2, amount: -200 },
        ],
        users: [{ id: 3, name: 'Asha' }],
      },
      identityUser,
    )
    expect(mapped.dashboardStats).toMatchObject({
      ordersToday: 4,
      slaCompliance: { week: [90, 95], month: [90, 95] },
    })
    expect(mapped.hubs[0]).toMatchObject({ id: '7', hubCode: 'HUB-01', isActive: false })
    expect(mapped.drivers[0]).toMatchObject({ hubId: '7', rating: 4.5, avatarColor: 'bg-red-600' })
    expect(mapped.topDrivers[0]).toMatchObject({
      hubId: '7',
      avatarColor: 'bg-red-600',
      trips: 3,
      rating: 4.5,
    })
    expect(mapped.transactions[0]).toMatchObject({
      id: '1',
      hubId: '7',
      type: 'REVENUE_ONLINE',
      status: 'Completed',
    })
    expect(mapped.creditBalance).toBe(500)
    expect(mapped.users).toEqual([{ id: '3', name: 'Asha' }])
  })
})
