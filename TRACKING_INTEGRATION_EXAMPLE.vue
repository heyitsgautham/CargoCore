<!-- Example: How to integrate live tracking in customer view -->
<template>
    <div class="tracking-container">
        <!-- Map container -->
        <div class="map-wrapper">
            <div v-if="!driver || !driver.latitude" class="map-placeholder">
                <span class="material-symbols-outlined">map</span>
                <p>{{ loading ? 'Loading driver location...' : 'Driver location unavailable' }}</p>
            </div>

            <div v-else class="live-map">
                <!-- Replace with actual map library (Leaflet, Google Maps, Mapbox, etc.) -->
                <div class="map-marker" :style="`top: ${driver.latitude}%; left: ${driver.longitude}%`">
                    <span class="material-symbols-outlined">local_shipping</span>
                    <div class="driver-tooltip">
                        {{ driver.driver_name }}<br>
                        {{ driver.vehicle_code }}
                    </div>
                </div>
            </div>
        </div>

        <!-- Driver Info Card -->
        <div v-if="driver" class="driver-info">
            <h3>Driver: {{ driver.driver_name }}</h3>
            <p>Vehicle: {{ driver.vehicle_code }}</p>
            <p>Status: {{ driver.status }}</p>
            <p class="last-update">Last updated: {{ formatTime(driver.last_updated) }}</p>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'

const props = defineProps({
    orderId: {
        type: String,
        required: true
    }
})

// Auto-polls every 10 seconds
const { driver, loading, error } = useRealTimeTracking(props.orderId)

function formatTime(isoString) {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-IN')
}
</script>

<style scoped>
.map-wrapper {
    height: 400px;
    background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
    border-radius: 16px;
    position: relative;
    overflow: hidden;
}

.map-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
}

.live-map {
    width: 100%;
    height: 100%;
    position: relative;
    background: #e8f5e9;
}

.map-marker {
    position: absolute;
    width: 40px;
    height: 40px;
    background: #1CE783;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-center;
    color: white;
    animation: pulse 2s infinite;
    cursor: pointer;
}

.driver-tooltip {
    position: absolute;
    bottom: 50px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    white-space: nowrap;
    font-size: 12px;
    display: none;
}

.map-marker:hover .driver-tooltip {
    display: block;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(28, 231, 131, 0.7); }
    50% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(28, 231, 131, 0); }
}

.driver-info {
    margin-top: 20px;
    padding: 16px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.last-update {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
}
</style>
