<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="isOpen" class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
                @click.self="closeModal">
                <!-- Backdrop -->
                <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

                <!-- Modal -->
                <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[92vh] overflow-y-auto flex flex-col pb-2"
                    @click.stop>
                    <!-- Header -->
                    <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                            {{ title }}
                        </h3>
                        <button @click="closeModal"
                            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <!-- Search Bar -->
                    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                        <div class="relative">
                            <input v-model="searchQuery" @input="handleSearch" @keydown.enter.prevent="applyTypedAddress" type="text"
                                placeholder="Search for a location..."
                                class="w-full px-4 py-3 pl-12 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
                            <span
                                class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">search</span>

                            <!-- Loading indicator -->
                            <div v-if="isSearching" class="absolute right-4 top-1/2 -translate-y-1/2">
                                <div class="animate-spin h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full"></div>
                            </div>

                            <!-- Search Results Dropdown -->
                            <div v-if="searchResults.length > 0"
                                class="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl max-h-64 overflow-y-auto z-[1200]">
                                <button v-for="(result, index) in searchResults" :key="index"
                                    @click="selectSearchResult(result)"
                                    class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0 transition-colors">
                                    <div class="flex items-start gap-3">
                                        <span class="material-symbols-outlined text-green-600 mt-0.5">location_on</span>
                                        <div class="flex-1 min-w-0">
                                            <p class="text-sm font-medium text-gray-900 dark:text-white">
                                                {{ result.display_name }}
                                            </p>
                                        </div>
                                    </div>
                                </button>
                            </div>

                            <!-- No results message -->
                            <div v-if="searchQuery.length >= 3 && !isSearching && searchResults.length === 0"
                                class="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 z-[1200]">
                                <p class="text-sm text-gray-500 dark:text-gray-400 text-center">No results found</p>
                            </div>
                        </div>
                        <div class="mt-3 flex flex-wrap items-center gap-2">
                            <button @click="useCurrentLocation" :disabled="isLocating" type="button"
                                class="px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium transition-colors">
                                {{ isLocating ? 'Locating...' : 'Use Current Location' }}
                            </button>
                            <button v-if="searchQuery.trim()" @click="applyTypedAddress" type="button"
                                class="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                                Use Typed Address
                            </button>
                        </div>
                    </div>

                    <!-- Map Container -->
                    <div class="relative h-[50vh] min-h-[320px] max-h-[520px]">
                        <div ref="mapContainer" class="absolute inset-0"></div>
                    </div>

                    <!-- Selected Address Display -->
                    <div v-if="selectedAddress || isFetchingAddress"
                        class="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
                        <div class="flex items-start gap-3">
                            <span class="material-symbols-outlined text-green-600">location_on</span>
                            <div class="flex-1 min-w-0">
                                <p class="text-sm font-medium text-gray-900 dark:text-white">Selected Location</p>
                                <div v-if="isFetchingAddress" class="flex items-center gap-2 mt-1">
                                    <div class="animate-spin h-4 w-4 border-2 border-green-500 border-t-transparent rounded-full"></div>
                                    <p class="text-sm text-gray-600 dark:text-gray-400">Fetching address...</p>
                                </div>
                                <template v-else>
                                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ selectedAddress }}</p>
                                    <p v-if="selectedCoords" class="text-xs text-gray-500 mt-1">
                                        Coordinates: {{ selectedCoords.lat.toFixed(6) }}, {{ selectedCoords.lon.toFixed(6) }}
                                    </p>
                                </template>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div class="sticky bottom-0 z-[1300] bg-white dark:bg-gray-800 flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
                        <button @click="closeModal"
                            class="px-6 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium transition-colors">
                            Cancel
                        </button>
                        <button @click="confirmSelection" :disabled="!selectedAddress"
                            class="px-6 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold transition-colors">
                            Confirm Location
                        </button>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
    isOpen: Boolean,
    title: {
        type: String,
        default: 'Select Location on Map'
    },
    initialLat: {
        type: Number,
        default: 12.9716 // Bangalore default
    },
    initialLon: {
        type: Number,
        default: 77.5946
    }
})

const emit = defineEmits(['close', 'select'])

const mapContainer = ref(null)
const searchQuery = ref('')
const isSearching = ref(false)
const isLocating = ref(false)
const isFetchingAddress = ref(false)
const searchResults = ref([])
const selectedAddress = ref('')
const selectedCoords = ref(null)
let map = null
let marker = null
let searchTimeout = null

// Initialize map when modal opens
watch(() => props.isOpen, async (isOpen) => {
    if (isOpen) {
        // Reset address state so pickup and destination don't share the same value
        selectedAddress.value = ''
        selectedCoords.value = null
        searchQuery.value = ''
        searchResults.value = []
        await nextTick()
        initMap()
        setTimeout(() => {
            map?.invalidateSize()
        }, 0)
    } else {
        if (map) {
            map.remove()
            map = null
            marker = null
        }
    }
}, { immediate: true })

