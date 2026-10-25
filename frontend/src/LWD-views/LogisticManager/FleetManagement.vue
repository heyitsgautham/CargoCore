<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Fleet & Drivers Overview</h2>
            <div class="flex gap-3">
<button @click="generateMaintenanceReport"
                    class="bg-slate-800 hover:bg-slate-700 text-white font-medium dark:bg-white/10 dark:hover:bg-white/15 dark:text-white border border-slate-700 dark:border-white/10 py-2 px-4 rounded-lg transition-colors shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-sm">download</span> Maintenance Report
                </button>
<button @click="openVehicleModal('add')"
                    class="bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-lg border border-slate-700 dark:border-primary/30">
                    <span class="material-symbols-outlined">local_shipping</span> Add Vehicle
                </button>
            </div>
        </div>

        <!-- Live Fleet Map -->
        <div class="glass-panel w-full h-[300px] rounded-xl relative overflow-hidden border border-gray-200 dark:border-white/5">
            <!-- Live badge overlay -->
            <div class="absolute top-3 left-3 z-[401] pointer-events-none">
                <div class="bg-white/90 dark:bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full text-gray-900 dark:text-white text-xs font-bold flex items-center gap-2 border border-gray-200 dark:border-white/10 shadow-md">
                    <span class="w-2 h-2 rounded-full animate-pulse" :class="wsConnected ? 'bg-green-500' : 'bg-yellow-400'"></span>
                    Live Fleet Map &mdash; {{ liveDrivers.length }} driver{{ liveDrivers.length !== 1 ? 's' : '' }} tracked
                    <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" :class="wsConnected ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">{{ wsConnected ? 'WS' : 'POLL' }}</span>
                </div>
            </div>
            <l-map :zoom="11" :center="fleetMapCenter" :use-global-leaflet="false" style="height:300px;width:100%;border-radius:0.75rem;">
                <l-tile-layer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    layer-type="base"
                    name="CartoDB Voyager"
                />
                <l-marker v-for="d in liveDrivers" :key="d.driver_id" :lat-lng="[d.latitude, d.longitude]">
                    <l-popup>
                        <div class="text-xs p-1">
                            <div class="font-bold flex items-center gap-1 mb-1">
                                <span style="color:#22c55e;font-size:14px;" class="material-symbols-outlined">local_shipping</span>
                                {{ d.driver_name }}
                            </div>
                            <div class="text-gray-500 mb-0.5">Vehicle: <span class="font-medium text-gray-900">{{ d.vehicle_code || 'N/A' }}</span></div>
                            <div class="text-[9px] uppercase font-bold px-1.5 py-0.5 inline-block rounded mt-1"
                                :style="d.status === 'In-Transit' ? 'background:#dbeafe;color:#1d4ed8' : 'background:#dcfce7;color:#15803d'">
                                {{ d.status }}
                            </div>
                        </div>
                    </l-popup>
                </l-marker>
            </l-map>
        </div>

        <!-- Role Filter Tabs & Search -->
        <div class="flex flex-col sm:flex-row justify-between items-center border-b border-gray-200 dark:border-white/10 gap-4 pb-1">
            <!-- Tabs -->
            <div class="flex gap-4 overflow-x-auto w-full sm:w-auto no-scrollbar">
                <button v-for="tab in tabs" :key="tab" class="px-4 py-2 text-sm font-medium transition-colors relative whitespace-nowrap"
                    :class="activeTab === tab ? 'text-primary' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'"
                    @click="activeTab = tab">
                    {{ tab }}
                    <div v-if="activeTab === tab"
                        class="absolute bottom-[-5px] left-0 w-full h-1 bg-primary rounded-t-full"></div>
                </button>
            </div>

            <!-- Global Search -->
            <div class="relative w-full sm:w-64 mb-1 sm:mb-0">
                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">search</span>
                <input 
                    v-model="searchQuery" 
                    type="text" 
                    :placeholder="`Search ${activeTab}...`"
                    class="w-full bg-gray-100 dark:bg-white/5 border-none rounded-full py-1.5 pl-9 pr-4 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-primary/50 outline-none transition-shadow"
                />
            </div>
        </div>

        <FleetDriversTab />

        <FleetVehiclesTab />

        <FleetLogsTab />

        <VehicleDocumentsTab />

        <DriverDocumentsTab />

        <LiveLocationsTab />

        <!-- ======================= MODALS AND SLIDEOVERS ======================= -->

        <VehicleFormModal />


        <VehicleProfileModal />

        <DocumentViewerModal />
    </div>
