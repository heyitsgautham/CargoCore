<template>
    <div class="space-y-5">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Shipment Tracking</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Live visibility into all your shipments</p>
            </div>
            <div class="flex gap-2">
                <select v-model="statusFilter"
                    class="text-sm bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option value="all" class="bg-white dark:bg-gray-800">All Statuses</option>
                    <option value="pending" class="bg-white dark:bg-gray-800">Pending</option>
                    <option value="warehouse" class="bg-white dark:bg-gray-800">In Warehouse</option>
                    <option value="transit" class="bg-white dark:bg-gray-800">In Transit</option>
                    <option value="delivery" class="bg-white dark:bg-gray-800">Out for Delivery</option>
                    <option value="delivered" class="bg-white dark:bg-gray-800">Delivered</option>
                    <option value="cancelled" class="bg-white dark:bg-gray-800">Cancelled</option>
                </select>
            </div>
        </div>

        <!-- Stats Bar -->
        <TrackingStatsBar :store="store" />

        <!-- Main Layout -->
        <div class="flex gap-5" style="min-height: 78vh;">

            <ShipmentList />

            <!-- ── Right: Detail / Dashboard ──────────────────────────────── -->
            <div class="flex-1 min-w-0 flex flex-col gap-5">

                <!-- ── No selection: Global dashboard ── -->
                <template v-if="!selected">
                    <!-- Tabs -->
                    <div class="flex items-center gap-1 bg-gray-100 dark:bg-white/5 rounded-xl p-1 w-fit">
                        <button v-for="t in [['map','Live Map','map'], ['table','All Orders','table_rows'], ['graphs','Analytics','bar_chart']]"
                            :key="t[0]" @click="globalTab = t[0]"
                            class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                            :class="globalTab === t[0]
                                ? 'bg-white dark:bg-card-dark text-blue-600 dark:text-blue-400 shadow-sm'
                                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                            <span class="material-symbols-outlined text-[16px]">{{ t[2] }}</span> {{ t[1] }}
                        </button>
                    </div>

                    <GlobalLiveMap />

                    <AllOrdersTable />

                    <TrackingAnalytics />
                </template>

                <!-- ── Shipment selected: Detail view ── -->
                <template v-else>
                    <ShipmentHeader />

                    <RouteHeroCard />

                    <!-- Main content: single full-width column -->
                    <div class="space-y-4">

                        <ShipmentOverview />

                        <ShipmentDocuments />

                        <TransitLog />

                        <ProofOfDeliveryCard />

                        <!-- Need Help banner: navigates to AI Chat Support with this order pre-selected -->
                        <div @click="goToSupport"
                            class="p-4 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-700 text-white cursor-pointer hover:from-blue-700 hover:to-blue-800 transition-all group relative overflow-hidden">
                            <div class="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full group-hover:scale-150 transition-transform duration-300"></div>
                            <div class="relative flex items-center gap-3">
                                <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
                                    <span class="material-symbols-outlined text-[22px]">support_agent</span>
                                </div>
                                <div>
                                    <div class="text-sm font-bold">Need Help?</div>
                                    <div class="text-xs opacity-75">Chat with our support team — available 24/7</div>
                                </div>
                                <span class="material-symbols-outlined text-[20px] ml-auto opacity-60">chevron_right</span>
                            </div>
                        </div>

                    </div>
                </template>
            </div>
        </div>

        <AddressModal />

        <RescheduleModal />

        <DamageReportModal />
        <SupportModal />

        <DriverRatingModal />

        <DriverCallModal />

        <DriverChatModal />

    </div>
</template>

<script setup>
import ShipmentList from './tracking/ShipmentList.vue'
import GlobalLiveMap from './tracking/GlobalLiveMap.vue'
import AllOrdersTable from './tracking/AllOrdersTable.vue'
import TrackingAnalytics from './tracking/TrackingAnalytics.vue'
import ShipmentHeader from './tracking/ShipmentHeader.vue'
import RouteHeroCard from './tracking/RouteHeroCard.vue'
import ShipmentOverview from './tracking/ShipmentOverview.vue'
import ShipmentDocuments from './tracking/ShipmentDocuments.vue'
import TransitLog from './tracking/TransitLog.vue'
import ProofOfDeliveryCard from './tracking/ProofOfDeliveryCard.vue'
import AddressModal from './tracking/AddressModal.vue'
import RescheduleModal from './tracking/RescheduleModal.vue'
import DamageReportModal from './tracking/DamageReportModal.vue'
import SupportModal from './tracking/SupportModal.vue'
import DriverRatingModal from './tracking/DriverRatingModal.vue'
import DriverCallModal from './tracking/DriverCallModal.vue'
import DriverChatModal from './tracking/DriverChatModal.vue'
import { vendorTrackingPageKey } from './tracking/vendorTrackingPageContext'
import TrackingStatsBar from './tracking/TrackingStatsBar.vue'
import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useRouter } from 'vue-router'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix Leaflet default icon URLs
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
    iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
    shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
});

const { openSlipWithData, SLIP_LABELS, SLIP_ICONS } = useSlipPrinter()
const authStore = useAuthStore()
const router = useRouter()

function currentUser() {
    return authStore.currentUser || {}
}

// Navigate to AI Chat Support page with the current shipment pre-selected
function goToSupport() {
    if (!selected.value) return
    router.push({
        name: 'VendorSupport',
        query: {
            tab: 'chat',
            shipmentId: selected.value.backendId || selected.value.id,
        },
    })
}

// Chart.js Imports
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js'

