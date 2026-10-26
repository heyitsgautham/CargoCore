// Warehouse context and archived-hub checks for warehouse managers and dispatchers.
import { getStoredAccessToken, authenticatedJsonRequest } from '@/config/api'
import { buildHubAccessState, isHubScopedRole } from './roleRouting'

export function useHubAccess({
  assignedHubAccess,
  currentWarehouse,
  persistUserProfile,
  syncWarehouseStateFromUser,
  user,
}) {
  async function ensureWarehouseContext() {
    if (!getStoredAccessToken() || !user.value) return null
    if (user.value?.role !== 'WAREHOUSE_MANAGER') { currentWarehouse.value = null; return null }

    try {
      const refreshedProfile = await authenticatedJsonRequest('api/v1/auth/me')
      const profile = persistUserProfile(refreshedProfile)

      const data = await authenticatedJsonRequest('api/v1/warehouses?page=1&page_size=100')
      const warehouses = data.items || []
      const linked = warehouses.find(w =>
        w.id === profile.warehouse_id || w.manager_id === profile.id
      ) || (warehouses.length === 1 ? warehouses[0] : null)

      currentWarehouse.value = linked ? {
        ...linked,
        status: profile.warehouse_status || (linked.is_active === false ? 'Archived' : 'Active'),
      } : currentWarehouse.value
      if (linked && profile.warehouse_id !== linked.id) {
        persistUserProfile({ warehouse_id: linked.id })
      }
      return linked
    } catch {
      return null
    }
  }

  async function ensureHubOperationalAccess(force = false) {
    if (!getStoredAccessToken() || !user.value) {
      assignedHubAccess.value = buildHubAccessState(null)
      return assignedHubAccess.value
    }

    if (!isHubScopedRole(user.value?.role) || !user.value?.warehouse_id) {
      syncWarehouseStateFromUser(user.value)
      return assignedHubAccess.value
    }

    const hasKnownHubStatus = typeof user.value?.warehouse_is_active === 'boolean'
    if (!force && hasKnownHubStatus) {
      syncWarehouseStateFromUser(user.value)
      return assignedHubAccess.value
    }

    try {
      const profile = await authenticatedJsonRequest('api/v1/auth/me')
      persistUserProfile(profile)
    } catch {
      syncWarehouseStateFromUser(user.value)
    }

    return assignedHubAccess.value
  }

  return { ensureWarehouseContext, ensureHubOperationalAccess }
}
