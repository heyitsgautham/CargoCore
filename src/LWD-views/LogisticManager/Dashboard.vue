<template>
    <div class="space-y-6">
        <!-- Top KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div
                class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
                <div
                    class="absolute -right-6 -top-6 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors">
                </div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Total Orders Today</div>
                        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                            store.dashboardStats.ordersToday.toLocaleString()
                        }}
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <span class="material-symbols-outlined">shopping_cart</span>
                    </div>
                </div>
                <div class="flex items-center text-sm">
                    <span class="font-medium flex items-center" :class="ordersTrend >= 0 ? 'text-primary' : 'text-red-400'">
                        <span class="material-symbols-outlined text-[16px] mr-1">{{ ordersTrend >= 0 ? 'trending_up' : 'trending_down' }}</span>
                        {{ ordersTrend >= 0 ? '+' : '' }}{{ ordersTrend }}%
                    </span>
                    <span class="text-gray-500 dark:text-gray-400 ml-2">vs yesterday</span>
                </div>
            </div>

            <div
                class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
                <div
                    class="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-colors">
                </div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Active Deliveries</div>
                        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                            store.dashboardStats.activeDeliveries }}
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500">
                        <span class="material-symbols-outlined">local_shipping</span>
                    </div>
                </div>
                <div class="flex items-center text-sm">
                    <span class="text-gray-500 dark:text-gray-400 font-medium">
                        {{ store.dashboardStats.deliverySuccess }}% On-Time
                    </span>
                    <div class="ml-auto w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div class="h-full bg-blue-500 transition-all duration-500"
                            :style="{ width: `${Math.min(store.dashboardStats.deliverySuccess, 100)}%` }"></div>
                    </div>
                </div>
            </div>

            <div
                class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
                <div
                    class="absolute -right-6 -top-6 w-24 h-24 bg-purple-500/10 rounded-full blur-2xl group-hover:bg-purple-500/20 transition-colors">
                </div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Delivery Success Rate</div>
                        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">{{
                            store.dashboardStats.deliverySuccess }}%
                        </div>
                    </div>
                    <div class="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500">
                        <span class="material-symbols-outlined">verified</span>
                    </div>
                </div>
                <div class="flex items-center text-sm">
                    <span class="font-medium flex items-center" :class="successRateColor">
                        {{ successRateLabel }}
                    </span>
                    <span class="text-gray-500 dark:text-gray-400 ml-2">{{ successRateStatus }}</span>
                </div>
            </div>

            <div
                class="glass-panel p-5 rounded-2xl relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
                <div
                    class="absolute -right-6 -top-6 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-colors">
                </div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <div class="text-sm text-gray-500 dark:text-gray-400 font-medium">Revenue Today</div>
                        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-1">₹{{
                            (store.dashboardStats.revenueToday /
                                1000).toFixed(1) }}k</div>
                    </div>
                    <div
                        class="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                        <span class="material-symbols-outlined">payments</span>
                    </div>
                </div>
                <div class="flex items-center text-sm">
                    <span class="font-medium flex items-center" :class="revenueTrend >= 0 ? 'text-emerald-400' : 'text-red-400'">
                        <span class="material-symbols-outlined text-[16px] mr-1">{{ revenueTrend >= 0 ? 'trending_up' : 'trending_down' }}</span>
                        {{ revenueTrend >= 0 ? '+' : '' }}{{ revenueTrend }}%
                    </span>
                    <span class="text-gray-500 dark:text-gray-400 ml-2">vs yesterday</span>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">

            <!-- Live Fleet Map (Takes up 2 columns) -->
            <div class="lg:col-span-2 glass-panel rounded-2xl p-0 overflow-hidden flex flex-col relative group">
                <div class="absolute top-4 left-4 z-10 glass-panel px-3 py-1 rounded-full flex items-center gap-2" style="z-index:1000">
                    <span class="w-2 h-2 rounded-full animate-pulse" :class="wsConnected ? 'bg-green-500' : 'bg-yellow-500'"></span>
                    <span class="text-xs font-semibold text-gray-900 dark:text-white">LIVE FLEET VIEW</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ liveDrivers.length }} active</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" :class="wsConnected ? 'bg-green-500/20 text-green-600 dark:text-green-400' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                        {{ wsConnected ? 'WS' : 'POLL' }}
                    </span>
                </div>

                <!-- Real Leaflet Map -->
                <div class="flex-1 relative" style="min-height:0">
                    <l-map
                        ref="fleetMap"
                        :zoom="fleetMapZoom"
                        :center="fleetMapCenter"
                        :use-global-leaflet="false"
                        style="height:100%;width:100%;z-index:1"
                        @ready="onMapReady"
                    >
                        <l-tile-layer
                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                            layer-type="base"
                            name="CartoDB Voyager"
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                        />
                        <l-marker
                            v-for="driver in liveDrivers"
                            :key="driver.driver_id"
                            :lat-lng="[driver.latitude, driver.longitude]"
                            :icon="getDriverIcon(driver)"
                        >
                            <l-popup>
                                <div style="min-width:140px">
                                    <div style="font-weight:700;font-size:13px;margin-bottom:4px">{{ driver.driver_name }}</div>
                                    <div style="font-size:11px;color:#6b7280;text-transform:capitalize">{{ driver.status }}</div>
                                    <div v-if="driver.vehicle_code" style="font-size:11px;color:#6b7280">Vehicle: {{ driver.vehicle_code }}</div>
                                    <div v-if="driver.last_updated" style="font-size:10px;color:#9ca3af;margin-top:4px">
                                        Updated {{ new Date(driver.last_updated).toLocaleTimeString() }}
                                    </div>
                                </div>
                            </l-popup>
                        </l-marker>
                    </l-map>

                    <!-- Empty state overlay when no drivers have location -->
                    <div v-if="liveDrivers.length === 0 && !fleetLoading"
                        class="absolute inset-0 flex flex-col items-center justify-center bg-white/60 dark:bg-background-dark/60 pointer-events-none"
                        style="z-index:2">
                        <span class="material-symbols-outlined text-4xl text-gray-400 mb-2">local_shipping</span>
                        <div class="text-sm text-gray-500 dark:text-gray-400">No active drivers with location data</div>
                    </div>
                </div>

                <!-- Map Controls Overlay -->
                <div class="absolute bottom-4 right-4 flex flex-col gap-2" style="z-index:1000">
                    <button @click="mapZoomIn"
                        class="w-8 h-8 glass-panel rounded-lg flex items-center justify-center hover:bg-white/10 text-gray-700 dark:text-white transition-colors"><span
                            class="material-symbols-outlined text-[18px]">add</span></button>
                    <button @click="mapZoomOut"
                        class="w-8 h-8 glass-panel rounded-lg flex items-center justify-center hover:bg-white/10 text-gray-700 dark:text-white transition-colors"><span
                            class="material-symbols-outlined text-[18px]">remove</span></button>
                </div>
            </div>

            <!-- Right Panel: Alerts & Bottlenecks -->
            <div class="glass-panel rounded-2xl p-5 flex flex-col h-full">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center">
                        <span class="material-symbols-outlined mr-2 text-yellow-500">warning</span>
                        Attention Needed
                    </h3>

                    <!-- Search -->
                    <div class="relative flex items-center">
                        <input v-if="store.isSearchOpen" v-model="store.searchQuery" type="text"
                            placeholder="Search drivers, alerts..."
                            class="w-48 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:border-primary/50 transition-all absolute right-10 shadow-sm"
                            autofocus />
                        <button @click="store.toggleSearch"
                            class="w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                            :class="{ 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white': store.isSearchOpen }">
                            <span class="material-symbols-outlined text-[18px]">search</span>
                        </button>
                    </div>
                </div>

                <div class="flex-1 relative">
                    <div class="absolute inset-0 overflow-y-auto pr-1 space-y-3 no-scrollbar">
                        <div v-if="store.alerts.length === 0" class="text-center py-8 text-gray-500 text-sm">
                            No active alerts. Good job!
                        </div>
                        <!-- Alert Item -->
                        <div v-for="alert in store.alerts" :key="alert.id"
                            class="p-3 rounded-lg border flex gap-3 transition-colors" :class="[
                                alert.severity === 'high' ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20' : 'bg-yellow-50 dark:bg-yellow-500/10 border-yellow-200 dark:border-yellow-500/20'
                            ]">
                            <div class="mt-1 min-w-[24px]">
                                <span class="material-symbols-outlined text-[20px]" :class="[
                                    alert.severity === 'high' ? 'text-red-500' : 'text-yellow-500'
                                ]">{{ alert.icon }}</span>
                            </div>
                            <div>
                                <h4 class="text-sm font-semibold text-gray-900 dark:text-white">{{ alert.title }}</h4>
                                <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{{ alert.description }}</p>
                                <button @click="store.openModal('alert-details', alert)"
                                    class="mt-2 text-xs font-medium hover:underline" :class="[
                                        alert.severity === 'high' ? 'text-red-600 dark:text-red-400 hover:text-red-500 dark:hover:text-red-300' : 'text-yellow-600 dark:text-yellow-400 hover:text-yellow-500 dark:hover:text-yellow-300'
                                    ]">
                                    {{ alert.severity === 'high' ? 'View Details' : 'Investigate' }}
                                </button>
                            </div>
                        </div>

                        <!-- List of Drivers Needing Attention -->
                        <div class="mt-4 pt-4 border-t border-gray-100 dark:border-white/5">
                            <h4
                                class="text-xs font-semibold text-gray-500 dark:text-gray-500 uppercase tracking-wider mb-2">
                                Drivers Needing
                                Support</h4>
                            <div v-if="driversNeedingSupport.length" class="space-y-2">
                                <div v-for="driver in driversNeedingSupport" :key="driver.id"
                                    @click="store.openModal('driver-profile', driver)"
                                    class="flex items-center justify-between p-2 rounded hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer group transition-colors">
                                    <div class="flex items-center gap-3">
                                        <div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-sm"
                                            :class="driver.avatarColor">
                                            {{ driver.name.charAt(0) }}
                                        </div>
                                        <div>
                                            <div
                                                class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary transition-colors">
                                                {{ driver.name }}</div>
                                            <div class="text-[10px]" :class="[
                                                driver.supportTone === 'critical' ? 'text-red-500 dark:text-red-400' : 'text-yellow-500 dark:text-yellow-400'
                                            ]">{{ driver.supportStatusLabel }}</div>
                                        </div>
                                    </div>
                                    <span
                                        class="material-symbols-outlined text-gray-400 dark:text-gray-500 text-[18px]">chevron_right</span>
                                </div>
                            </div>
                            <div v-else class="rounded-xl border border-dashed border-gray-200 dark:border-white/10 px-3 py-4 text-xs text-gray-500 dark:text-gray-400">
                                No drivers currently need support.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bottom Section: KPI Charts & Hub Performance -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Active Delivery Pipeline -->
            <div class="glass-panel p-5 rounded-2xl flex flex-col justify-between">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">Active Delivery Pipeline</h3>
                    <div
                        class="px-2 py-1 bg-primary/10 text-primary rounded text-xs font-bold uppercase tracking-wider">
                        Live Pulse
                    </div>
                </div>

                <div class="space-y-6 my-auto">
                    <!-- Stage: Processing -->
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                                Processing at Hubs
                            </span>
                            <span class="text-gray-900 dark:text-white font-bold">{{
                                store.dashboardStats.processing.toLocaleString() }}</span>
                        </div>
                        <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                            <div class="h-full bg-blue-500 rounded-full transition-all duration-1000"
                                :style="{ width: pipelinePercentages.processing + '%' }"></div>
                        </div>
                    </div>

                    <!-- Stage: In Transit -->
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
                                In Transit
                            </span>
                            <span class="text-gray-900 dark:text-white font-bold">{{
                                store.dashboardStats.activeDeliveries.toLocaleString() }}</span>
                        </div>
                        <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                            <div class="h-full bg-yellow-500 rounded-full transition-all duration-1000"
                                :style="{ width: pipelinePercentages.inTransit + '%' }"></div>
                        </div>
                    </div>

                    <!-- Stage: Delivered -->
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span class="text-gray-500 dark:text-gray-400 font-medium flex items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-green-500"></span>
                                Delivered Today
                            </span>
                            <span class="text-gray-900 dark:text-white font-bold">{{
                                store.dashboardStats.ordersToday.toLocaleString() }}</span>
                        </div>
                        <div class="w-full h-2 bg-gray-200 dark:bg-gray-700/50 rounded-full overflow-hidden">
                            <div class="h-full bg-green-500 rounded-full transition-all duration-1000"
                                :style="{ width: pipelinePercentages.delivered + '%' }"></div>
                        </div>
                    </div>
                </div>

                <div
                    class="mt-6 pt-4 border-t border-gray-100 dark:border-white/5 flex gap-4 text-xs font-medium text-gray-500 dark:text-gray-400">
                    <div>
                        <span class="text-gray-900 dark:text-white font-bold">{{
                            store.dashboardStats.deliverySuccess
                        }}%</span> Success Rate
                    </div>
                    <div>
                        <span class="text-gray-900 dark:text-white font-bold">{{ store.dashboardStats.activeDrivers ?? '—' }}</span> Active Drivers
                    </div>
                </div>
            </div>

            <!-- Hub Performance Table / Interactive View -->
            <div class="glass-panel p-4 lg:p-5 rounded-2xl flex flex-col justify-between h-full overflow-hidden">
                <!-- Header -->
                <div class="flex justify-between items-center mb-2">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                        <span v-if="store.activeWarehouse === 'all'">Hub Performance</span>
                        <span v-else>{{ store.activeWarehouseName }} Overview</span>
                    </h3>
                    <button v-if="store.activeWarehouse !== 'all'" @click="store.setWarehouse('all')"
                        class="text-xs text-primary hover:underline font-medium flex items-center">
                        <span class="material-symbols-outlined text-[14px] mr-0.5">arrow_back</span>
                        View All
                    </button>
                </div>

                <!-- ALL HUBS VIEW -->
                <div v-if="store.activeWarehouse === 'all'" class="overflow-x-auto my-auto py-2">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr
                                class="text-xs text-gray-500 dark:text-gray-500 border-b border-gray-200 dark:border-white/10">
                                <th class="py-2 font-medium">Hub Name</th>
                                <th class="py-2 font-medium">Capacity</th>
                                <th class="py-2 font-medium">Efficiency</th>
                                <th class="py-2 font-medium">Process Rate</th>
                                <th class="py-2 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody class="text-sm">
                            <tr v-for="hub in store.hubs" :key="hub.id"
                                class="border-b border-b-gray-100 dark:border-b-white/5 last:border-0 transition-all cursor-pointer relative"
                                :class="[
                                    store.activeWarehouse === hub.id
                                        ? 'bg-primary/5 dark:bg-primary/10 border-l-4 border-l-primary'
                                        : 'hover:bg-gray-50 dark:hover:bg-white/5 border-l-4 border-l-transparent'
                                ]" @click="store.setWarehouse(hub.id)">
                                <td class="py-3 text-gray-900 dark:text-white font-medium">{{ hub.name }}</td>
                                <td class="py-3 text-gray-500 dark:text-gray-300">
                                    <div class="flex items-center gap-2">
                                        <div
                                            class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <div class="h-full" :class="hub.bg" :style="{ width: hub.capacity + '%' }">
                                            </div>
                                        </div>
                                        <span class="text-xs">{{ hub.capacity }}%</span>
                                    </div>
                                </td>
                                <!-- Added Efficiency Column -->
                                <td class="py-3 text-gray-500 dark:text-gray-300">
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs font-semibold"
                                            :class="hub.efficiency > 85 ? 'text-green-500' : (hub.efficiency > 60 ? 'text-yellow-500' : 'text-red-500')">
                                            {{ hub.efficiency }}%
                                        </span>
                                    </div>
                                </td>
                                <td class="py-3 text-gray-500 dark:text-gray-300">{{
                                    hub.processRate.toLocaleString() }}
                                    pkgs/hr</td>
                                <td class="py-3">
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase"
                                        :class="hub.status.toLowerCase() === 'optimal' ? 'bg-green-500/20 text-green-600 dark:text-green-500' : (hub.status.toLowerCase() === 'congested' ? 'bg-red-500/20 text-red-600 dark:text-red-500' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-500')">
                                        {{ hub.status }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- SINGLE HUB INTERACTIVE VIEW -->
                <div v-else-if="currentHub" class="flex flex-col h-full animate-fade-in py-2">
                    <div class="flex flex-wrap lg:flex-nowrap items-center justify-between gap-4 lg:gap-6 my-auto">

                        <!-- Main Stats Group -->
                        <div class="flex items-center gap-4">
                            <!-- Capacity Circular Progress -->
                            <div class="relative w-20 h-20 lg:w-24 lg:h-24 flex-shrink-0 group">
                                <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="transition-all duration-1000 ease-out"
                                        :class="currentHub.capacity > 85 ? 'stroke-red-500' : (currentHub.capacity > 60 ? 'stroke-yellow-500' : 'stroke-green-500')"
                                        stroke-width="3" :stroke-dasharray="`${currentHub.capacity}, 100`"
                                        stroke-linecap="round"></circle>
                                </svg>
                                <div class="absolute inset-0 flex flex-col items-center justify-center">
                                    <span
                                        class="text-lg lg:text-2xl font-bold text-gray-900 dark:text-white leading-none">
                                        {{ currentHub.capacity }}%
                                    </span>
                                    <span
                                        class="text-[9px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5 lg:mt-1">Load</span>
                                </div>
                            </div>

                            <!-- Pkgs/Hr Stats & Status -->
                            <div>
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border"
                                        :class="currentHub.status.toLowerCase() === 'optimal' ? 'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-500' : (currentHub.status.toLowerCase() === 'congested' ? 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-500' : 'bg-yellow-50 border-yellow-200 text-yellow-600 dark:bg-yellow-500/10 dark:border-yellow-500/20 dark:text-yellow-500')">
                                        <span class="inline-block w-1.5 h-1.5 rounded-full mr-0.5"
                                            :class="currentHub.status.toLowerCase() === 'optimal' ? 'bg-green-500' : (currentHub.status.toLowerCase() === 'congested' ? 'bg-red-500' : 'bg-yellow-500')"></span>
                                        {{ currentHub.status }}
                                    </span>
                                </div>
                                <div class="flex items-baseline gap-1">
                                    <span class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">{{
                                        currentHub.processRate.toLocaleString() }}</span>
                                    <span
                                        class="text-xs lg:text-sm font-medium text-gray-500 dark:text-gray-400">pkgs/hr</span>
                                </div>
                            </div>
                        </div>

                        <!-- Secondary Metrics Group (Circular) -->
                        <div class="flex items-center gap-3 lg:gap-4 justify-around w-full lg:w-auto mt-4 lg:mt-0">
                            <!-- Efficiency Circular -->
                            <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                                <svg class="w-full h-full transform -rotate-90 drop-shadow-sm" viewBox="0 0 36 36">
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="transition-all duration-1000 ease-out"
                                        :class="currentHub.efficiency > 85 ? 'stroke-green-500' : (currentHub.efficiency > 60 ? 'stroke-yellow-500' : 'stroke-red-500')"
                                        stroke-width="3" :stroke-dasharray="`${currentHub.efficiency}, 100`"
                                        stroke-linecap="round"></circle>
                                </svg>
                                <div class="absolute inset-0 flex flex-col items-center justify-center">
                                    <span
                                        class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                        {{ currentHub.efficiency }}%
                                    </span>
                                    <span
                                        class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Effic.</span>
                                </div>
                            </div>

                            <!-- Staff Circular -->
                            <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                                <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="transition-all duration-1000 ease-out stroke-blue-500" stroke-width="3"
                                        :stroke-dasharray="`${staffFillPercent}, 100`"
                                        stroke-linecap="round"></circle>
                                </svg>
                                <div class="absolute inset-0 flex flex-col items-center justify-center">
                                    <span
                                        class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                        {{ currentHub.staffActive }}<span
                                            class="text-[10px] lg:text-xs text-gray-400 font-normal">/{{
                                                currentHub.staffTotal }}</span>
                                    </span>
                                    <span
                                        class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Staff</span>
                                </div>
                            </div>

                            <!-- Vehicles Circular -->
                            <div class="relative w-14 h-14 lg:w-16 lg:h-16 flex-shrink-0 group">
                                <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="stroke-gray-100 dark:stroke-white/5" stroke-width="3"></circle>
                                    <circle cx="18" cy="18" r="15.9155" fill="none"
                                        class="transition-all duration-1000 ease-out stroke-purple-500" stroke-width="3"
                                        :stroke-dasharray="`${vehicleFillPercent}, 100`"
                                        stroke-linecap="round"></circle>
                                </svg>
                                <div class="absolute inset-0 flex flex-col items-center justify-center">
                                    <span
                                        class="text-base lg:text-xl font-bold text-gray-900 dark:text-white leading-none">
                                        {{ currentHub.vehiclesActive }}<span
                                            class="text-[10px] lg:text-xs text-gray-400 font-normal">/{{
                                                currentHub.vehiclesTotal
                                            }}</span>
                                    </span>
                                    <span
                                        class="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">Vehs</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Interactive Actions -->
                    <div class="grid grid-cols-2 gap-3 mt-6">
                        <button @click="optimizeHub" :disabled="isOptimizing"
                            class="border rounded-xl p-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300"
                            :class="isOptimizing ? 'bg-primary/20 text-primary border-primary/20 cursor-wait' : 'bg-primary/10 hover:bg-primary/20 text-primary border-primary/20'">
                            <span v-if="!isOptimizing" class="material-symbols-outlined text-[18px]">tune</span>
                            <span v-else class="material-symbols-outlined text-[18px] animate-spin">sync</span>
                            {{ isOptimizing ? 'Optimizing...' : 'Optimize Load' }}
                        </button>
                        <button @click="contactHub"
                            class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 border border-transparent rounded-xl p-3 text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-300">
                            <span class="material-symbols-outlined text-[18px]">support_agent</span>
                            Contact Hub
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Full Width SLA Compliance Chart -->
        <div class="glass-panel p-5 rounded-2xl w-full mt-6 flex flex-col">
            <!-- Tabs Header -->
            <div
                class="flex items-center gap-4 mb-6 border-b border-gray-200 dark:border-white/10 pb-2 overflow-x-auto hide-scrollbar">
                <button @click="activeTab = 'sla'"
                    class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                    :class="activeTab === 'sla' ? 'text-primary border-b-2 border-primary -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                    SLA Compliance Trend
                </button>
                <button @click="activeTab = 'revenue'"
                    class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                    :class="activeTab === 'revenue' ? 'text-emerald-500 border-b-2 border-emerald-500 -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                    Revenue Analysis
                </button>
                <button @click="activeTab = 'orders'"
                    class="px-4 py-2 text-sm font-bold transition-colors whitespace-nowrap"
                    :class="activeTab === 'orders' ? 'text-purple-500 border-b-2 border-purple-500 -mb-[3px]' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white border-b-2 border-transparent -mb-[3px]'">
                    Order Volume
                </button>
                <div class="ml-auto flex-shrink-0 pl-4">
                    <!-- Time Period Selection -->
                    <select v-model="selectedTimePeriod"
                        class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg text-xs text-gray-700 dark:text-gray-300 px-3 py-1.5 outline-none transition-colors cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700">
                        <option value="week" class="bg-white dark:bg-gray-800">Last 7 Days</option>
                        <option value="month" class="bg-white dark:bg-gray-800">This Month</option>
                    </select>
                </div>
            </div>

            <!-- Chart Container -->
            <div class="h-64 lg:h-80 w-full relative">
                <Line :key="activeTab + '-' + selectedTimePeriod" :data="chartData" :options="chartOptions" />
            </div>
        </div>

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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import AlertDetailsModal from '@/LWD-components/AlertDetailsModal.vue'
import DriverProfileModal from '@/LWD-components/DriverProfileModal.vue'
import ContactHubModal from '@/LWD-components/ContactHubModal.vue'
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { apiUrl } from '@/config/api'

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
import { API_BASE_URL } from '@/config/api'

