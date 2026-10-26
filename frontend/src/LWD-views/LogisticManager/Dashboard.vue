<template>
    <div class="space-y-6">
        <KpiCards />

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">

            <LiveFleetMapPanel />

            <AlertsPanel />
        </div>

        <!-- Bottom Section: KPI Charts & Hub Performance -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DeliveryPipeline />

            <HubPerformancePanel />
        </div>

        <!-- Full Width SLA Compliance Chart -->
        <SlaChartPanel />

        <!-- Modals -->
        <AlertDetailsModal :is-open="store.activeModal === 'alert-details'" :alert="store.selectedItem"
            @close="store.closeModal()" @action="handleAlertAction" />

        <DriverProfileModal :key="store.selectedItem?.id || 'driver-profile'"
            :is-open="store.activeModal === 'driver-profile'" :driver="store.selectedItem"
            @close="store.closeModal()" />

        <ContactHubModal :is-open="store.activeModal === 'contact-hub'" :hub="currentHub" @close="store.closeModal()" />

    </div>
</template>

<script setup>
import KpiCards from './dashboard/KpiCards.vue'
import LiveFleetMapPanel from './dashboard/LiveFleetMapPanel.vue'
import AlertsPanel from './dashboard/AlertsPanel.vue'
import DeliveryPipeline from './dashboard/DeliveryPipeline.vue'
import HubPerformancePanel from './dashboard/HubPerformancePanel.vue'
import SlaChartPanel from './dashboard/SlaChartPanel.vue'
import { trendChartData, trendChartOptions } from './dashboard/trendChart'
import { lmDashboardPageKey } from './dashboard/lmDashboardPageContext'
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useFleetLiveFeed } from '@/composables/useFleetLiveFeed'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import AlertDetailsModal from '@/LWD-components/AlertDetailsModal.vue'
import DriverProfileModal from '@/LWD-components/DriverProfileModal.vue'
import ContactHubModal from '@/LWD-components/ContactHubModal.vue'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

const store = useLogisticStore()
const dispatcherStore = useDispatcherStore()
const EMPTY_HUB = {
    id: 'all',
    hubCode: 'GLOBAL',
    name: 'All Warehouses',
    location: 'No warehouse data yet',
    address: '',
    capacity: 0,
    efficiency: 0,
    staffActive: 0,
    staffTotal: 0,
    vehiclesActive: 0,
    vehiclesTotal: 0,
    processRate: 0,
    status: 'Monitoring',
    statusColor: 'yellow',
    bg: 'bg-slate-700',
}
// ─── Live Fleet Map ────────────────────────────────────────────────────────────

const fleetMap = ref(null)
const fleetMapZoom = ref(5)
const fleetMapCenter = ref([20.5937, 78.9629]) // India center

function getDriverIcon(driver) {
    const isAttention = ['breakdown', 'deviation', 'delayed'].includes((driver.status || '').toLowerCase())
    const color = isAttention ? '#f59e0b' : '#3b82f6'
    return L.divIcon({
        html: `<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:${color}22;border:2px solid ${color};border-radius:50%;font-size:14px">🚚</div>`,
        className: '',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -18],
    })
}

const { liveDrivers, fleetLoading, wsConnected, connectFleetWs, disconnectFleetWs, fetchLiveDrivers } =
    useFleetLiveFeed({ mapRef: fleetMap })

function onMapReady() {
    fetchLiveDrivers()
}

onMounted(() => {
    connectFleetWs()
    // Always do one immediate REST fetch to pre-populate the map
    fetchLiveDrivers()
})

onUnmounted(() => {
    disconnectFleetWs()
})

// --- Active Hub Logic ---
function resolveNetworkStatus(hubs) {
    const normalizedStatuses = hubs.map((hub) => String(hub.status || '').toLowerCase())

    if (normalizedStatuses.some((status) => status === 'congested')) {
        return 'Congested'
    }

    if (normalizedStatuses.some((status) => status && status !== 'optimal')) {
        return 'Monitoring'
    }

    return 'Optimal'
}

