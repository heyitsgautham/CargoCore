import { describe, expect, it } from 'vitest'
import {
  ROLE_DASHBOARD_MAP,
  buildHubAccessState,
  getArchivedHubRoute,
  isHubScopedRole,
  resolveRoleHome,
} from '@/stores/auth/roleRouting'

describe('resolveRoleHome', () => {
  it.each([
    ['INDIVIDUAL', '/individual/dashboard'],
    ['VENDOR', '/vendor/dashboard'],
    ['LOGISTIC_MANAGER', '/logistic/dashboard'],
    ['WAREHOUSE_MANAGER', '/warehouse/dashboard'],
    ['DISPATCHER', '/dispatcher/dashboard'],
    ['DRIVER', '/driver/dashboard'],
    ['AI_AGENT', '/ai/dashboard'],
    ['customer_support', '/ai/dashboard'],
  ])('sends %s to %s', (role, path) => {
    expect(resolveRoleHome({ role })).toBe(path)
  })

  it('sends unknown or missing roles to login', () => {
    expect(resolveRoleHome({ role: 'LABOURER' })).toBe('/login')
    expect(resolveRoleHome(null)).toBe('/login')
  })

  it('sends hub staff of an archived warehouse to the archived-access screen', () => {
    const archivedManager = {
      role: 'WAREHOUSE_MANAGER',
      warehouse_id: 'w1',
      warehouse_is_active: false,
    }
    const archivedDispatcher = {
      role: 'dispatcher',
      warehouse_id: 'w1',
      warehouse_is_active: false,
    }

    expect(resolveRoleHome(archivedManager)).toBe('/warehouse/archived-access')
    expect(resolveRoleHome(archivedDispatcher)).toBe('/dispatcher/archived-access')
  })

  it('ignores an archived warehouse for roles that are not hub scoped', () => {
    expect(
      resolveRoleHome({ role: 'LOGISTIC_MANAGER', warehouse_id: 'w1', warehouse_is_active: false }),
    ).toBe(ROLE_DASHBOARD_MAP.LOGISTIC_MANAGER)
  })
})

describe('buildHubAccessState', () => {
  it('derives Active and Archived status when the backend sends none', () => {
    expect(buildHubAccessState({ role: 'DISPATCHER', warehouse_id: 'w1' })).toMatchObject({
      warehouseStatus: 'Active',
      isArchived: false,
    })
    expect(
      buildHubAccessState({ role: 'DISPATCHER', warehouse_id: 'w1', warehouse_is_active: false }),
    ).toMatchObject({ warehouseStatus: 'Archived', isArchived: true })
  })

  it('prefers the backend warehouse_status and copies the hub details', () => {
    const state = buildHubAccessState({
      role: 'WAREHOUSE_MANAGER',
      warehouse_id: 'w9',
      warehouse_name: 'North Hub',
      warehouse_address: '12 Dock Rd',
      warehouse_status: 'Maintenance',
    })

    expect(state).toEqual({
      role: 'WAREHOUSE_MANAGER',
      warehouseId: 'w9',
      warehouseName: 'North Hub',
      warehouseAddress: '12 Dock Rd',
      warehouseStatus: 'Maintenance',
      isArchived: false,
    })
  })

  it('returns an empty state for a signed-out user', () => {
    expect(buildHubAccessState(null)).toEqual({
      role: '',
      warehouseId: null,
      warehouseName: '',
      warehouseAddress: '',
      warehouseStatus: null,
      isArchived: false,
    })
  })
})

describe('hub scoped roles', () => {
  it('covers warehouse managers and dispatchers in every spelling', () => {
    expect(
      ['WAREHOUSE_MANAGER', 'warehouse', 'DISPATCHER', 'dispatcher'].every(isHubScopedRole),
    ).toBe(true)
    expect(isHubScopedRole('DRIVER')).toBe(false)
    expect(isHubScopedRole()).toBe(false)
  })

  it('has an archived route only for hub scoped roles', () => {
    expect(getArchivedHubRoute('warehouse_manager')).toBe('/warehouse/archived-access')
    expect(getArchivedHubRoute('VENDOR')).toBeNull()
  })
})