const fleetMap = ref(null)
const fleetMapZoom = ref(5)
const fleetMapCenter = ref([20.5937, 78.9629]) // India center
const liveDrivers = ref([])
const fleetLoading = ref(false)
const wsConnected = ref(false)

let fleetWs = null
let wsReconnectTimer = null
let wsReconnectDelay = 2000   // start at 2s, backs off to 30s max
let pollFallbackTimer = null  // only used when WS is down

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

// ── WebSocket ──────────────────────────────────────────────────────────────────
function buildWsUrl() {
    const token = localStorage.getItem('auth_token') || ''
    // Convert http(s):// → ws(s)://
    const wsBase = API_BASE_URL.replace(/^http/, 'ws')
    return `${wsBase}/ws/fleet?token=${encodeURIComponent(token)}`
}

function applyLocationUpdate(msg) {
    if (msg.latitude == null || msg.longitude == null) return
    const existing = liveDrivers.value.findIndex(d => d.driver_id === msg.driver_id)
    const entry = {
        driver_id: msg.driver_id,
        driver_name: msg.driver_name,
        latitude: msg.latitude,
        longitude: msg.longitude,
        status: msg.status,
        vehicle_code: msg.vehicle_code,
        vehicle_id: msg.vehicle_id,
        last_updated: msg.last_updated,
    }
    if (existing >= 0) {
        liveDrivers.value[existing] = entry
    } else {
        liveDrivers.value.push(entry)
    }
}

