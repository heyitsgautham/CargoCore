import { createRouter, createWebHashHistory } from 'vue-router'
import { useDriverStore } from '../stores/driverStore.js'
import { useJobStore } from '../stores/jobStore.js'
import { useUiStore } from '../stores/uiStore.js'
import { routes } from './routes.js'

const router = createRouter({
    history: createWebHashHistory(),
    routes,
    scrollBehavior() {
        return { top: 0 }
    }
})


// Navigation Guard
router.beforeEach((to, from, next) => {
    const driverStore = useDriverStore()
    const uiStore = useUiStore()
    const jobStore = useJobStore()

    if (to.name !== 'splash' && from.name !== undefined) {
        uiStore.setLoading(true)
    }

    // Camera screens bypass all auth and flow guards
    if (to.meta.cameraScreen) return next()

    if (to.meta.requiresAuth && !driverStore.isAuthenticated) {
        return next({ name: 'login' })
    }
    if (to.meta.public && driverStore.isAuthenticated && to.name === 'login') {
        return next({ name: driverStore.preShiftDone ? 'dashboard' : 'pre-shift' })
    }

    // ── Shift flow enforcement (dashboard-first) ────────────────
    // Pages that are always accessible once authenticated (no flow guard)
    const flowExempt = ['pre-shift', 'settings', 'notifications']
    if (to.meta.requiresAuth && !flowExempt.includes(to.name)) {
        // Must complete pre-shift before anything else
        if (!driverStore.preShiftDone) {
            return next({ name: 'pre-shift' })
        }
        // Must bind vehicle before inspection+
        if (!driverStore.vehicleBound && to.name !== 'vehicle-binding') {
            return next({ name: 'vehicle-binding' })
        }
        // Must inspect before entering post-check flow
        if (!driverStore.inspectionDone && !['vehicle-binding', 'vehicle-inspection'].includes(to.name)) {
            return next({ name: 'vehicle-inspection' })
        }

        // After mandatory checks, dashboard must stay reachable even with no active job.
        if (['dashboard', 'house-shift-dashboard'].includes(to.name)) {
            return next()
        }

        // If no active job is loaded yet, skip job-type-specific blockers.
        if (!jobStore.jobType) {
            return next()
        }

        // ── Job-type-specific flow guards ──────────────────────
        const isHouseShift = jobStore.jobType === 'HOUSE_SHIFT'
        const isPickup = jobStore.jobType === 'PARCEL_PICKUP'
        const dailyStartPages = ['vehicle-binding', 'vehicle-inspection', 'job-assignment']

        if (isHouseShift) {
            // House Shift: require crew → gate (NO load-verify for house shift)
            if (!driverStore.crewCheckedIn && !['crew', ...dailyStartPages].includes(to.name)) {
                return next({ name: 'crew' })
            }
            if (!driverStore.gateExited && !['crew', 'gate-exit', ...dailyStartPages].includes(to.name)) {
                return next({ name: 'gate-exit' })
            }
        } else if (isPickup) {
            // Pickup: skip load-verify at start, require gate directly
            if (!driverStore.gateExited && !['gate-exit', ...dailyStartPages].includes(to.name)) {
                return next({ name: 'gate-exit' })
            }
        } else {
            // Delivery: skip crew, require load → gate
            if (!driverStore.loadVerified && !['load-verify', ...dailyStartPages].includes(to.name)) {
                return next({ name: 'load-verify' })
            }
            if (!driverStore.gateExited && !['load-verify', 'gate-exit', ...dailyStartPages].includes(to.name)) {
                return next({ name: 'gate-exit' })
            }
        }
    }

    next()
})

router.afterEach(() => {
    const uiStore = useUiStore()
    setTimeout(() => {
        uiStore.setLoading(false)
    }, 600)
})

export default router
