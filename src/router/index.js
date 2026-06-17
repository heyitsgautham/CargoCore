import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ── Landing & Public Pages ─────────────────────────────────
  {
    path: '/',
    name: 'Home',
    component: () => import('../LWDDVI-views/Home.vue'),
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../LWDDVI-views/About.vue'),
  },
  {
    path: '/article',
    name: 'Article',
    component: () => import('../LWDDVI-views/Article.vue'),
  },
  {
    path: '/contact',
    name: 'Contact',
    component: () => import('../LWDDVI-views/Contact.vue'),
  },
  {
    path: '/terms',
    name: 'Terms',
    component: () => import('../LWDDVI-views/Terms.vue'),
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: () => import('../LWDDVI-views/Privacy.vue'),
  },

  // ── Authentication — AuthLayout handles view switching internally ──
  {
    path: '/login',
    name: 'Login',
    component: () => import('../layouts/AuthLayout.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../layouts/AuthLayout.vue'),
    meta: { guest: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../layouts/AuthLayout.vue'),
    meta: { guest: true },
  },
  {
    path: '/verify-otp',
    name: 'VerifyOTP',
    component: () => import('../layouts/AuthLayout.vue'),
  },
  {
    path: '/setup-tfa',
    name: 'SetupTFA',
    component: () => import('../layouts/AuthLayout.vue'),
    meta: { requiresAuth: true },
  },

  // ── Legacy login paths — redirect to unified /login ─────────
  {
    path: '/login-hub',
    redirect: '/login',
  },
  {
    path: '/login/:role',
    redirect: '/login',
  },
  {
    path: '/signup',
    redirect: '/register',
  },
  {
    path: '/2fa',
    redirect: '/verify-otp',
  },
  {
    path: '/signup-success',
    redirect: '/login',
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('../pages/ResetPassword.vue'),
  },
  {
    path: '/dashboard',
    redirect: () => {
      try {
        const user = JSON.parse(localStorage.getItem('auth_user') || 'null')
        const map = {
          INDIVIDUAL: '/individual/dashboard',
          VENDOR: '/vendor/dashboard',
          LOGISTIC_MANAGER: '/logistic/dashboard',
          LOGISTIC_MANAGER: '/logistic/dashboard',
          WAREHOUSE_MANAGER: '/warehouse/dashboard',
          DISPATCHER: '/dispatcher/dashboard',
          DRIVER: '/driver/dashboard',
          AI_AGENT: '/ai/dashboard',
          AI_SUPPORT: '/ai/dashboard',
          CUSTOMER_SUPPORT: '/ai/dashboard',
          ai_agent: '/ai/dashboard',
          ai_support: '/ai/dashboard',
          customer_support: '/ai/dashboard',
        }
        return map[user?.role] || '/login'
      } catch {
        return '/login'
      }
    },
  },

  // ── Individual User Routes ────────────────────────────────────
  {
    path: '/individual',
    component: () => import('../layouts/IndividualLayout.vue'),
    children: [
      { path: 'dashboard', name: 'IndividualDashboard', component: () => import('../IV-views/Individual/Dashboard.vue') },
      { path: 'book-move', name: 'IndividualBookMove', component: () => import('../IV-views/Individual/BookMove.vue') },
      { path: 'orders', name: 'IndividualOrders', component: () => import('../IV-views/Individual/Orders.vue') },
      { path: 'quotes', name: 'IndividualQuotes', component: () => import('../IV-views/Individual/Quotes.vue') },
      { path: 'estimator', name: 'IndividualEstimator', component: () => import('../IV-views/Individual/Estimator.vue') },
      { path: 'payments', name: 'IndividualPayments', component: () => import('../IV-views/Individual/Payments.vue') },
      { path: 'wallet', name: 'IndividualWallet', component: () => import('../IV-views/Individual/Wallet.vue') },
      { path: 'support', name: 'IndividualSupport', component: () => import('../IV-views/Individual/Support.vue') },
      { path: 'profile', name: 'IndividualProfile', component: () => import('../IV-views/Individual/Profile.vue') },
      { path: 'tracking', name: 'IndividualTracking', component: () => import('../IV-views/Individual/Tracking.vue') },
      { path: 'damage-report', name: 'IndividualDamageReport', component: () => import('../IV-views/Individual/DamageReport.vue') },
      { path: 'settings', name: 'IndividualSettings', component: () => import('../IV-views/Individual/Settings.vue') },
    ],
  },

  // ── Vendor Routes ──────────────────────────────────────────────
  {
    path: '/vendor',
    component: () => import('../layouts/VendorLayout.vue'),
    children: [
      { path: 'dashboard', name: 'VendorDashboard', component: () => import('../IV-views/Vendor/Dashboard.vue') },
      { path: 'create-shipment', name: 'VendorCreateShipment', component: () => import('../IV-views/Vendor/CreateShipment.vue') },
      { path: 'orders', name: 'VendorOrders', component: () => import('../IV-views/Vendor/Orders.vue') },
      { path: 'tracking', name: 'VendorTracking', component: () => import('../IV-views/Vendor/Tracking.vue') },
      { path: 'recurring', name: 'VendorRecurring', component: () => import('../IV-views/Vendor/RecurringShipments.vue') },
      { path: 'bulk-upload', name: 'VendorBulkUpload', component: () => import('../IV-views/Vendor/BulkUpload.vue') },
      { path: 'proof-of-delivery', name: 'VendorProofOfDelivery', component: () => import('../IV-views/Vendor/ProofOfDelivery.vue') },
      { path: 'invoices', name: 'VendorInvoices', component: () => import('../IV-views/Vendor/Invoices.vue') },
      { path: 'wallet', name: 'VendorWallet', component: () => import('../IV-views/Vendor/Wallet.vue') },
      { path: 'analytics', name: 'VendorAnalytics', component: () => import('../IV-views/Vendor/Analytics.vue') },
      { path: 'settings', name: 'VendorSettings', component: () => import('../IV-views/Vendor/Settings.vue') },
      { path: 'support', name: 'VendorSupport', component: () => import('../IV-views/Vendor/Support.vue') },
    ],
  },
  {
    path: '/vendor/api-docs',
    name: 'VendorApiDocs',
    component: () => import('../IV-views/Vendor/ApiDocs.vue'),
  },

  // ── Logistic Manager Routes ─────────────────────────────────────
  {
    path: '/logistic',
    component: () => import('../layouts/LogisticLayout.vue'),
    redirect: '/logistic/dashboard',
    children: [
      { path: 'dashboard', name: 'LogisticDashboard', component: () => import('../LWD-views/LogisticManager/Dashboard.vue') },
      { path: 'warehouses', name: 'LogisticWarehouseManagement', component: () => import('../LWD-views/LogisticManager/WarehouseManagement.vue') },
      { path: 'users', name: 'LogisticUserManagement', component: () => import('../LWD-views/LogisticManager/UserManagement.vue') },
      { path: 'fleet', name: 'LogisticFleetManagement', component: () => import('../LWD-views/LogisticManager/FleetManagement.vue') },
      { path: 'geofencing', name: 'LogisticGeofencing', component: () => import('../LWD-views/LogisticManager/Geofencing.vue') },
      { path: 'finance', name: 'LogisticFinance', component: () => import('../LWD-views/LogisticManager/Finance.vue') },
      { path: 'rate-governance', name: 'LogisticRateGovernance', component: () => import('../LWD-views/LogisticManager/RateGovernance.vue') },
      { path: 'reverse-logistics', name: 'LogisticReverseLogistics', component: () => import('../LWD-views/LogisticManager/ReverseLogistics.vue') },
      { path: 'reports', name: 'LogisticReports', component: () => import('../LWD-views/LogisticManager/Reports.vue') },
      { path: 'ai', name: 'LogisticAIIntelligence', component: () => import('../LWD-views/LogisticManager/AIIntelligence.vue') },
      { path: 'recovery-tickets', name: 'LogisticRecoveryTickets', component: () => import('../LWD-views/LogisticManager/RecoveryTickets.vue') },
      { path: 'communication', name: 'LogisticCommunication', component: () => import('../LWD-views/LogisticManager/Communication.vue') },
      { path: 'comparative-viewers', name: 'LogisticComparativeViewers', component: () => import('../LWD-views/LogisticManager/ComparativeViewers.vue') },
    ],
  },

  // ── Warehouse Manager Routes ────────────────────────────────────
  {
    path: '/warehouse',
    component: () => import('../layouts/WarehouseLayout.vue'),
    redirect: '/warehouse/dashboard',
    children: [
      { path: 'dashboard', name: 'WarehouseDashboard', component: () => import('../LWD-views/WarehouseManager/Dashboard.vue') },
      { path: 'new-orders', name: 'WarehouseNewOrders', component: () => import('../LWD-views/WarehouseManager/NewOrders.vue') },
      { path: 'inventory', name: 'WarehouseInventory', component: () => import('../LWD-views/WarehouseManager/Inventory.vue') },
      { path: 'inbound', name: 'WarehouseInbound', component: () => import('../LWD-views/WarehouseManager/Inbound.vue') },
      { path: 'floor-plan', name: 'WarehouseFloorPlan', component: () => import('../LWD-views/WarehouseManager/FloorPlan.vue') },
      { path: 'picking', name: 'WarehousePicking', component: () => import('../LWD-views/WarehouseManager/Picking.vue') },
      { path: 'packing-materials', name: 'WarehousePackingMaterials', component: () => import('../LWD-views/WarehouseManager/PackingMaterials.vue') },
      { path: 'safety-stock', name: 'WarehouseSafetyStock', component: () => import('../LWD-views/WarehouseManager/SafetyStock.vue') },
      { path: 'dock', name: 'WarehouseLoadingDock', component: () => import('../LWD-views/WarehouseManager/LoadingDock.vue') },
      { path: 'returns', name: 'WarehouseReturns', component: () => import('../LWD-views/WarehouseManager/ReturnsWarehouse.vue') },
      { path: 'labor', name: 'WarehouseLaborManagement', component: () => import('../LWD-views/WarehouseManager/LaborManagement.vue') },
      { path: 'performance', name: 'WarehousePerformance', component: () => import('../LWD-views/WarehouseManager/Performance.vue') },
      { path: 'ai', name: 'WarehouseSmartWMS', component: () => import('../LWD-views/WarehouseManager/SmartWMS.vue') },
      { path: 'comparative-viewers', name: 'WarehouseComparativeViewers', component: () => import('../LWD-views/WarehouseManager/ComparativeViewers.vue') },
      { path: 'messages', name: 'WarehouseCommunication', component: () => import('../LWD-views/WarehouseManager/Communication.vue') },
    ],
  },

  // ── Dispatcher Routes ───────────────────────────────────────────
  {
    path: '/dispatcher',
    component: () => import('../layouts/DispatcherLayout.vue'),
    redirect: '/dispatcher/dashboard',
    children: [
      { path: 'dashboard', name: 'DispatcherDashboard', component: () => import('../LWD-views/Dispatcher/Dashboard.vue') },
      { path: 'pending-queue', name: 'DispatcherPendingQueue', component: () => import('../LWD-views/Dispatcher/PendingDispatchQueue.vue') },
      { path: 'clustering', name: 'DispatcherOrderClustering', component: () => import('../LWD-views/Dispatcher/OrderClustering.vue') },
      { path: 'optimization', name: 'DispatcherRouteOptimization', component: () => import('../LWD-views/Dispatcher/RouteOptimization.vue') },
      { path: 'load-balancing', name: 'DispatcherLoadBalancing', component: () => import('../LWD-views/Dispatcher/LoadBalancing.vue') },
      { path: 'drivers', name: 'DispatcherDriverManagement', component: () => import('../LWD-views/Dispatcher/DriverManagement.vue') },
      { path: 'manifest', name: 'DispatcherManifestCenter', component: () => import('../LWD-views/Dispatcher/ManifestCenter.vue') },
      { path: 'service-moves', name: 'DispatcherServiceMoves', component: () => import('../LWD-views/Dispatcher/ServiceMoves.vue') },
      { path: 'order-status', name: 'DispatcherOrderStatus', component: () => import('../LWD-views/Dispatcher/OrderStatusControl.vue') },
      { path: 'crisis', name: 'DispatcherCrisisManagement', component: () => import('../LWD-views/Dispatcher/CrisisManagement.vue') },
      { path: 'communication', name: 'DispatcherCommunication', component: () => import('../LWD-views/Dispatcher/Communication.vue') },
      { path: 'performance', name: 'DispatcherPerformanceMetrics', component: () => import('../LWD-views/Dispatcher/PerformanceMetrics.vue') },
      { path: 'ai-assistant', name: 'DispatcherSmartDispatcher', component: () => import('../LWD-views/Dispatcher/SmartDispatcher.vue') },
    ],
  },

  // ── AI Support Routes ──────────────────────────────────────────
  {
    path: '/ai',
    component: () => import('../layouts/AILayout.vue'),
    redirect: '/ai/dashboard',
    children: [
      { path: 'dashboard', name: 'AIDashboard', component: () => import('../Ai-views/Dashboard.vue') },
      { path: 'contact-forms', name: 'AIContactForms', component: () => import('../Ai-views/ContactForms.vue') },
      { path: 'live-conversations', name: 'AILiveConversations', component: () => import('../Ai-views/LiveConversations.vue') },
      { path: 'escalations', name: 'AIEscalations', component: () => import('../Ai-views/EscalationCenter.vue') },
      { path: 'tickets', name: 'AITickets', component: () => import('../Ai-views/Tickets.vue') },
      { path: 'reverse-logistics', name: 'AIReverseLogistics', component: () => import('../Ai-views/ReverseLogistics.vue') },
      { path: 'refund-center', name: 'AIRefundCenter', component: () => import('../Ai-views/RefundCenter.vue') },
      { path: 'analytics', name: 'AIAnalytics', component: () => import('../Ai-views/AIAnalytics.vue') },
      { path: 'knowledge-base', name: 'AIKnowledgeBase', component: () => import('../Ai-views/KnowledgeBase.vue') },
      { path: 'legal', name: 'AILegalCompliance', component: () => import('../Ai-views/LegalCompliance.vue') },
      { path: 'settings', name: 'AISettings', component: () => import('../Ai-views/Settings.vue') },
    ],
  },

  // ── Meeting Room (shared) ───────────────────────────────────────
  {
    path: '/logistic/meeting-room',
    name: 'LogisticMeetingRoom',
    component: () => import('../views/MeetingRoom/MeetingRoom.vue'),
  },
  {
    path: '/dispatcher/meeting-room',
    name: 'DispatcherMeetingRoom',
    component: () => import('../views/MeetingRoom/MeetingRoom.vue'),
  },
  {
    path: '/warehouse/meeting-room',
    name: 'WarehouseMeetingRoom',
    component: () => import('../views/MeetingRoom/MeetingRoom.vue'),
  },

  // ── Misc ────────────────────────────────────────────────────────
  {
    path: '/offline',
    name: 'NoInternet',
    component: () => import('../views/NoInternet.vue'),
  },
  {
    path: '/slip-preview',
    name: 'SlipPreview',
    component: () => import('../pages/SlipPreview.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── Auth Guard ──────────────────────────────────────────────────

const ROLE_DASHBOARD_MAP = {
  INDIVIDUAL: '/individual/dashboard',
  VENDOR: '/vendor/dashboard',
  LOGISTIC_MANAGER: '/logistic/dashboard',
  WAREHOUSE_MANAGER: '/warehouse/dashboard',
  DISPATCHER: '/dispatcher/dashboard',
  DRIVER: '/driver/dashboard',
  AI_AGENT: '/ai/dashboard',
  AI_SUPPORT: '/ai/dashboard',
  CUSTOMER_SUPPORT: '/ai/dashboard',
  ai_agent: '/ai/dashboard',
  ai_support: '/ai/dashboard',
  customer_support: '/ai/dashboard',
  manager: '/logistic/dashboard',
  warehouse: '/warehouse/dashboard',
  dispatcher: '/dispatcher/dashboard',
  driver: '/driver/dashboard',
}

const PROTECTED_PREFIXES = {
  '/individual': ['INDIVIDUAL'],
  '/vendor':     ['VENDOR'],
  '/logistic':   ['LOGISTIC_MANAGER', 'manager'],
  '/warehouse':  ['WAREHOUSE_MANAGER', 'warehouse'],
  '/dispatcher': ['DISPATCHER', 'dispatcher'],
  '/driver':     ['DRIVER', 'driver'],
  '/ai':         ['AI_AGENT', 'ai_agent', 'AI_SUPPORT', 'ai_support', 'CUSTOMER_SUPPORT', 'customer_support'],
}

function isTokenExpired(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64))
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

router.beforeEach((to, _from, next) => {
  const rawToken = localStorage.getItem('auth_token')
  const token = rawToken && !isTokenExpired(rawToken) ? rawToken : null

  // Clear stale expired token
  if (rawToken && !token) {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_refresh_token')
    localStorage.removeItem('auth_user')
  }

  // Guest-only routes (login, register, forgot-password) — redirect if already logged in
  if (to.meta.guest && token) {
    try {
      const user = JSON.parse(localStorage.getItem('auth_user') || 'null')
      const dest = ROLE_DASHBOARD_MAP[user?.role]
      if (dest) return next({ path: dest, replace: true })
    } catch { /* ignore */ }
  }

  // Auth-required routes (setup-tfa) — redirect to login if not authenticated
  if (to.meta.requiresAuth && !token) {
    return next({ path: '/login', query: { redirect: to.fullPath }, replace: true })
  }

  // Protected role prefixes — check token and role
  const matchedPrefix = Object.keys(PROTECTED_PREFIXES).find(p => to.path.startsWith(p))
  if (matchedPrefix) {
    if (!token) {
      return next({ path: '/login', query: { redirect: to.fullPath }, replace: true })
    }

    const allowedRoles = PROTECTED_PREFIXES[matchedPrefix]
    if (allowedRoles.length > 0) {
      try {
        const user = JSON.parse(localStorage.getItem('auth_user') || 'null')
        if (user?.role && !allowedRoles.includes(user.role)) {
          const ownDashboard = ROLE_DASHBOARD_MAP[user.role] || '/login'
          return next({ path: ownDashboard, replace: true })
        }
      } catch { /* ignore */ }
    }
  }

  next()
})

export default router