function connectFleetWs() {
    if (fleetWs && fleetWs.readyState <= WebSocket.OPEN) return

    try {
        fleetWs = new WebSocket(buildWsUrl())
    } catch (e) {
        scheduleWsReconnect()
        return
    }

    fleetWs.onopen = () => {
        wsConnected.value = true
        wsReconnectDelay = 2000
        // WebSocket is up — stop polling fallback
        clearInterval(pollFallbackTimer)
        pollFallbackTimer = null
    }

    fleetWs.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'location_update') applyLocationUpdate(msg)
            if (msg.type === 'ping') fleetWs.send(JSON.stringify({ type: 'pong' }))
        } catch (e) { /* ignore malformed frames */ }
    }

    fleetWs.onerror = () => { /* handled in onclose */ }

    fleetWs.onclose = () => {
        wsConnected.value = false
        fleetWs = null
        // Fall back to polling while WS is reconnecting
        if (!pollFallbackTimer) {
            pollFallbackTimer = setInterval(fetchLiveDrivers, 30000)
        }
        scheduleWsReconnect()
    }
}

function scheduleWsReconnect() {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = setTimeout(() => {
        connectFleetWs()
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000) // cap at 30s
    }, wsReconnectDelay)
}

function disconnectFleetWs() {
    clearTimeout(wsReconnectTimer)
    clearInterval(pollFallbackTimer)
    if (fleetWs) {
        fleetWs.onclose = null // prevent reconnect loop on intentional close
        fleetWs.close()
        fleetWs = null
    }
    wsConnected.value = false
}

