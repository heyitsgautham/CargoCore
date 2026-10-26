import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUiStore } from './uiStore.js'
import { useDriverStore } from './driverStore.js'
import * as api from '../services/api'
import { JOB_TYPE_BADGE_COLORS, JOB_TYPE_LABELS, STATE_LABELS, fsmConfig, mapStateToOrderStatus } from './job/fsm.js'
import { mapOrderToJob } from './job/orderMapping.js'

/**
 * Job Store - Finite State Machine Implementation
 * Manages job state for all 3 job types (Parcel Delivery, Parcel Pickup, House Shift)
 *
 */
export const useJobStore = defineStore('job', () => {
    // ── Core State ──────────────────────────────────────
    const jobType = ref(null) // 'PARCEL_DELIVERY' | 'PARCEL_PICKUP' | 'HOUSE_SHIFT'
    const jobState = ref('IDLE')
    const jobData = ref(null)
    const currentStopIndex = ref(0)
    const stateHistory = ref([])
    const currentLocation = ref(null)

    // ── Computed Properties ─────────────────────────────
    const allowedTransitions = computed(() => {
        if (!jobType.value || !jobState.value) return []
        return fsmConfig[jobType.value]?.[jobState.value] || []
    })

    const currentStop = computed(() => {
        if (!jobData.value?.stops?.length) return null
        return jobData.value.stops[currentStopIndex.value]
    })

    const currentStopId = computed(() => currentStop.value?.id || null)

    const isLastStop = computed(() => {
        if (!jobData.value?.stops) return false
        return currentStopIndex.value >= jobData.value.stops.length - 1
    })

    const totalStops = computed(() => jobData.value?.stops?.length || 0)

    const completedStopsCount = computed(() => {
        if (!jobData.value?.stops) return 0
        return jobData.value.stops.filter(s => s.status === 'completed').length
    })

    const progressPercent = computed(() => {
        if (!totalStops.value) return 0
        return Math.round((completedStopsCount.value / totalStops.value) * 100)
    })

    function getStopIndex(stopId) {
        if (!jobData.value?.stops?.length) return -1
        return jobData.value.stops.findIndex(stop => String(stop.id) === String(stopId))
    }

    function getStopById(stopId) {
        const index = getStopIndex(stopId)
        return index >= 0 ? jobData.value.stops[index] : null
    }

    function setCurrentStopById(stopId) {
        const index = getStopIndex(stopId)
        if (index >= 0) {
            currentStopIndex.value = index
        }
        return index
    }

    function getOrderIdForStop(stopId = null) {
        const stop = stopId ? getStopById(stopId) : currentStop.value
        return stop?.orderId || stop?.id || null
    }

    const jobTypeLabel = computed(() => JOB_TYPE_LABELS[jobType.value] || 'No Job')

    const jobTypeBadgeColor = computed(() => JOB_TYPE_BADGE_COLORS[jobType.value] || 'bg-gray-400')

    const stateLabel = computed(() => STATE_LABELS[jobState.value] || jobState.value)

    // ── State Transition Logic ──────────────────────────

    function transition(newState, metadata = {}) {
        const uiStore = useUiStore()

        // Validate transition
        if (!allowedTransitions.value.includes(newState)) {
            console.error(`❌ Job Transition Failed: ${jobState.value} → ${newState}`)
            console.log('Allowed transitions:', allowedTransitions.value)

            uiStore.showToast(
                `Cannot skip steps. Complete current task first.`,
                'error',
                2000
            )
            throw new Error(`Invalid transition: ${jobState.value} → ${newState}`)
        }

        const oldState = jobState.value

        // Log transition for audit trail
        stateHistory.value.push({
            from: oldState,
            to: newState,
            timestamp: new Date().toISOString(),
            metadata
        })

        // Update state
        jobState.value = newState

        // Sync with backend
        syncOrderStatusToBackend(newState).catch(err => {
            console.error('Failed to sync order status to backend:', err)
        })

        // Handle state-specific logic
        handleStateEntry(newState, metadata)

        console.log(`✅ Job state transition: ${oldState} → ${newState}`)
    }

    async function syncOrderStatusToBackend(state) {
        const orderId = getOrderIdForStop(currentStopId.value)
        if (!orderId) {
            console.warn('No orderId found for syncing order status')
            return
        }

        // PARCEL_PICKUP completion uses the dedicated return endpoint which
        // transitions the order to DELIVERED, sets warehouse_substatus=RETURN_ARRIVED,
        // and auto-creates a pending ReturnGrading for the Warehouse Manager queue.
        if (state === 'COMPLETED' && jobType.value === 'PARCEL_PICKUP') {
            try {
                await api.completeReturn(orderId)
                console.log(`✅ Return order ${orderId} completed — sent to warehouse inspection queue`)
            } catch (err) {
                console.error(`❌ Failed to complete return order ${orderId}:`, err)
            }
            return
        }

        const backendStatus = mapStateToOrderStatus(state)
        if (!backendStatus) {
            console.log(`State ${state} does not require backend sync`)
            return
        }

        try {
            await api.updateOrderStatus(orderId, backendStatus)
            console.log(`✅ Order ${orderId} status synced to backend: ${backendStatus}`)
        } catch (err) {
            console.error(`❌ Failed to sync order ${orderId} status to backend:`, err)
        }
    }

    function handleStateEntry(state, metadata) {
        const uiStore = useUiStore()

        // Trigger side effects when entering certain states
        switch (state) {
            case 'ASSIGNED':
                uiStore.showToast(`${jobTypeLabel.value} job assigned`, 'success', 2000)
                break
            case 'IN_TRANSIT':
            case 'IN_TRANSIT_TO_PICKUP':
            case 'IN_TRANSIT_TO_SOURCE':
                // Start live GPS tracking when the route is active.
                startSimulatedTracking()
                break
            case 'ARRIVED':
            case 'ARRIVE_PICKUP':
            case 'ARRIVE_SOURCE':
            case 'ARRIVE_DEST':
                // Stop GPS tracking, log arrival
                stopSimulatedTracking()
                if (currentStop.value) {
                    currentStop.value.arrivedAt = new Date().toISOString()
                }
                break
            case 'NEXT_STOP':
                // Move to the next pending stop instead of skipping directly to completion.
                currentStopIndex.value++
                if (currentStopIndex.value < (jobData.value?.stops?.length || 0)) {
                    transition('IN_TRANSIT')
                } else {
                    transition('COMPLETED')
                }
                break
            case 'COMPLETED':
                // Stop all tracking, cleanup
                stopSimulatedTracking()
                uiStore.showToast('Job completed successfully! 🎉', 'success', 3000)
                break
        }
    }

    function canTransitionTo(targetState) {
        return allowedTransitions.value.includes(targetState)
    }

    function transitionAlongPath(path, metadata = {}) {
        if (!Array.isArray(path) || path.length === 0) return false

        const currentIndex = path.indexOf(jobState.value)
        if (currentIndex === -1) return false
        if (currentIndex === path.length - 1) return true

        for (let i = currentIndex + 1; i < path.length; i += 1) {
            const nextState = path[i]
            if (!canTransitionTo(nextState)) {
                return false
            }
            transition(nextState, metadata)
        }
        return true
    }

    function ensureTransitState(metadata = {}) {
        const transitPathMap = {
            PARCEL_DELIVERY: ['ASSIGNED', 'LOAD_VERIFICATION', 'START_ROUTE', 'IN_TRANSIT'],
            PARCEL_PICKUP: ['ASSIGNED', 'START_ROUTE', 'IN_TRANSIT_TO_PICKUP'],
            HOUSE_SHIFT: ['ASSIGNED', 'CREW_CHECKIN', 'START_ROUTE', 'IN_TRANSIT_TO_SOURCE'],
        }

        // House-shift destination leg uses a different transit state.
        if (jobType.value === 'HOUSE_SHIFT' && ['LOADING_INVENTORY', 'TRANSIT_TO_DEST'].includes(jobState.value)) {
            const destinationPath = ['LOADING_INVENTORY', 'TRANSIT_TO_DEST']
            return transitionAlongPath(destinationPath, metadata)
        }

        const path = transitPathMap[jobType.value]
        if (!path) return false
        return transitionAlongPath(path, metadata)
    }

    function ensureArrivalState(stopId = null, metadata = {}) {
        const resolvedStopId = stopId || currentStopId.value || currentStop.value?.id || null
        if (resolvedStopId) {
            setCurrentStopById(resolvedStopId)
        }

        const arrivalStateMap = {
            PARCEL_DELIVERY: 'ARRIVED',
            PARCEL_PICKUP: 'ARRIVE_PICKUP',
            HOUSE_SHIFT: jobState.value === 'TRANSIT_TO_DEST' ? 'ARRIVE_DEST' : 'ARRIVE_SOURCE',
        }

        const arrivalState = arrivalStateMap[jobType.value]
        if (!arrivalState) return false

        if (jobState.value === arrivalState) {
            return true
        }

        ensureTransitState({
            stopId: resolvedStopId,
            ...metadata,
        })

        if (!canTransitionTo(arrivalState)) {
            return false
        }

        transition(arrivalState, {
            stopId: resolvedStopId,
            ...metadata,
        })

        return true
    }

    function resolveCurrentStopIndex(job) {
        if (Number.isInteger(job?.currentStopIndex)) {
            return job.currentStopIndex
        }

        const stops = Array.isArray(job?.stops) ? job.stops : []
        const nextPendingIndex = stops.findIndex(stop => stop.status !== 'completed')
        return nextPendingIndex >= 0 ? nextPendingIndex : 0
    }

    // ── Job Management ──────────────────────────────────

    function loadJob(job) {
        if (!job) {
            reset()
            return
        }

        const clonedStops = Array.isArray(job.stops)
            ? job.stops.map(stop => ({
                ...stop,
                orderId: stop.orderId || stop.id,
                location: stop.location || (
                    stop.lat != null || stop.lng != null
                        ? { lat: stop.lat ?? null, lng: stop.lng ?? null }
                        : null
                ),
                itemsScanned: Array.isArray(stop.itemsScanned) ? [...stop.itemsScanned] : [],
                packages: Array.isArray(stop.packages) ? [...stop.packages] : [],
            }))
            : []

        jobType.value = job.jobType
        jobState.value = job.currentState || 'ASSIGNED'
        jobData.value = {
            ...job,
            stops: clonedStops,
        }
        currentStopIndex.value = resolveCurrentStopIndex(jobData.value)
        stateHistory.value = []
    }

    function completeCurrentStop() {
        if (currentStop.value) {
            currentStop.value.status = 'completed'
            currentStop.value.completedAt = new Date().toISOString()
        }
    }

    function markStopException(stopId, reason) {
        const stop = jobData.value.stops.find(s => s.id === stopId)
        if (stop) {
            stop.status = 'exception'
            stop.exceptionReason = reason
            stop.exceptionAt = new Date().toISOString()
        }
    }

    function addCODPayment(amount, method) {
        if (!currentStop.value) return
        currentStop.value.codCollected = true
        currentStop.value.codAmount = amount
        currentStop.value.codMethod = method
        currentStop.value.codCollectedAt = new Date().toISOString()
    }

    function addPOD(podData) {
        if (!currentStop.value) return
        currentStop.value.pod = {
            photo: podData.photo,
            signature: podData.signature,
            customerName: podData.customerName,
            notes: podData.notes,
            capturedAt: new Date().toISOString(),
            location: currentLocation.value
                ? {
                    lat: currentLocation.value.lat,
                    lng: currentLocation.value.lng,
                }
                : null
        }
    }

    function reset() {
        jobType.value = null
        jobState.value = 'IDLE'
        jobData.value = null
        currentStopIndex.value = 0
        stateHistory.value = []
        currentLocation.value = null
        stopSimulatedTracking()
    }

    // ── Live GPS Tracking ───────────────────────────────
    let geoWatchId = null
    let lastLocationPushAt = 0
    const LOCATION_PUSH_INTERVAL_MS = 5000 // push at most every 5 seconds

    function startSimulatedTracking() {
        if (geoWatchId !== null || typeof navigator === 'undefined' || !navigator.geolocation) {
            return
        }

        geoWatchId = navigator.geolocation.watchPosition(
            position => {
                currentLocation.value = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    speed: position.coords.speed || 0,
                    heading: position.coords.heading || 0,
                    timestamp: new Date(position.timestamp).toISOString(),
                }

                // Throttle: only push to backend if ≥5s since last push
                const now = Date.now()
                if (now - lastLocationPushAt >= LOCATION_PUSH_INTERVAL_MS) {
                    lastLocationPushAt = now
                    api.updateDriverLocation(currentLocation.value.lat, currentLocation.value.lng)
                        .catch(err => console.warn('Failed to push GPS update', err))
                }
            },
            error => {
                console.warn('Live GPS tracking unavailable', error)
            },
            {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 30000,
            }
        )
    }

    function stopSimulatedTracking() {
        if (geoWatchId !== null && typeof navigator !== 'undefined' && navigator.geolocation) {
            navigator.geolocation.clearWatch(geoWatchId)
            geoWatchId = null
        }
    }

    // ── API Integration ─────────────────────────────────────────────────────
    async function fetchAssignedOrders() {
        const driverStore = useDriverStore()
        try {
            const dashboard = driverStore.dashboard || await driverStore.refreshDashboard()
            const orders = await api.getAssignedOrders()
            return orders.map(order => mapOrderToJob(order, dashboard))
        } catch (err) {
            console.error('Failed to fetch assigned orders:', err)
            const uiStore = useUiStore()
            uiStore.showToast('Could not load assigned orders', 'error', 3000)
            return []
        }
    }

    return {
        // State
        jobType,
        jobState,
        jobData,
        currentStopIndex,
        stateHistory,
        currentLocation,

        // Computed
        allowedTransitions,
        currentStop,
        currentStopId,
        isLastStop,
        totalStops,
        completedStopsCount,
        progressPercent,
        jobTypeLabel,
        jobTypeBadgeColor,
        stateLabel,

        // Methods
        transition,
        canTransitionTo,
        ensureTransitState,
        ensureArrivalState,
        getStopById,
        getStopIndex,
        setCurrentStopById,
        getOrderIdForStop,
        loadJob,
        completeCurrentStop,
        markStopException,
        addCODPayment,
        addPOD,
        reset,
        startSimulatedTracking,
        stopSimulatedTracking,
        fetchAssignedOrders
    }
}, { persist: true })
