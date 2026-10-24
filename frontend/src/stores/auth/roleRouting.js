/**
 * Role routing rules: which dashboard each role lands on, and the archived-hub
 * screen that warehouse managers and dispatchers see when their hub is closed.
 */

export const ROLE_DASHBOARD_MAP = {
  INDIVIDUAL: '/individual/dashboard',
  VENDOR: '/vendor/dashboard',
  LOGISTIC_MANAGER: '/logistic/dashboard',
  WAREHOUSE_MANAGER: '/warehouse/dashboard',
  DISPATCHER: '/dispatcher/dashboard',
  DRIVER: '/driver/dashboard',
  AI_AGENT: '/ai/dashboard',
  AI_SUPPORT: '/ai/dashboard',
  CUSTOMER_SUPPORT: '/ai/dashboard',
  // lowercase variants used in some legacy code
  ai_agent: '/ai/dashboard',
  ai_support: '/ai/dashboard',
  customer_support: '/ai/dashboard',
  logistics_manager: '/logistic/dashboard',
  warehouse_manager: '/warehouse/dashboard',
  dispatcher: '/dispatcher/dashboard',
  vendor: '/vendor/dashboard',
  customer: '/individual/dashboard',
  manager: '/logistic/dashboard',
  warehouse: '/warehouse/dashboard',
  driver: '/driver/dashboard',
}

const HUB_ARCHIVED_ROUTE_MAP = {
  WAREHOUSE_MANAGER: '/warehouse/archived-access',
  warehouse_manager: '/warehouse/archived-access',
  warehouse: '/warehouse/archived-access',
  DISPATCHER: '/dispatcher/archived-access',
  dispatcher: '/dispatcher/archived-access',
}

const HUB_SCOPED_ROLES = new Set([
  'WAREHOUSE_MANAGER',
  'warehouse_manager',
  'warehouse',
  'DISPATCHER',
  'dispatcher',
])

export function isHubScopedRole(role = '') {
  return HUB_SCOPED_ROLES.has(role)
}

export function getArchivedHubRoute(role = '') {
  return HUB_ARCHIVED_ROUTE_MAP[role] || null
}

export function buildHubAccessState(userData) {
  const role = userData?.role ?? ''
  const warehouseId = userData?.warehouse_id ?? null
  const warehouseIsActive = userData?.warehouse_is_active
  const warehouseStatus = userData?.warehouse_status
    || (warehouseIsActive === false ? 'Archived' : (warehouseId ? 'Active' : null))

  return {
    role,
    warehouseId,
    warehouseName: userData?.warehouse_name || '',
    warehouseAddress: userData?.warehouse_address || '',
    warehouseStatus,
    isArchived: Boolean(isHubScopedRole(role) && warehouseId && warehouseIsActive === false),
  }
}

export function resolveRoleHome(userData) {
  const archivedRoute = getArchivedHubRoute(userData?.role)
  if (archivedRoute && buildHubAccessState(userData).isArchived) {
    return archivedRoute
  }

  return ROLE_DASHBOARD_MAP[userData?.role] || '/login'
}