// ── Initial REST fetch (fills map before first WS update) ──────────────────────
async function fetchLiveDrivers() {
    fleetLoading.value = true
    try {
        const token = localStorage.getItem('auth_token')
        const res = await fetch(apiUrl('api/v1/tracking/drivers'), {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!res.ok) return
        const data = await res.json()
        liveDrivers.value = data.filter(d => d.latitude != null && d.longitude != null)
        if (liveDrivers.value.length > 0 && fleetMap.value?.leafletObject) {
            const bounds = L.latLngBounds(liveDrivers.value.map(d => [d.latitude, d.longitude]))
            fleetMap.value.leafletObject.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 })
        }
    } catch (e) { /* silent */ } finally {
        fleetLoading.value = false
    }
}

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
    Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

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

const chartData = computed(() => {
    const isWeek = selectedTimePeriod.value === 'week'
    let data = []
    let labelString = ''
    let config = {}

    // 1. Resolve Data Array and Config based on Tab
    if (activeTab.value === 'sla') {
        data = store.dashboardStats.slaCompliance[selectedTimePeriod.value] || []
        labelString = 'SLA Compliance (%)'
        config = {
            bg: 'rgba(56, 189, 248, 0.1)', // Tailwind Primary (Sky-400)
            border: 'rgb(56, 189, 248)'
        }
    } else if (activeTab.value === 'revenue') {
        data = store.dashboardStats.revenue[selectedTimePeriod.value] || []
        labelString = 'Revenue ($)'
        config = {
            bg: 'rgba(16, 185, 129, 0.1)', // Tailwind Emerald-500
            border: 'rgb(16, 185, 129)'
        }
    } else if (activeTab.value === 'orders') {
        data = store.dashboardStats.orders[selectedTimePeriod.value] || []
        labelString = 'Order Volume'
        config = {
            bg: 'rgba(168, 85, 247, 0.1)', // Tailwind Purple-500
            border: 'rgb(168, 85, 247)'
        }
    }

    // 2. Create X-Axis Labels
    let labels = []
    if (isWeek) {
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    } else {
        // Generate nice month labels, e.g., '1', '5', '10' etc. or just numbers
        labels = Array.from({ length: data.length }, (_, i) => i + 1)
    }

    return {
        labels,
        datasets: [
            {
                label: labelString,
                backgroundColor: config.bg,
                borderColor: config.border,
                borderWidth: 2,
                pointBackgroundColor: config.border,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: config.border,
                fill: true,
                tension: 0.4, // Smooth curve
                data: data
            }
        ]
    }
})