const currentHub = computed(() => {
    const hubs = store.hubs || []

    if (store.activeWarehouse !== 'all') {
        return hubs.find((hub) => hub.id === store.activeWarehouse) || hubs[0] || EMPTY_HUB
    }

    if (hubs.length === 0) {
        return EMPTY_HUB
    }

    if (hubs.length === 1) {
        return hubs[0]
    }

    const totalCapacity = hubs.reduce((sum, hub) => sum + (Number(hub.capacity) || 0), 0)
    const totalEfficiency = hubs.reduce((sum, hub) => sum + (Number(hub.efficiency) || 0), 0)
    const totalStaffActive = hubs.reduce((sum, hub) => sum + (Number(hub.staffActive) || 0), 0)
    const totalStaffTotal = hubs.reduce((sum, hub) => sum + (Number(hub.staffTotal) || 0), 0)
    const totalVehiclesActive = hubs.reduce((sum, hub) => sum + (Number(hub.vehiclesActive) || 0), 0)
    const totalVehiclesTotal = hubs.reduce((sum, hub) => sum + (Number(hub.vehiclesTotal) || 0), 0)
    const totalProcessRate = hubs.reduce((sum, hub) => sum + (Number(hub.processRate) || 0), 0)

    return {
        ...EMPTY_HUB,
        location: `${hubs.length} hubs connected`,
        capacity: Math.round(totalCapacity / hubs.length),
        efficiency: Math.round(totalEfficiency / hubs.length),
        staffActive: totalStaffActive,
        staffTotal: totalStaffTotal,
        vehiclesActive: totalVehiclesActive,
        vehiclesTotal: totalVehiclesTotal,
        processRate: totalProcessRate,
        status: resolveNetworkStatus(hubs),
    }
})

const SUPPORT_DRIVER_STATUSES = new Set(['breakdown', 'deviation', 'delayed', 'suspended'])

function getDriverSupportStatus(driver) {
    if (!driver) return ''
    const id = String(driver.id || '')
    if (id && dispatcherStore.isDriverSuspended(id)) {
        return 'suspended'
    }
    return String(driver.status || '').trim().toLowerCase()
}

function getDriverSupportTone(status) {
    return ['breakdown', 'suspended'].includes(status) ? 'critical' : 'warning'
}

function formatDriverSupportStatus(status) {
    if (!status) return 'Needs review'
    return status
        .split(/[\s_-]+/)
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ')
}

const driversNeedingSupport = computed(() => (
    store.filteredDrivers
        .filter((driver) => SUPPORT_DRIVER_STATUSES.has(getDriverSupportStatus(driver)))
        .map((driver) => {
            const supportStatus = getDriverSupportStatus(driver)
            return {
                ...driver,
                supportStatus,
                supportStatusLabel: formatDriverSupportStatus(supportStatus),
                supportTone: getDriverSupportTone(supportStatus),
            }
        })
))

// --- KPI Card Computed ---
const ordersTrend = computed(() => {
    const week = store.dashboardStats.orders?.week || []
    if (week.length < 2) return store.dashboardStats.ordersTrend
    const yesterday = week[week.length - 2] || 0
    const today = week[week.length - 1] || 0
    if (yesterday === 0) return today > 0 ? 100 : 0
    return Math.round(((today - yesterday) / yesterday) * 100)
})

const revenueTrend = computed(() => {
    const week = store.dashboardStats.revenue?.week || []
    if (week.length < 2) return store.dashboardStats.revenueTrend
    const yesterday = week[week.length - 2] || 0
    const today = week[week.length - 1] || 0
    if (yesterday === 0) return today > 0 ? 100 : 0
    return Math.round(((today - yesterday) / yesterday) * 100)
})

