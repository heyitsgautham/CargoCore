// Route table for the driver app. The guards that enforce sign-in and the shift flow live in index.js.
/**
 * Route Architecture — Two layout shells, zero per-page layout boilerplate.
 *
 * App.vue
 *  └─ <RouterView>
 *       ├─ PublicLayout  (splash, login, login-help)
 *       │     └─ <RouterView>  ← full-screen, no BottomNav
 *       └─ MainLayout    (all authenticated routes)
 *             └─ <RouterView>  ← bounded by status-bar-spacer + BottomNav
 *
 * Child paths do NOT start with "/" so they inherit the parent "/" prefix correctly.
 * Adding a new authenticated screen = add one entry to MainLayout's children array.
 */
export const routes = [

    // ── PUBLIC LAYOUT (no bottom navigation) ─────────────────────────────
    {
        path: '/',
        component: () => import('../layouts/PublicLayout.vue'),
        children: [
            {
                path: '',
                name: 'splash',
                component: () => import('../views/SplashScreen.vue'),
                meta: { public: true }
            },
            {
                path: 'login',
                name: 'login',
                component: () => import('../views/LoginScreen.vue'),
                meta: { public: true }
            },
            {
                path: 'login-help',
                name: 'login-help',
                component: () => import('../views/LoginHelp.vue'),
                meta: { public: true }
            },
        ]
    },

    // ── MAIN LAYOUT (authenticated — BottomNav + safe area automatic) ─────
    {
        path: '/',
        component: () => import('../layouts/MainLayout.vue'),
        children: [

            // ── Daily Start Flow ─────────────────────────
            {
                path: 'pre-shift',
                name: 'pre-shift',
                component: () => import('../views/PreShiftSafety.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'vehicle-binding',
                name: 'vehicle-binding',
                component: () => import('../views/VehicleBinding.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'vehicle-inspection',
                name: 'vehicle-inspection',
                component: () => import('../views/VehicleInspection.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'job-type-selection',
                name: 'job-type-selection',
                component: () => import('../views/JobTypeSelection.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Job Assignment & Completion ─────────────
            {
                path: 'job-assignment',
                name: 'job-assignment',
                component: () => import('../views/JobAssignment.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'job-completion',
                name: 'job-completion',
                component: () => import('../views/JobCompletion.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Main Dashboard ───────────────────────────
            {
                path: 'dashboard',
                name: 'dashboard',
                component: () => import('../views/CommandCenter.vue'),
                meta: { requiresAuth: true }
            },
            {
                path: 'house-shift-dashboard',
                name: 'house-shift-dashboard',
                component: () => import('../views/HouseShiftDashboard.vue'),
                meta: { requiresAuth: true }
            },

            // ── Manifest & Route ─────────────────────────
            {
                path: 'manifest',
                name: 'manifest',
                component: () => import('../views/ManifestView.vue'),
                meta: { requiresAuth: true }
            },
            {
                path: 'stop/:id',
                name: 'stop-detail',
                component: () => import('../views/StopDetail.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'route-progress',
                name: 'route-progress',
                component: () => import('../views/RouteProgress.vue'),
                meta: { requiresAuth: true }
            },
            {
                path: 'navigation',
                name: 'navigation',
                component: () => import('../views/LiveNavigation.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Load & Crew ──────────────────────────────
            {
                path: 'load-verify',
                name: 'load-verify',
                component: () => import('../views/LoadVerification.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'crew',
                name: 'crew',
                component: () => import('../views/CrewManagement.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'gate-exit',
                name: 'gate-exit',
                component: () => import('../views/GateExit.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── House Shift Execution ────────────────────
            {
                path: 'packing-progress',
                name: 'packing-progress',
                component: () => import('../views/PackingProgress.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'loading-inventory',
                name: 'loading-inventory',
                component: () => import('../views/LoadingInventory.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'transit-mode',
                name: 'transit-mode',
                component: () => import('../views/TransitMode.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'unloading-inventory',
                name: 'unloading-inventory',
                component: () => import('../views/UnloadingInventory.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'final-walkthrough',
                name: 'final-walkthrough',
                component: () => import('../views/FinalWalkthrough.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'customer-signoff',
                name: 'customer-signoff',
                component: () => import('../views/CustomerSignOff.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'packing-return',
                name: 'packing-return',
                component: () => import('../views/PackingReturn.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Geofence & Deviation ─────────────────────
            {
                path: 'geofence-arrival/:id',
                name: 'geofence-arrival',
                component: () => import('../views/GeofenceArrival.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'route-deviation',
                name: 'route-deviation',
                component: () => import('../views/RouteDeviation.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Delivery Execution ───────────────────────
            {
                path: 'delivery/:id',
                name: 'delivery',
                component: () => import('../views/DeliveryExecution.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'exception/:id',
                name: 'exception',
                component: () => import('../views/DeliveryException.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'service-checklist/:id',
                name: 'service-checklist',
                component: () => import('../views/ServiceChecklist.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'pod/:id',
                name: 'pod',
                component: () => import('../views/ProofOfDelivery.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'cod/:id',
                name: 'cod',
                component: () => import('../views/CODPayment.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Parcel Pickup Flow ──────────────────────
            {
                path: 'pickup-arrival/:id',
                name: 'pickup-arrival',
                component: () => import('../views/PickupArrival.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'pickup-scanning/:id',
                name: 'pickup-scanning',
                component: () => import('../views/ItemScanning.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'pickup-signature/:id',
                name: 'pickup-signature',
                component: () => import('../views/PickupSignature.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'warehouse-return',
                name: 'warehouse-return',
                component: () => import('../views/WarehouseReturn.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'unload-verification',
                name: 'unload-verification',
                component: () => import('../views/UnloadVerification.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'pickup-completion',
                name: 'pickup-completion',
                component: () => import('../views/PickupCompletion.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Financial ────────────────────────────────
            {
                path: 'wallet',
                name: 'wallet',
                component: () => import('../views/DriverWallet.vue'),
                meta: { requiresAuth: true }
            },
            {
                path: 'fuel-receipt',
                name: 'fuel-receipt',
                component: () => import('../views/FuelReceipt.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Communication & AI ───────────────────────
            {
                path: 'chat',
                name: 'chat',
                component: () => import('../views/DispatchChat.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'manager-chat',
                name: 'manager-chat',
                component: () => import('../views/ManagerChat.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'voice',
                name: 'voice',
                component: () => import('../views/VoiceAssistant.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Crisis & Returns ─────────────────────────
            {
                path: 'crisis',
                name: 'crisis',
                component: () => import('../views/CrisisMode.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'returns',
                name: 'returns',
                component: () => import('../views/ReverseLogistics.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'damage-report',
                name: 'damage-report',
                component: () => import('../views/DamageReport.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── End of Day ───────────────────────────────
            {
                path: 'shift-summary',
                name: 'shift-summary',
                component: () => import('../views/ShiftSummary.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'vehicle-return',
                name: 'vehicle-return',
                component: () => import('../views/VehicleReturn.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Reports & Safety ─────────────────────────
            {
                path: 'audit',
                name: 'audit',
                component: () => import('../views/AuditLog.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },

            // ── Settings & Profile ───────────────────────
            {
                path: 'settings',
                name: 'settings',
                component: () => import('../views/Settings.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'offline',
                name: 'offline',
                component: () => import('../views/OfflineQueue.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
            {
                path: 'notifications',
                name: 'notifications',
                component: () => import('../views/NotificationCenter.vue'),
                meta: { requiresAuth: true, hideNav: true }
            },
        ]
    },

    // ── Camera Screens (full-screen native, no nav, no auth flow guard) ──
    {
        path: '/camera',
        component: () => import('../layouts/CameraLayout.vue'),
        meta: { cameraScreen: true },
        children: [
            {
                path: 'qr',
                name: 'camera-qr',
                component: () => import('../components/scanners/PremiumQrScanner.vue'),
                meta: { cameraScreen: true }
            },
            {
                path: 'photo',
                name: 'camera-photo',
                component: () => import('../components/scanners/PremiumCameraView.vue'),
                meta: { cameraScreen: true }
            },
            {
                path: 'ocr',
                name: 'camera-ocr',
                component: () => import('../components/scanners/PremiumOcrScanner.vue'),
                meta: { cameraScreen: true }
            },
        ]
    },

    // ── Fallback ─────────────────────────────────────────────────────────
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
]
