/**
 * Real-time driver location tracking composable
 * Uses polling to fetch live GPS positions for dispatchers and customers
 */

import { ref, onMounted, onUnmounted, computed, unref, watch } from 'vue'
import { authenticatedJsonRequest } from '../config/api.js'

export function useRealTimeTracking(orderId = null, options = {}) {
    const drivers = ref([])
    const loading = ref(false)
    const error = ref(null)
    let pollInterval = null

    const trackingMode = options.mode || 'auto'
    const trackingEnabled = options.enabled

    function isTrackingEnabled() {
        return trackingEnabled === undefined ? true : unref(trackingEnabled) !== false
    }

    function shouldFetchSingleOrder() {
        if (trackingMode === 'single') return true
        if (trackingMode === 'all') return false
        return Boolean(unref(orderId))
    }

    /**
     * Fetch all active driver locations (for dispatchers)
     */
    async function fetchAllDrivers() {
        try {
            loading.value = true
            error.value = null
            const response = await authenticatedJsonRequest('/api/v1/tracking/drivers', {
                method: 'GET'
            })
            drivers.value = response
        } catch (err) {
            error.value = err.message || 'Failed to fetch driver locations'
            console.error('Tracking error:', err)
        } finally {
            loading.value = false
        }
    }

    /**
     * Fetch single driver location for an order (for customers)
     */
    async function fetchOrderDriver() {
        const currentOrderId = unref(orderId)
        if (!currentOrderId) {
            drivers.value = []
            return
        }

        try {
            loading.value = true
            error.value = null
            const response = await authenticatedJsonRequest(`/tracking/orders/${currentOrderId}/driver`, {
                method: 'GET'
            })

            if (response) {
                drivers.value = [response]
            } else {
                drivers.value = []
            }
        } catch (err) {
            drivers.value = []
            error.value = err.message || 'Failed to fetch driver location'
            console.error('Tracking error:', err)
        } finally {
            loading.value = false
        }
    }

    /**
     * Start polling for location updates
     * @param {number} intervalMs - Poll interval in milliseconds (default: 10 seconds)
     */
    function startPolling(intervalMs = 10000) {
        const fetchCurrent = () => {
            if (!isTrackingEnabled()) {
                drivers.value = []
                error.value = null
                return
            }

            return shouldFetchSingleOrder() ? fetchOrderDriver() : fetchAllDrivers()
        }
        
        // Initial fetch
        fetchCurrent()

        // Poll every X seconds
        pollInterval = setInterval(fetchCurrent, intervalMs)

        console.log(`✅ Live tracking started (polling every ${intervalMs / 1000}s)`)
    }

    /**
     * Stop polling
     */
    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
            console.log('⏹️  Live tracking stopped')
        }
    }

    /**
     * Get drivers with valid GPS coordinates
     */
    const activeDrivers = computed(() =>
        drivers.value.filter(d => d.latitude && d.longitude)
    )

    /**
     * Get single driver (for order tracking)
     */
    const driver = computed(() => drivers.value[0] || null)

    // Auto-start/stop on mount/unmount
    onMounted(() => {
        startPolling()
    })

    onUnmounted(() => {
        stopPolling()
    })
    
    // Watch for orderId changes
    watch(() => unref(orderId), () => {
        if (pollInterval) {
            stopPolling()
            startPolling()
        }
    })

    watch(() => (trackingEnabled === undefined ? true : unref(trackingEnabled)), () => {
        if (pollInterval) {
            stopPolling()
            startPolling()
        }
    })

    return {
        drivers,
        activeDrivers,
        driver,
        loading,
        error,
        fetchAllDrivers,
        fetchOrderDriver,
        startPolling,
        stopPolling
    }
}