</template>

<script setup>
import FleetDriversTab from './fleet/FleetDriversTab.vue'
import FleetVehiclesTab from './fleet/FleetVehiclesTab.vue'
import FleetLogsTab from './fleet/FleetLogsTab.vue'
import VehicleDocumentsTab from './fleet/VehicleDocumentsTab.vue'
import DriverDocumentsTab from './fleet/DriverDocumentsTab.vue'
import LiveLocationsTab from './fleet/LiveLocationsTab.vue'
import VehicleFormModal from './fleet/VehicleFormModal.vue'
import VehicleProfileModal from './fleet/VehicleProfileModal.vue'
import DocumentViewerModal from './fleet/DocumentViewerModal.vue'
import { fleetPageKey } from './fleet/fleetPageContext'
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { storeToRefs } from 'pinia'
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useFleetLiveTracking } from './fleet/useFleetLiveTracking'
import { useVehicleForm } from './fleet/useVehicleForm'
import { useFleetDocuments } from './fleet/useFleetDocuments'
import {
    computeLogStats,
    groupDriverDocs,
    groupVehicleDocs,
    maintenanceCostLabel,
    maintenanceReportCsv,
    searchDrivers,
    searchLogs,
    searchMaintenance,
    searchTopDrivers,
    searchVehicles,
    vehicleServiceHistory,
} from './fleet/fleetViews'

// Fix Leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
    iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
    shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

const store = useLogisticStore()
const { filteredTopDrivers, filteredMaintenance } = storeToRefs(store)

// Dispatcher store — shared reactive suspend state (same Pinia instance, no localStorage polling needed)
const dispatcherStore = useDispatcherStore()

const {
    liveDrivers,
    liveDriverLocation,
    connectFleetWs,
    disconnectFleetWs,
    fetchLiveDrivers,
    fleetMapCenter,
    wsConnected,
} = useFleetLiveTracking(store)

const {
    isVehicleModalOpen,
    vehicleModalMode,
    isSubmitting,
    vehicleFormData,
    openVehicleModal,
    handleVehicleDocUpload,
    closeVehicleModal,
    submitVehicle,
} = useVehicleForm(store)

const {
    activeDoc,
    expandedDocs,
    isShareModalOpen,
    shareStep,
    shareFormData,
    downloadDoc,
    printDoc,
    openShareModal,
    shareVia,
    submitShare,
    toggleDocExpand,
    openDocModal,
    closeDocModal,
} = useFleetDocuments(store)

// Selected driver for zoom-to focus on live map
const selectedFleetDriver = ref(null)

const tabs = ['Active Drivers', 'Fleet Vehicles', 'Fleet Logs', 'Vehicle Documents', 'Driver Documents', 'Live Locations']
const activeTab = ref('Active Drivers')
const activeDropdown = ref(null)
const searchQuery = ref('')

const logTypes = ['Fuel Logs', 'Service Logs', 'Maintenance Logs', 'Cleaning Logs']
const activeLogType = ref('Fuel Logs')

const isUploadModalOpen = ref(false)
const uploadMode = ref('VEHICLE') // 'VEHICLE' or 'DRIVER'
const uploadFormData = ref({ entityId: '', docType: '', expiryDate: '', fileBase64: null, fileName: '' })