import { spendChart, spendChartOptions, volumeChart, volumeChartOptions } from './tracking/trackingCharts'
import { useShipmentActions } from './tracking/useShipmentActions'
import {
    buildTrackingLogs,
    filterShipments,
    liveDriverPosition,
    severityClass,
    shipmentDocuments,
    shipmentPhase,
    statusClass,
    topRoutes as rankTopRoutes,
} from './tracking/shipmentView'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const store = useVendorStore()
const selected = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')

// ── Live status refresh ────────────────────────────────────────────────────
// Re-fetch shipments when the Tracking page is opened so dispatcher status
// changes (e.g. IN_TRANSIT → DELIVERED) appear immediately without a full
// page reload. Also poll every 30 s for continuous updates.
let _pollTimer = null
onMounted(async () => {
    try { await store.fetchShipments() } catch (_) {}
    _pollTimer = setInterval(async () => {
        try { await store.fetchShipments() } catch (_) {}
    }, 30_000)
})
onUnmounted(() => {
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null }
})

// When shipments refresh, sync the currently selected shipment so the detail
// view reflects the latest status (e.g. In Transit → Delivered) automatically.
watch(() => store.shipments, (list) => {
    if (!selected.value) return
    const fresh = list.find(s => s.backendId === selected.value.backendId || s.id === selected.value.id)
    if (fresh) selected.value = fresh
}, { deep: false })

const {
    showAddressModal,
    showRescheduleModal,
    showDamageModal,
    showSupportModal,
    showCallModal,
    showChatModal,
    newAddress,
    newDate,
    rescheduleReason,
    supportMessage,
    newChatMessage,
    chatMessages,
    damageForm,
    vendorRatingModal,
    sendChatMessage,
    handleFileUpload,
    submitSupport,
    updateAddress,
    reschedule,
    handleCancel,
    submitDamage,
    openVendorRatingModal,
    submitVendorRating,
} = useShipmentActions(store, selected)
const globalTab = ref('map')
const detailTab = ref('overview')

// ─── Real-Time Tracking (all active drivers for vendor global view) ───
const { activeDrivers } = useRealTimeTracking()

const globalMapCenter = computed(() =>
    activeDrivers.value.length > 0
        ? [activeDrivers.value[0].latitude, activeDrivers.value[0].longitude]
        : [20.5937, 78.9629]
)
const globalMapZoom = ref(5)
const selectedMapZoom = ref(10)

const selectedIsDelivered = computed(() => selected.value?.statusKey === 'delivered')
const selectedIsCancelled = computed(() => selected.value?.statusKey === 'cancelled')
const selectedHasLiveTracking = computed(() => Boolean(liveDriverPosition(selected.value)))
const selectedMapCenter = computed(() => liveDriverPosition(selected.value) || [20.5937, 78.9629])
const selectedPhase = computed(() => shipmentPhase(selected.value))
const selectedEtaLabel = computed(() => selectedPhase.value.etaLabel)
const selectedEtaClass = computed(() => selectedPhase.value.etaClass)
const selectedDriverStatus = computed(() => selectedPhase.value.driver)
const selectedDriverMapStatusLabel = computed(() => selectedPhase.value.mapLabel)
const canCallDriver = computed(() => Boolean(String(selected.value?.driverPhone || '').trim()))
const podSignatureBroken = ref(false)

watch(selected, () => {
    podSignatureBroken.value = false
})

const availableDocuments = computed(() => shipmentDocuments(selected.value, {
    labels: SLIP_LABELS,
    icons: SLIP_ICONS,
    open: (key) => openSlipWithData(key, selected.value, currentUser()),
}))

// Transport Log — real status history from backend
const trackingLogs = computed(() => buildTrackingLogs(selected.value))

// Analytics Charts (Chart.js)
const spendChartData = computed(() => spendChart(store.analyticsData.monthly))
const volumeChartData = computed(() => volumeChart(store.analyticsData.monthly))

const mapAlertCount = computed(() =>
    store.overdueInvoices.length + store.shipments.filter(s => s.statusKey === 'cancelled').length
)
const topRoutes = computed(() => rankTopRoutes(store.shipments))
const filteredShipments = computed(() => filterShipments(store.shipments, statusFilter.value, searchQuery.value))

provide(vendorTrackingPageKey, {
    activeDrivers,
    availableDocuments,
    canCallDriver,
    chatMessages,
    currentUser,
    damageForm,
    detailTab,
    filteredShipments,
    globalMapCenter,
    globalMapZoom,
    globalTab,
    handleCancel,
    handleFileUpload,
    mapAlertCount,
    newAddress,
    newChatMessage,
    newDate,
    openSlipWithData,
    openVendorRatingModal,
    podSignatureBroken,
    reschedule,
    rescheduleReason,
    searchQuery,
    selected,
    selectedDriverMapStatusLabel,
    selectedDriverStatus,
    selectedEtaClass,
    selectedEtaLabel,
    selectedHasLiveTracking,
    selectedIsCancelled,
    selectedIsDelivered,
    selectedMapCenter,
    selectedMapZoom,
    sendChatMessage,
    severityClass,
    showAddressModal,
    showCallModal,
    showChatModal,
    showDamageModal,
    showRescheduleModal,
    showSupportModal,
    spendChartData,
    spendChartOptions,
    statusClass,
    store,
    submitDamage,
    submitSupport,
    submitVendorRating,
    supportMessage,
    topRoutes,
    trackingLogs,
    updateAddress,
    vendorRatingModal,
    volumeChartData,
    volumeChartOptions,
})
</script>