function initMap() {
    if (!mapContainer.value || map) return

    // Create map
    map = L.map(mapContainer.value).setView([props.initialLat, props.initialLon], 13)

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map)

    // Add marker
    const customIcon = L.divIcon({
        className: 'custom-marker',
        html: '<div style="background: #16a34a; width: 32px; height: 32px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
        iconSize: [32, 32],
        iconAnchor: [16, 32]
    })

    marker = L.marker([props.initialLat, props.initialLon], {
        icon: customIcon,
        draggable: true
    }).addTo(map)

    // Handle marker drag
    marker.on('dragend', async () => {
        const pos = marker.getLatLng()
        await reverseGeocode(pos.lat, pos.lng)
    })

    // Handle map click
    map.on('click', async (e) => {
        marker.setLatLng(e.latlng)
        await reverseGeocode(e.latlng.lat, e.latlng.lng)
    })
}

async function handleSearch() {
    clearTimeout(searchTimeout)
    
    if (searchQuery.value.trim().length < 3) {
        searchResults.value = []
        isSearching.value = false
        return
    }

    isSearching.value = true
    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(
                `http://localhost:8000/api/v1/geocoding/search?q=${encodeURIComponent(searchQuery.value)}&limit=5`
            )
            const data = await response.json()
            searchResults.value = Array.isArray(data) ? data : []
            isSearching.value = false
        } catch (error) {
            console.error('Search error:', error)
            searchResults.value = []
            isSearching.value = false
        }
    }, 300)
}

function selectSearchResult(result) {
    selectedAddress.value = result.display_name
    selectedCoords.value = { lat: result.lat, lon: result.lon }
    searchResults.value = []
    searchQuery.value = result.display_name

    // Move map and marker to selected location
    if (map && marker) {
        map.setView([result.lat, result.lon], 15)
        marker.setLatLng([result.lat, result.lon])
    }
}

function applyTypedAddress() {
    const typed = searchQuery.value.trim()
    if (!typed) return

    if (searchResults.value.length > 0) {
        selectSearchResult(searchResults.value[0])
        return
    }

    selectedAddress.value = typed
    if (marker) {
        const pos = marker.getLatLng()
        selectedCoords.value = { lat: pos.lat, lon: pos.lng }
    } else if (map) {
        const center = map.getCenter()
        selectedCoords.value = { lat: center.lat, lon: center.lng }
    } else {
        selectedCoords.value = { lat: props.initialLat, lon: props.initialLon }
    }
}

function useCurrentLocation() {
    if (!navigator.geolocation) {
        return
    }

    isLocating.value = true
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const lat = position.coords.latitude
            const lon = position.coords.longitude

            if (map && marker) {
                map.setView([lat, lon], 16)
                marker.setLatLng([lat, lon])
            }

            await reverseGeocode(lat, lon)
            isLocating.value = false
        },
        () => {
            isLocating.value = false
        },
        { enableHighAccuracy: true, timeout: 10000 }
    )
}

async function reverseGeocode(lat, lon) {
    isFetchingAddress.value = true
    try {
        const response = await fetch(
            `http://localhost:8000/api/v1/geocoding/reverse?lat=${lat}&lon=${lon}`
        )

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log('Reverse geocode response:', data)

        // Check if we got a proper address or just coordinates
        if (data.display_name && !data.display_name.match(/^-?\d+\.\d+,\s*-?\d+\.\d+$/)) {
            selectedAddress.value = data.display_name
        } else {
            // Fallback: show coordinates with a message
            selectedAddress.value = `Location: ${lat.toFixed(6)}, ${lon.toFixed(6)} (Address not available)`
        }
        selectedCoords.value = { lat, lon }
    } catch (error) {
        console.error('Reverse geocode error:', error)
        selectedAddress.value = `Location: ${lat.toFixed(6)}, ${lon.toFixed(6)} (Unable to fetch address)`
        selectedCoords.value = { lat, lon }
    } finally {
        isFetchingAddress.value = false
    }
}

function closeModal() {
    emit('close')
}

function confirmSelection() {
    if (selectedAddress.value && selectedCoords.value) {
        emit('select', {
            address: selectedAddress.value,
            lat: selectedCoords.value.lat,
            lon: selectedCoords.value.lon
        })
        closeModal()
    }
}

onUnmounted(() => {
    if (map) {
        map.remove()
    }
    clearTimeout(searchTimeout)
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

.modal-enter-active>div,
.modal-leave-active>div {
    transition: transform 0.3s ease;
}

.modal-enter-from>div,
.modal-leave-to>div {
    transform: scale(0.9);
}
</style>