const openUploadModal = (mode) => {
    uploadMode.value = mode
    uploadFormData.value = { entityId: '', docType: '', expiryDate: '', fileBase64: null, fileName: '' }
    isUploadModalOpen.value = true
}

const activeVehicleProfile = ref(null)

const isDriverSuspendedInFleet = (driver) => {
    const id = String(driver?.id || '')
    const status = String(driver?.status || '').toLowerCase()
    if (status === 'suspended') return true
    if (id && dispatcherStore.isDriverSuspended(id)) return true
    return store.drivers.some((item) =>
        String(item.id) === id && String(item.status || '').toLowerCase() === 'suspended'
    )
}

const searchedDrivers = computed(() => searchDrivers(store.filteredDrivers, searchQuery.value, isDriverSuspendedInFleet))
const searchedTopDrivers = computed(() => searchTopDrivers(filteredTopDrivers.value, searchQuery.value, isDriverSuspendedInFleet))
const searchedVehicles = computed(() => searchVehicles(store.filteredVehicles, searchQuery.value))
const searchedMaintenance = computed(() => searchMaintenance(filteredMaintenance.value, searchQuery.value))
const searchedLogs = computed(() => searchLogs(store.fleetLogs[activeLogType.value], searchQuery.value, store.activeWarehouse))
const logStats = computed(() => computeLogStats(activeLogType.value, searchedLogs.value))
const groupedVehicleDocs = computed(() => groupVehicleDocs(store.filteredVehicleDocuments, store.activeWarehouse, searchQuery.value))
const groupedDriverDocs = computed(() => groupDriverDocs(store.filteredDriverDocuments, store.activeWarehouse, searchQuery.value))

const generateMaintenanceReport = () => {
    const vehicles = store.filteredVehicles
    if (!vehicles.length) {
        window.alert('No vehicle data available to download.')
        return
    }
    const blob = new Blob([maintenanceReportCsv(vehicles, store.hubs)], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fleet_maintenance_report_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

const toggleVehicleDropdown = (id) => {
    activeDropdown.value = activeDropdown.value === id ? null : id
}

const closeDropdowns = () => {
    activeDropdown.value = null
}

onMounted(() => {
    document.addEventListener('click', closeDropdowns)
    store.refresh().catch(() => {})
    connectFleetWs()
    fetchLiveDrivers()
})

onUnmounted(() => {
    document.removeEventListener('click', closeDropdowns)
    disconnectFleetWs()
})

const maintenanceCost = (vehicleId) => maintenanceCostLabel(store.filteredVehicles, store.fleetLogs, vehicleId)

const openVehicleProfile = (vehicle, viewMode = 'full') => {
    const { history, total } = vehicleServiceHistory(store.fleetLogs, vehicle.id)
    activeVehicleProfile.value = { ...vehicle, viewMode, serviceHistory: history, totalMaintenanceCost: total }
}
const closeVehicleProfile = () => {
    activeVehicleProfile.value = null
}


provide(fleetPageKey, {
    activeDoc,
    activeDropdown,
    activeLogType,
    activeTab,
    activeVehicleProfile,
    closeDocModal,
    closeVehicleModal,
    closeVehicleProfile,
    downloadDoc,
    expandedDocs,
    groupedDriverDocs,
    groupedVehicleDocs,
    handleVehicleDocUpload,
    isShareModalOpen,
    isSubmitting,
    isVehicleModalOpen,
    liveDriverLocation,
    liveDrivers,
    logStats,
    logTypes,
    maintenanceCost,
    openDocModal,
    openShareModal,
    openUploadModal,
    openVehicleModal,
    openVehicleProfile,
    printDoc,
    searchedDrivers,
    searchedLogs,
    searchedMaintenance,
    searchedTopDrivers,
    searchedVehicles,
    selectedFleetDriver,
    shareFormData,
    shareStep,
    shareVia,
    store,
    submitShare,
    submitVehicle,
    toggleDocExpand,
    toggleVehicleDropdown,
    vehicleFormData,
    vehicleModalMode,
    wsConnected,
})
</script>