const successRateLabel = computed(() => {
    const rate = store.dashboardStats.deliverySuccess
    if (rate >= 95) return 'Excellent'
    if (rate >= 85) return 'High Perf.'
    if (rate >= 70) return 'Moderate'
    return 'Needs Work'
})

const successRateStatus = computed(() => {
    const rate = store.dashboardStats.deliverySuccess
    if (rate >= 95) return 'Outstanding'
    if (rate >= 85) return 'Consistent'
    if (rate >= 70) return 'Improving'
    return 'Attention needed'
})

const successRateColor = computed(() => {
    const rate = store.dashboardStats.deliverySuccess
    if (rate >= 95) return 'text-emerald-400'
    if (rate >= 85) return 'text-purple-400'
    if (rate >= 70) return 'text-yellow-400'
    return 'text-red-400'
})

const staffFillPercent = computed(() => {
    const total = Number(currentHub.value.staffTotal) || 0
    if (total <= 0) return 0
    return Math.round(((Number(currentHub.value.staffActive) || 0) / total) * 100)
})

const vehicleFillPercent = computed(() => {
    const total = Number(currentHub.value.vehiclesTotal) || 0
    if (total <= 0) return 0
    return Math.round(((Number(currentHub.value.vehiclesActive) || 0) / total) * 100)
})

// --- Chart Controls ---
const selectedTimePeriod = ref('week')
const activeTab = ref('sla')

// --- Interactive Actions ---
const isOptimizing = ref(false)
const optimizeHub = () => {
    isOptimizing.value = true
    setTimeout(() => {
        isOptimizing.value = false
        store.addAlert({
            id: Date.now(),
            title: `Appx 12% boost achieved`,
            description: `AI successfully recalibrated loads for ${currentHub.value.name}.`,
            severity: 'low',
            type: 'system',
            icon: 'check_circle',
            location: currentHub.value.location || 'Global Sector',
            timestamp: 'Just now',
            recommendation: 'Monitor load throughput for the next 15 minutes to verify stabilization.'
        })
    }, 2000)
}

const contactHub = () => {
    store.openModal('contact-hub', currentHub.value)
}

const mapZoomIn = () => { fleetMapZoom.value = Math.min(fleetMapZoom.value + 1, 18) }
const mapZoomOut = () => { fleetMapZoom.value = Math.max(fleetMapZoom.value - 1, 2) }

// --- Chart.js Setup ---
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Filler,
    Legend,
} from 'chart.js'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Filler,
    Legend
)

// --- Pipeline Logic ---
const pipelinePercentages = computed(() => {
    const stats = store.dashboardStats
    const total = stats.processing + stats.activeDeliveries + stats.ordersToday

    // Guard against division by zero
    if (total === 0) return { processing: 0, inTransit: 0, delivered: 0 }

    return {
        processing: Math.round((stats.processing / total) * 100),
        inTransit: Math.round((stats.activeDeliveries / total) * 100),
        delivered: Math.round((stats.ordersToday / total) * 100)
    }
})

const chartData = computed(() => trendChartData(store.dashboardStats, activeTab.value, selectedTimePeriod.value))
const chartOptions = computed(() => trendChartOptions(activeTab.value))

function handleAlertAction({ type, alertId }) {
    if (type === 'acknowledge' || type === 'ignore') {
        store.resolveAlert(alertId)
    }
}

provide(lmDashboardPageKey, {
    activeTab,
    chartData,
    chartOptions,
    contactHub,
    currentHub,
    driversNeedingSupport,
    fleetLoading,
    fleetMap,
    fleetMapCenter,
    fleetMapZoom,
    getDriverIcon,
    isOptimizing,
    liveDrivers,
    mapZoomIn,
    mapZoomOut,
    onMapReady,
    optimizeHub,
    ordersTrend,
    pipelinePercentages,
    revenueTrend,
    selectedTimePeriod,
    staffFillPercent,
    store,
    successRateColor,
    successRateLabel,
    successRateStatus,
    vehicleFillPercent,
    wsConnected,
})
</script>