// Progressive Animation Logic for Chart.js
const totalDuration = 1000;
const delayBetweenPoints = totalDuration / 30; // Max points is ~30 for month
const previousY = (ctx) => ctx.index === 0 ? ctx.chart.scales.y.getPixelForValue(100) : ctx.chart.getDatasetMeta(ctx.datasetIndex).data[ctx.index - 1].getProps(['y'], true).y;

const animationConfig = {
    x: {
        type: 'number',
        easing: 'linear',
        duration: delayBetweenPoints,
        from: NaN, // the point is initially skipped
        delay(ctx) {
            if (ctx.type !== 'data' || ctx.xStarted) {
                return 0;
            }
            ctx.xStarted = true;
            return ctx.index * delayBetweenPoints;
        }
    },
    y: {
        type: 'number',
        easing: 'linear',
        duration: delayBetweenPoints,
        from: previousY,
        delay(ctx) {
            if (ctx.type !== 'data' || ctx.yStarted) {
                return 0;
            }
            ctx.yStarted = true;
            return ctx.index * delayBetweenPoints;
        }
    }
}

const chartOptions = computed(() => {
    // Dynamic Y-axis scaling based on tab
    let minBuild = undefined;
    let maxBuild = undefined;

    if (activeTab.value === 'sla') {
        minBuild = 70;
        maxBuild = 100;
    } else {
        minBuild = 0;
    }

    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: animationConfig, // Inject progressive animation
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function (context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (activeTab.value === 'sla') {
                            label += context.parsed.y + '%';
                        } else if (activeTab.value === 'revenue') {
                            label += '$' + context.parsed.y.toLocaleString();
                        } else {
                            label += context.parsed.y.toLocaleString();
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                min: minBuild,
                max: maxBuild,
                grid: {
                    color: 'rgba(156, 163, 175, 0.1)',
                    drawBorder: false,
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false,
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    }
})

function handleAlertAction({ type, alertId }) {
    if (type === 'acknowledge' || type === 'ignore') {
        store.resolveAlert(alertId)
    }
}
</script>
