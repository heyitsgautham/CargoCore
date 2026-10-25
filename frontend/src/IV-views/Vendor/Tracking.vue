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

            <!-- ── Left: Shipment List ─────────────────────────────────────── -->
            <div class="w-80 flex-shrink-0 glass-panel rounded-2xl overflow-hidden flex flex-col">
                <!-- Search -->
                <div class="p-4 border-b border-gray-200 dark:border-white/5">
                    <div class="relative">
                        <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-[18px]">search</span>
                        <input v-model="searchQuery" type="text" placeholder="Search ID or destination…"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl py-2 pl-9 pr-4 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-blue-500/50">
                    </div>
                </div>
                <!-- List -->
                <div class="flex-1 overflow-y-auto p-3 space-y-2">
                    <div v-if="filteredShipments.length === 0" class="py-16 text-center text-gray-400 text-sm">
                        <span class="material-symbols-outlined text-4xl mb-2 block text-gray-300">inbox</span>
                        No shipments found
                    </div>
                    <div v-for="s in filteredShipments" :key="s.id"
                        @click="selected = s; detailTab = 'overview'"
                        class="rounded-xl cursor-pointer transition-all border overflow-hidden"
                        :class="selected?.id === s.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10 shadow-md shadow-blue-500/10'
                            : 'border-gray-100 dark:border-white/5 bg-white dark:bg-white/5 hover:border-blue-300 dark:hover:border-blue-500/30 hover:shadow-sm'">
                        <!-- Color bar -->
                        <div class="h-1 w-full" :class="{
                            'bg-yellow-400': s.statusKey === 'pending',
                            'bg-purple-500': s.statusKey === 'warehouse',
                            'bg-blue-500': s.statusKey === 'transit',
                            'bg-indigo-500': s.statusKey === 'delivery',
                            'bg-green-500': s.statusKey === 'delivered',
                            'bg-red-400': s.statusKey === 'cancelled',
                        }"></div>
                        <div class="p-3">
                            <div class="flex justify-between items-start mb-1.5">
                                <span class="font-mono font-bold text-gray-900 dark:text-white text-[11px]">{{ s.id }}</span>
                                <span class="text-[9px] font-bold px-2 py-0.5 rounded-full" :class="statusClass(s.statusKey)">{{ s.status }}</span>
                            </div>
                            <div class="flex items-center gap-1 text-[11px] text-gray-500 dark:text-gray-400 mb-2">
                                <span class="font-medium text-gray-700 dark:text-gray-300 truncate">{{ s.origin }}</span>
                                <span class="material-symbols-outlined text-[12px] flex-shrink-0 text-blue-400">arrow_forward</span>
                                <span class="truncate">{{ s.destination }}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-[10px] text-gray-400 flex items-center gap-0.5">
                                    <span class="material-symbols-outlined text-[10px]">schedule</span> {{ s.eta }}
                                </span>
                                <span class="text-xs font-bold text-green-600 dark:text-green-400">₹{{ s.amount.toLocaleString() }}</span>
                            </div>
                            <!-- Progress bar -->
                            <div v-if="s.progress > 0 && s.statusKey !== 'delivered' && s.statusKey !== 'cancelled'" class="mt-2">
                                <div class="w-full h-1 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                                    <div class="h-full bg-blue-500 rounded-full transition-all" :style="{ width: s.progress + '%' }"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

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

                    <!-- Live Map -->
                    <div v-if="globalTab === 'map'" class="flex-1 glass-panel rounded-2xl overflow-hidden relative" style="min-height:500px;">
                        <!-- Real Leaflet Map -->
                        <l-map v-model:zoom="globalMapZoom" :center="globalMapCenter" :use-global-leaflet="false"
                            style="position:absolute; inset:0; height:100%; width:100%;">
                            <l-tile-layer
                                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                                layer-type="base"
                                name="CartoDB Voyager"
                            ></l-tile-layer>
                            <!-- Active driver markers -->
                            <l-marker v-for="d in activeDrivers" :key="'drv-' + d.order_id"
                                :lat-lng="[d.latitude, d.longitude]">
                                <l-popup>
                                    <div class="text-xs p-1">
                                        <div class="font-bold flex items-center gap-1 mb-1">
                                            <span class="material-symbols-outlined text-[14px] text-blue-500">local_shipping</span>
                                            {{ d.driver_name }}
                                        </div>
                                        <div class="text-gray-500 mb-0.5">Order: <span class="font-medium text-gray-800">{{ d.order_id }}</span></div>
                                        <div class="text-gray-500 mb-0.5">Vehicle: <span class="font-medium text-gray-800">{{ d.vehicle_code }}</span></div>
                                        <div class="mt-1 text-[9px] uppercase font-bold bg-blue-100 text-blue-700 rounded px-1.5 py-0.5 inline-block">{{ d.status }}</div>
                                    </div>
                                </l-popup>
                            </l-marker>
                        </l-map>
                        <!-- No drivers overlay -->
                        <div v-if="activeDrivers.length === 0" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style="z-index:500;">
                            <span class="material-symbols-outlined text-5xl text-gray-400/50 mb-2">location_off</span>
                            <p class="text-gray-400/70 text-sm font-medium">No active drivers on the road</p>
                        </div>
                        <!-- Fleet overlay -->
                        <div class="absolute top-4 right-4 bottom-16 w-52 bg-white/90 dark:bg-black/50 backdrop-blur-md rounded-xl border border-gray-200 dark:border-white/10 hidden md:flex flex-col overflow-hidden shadow-lg" style="z-index:1000;">
                            <div class="p-3 border-b border-gray-200 dark:border-white/10 flex items-center justify-between">
                                <span class="text-[10px] font-bold text-gray-900 dark:text-white uppercase tracking-wider">Active Fleet</span>
                                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            </div>
                            <div class="flex-1 overflow-y-auto p-2">
                                <div v-for="s in store.activeShipments.slice(0, 6)" :key="'fleet-'+s.id" @click="selected = s"
                                    class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 cursor-pointer transition-colors mb-1">
                                    <div class="flex justify-between items-center mb-0.5">
                                        <span class="text-[10px] font-mono font-bold text-blue-500 truncate">{{ s.id }}</span>
                                        <span class="text-[9px] px-1.5 bg-blue-500/10 text-blue-600 rounded font-bold flex-shrink-0">{{ s.progress }}%</span>
                                    </div>
                                    <div class="text-[9px] text-gray-500 truncate">→ {{ s.destination }}</div>
                                </div>
                                <div v-if="store.activeShipments.length === 0" class="text-center py-4 text-[10px] text-gray-400">No active shipments</div>
                            </div>
                            <div class="p-2 bg-blue-500/5 text-center text-[9px] text-gray-500 border-t border-gray-100 dark:border-white/10">
                                {{ store.activeShipments.length }} vehicles in motion
                            </div>
                        </div>
                        <!-- Legend -->
                        <div class="absolute bottom-4 left-4 right-4 md:right-60 bg-white/90 dark:bg-black/60 backdrop-blur-md p-3 rounded-xl border border-gray-200 dark:border-white/10 flex items-center justify-between" style="z-index:1000;">
                            <div>
                                <div class="text-[11px] font-bold text-gray-900 dark:text-white mb-1">Global Live Tracking</div>
                                <div class="flex items-center gap-3 text-[9px] text-gray-600 dark:text-gray-300">
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500 inline-block"></span> In-Transit</span>
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span> Origin</span>
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span> Destination</span>
                                </div>
                            </div>
                            <div v-if="mapAlertCount > 0" class="px-2 py-1 bg-yellow-500/10 rounded-lg flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-yellow-500 text-[14px]">warning</span>
                                <span class="text-[9px] font-bold text-yellow-600">{{ mapAlertCount }} Alert{{ mapAlertCount !== 1 ? 's' : '' }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- All Orders Table -->
                    <div v-if="globalTab === 'table'" class="flex-1 glass-panel rounded-2xl overflow-hidden flex flex-col">
                        <!-- Mini stats -->
                        <div class="grid grid-cols-4 divide-x divide-gray-100 dark:divide-white/5 border-b border-gray-100 dark:border-white/5">
                            <div class="p-4">
                                <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Total Valuation</div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">₹{{ (store.shipments.reduce((a, s) => a + s.amount, 0)).toLocaleString() }}</div>
                            </div>
                            <div class="p-4">
                                <div class="text-[9px] text-blue-500 uppercase font-bold mb-1">Active</div>
                                <div class="text-sm font-bold text-blue-600 dark:text-blue-400">{{ store.activeShipments.length }} shipments</div>
                            </div>
                            <div class="p-4">
                                <div class="text-[9px] text-green-500 uppercase font-bold mb-1">On-Time Rate</div>
                                <div class="text-sm font-bold text-green-600 dark:text-green-400">{{ store.analyticsData.onTime }}%</div>
                            </div>
                            <div class="p-4">
                                <div class="text-[9px] text-purple-500 uppercase font-bold mb-1">Avg Transit</div>
                                <div class="text-sm font-bold text-purple-600 dark:text-purple-400">{{ store.analyticsData.avgTransit }} days</div>
                            </div>
                        </div>
                        <div class="flex-1 overflow-auto">
                            <table class="w-full text-left text-sm min-w-[640px]">
                                <thead class="text-gray-500 dark:text-gray-400 uppercase text-[10px] border-b border-gray-100 dark:border-white/5 sticky top-0 bg-white dark:bg-card-dark z-10">
                                    <tr>
                                        <th class="px-5 py-3 font-semibold">Order ID</th>
                                        <th class="px-5 py-3 font-semibold">Route</th>
                                        <th class="px-5 py-3 font-semibold">Amount</th>
                                        <th class="px-5 py-3 font-semibold">ETA</th>
                                        <th class="px-5 py-3 font-semibold">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-50 dark:divide-white/5">
                                    <tr v-for="s in filteredShipments" :key="'tbl-'+s.id"
                                        @click="selected = s; detailTab = 'overview'"
                                        class="hover:bg-blue-50/50 dark:hover:bg-white/5 cursor-pointer transition-colors group">
                                        <td class="px-5 py-3 font-mono text-blue-500 text-xs font-bold group-hover:text-blue-600">{{ s.id }}</td>
                                        <td class="px-5 py-3">
                                            <div class="text-xs font-semibold text-gray-900 dark:text-white">{{ s.origin }}</div>
                                            <div class="text-[10px] text-gray-400 flex items-center gap-0.5 mt-0.5">
                                                <span class="material-symbols-outlined text-[10px]">arrow_forward</span> {{ s.destination }}
                                            </div>
                                        </td>
                                        <td class="px-5 py-3 font-bold text-green-600 dark:text-green-400 text-xs">₹{{ s.amount.toLocaleString() }}</td>
                                        <td class="px-5 py-3 text-gray-600 dark:text-gray-300 text-xs">{{ s.eta }}</td>
                                        <td class="px-5 py-3">
                                            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold" :class="statusClass(s.statusKey)">{{ s.status }}</span>
                                        </td>
                                    </tr>
                                    <tr v-if="filteredShipments.length === 0">
                                        <td colspan="5" class="px-5 py-12 text-center text-gray-400 text-sm">No shipments match</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Analytics -->
                    <div v-if="globalTab === 'graphs'" class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div class="glass-panel p-6 rounded-2xl flex flex-col">
                            <div class="flex items-center justify-between mb-5">
                                <h4 class="text-sm font-bold text-gray-900 dark:text-white">Spend Overview</h4>
                                <span class="text-[10px] font-bold text-blue-500 bg-blue-500/10 px-2 py-1 rounded-lg">Last 6 Months</span>
                            </div>
                            <div class="flex-1 relative min-h-[200px]"><Bar :data="spendChartData" :options="spendChartOptions" /></div>
                            <div class="mt-5 pt-4 border-t border-gray-100 dark:border-white/5 grid grid-cols-2 gap-4">
                                <div>
                                    <div class="text-[10px] text-gray-400 uppercase font-bold mb-1">Transit Efficiency</div>
                                    <div class="flex items-end gap-1">
                                        <div class="text-2xl font-black text-gray-900 dark:text-white">{{ store.analyticsData.onTime }}%</div>
                                        <span class="text-[10px] text-green-500 font-bold mb-0.5 flex items-center"><span class="material-symbols-outlined text-[12px]">trending_up</span>+1.2%</span>
                                    </div>
                                    <div class="text-[9px] text-gray-400">vs last month</div>
                                </div>
                                <div>
                                    <div class="text-[10px] text-gray-400 uppercase font-bold mb-1">Success Rate</div>
                                    <div class="text-2xl font-black text-gray-900 dark:text-white">{{ store.analyticsData.successRate }}%</div>
                                    <div class="flex items-end gap-0.5 mt-1.5">
                                        <div v-for="i in 5" :key="'spark-'+i" class="w-2.5 rounded-sm bg-blue-500/40" :style="{ height: (8 + i * 3) + 'px' }"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="glass-panel p-6 rounded-2xl flex flex-col">
                            <div class="flex items-center justify-between mb-5">
                                <h4 class="text-sm font-bold text-gray-900 dark:text-white">Volume Overview</h4>
                                <div class="flex items-center gap-1.5 text-[10px] text-gray-500">
                                    <div class="w-2 h-2 rounded-full bg-blue-500"></div> Daily Orders
                                </div>
                            </div>
                            <div class="flex-1 relative min-h-[160px] mb-4"><Line :data="volumeChartData" :options="volumeChartOptions" /></div>
                            <div class="space-y-2">
                                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">High Volume Routes</div>
                                <div v-if="topRoutes.length === 0" class="text-[10px] text-gray-400 text-center py-3">No route data yet</div>
                                <div v-for="r in topRoutes" :key="r.route"
                                    class="flex items-center justify-between p-2.5 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                                    <div class="flex items-center gap-2.5">
                                        <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 font-black text-[11px]">{{ r.rank }}</div>
                                        <div>
                                            <div class="text-[11px] font-bold text-gray-900 dark:text-white">{{ r.route }}</div>
                                            <div class="text-[9px] text-gray-400">{{ r.count }} trips</div>
                                        </div>
                                    </div>
                                    <div class="text-[11px] font-bold text-green-500">{{ r.onTime }}% on-time</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>

                <!-- ── Shipment selected: Detail view ── -->
                <template v-else>
                    <!-- Header bar -->
                    <div class="flex items-center justify-between gap-4 flex-wrap">
                        <div class="flex items-center gap-3">
                            <button @click="selected = null"
                                class="w-9 h-9 flex items-center justify-center rounded-xl bg-gray-100 dark:bg-white/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-gray-600 dark:text-gray-300 hover:text-blue-600 transition-colors">
                                <span class="material-symbols-outlined text-[20px]">arrow_back</span>
                            </button>
                            <div>
                                <div class="flex items-center gap-2">
                                    <span class="font-mono font-black text-gray-900 dark:text-white text-lg">{{ selected.id }}</span>
                                    <span class="px-3 py-1 rounded-full text-xs font-bold" :class="statusClass(selected.statusKey)">{{ selected.status }}</span>
                                </div>
                                <div class="text-xs text-gray-400 mt-0.5">{{ selected.route }}</div>
                            </div>
                        </div>
                        <!-- Actions -->
                        <div v-if="selected.statusKey !== 'delivered' && selected.statusKey !== 'cancelled'" class="flex items-center gap-2">
                            <!-- Update Address: hidden for recurring orders -->
                            <button v-if="!selected.isRecurring" @click="showAddressModal = true" class="px-3 py-1.5 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[15px]">edit_location</span> Update Address
                            </button>
                            <!-- Reschedule: hidden for recurring orders -->
                            <button v-if="!selected.isRecurring" @click="showRescheduleModal = true" class="px-3 py-1.5 bg-purple-50 dark:bg-purple-500/10 hover:bg-purple-100 text-purple-600 dark:text-purple-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[15px]">event</span> Reschedule
                            </button>
                            <button @click="showDamageModal = true" class="px-3 py-1.5 bg-orange-50 dark:bg-orange-500/10 hover:bg-orange-100 text-orange-600 dark:text-orange-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[15px]">report_problem</span> Report Issue
                            </button>
                            <button @click="handleCancel" class="px-3 py-1.5 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 text-red-600 dark:text-red-400 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5">
                                <span class="material-symbols-outlined text-[15px]">cancel</span> Cancel
                            </button>
                        </div>
                    </div>

                    <!-- Route Hero Card -->
                    <div class="glass-panel rounded-2xl overflow-hidden">
                        <!-- Map visualization - Real Leaflet Map -->
                        <div class="relative h-52 overflow-hidden">
                            <l-map :zoom="selectedMapZoom" :center="selectedMapCenter" :use-global-leaflet="false"
                                style="position:absolute; inset:0; height:100%; width:100%;">
                                <l-tile-layer
                                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                                    layer-type="base"
                                ></l-tile-layer>
                                <!-- Driver live position -->
                                <l-marker v-if="selectedHasLiveTracking && selected?.driverLat && selected?.driverLng"
                                    :lat-lng="[selected.driverLat, selected.driverLng]">
                                    <l-popup>
                                        <div class="text-xs p-1">
                                            <div class="font-bold flex items-center gap-1 mb-1">
                                                <span class="material-symbols-outlined text-[14px] text-blue-500">local_shipping</span>
                                                {{ selected.driver || 'Driver' }}
                                            </div>
                                            <div class="text-gray-500">Vehicle: <span class="font-medium text-gray-800">{{ selected.vehicle }}</span></div>
                                            <div class="mt-1 text-[9px] uppercase font-bold bg-blue-100 text-blue-700 rounded px-1.5 py-0.5 inline-block">{{ selectedDriverMapStatusLabel }}</div>
                                        </div>
                                    </l-popup>
                                </l-marker>
                            </l-map>
                            <div v-if="selectedIsDelivered" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none bg-slate-950/25" style="z-index:500;">
                                <span class="material-symbols-outlined text-3xl text-green-400/90 mb-1">verified</span>
                                <p class="text-green-100 text-xs font-semibold">Shipment delivered</p>
                                <p class="text-white/60 text-[11px] mt-1">Live route tracking has ended for this order</p>
                            </div>
                            <div v-else-if="selectedIsCancelled" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none bg-slate-950/25" style="z-index:500;">
                                <span class="material-symbols-outlined text-3xl text-red-300/80 mb-1">cancel</span>
                                <p class="text-red-100 text-xs font-semibold">Shipment cancelled</p>
                            </div>
                            <!-- No GPS fallback -->
                            <div v-else-if="!selectedHasLiveTracking" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style="z-index:500;">
                                <span class="material-symbols-outlined text-3xl text-gray-400/50 mb-1">gps_off</span>
                                <p class="text-gray-400/60 text-xs font-medium">Live GPS not available</p>
                            </div>
                            <!-- Origin label -->
                            <div class="absolute top-3 left-3" style="z-index:1000;">
                                <div class="bg-black/70 text-white text-[9px] px-2 py-1 rounded-lg whitespace-nowrap font-medium flex items-center gap-1.5 shadow">
                                    <span class="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></span>{{ selected.origin }}
                                </div>
                            </div>
                            <!-- Destination label -->
                            <div class="absolute top-3 right-3" style="z-index:1000;">
                                <div class="bg-black/70 text-white text-[9px] px-2 py-1 rounded-lg whitespace-nowrap font-medium flex items-center gap-1.5 shadow">
                                    {{ selected.destination }}<span class="w-2 h-2 bg-red-400 rounded-full flex-shrink-0"></span>
                                </div>
                            </div>
                            <!-- Arriving Soon badge -->
                            <div v-if="selected.progress >= 80 && selected.statusKey !== 'delivered'"
                                class="absolute bottom-3 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 animate-pulse shadow-lg shadow-green-500/30" style="z-index:1000;">
                                <span class="material-symbols-outlined text-sm">my_location</span>
                                Arriving in ~{{ Math.max(5, Math.round((100 - selected.progress) * 1.5)) }} min
                            </div>
                        </div>
                        <!-- Progress strip -->
                        <div class="px-6 py-4 flex items-center gap-4 border-t border-gray-100 dark:border-white/5">
                            <div class="flex-1">
                                <div class="flex items-center justify-between mb-1.5">
                                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400">Trip Progress</span>
                                    <span class="text-sm font-black text-blue-600 dark:text-blue-400">{{ selected.progress }}%</span>
                                </div>
                                <div class="w-full h-2.5 bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
                                    <div class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-700"
                                        :style="{ width: selected.progress + '%' }"></div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-[10px] text-gray-400 uppercase font-bold">ETA</div>
                                <div class="text-sm font-bold" :class="selectedEtaClass">{{ selectedEtaLabel }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Main content: single full-width column -->
                    <div class="space-y-4">

                        <!-- Row 1: Shipment Details + Driver side by side -->
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">

                            <!-- Shipment details -->
                            <div class="glass-panel rounded-2xl p-5">
                                <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">Shipment Details</h4>
                                <div class="space-y-3">
                                    <div class="rounded-2xl border border-green-100 dark:border-green-500/20 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-500/10 dark:to-emerald-500/10 p-4 sm:p-5 overflow-hidden">
                                        <div class="flex items-start justify-between gap-3">
                                            <div class="min-w-0">
                                                <div class="text-[10px] text-green-700 dark:text-green-400 uppercase font-bold tracking-[0.18em]">Shipment Amount</div>
                                                <div class="mt-2 text-[clamp(1.75rem,4vw,2.6rem)] font-black leading-none text-green-600 dark:text-green-400">
                                                    ₹{{ formatCurrencyAmount(selected.amount) }}
                                                </div>
                                            </div>
                                            <div class="w-11 h-11 rounded-2xl bg-white/80 dark:bg-white/10 border border-green-200/70 dark:border-green-400/20 flex items-center justify-center flex-shrink-0">
                                                <span class="material-symbols-outlined text-[20px] text-green-600 dark:text-green-400">account_balance_wallet</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                            <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Weight</div>
                                            <div class="text-lg font-bold text-gray-900 dark:text-white leading-tight">
                                                {{ formatMetricValue(selected.weight) }}<span class="text-xs font-medium text-gray-400 ml-1">kg</span>
                                            </div>
                                        </div>
                                        <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                            <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Pallets</div>
                                            <div class="text-lg font-bold text-gray-900 dark:text-white leading-tight">{{ formatMetricValue(selected.pallets) }}</div>
                                        </div>
                                        <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                            <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Payment</div>
                                            <div class="text-sm font-bold text-gray-900 dark:text-white leading-snug break-words">{{ selected.paymentMode }}</div>
                                        </div>
                                        <div class="min-w-0 p-3.5 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 flex items-start gap-3">
                                            <span class="material-symbols-outlined text-blue-400 text-[20px] mt-0.5">category</span>
                                            <div class="min-w-0">
                                                <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Category</div>
                                                <div class="text-sm font-semibold text-gray-900 dark:text-white leading-snug break-words">{{ selected.category }}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Driver card -->
                            <div v-if="selected.driver" class="glass-panel rounded-2xl p-5">
                                <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">Driver</h4>

                                <!-- Row 1: Avatar + Name/Vehicle/Status -->
                                <div class="flex items-center gap-4 mb-4">
                                    <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20 flex-shrink-0">
                                        <span class="material-symbols-outlined text-white text-[28px]">person</span>
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="font-bold text-gray-900 dark:text-white truncate">{{ selected.driver }}</div>
                                        <div class="flex items-center gap-1.5 mt-0.5 text-xs text-gray-400">
                                            <span class="material-symbols-outlined text-[13px]">directions_car</span>
                                            <span>{{ selected.vehicle || '—' }}</span>
                                        </div>
                                        <div class="flex items-center gap-1 mt-1.5">
                                            <span class="w-2 h-2 rounded-full" :class="selectedDriverStatus.dotClass"></span>
                                            <span class="text-[10px] font-bold" :class="selectedDriverStatus.textClass">{{ selectedDriverStatus.label }}</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Row 2: Phone + Call button -->
                                <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5">
                                    <div>
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Phone</div>
                                        <div class="text-sm font-bold text-gray-900 dark:text-white tracking-wide">
                                            {{ selected.driverPhone || '—' }}
                                        </div>
                                    </div>
                                    <button @click="showCallModal = true" :disabled="!canCallDriver"
                                        class="w-10 h-10 rounded-xl text-white transition-colors flex items-center justify-center shadow-md"
                                        :class="canCallDriver ? 'bg-green-500 hover:bg-green-600 shadow-green-500/20' : 'bg-gray-300 dark:bg-white/10 cursor-not-allowed shadow-none'"
                                        title="Call Driver">
                                        <span class="material-symbols-outlined text-[20px]">call</span>
                                    </button>
                                </div>
                            </div>
                            <!-- No driver placeholder to keep grid balanced -->
                            <div v-else class="glass-panel rounded-2xl p-5 flex items-center justify-center text-gray-400">
                                <div class="text-center">
                                    <span class="material-symbols-outlined text-3xl text-gray-300 block mb-1">person_off</span>
                                    <div class="text-xs">No driver assigned yet</div>
                                </div>
                            </div>
                        </div>

                        <!-- Row 2: Documents (full width) -->
                        <div class="glass-panel rounded-2xl p-5">
                            <div class="flex items-start justify-between gap-3 mb-3">
                                <div>
                                    <h4 class="text-sm font-bold text-gray-900 dark:text-white">Documents</h4>
                                    <p class="text-xs text-gray-400 mt-1">Only ready-to-download shipment documents are shown here.</p>
                                </div>
                            </div>
                            <div v-if="availableDocuments.length > 0" class="flex gap-3 flex-wrap">
                                <button v-for="doc in availableDocuments" :key="doc.key" @click="doc.action()"
                                    class="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 cursor-pointer transition-all group flex-1 min-w-[220px] text-left"
                                    :class="doc.hoverClass">
                                    <span class="material-symbols-outlined text-xl" :class="doc.iconClass">{{ doc.icon }}</span>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate">{{ doc.label }}</div>
                                        <div class="text-[10px] text-gray-400 mt-0.5 truncate">{{ doc.description }}</div>
                                    </div>
                                    <span class="material-symbols-outlined text-gray-400 text-sm transition-colors" :class="doc.downloadClass">download</span>
                                </button>
                            </div>
                            <div v-else class="rounded-xl border border-dashed border-gray-200 dark:border-white/10 bg-gray-50/60 dark:bg-white/5 px-4 py-5 text-sm text-gray-400">
                                No downloadable documents are available for this shipment yet.
                            </div>
                        </div>

                        <!-- Row 3: Transit Log — full width, horizontal scroll of steps -->
                        <div class="glass-panel rounded-2xl p-5">
                            <div class="flex items-center justify-between mb-5">
                                <div class="flex items-center gap-2">
                                    <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                        <span class="material-symbols-outlined text-blue-500 text-[15px]">timeline</span>
                                    </div>
                                    <h4 class="font-bold text-gray-900 dark:text-white text-sm">Transit Log</h4>
                                    <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                                </div>
                                <button class="text-xs font-bold text-blue-500 bg-blue-500/10 hover:bg-blue-500/20 px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-colors">
                                    <span class="material-symbols-outlined text-[13px]">download</span> Export
                                </button>
                            </div>

                            <div v-if="trackingLogs.length === 0" class="text-center py-8 text-gray-400 text-sm">
                                <span class="material-symbols-outlined text-3xl block mb-2 text-gray-300">history</span>
                                No status history yet
                            </div>

                            <!-- Horizontal step-by-step timeline -->
                            <div v-else class="overflow-x-auto pb-2">
                                <div class="flex items-start gap-0 min-w-max">
                                    <div v-for="(log, idx) in trackingLogs" :key="'log-'+idx" class="flex items-start">
                                        <!-- Step -->
                                        <div class="flex flex-col items-center w-40">
                                            <!-- Icon -->
                                            <div class="w-10 h-10 rounded-full flex items-center justify-center shadow-sm flex-shrink-0 transition-all"
                                                :class="log.isCurrent
                                                    ? 'bg-blue-500 shadow-blue-500/30 ring-4 ring-blue-500/20'
                                                    : 'bg-green-500 shadow-green-500/20'">
                                                <span class="material-symbols-outlined text-white text-[16px]">{{ log.icon }}</span>
                                            </div>
                                            <!-- Label -->
                                            <div class="mt-3 text-center px-2">
                                                <div class="text-xs font-bold leading-tight"
                                                    :class="log.isCurrent ? 'text-blue-600 dark:text-blue-400' : 'text-gray-800 dark:text-gray-200'">
                                                    {{ log.action }}
                                                </div>
                                                <div class="text-[10px] text-gray-400 mt-1 flex items-center justify-center gap-0.5">
                                                    <span class="material-symbols-outlined text-[10px]">location_on</span>
                                                    <span class="truncate max-w-[100px]">{{ log.location }}</span>
                                                </div>
                                                <div class="text-[9px] text-gray-400 mt-0.5">{{ log.date }} {{ log.time }}</div>
                                                <div v-if="log.isCurrent" class="mt-1.5 inline-flex items-center gap-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-[9px] font-bold px-2 py-0.5 rounded-full">
                                                    <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                                                    Now
                                                </div>
                                            </div>
                                        </div>
                                        <!-- Connector line between steps -->
                                        <div v-if="idx < trackingLogs.length - 1"
                                            class="flex-shrink-0 flex items-center mt-5">
                                            <div class="w-8 h-px bg-gray-200 dark:bg-white/10"></div>
                                            <span class="material-symbols-outlined text-gray-300 dark:text-white/20 text-[14px]">chevron_right</span>
                                            <div class="w-8 h-px bg-gray-200 dark:bg-white/10"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- PoD (if delivered) -->
                        <div v-if="selected.pod && selected.pod.confirmed" class="glass-panel rounded-2xl p-5">
                            <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
                                <span class="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
                                    <span class="material-symbols-outlined text-green-500 text-[16px]">verified</span>
                                </span>
                                Proof of Delivery
                            </h4>
                            <div class="grid grid-cols-1 gap-4">
                                <div class="space-y-2">
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Timestamp</div>
                                        <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.timestamp }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Location</div>
                                        <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.location }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Received By</div>
                                        <div class="text-xs font-medium text-gray-900 dark:text-white">{{ selected.pod.signedBy || 'Receiver' }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Recipient Signature</div>
                                        <div v-if="selected.pod.signature && !podSignatureBroken" class="mt-2 h-20 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-slate-950/60 overflow-hidden flex items-center justify-center">
                                            <img :src="selected.pod.signature" alt="Recipient signature" class="max-h-full max-w-full object-contain" @error="podSignatureBroken = true">
                                        </div>
                                        <div v-else class="text-xs text-gray-400">No signature was uploaded for this delivery.</div>
                                    </div>
                                    <div v-if="selected.pod.notes" class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="text-[9px] text-gray-400 uppercase font-bold mb-0.5">Notes</div>
                                        <div class="text-xs font-medium text-gray-900 dark:text-white whitespace-pre-line">{{ selected.pod.notes }}</div>
                                    </div>
                                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                        <div class="flex items-start justify-between gap-3">
                                            <div>
                                                <div class="text-[9px] text-gray-400 uppercase font-bold mb-1">Delivery Rating</div>
                                                <div v-if="selected.customerRating" class="flex items-center gap-1.5">
                                                    <span v-for="n in 5" :key="`pod-rating-${n}`" class="text-base"
                                                        :class="n <= selected.customerRating ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
                                                    <span class="text-xs font-semibold text-gray-700 dark:text-gray-200 ml-1">{{ Number(selected.customerRating).toFixed(1) }}/5.0</span>
                                                </div>
                                                <div v-else class="text-xs text-gray-400">No delivery rating has been submitted yet.</div>
                                            </div>
                                            <button v-if="!selected.customerRating" @click="openVendorRatingModal(selected)"
                                                class="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 text-[11px] font-bold transition-colors">
                                                Rate Delivery
                                            </button>
                                        </div>
                                        <div v-if="selected.customerFeedback" class="mt-2 text-xs text-gray-600 dark:text-gray-300 whitespace-pre-line">
                                            {{ selected.customerFeedback }}
                                        </div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button @click="openSlipWithData('proofOfDelivery', selected, currentUser())"
                                            class="flex-1 flex items-center justify-center gap-1.5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-xs font-bold transition-colors">
                                            <span class="material-symbols-outlined text-[14px]">verified</span> Download PoD
                                        </button>
                                        <button @click="openSlipWithData('finalTaxInvoice', selected, currentUser())"
                                            class="flex-1 flex items-center justify-center gap-1.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors">
                                            <span class="material-symbols-outlined text-[14px]">request_quote</span> Tax Invoice
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

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

        <!-- Address Update Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showAddressModal" @close="showAddressModal = false">
                <template #title>Update Delivery Address</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current Address</label>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                            {{
                                selected?.destination }}</div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Address *</label>
                        <input v-model="newAddress" type="text" placeholder="Enter new delivery address"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                </div>
                <template #footer>
                    <button @click="showAddressModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="updateAddress" :disabled="!newAddress.trim()"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Update
                        Address</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Reschedule Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showRescheduleModal" @close="showRescheduleModal = false">
                <template #title>Reschedule Delivery</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Current ETA</label>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm text-gray-600 dark:text-gray-300">
                            {{
                                selected?.eta }}</div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">New Delivery Date *</label>
                        <input v-model="newDate" type="date"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Reason</label>
                        <textarea v-model="rescheduleReason" rows="2" placeholder="Optional reason"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                </div>
                <template #footer>
                    <button @click="showRescheduleModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="reschedule" :disabled="!newDate"
                        class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-bold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Reschedule</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Damage Report Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showDamageModal" @close="showDamageModal = false">
                <template #title>Report Damage / Issue</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Severity *</label>
                        <div class="flex gap-3">
                            <label v-for="sev in ['Low', 'Medium', 'High']" :key="sev"
                                class="flex-1 text-center px-3 py-2 rounded-lg border cursor-pointer text-sm font-medium transition-colors"
                                :class="damageForm.severity === sev ? severityClass(sev) : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400'">
                                <input type="radio" :value="sev" v-model="damageForm.severity" class="sr-only">{{ sev }}
                            </label>
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description *</label>
                        <textarea v-model="damageForm.description" rows="3"
                            placeholder="Describe the damage or issue..."
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Upload Evidence</label>
                        <div
                            class="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition-colors">
                            <span class="material-symbols-outlined text-3xl text-gray-400 mb-2">cloud_upload</span>
                            <div class="text-xs text-gray-500">Click to upload photos</div>
                        </div>
                    </div>
                </div>
                <template #footer>
                    <button @click="showDamageModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitDamage" :disabled="!damageForm.description.trim()"
                        class="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-bold hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Submit
                        Report</button>
                </template>
            </BaseModal>
        </Teleport>
        <!-- Support Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showSupportModal" @close="showSupportModal = false">
                <template #title>Contact Support</template>
                <div class="space-y-4">
                    <p class="text-sm text-gray-600 dark:text-gray-300">Our team is available 24/7 to help you with shipment <span class="font-bold">{{ selected?.id }}</span>.</p>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">How can we help?</label>
                        <textarea v-model="supportMessage" rows="4" placeholder="Describe the issue you're facing..."
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                    </div>
                </div>
                <template #footer>
                    <button @click="showSupportModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="submitSupport" :disabled="!supportMessage.trim()"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                        Send Message</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Driver Rating Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="vendorRatingModal.show" @close="vendorRatingModal.show = false">
                <template #title>Rate Your Driver</template>
                <div class="space-y-4 text-center">
                    <p class="text-sm text-gray-500 dark:text-gray-400">How was your delivery experience? (optional)</p>
                    <div class="flex justify-center gap-2">
                        <span v-for="n in 5" :key="n"
                            @click="vendorRatingModal.selected = n"
                            @mouseenter="vendorRatingModal.hover = n"
                            @mouseleave="vendorRatingModal.hover = 0"
                            class="text-4xl cursor-pointer transition-colors select-none"
                            :class="(vendorRatingModal.hover || vendorRatingModal.selected) >= n ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
                    </div>
                    <textarea v-model="vendorRatingModal.feedback" rows="2" placeholder="Leave a comment (optional)"
                        class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-400/50 outline-none resize-none"></textarea>
                </div>
                <template #footer>
                    <div class="flex gap-3 w-full">
                        <button @click="submitVendorRating" :disabled="!vendorRatingModal.selected"
                            class="flex-1 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 text-sm font-bold disabled:opacity-40">
                            Submit Rating
                        </button>
                        <button @click="vendorRatingModal.show = false"
                            class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm">
                            Skip
                        </button>
                    </div>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Driver Call Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showCallModal" @close="showCallModal = false">
                <template #title>Contact Driver</template>
                <div class="flex flex-col items-center justify-center p-6 space-y-4">
                    <div class="w-20 h-20 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 shadow-inner">
                        <span class="material-symbols-outlined text-4xl">person</span>
                    </div>
                    <div class="text-center">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ selected?.driver || 'Driver Name' }}</h3>
                        <p class="text-sm text-gray-500">{{ selected?.vehicle || 'Vehicle Number' }}</p>
                    </div>
                    <div class="w-full bg-gray-50 dark:bg-black/20 rounded-lg border border-gray-200 dark:border-white/10 p-4 text-center mt-4">
                        <div class="text-xs text-gray-500 uppercase font-bold mb-1">Direct Line</div>
                        <div class="text-2xl font-bold text-gray-900 dark:text-white tracking-wider flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-green-500">phone_iphone</span>
                            {{ selected?.driverPhone || '+1 (555) 000-0000' }}
                        </div>
                    </div>
                </div>
                <template #footer>
                    <button @click="showCallModal = false" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    <a v-if="canCallDriver" :href="`tel:${selected?.driverPhone?.replace(/\s+/g, '')}`"
                        class="px-8 py-2 bg-green-500 text-white rounded-lg text-sm font-bold hover:bg-green-600 transition-colors flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">call</span> Call Now
                    </a>
                    <span v-else class="px-8 py-2 bg-gray-200 dark:bg-white/10 text-gray-500 rounded-lg text-sm font-bold flex items-center gap-2 cursor-not-allowed">
                        <span class="material-symbols-outlined text-[18px]">call</span> No Phone
                    </span>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Driver Chat Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showChatModal" @close="showChatModal = false">
                <template #title>
                    <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500">
                           <span class="material-symbols-outlined text-xs">person</span>
                        </div>
                        Chat with {{ selected?.driver?.split(' ')[0] || 'Driver' }}
                    </div>
                </template>
                
                <div class="flex flex-col h-[400px] -mx-6 -mt-4 -mb-6 bg-gray-50 dark:bg-black/20">
                    <!-- Chat Messages Area -->
                    <div class="flex-1 overflow-y-auto p-4 space-y-4">
                        <!-- System Message -->
                        <div class="flex justify-center">
                            <span class="text-[10px] font-bold text-gray-400 bg-gray-200 dark:bg-white/5 px-3 py-1 rounded-full">
                                Shipment {{ selected?.id }} Dispatch Chat Start
                            </span>
                        </div>
                        
                        <!-- Mock Driver Message -->
                        <div class="flex items-end gap-2">
                            <div class="w-8 h-8 rounded-full bg-blue-500/20 flex-shrink-0 flex items-center justify-center text-blue-500">
                                <span class="material-symbols-outlined text-sm">person</span>
                            </div>
                            <div class="bg-white dark:bg-card-dark border border-gray-100 dark:border-white/5 rounded-2xl rounded-bl-sm p-3 max-w-[80%] shadow-sm">
                                <p class="text-sm text-gray-800 dark:text-gray-200">Hi, I have picked up the shipment and am en route. Traffic is light so I should arrive close to the ETA.</p>
                                <div class="text-[9px] text-gray-400 mt-1 text-right">10:45 AM</div>
                            </div>
                        </div>

                        <!-- User Messages -->
                        <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex justify-end items-end gap-2">
                            <div class="bg-blue-600 rounded-2xl rounded-br-sm p-3 max-w-[80%] shadow-sm text-white">
                                <p class="text-sm">{{ msg.text }}</p>
                                <div class="text-[9px] text-blue-200 mt-1 flex justify-end items-center gap-1">
                                    {{ msg.time }}
                                    <span class="material-symbols-outlined text-[10px]">done_all</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Input Area -->
                    <div class="p-3 bg-white dark:bg-card-dark border-t border-gray-200 dark:border-white/10">
                        <form @submit.prevent="sendChatMessage" class="flex items-center gap-2 relative">
                            <input type="file" ref="fileInput" class="hidden" @change="handleFileUpload" accept="image/*,.pdf,.doc,.docx" />
                            <button type="button" @click="$refs.fileInput.click()" class="p-2 text-gray-400 hover:text-blue-500 transition-colors tooltip-trigger relative group">
                                <span class="material-symbols-outlined text-[20px]">attach_file</span>
                                <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-30 font-bold pointer-events-none">Attach File</div>
                            </button>
                            <input v-model="newChatMessage" type="text" placeholder="Type your message..." 
                                class="flex-1 bg-gray-100 dark:bg-black/20 border border-transparent rounded-full px-4 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:bg-white dark:focus:bg-card-dark focus:border-blue-500 transition-all">
                            <button type="submit" :disabled="!newChatMessage.trim()"
                                class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                                <span class="material-symbols-outlined text-[18px]">send</span>
                            </button>
                        </form>
                    </div>
                </div>
                
                <template #footer>
                    <!-- Replacing default footer to ensure clean edge with the chat input box -->
                    <span class="hidden"></span>
                </template>
            </BaseModal>
        </Teleport>

    </div>
</template>

<script setup>
import TrackingStatsBar from './tracking/TrackingStatsBar.vue'
import { ref, computed, reactive, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { useRealTimeTracking } from '@/composables/useRealTimeTracking'
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
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
  Filler
} from 'chart.js'
import { Bar, Line } from 'vue-chartjs'
import {
    formatLogDate,
    formatLogTime,
    formatCurrencyAmount,
    formatMetricValue,
} from './tracking/trackingFormat'

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

// Modals
const showAddressModal = ref(false)
const showRescheduleModal = ref(false)
const showDamageModal = ref(false)
const showSupportModal = ref(false)
const showCallModal = ref(false)
const showChatModal = ref(false)
const newAddress = ref('')
const newDate = ref('')
const rescheduleReason = ref('')
const supportMessage = ref('')
const newChatMessage = ref('')
const chatMessages = ref([])
const fileInput = ref(null)
const damageForm = reactive({ severity: 'Medium', description: '' })
const vendorRatingModal = reactive({ show: false, order: null, selected: 0, hover: 0, feedback: '' })
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
const selectedHasLiveTracking = computed(() => {
    if (!selected.value || selectedIsDelivered.value || selectedIsCancelled.value) return false
    const lat = Number(selected.value.driverLat)
    const lng = Number(selected.value.driverLng)
    return Number.isFinite(lat) && Number.isFinite(lng)
})
const selectedMapCenter = computed(() =>
    selectedHasLiveTracking.value
        ? [Number(selected.value.driverLat), Number(selected.value.driverLng)]
        : [20.5937, 78.9629]
)
const selectedEtaLabel = computed(() => {
    if (selectedIsDelivered.value) return 'Delivered'
    if (selectedIsCancelled.value) return 'Cancelled'
    return selected.value?.eta || 'TBD'
})
const selectedEtaClass = computed(() => {
    if (selectedIsDelivered.value) return 'text-green-600 dark:text-green-400'
    if (selectedIsCancelled.value) return 'text-red-600 dark:text-red-400'
    return 'text-blue-600 dark:text-blue-400'
})
const selectedDriverStatus = computed(() => {
    if (selectedIsDelivered.value) {
        return {
            label: 'Trip Completed',
            dotClass: 'bg-green-500',
            textClass: 'text-green-500',
        }
    }
    if (selectedIsCancelled.value) {
        return {
            label: 'Assignment Closed',
            dotClass: 'bg-red-500',
            textClass: 'text-red-500',
        }
    }
    return {
        label: 'Active · On Route',
        dotClass: 'bg-green-500 animate-pulse',
        textClass: 'text-green-500',
    }
})
const selectedDriverMapStatusLabel = computed(() => {
    if (selectedIsDelivered.value) return 'Delivered'
    if (selectedIsCancelled.value) return 'Cancelled'
    return 'In Transit'
})
const canCallDriver = computed(() => Boolean(String(selected.value?.driverPhone || '').trim()))
const podSignatureBroken = ref(false)

watch(selected, () => {
    podSignatureBroken.value = false
})

const availableDocuments = computed(() => {
    if (!selected.value) return []

    const user = currentUser()
    const docs = [
        {
            key: 'bookingConfirmation',
            label: SLIP_LABELS.bookingConfirmation,
            description: 'Booking summary and shipment details',
            icon: SLIP_ICONS.bookingConfirmation,
            iconClass: 'text-indigo-500',
            hoverClass: 'hover:border-indigo-300 dark:hover:border-indigo-500/30',
            downloadClass: 'group-hover:text-indigo-500',
            action: () => openSlipWithData('bookingConfirmation', selected.value, user),
        },
    ]

    if (selected.value.statusKey === 'delivered') {
        docs.push(
            {
                key: 'proofOfDelivery',
                label: SLIP_LABELS.proofOfDelivery,
                description: selected.value.pod?.photoCount
                    ? `${selected.value.pod.photoCount} proof file${selected.value.pod.photoCount === 1 ? '' : 's'} recorded`
                    : 'Delivery confirmation slip',
                icon: SLIP_ICONS.proofOfDelivery,
                iconClass: 'text-green-500',
                hoverClass: 'hover:border-green-300 dark:hover:border-green-500/30',
                downloadClass: 'group-hover:text-green-500',
                action: () => openSlipWithData('proofOfDelivery', selected.value, user),
            },
            {
                key: 'finalTaxInvoice',
                label: SLIP_LABELS.finalTaxInvoice,
                description: 'Final billing document for this shipment',
                icon: SLIP_ICONS.finalTaxInvoice,
                iconClass: 'text-blue-500',
                hoverClass: 'hover:border-blue-300 dark:hover:border-blue-500/30',
                downloadClass: 'group-hover:text-blue-500',
                action: () => openSlipWithData('finalTaxInvoice', selected.value, user),
            }
        )
    }

    return docs
})

// Transport Log — real status history from backend
const STATUS_ICONS = {
    'Order Placed':    'shopping_cart',
    'Confirmed':       'verified',
    'In Warehouse':    'warehouse',
    'Awaiting Pick':   'inventory_2',
    'Picking':         'forklift',
    'Picked':          'check_circle',
    'Packing':         'inventory',
    'Packed':          'deployed_code',
    'QC Passed':       'fact_check',
    'In Transit':      'local_shipping',
    'Out for Delivery':'two_wheeler',
    'Delivered':       'done_all',
    'Cancelled':       'cancel',
}
function statusIcon(label) {
    for (const [key, icon] of Object.entries(STATUS_ICONS)) {
        if (label && label.toLowerCase().includes(key.toLowerCase())) return icon
    }
    return 'radio_button_checked'
}
const trackingLogs = computed(() => {
    if (!selected.value) return []
    const history = selected.value.statusHistory || []
    if (history.length > 0) {
        return history.slice().reverse().map((step, idx) => ({
            action: step.status,
            location: idx === 0
                ? (selected.value.statusKey === 'delivered' ? selected.value.destination : selected.value.route || '—')
                : selected.value.origin,
            date: formatLogDate(step.time),
            time: formatLogTime(step.time),
            icon: statusIcon(step.status),
            isCurrent: idx === 0,
        }))
    }
    // Fallback: single entry based on current status
    return [{
        action: selected.value.status,
        location: selected.value.route || '—',
        date: 'Today',
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        icon: statusIcon(selected.value.status),
        isCurrent: true,
    }]
})

// Driver actions
function sendChatMessage() {
    if (!newChatMessage.value.trim()) return
    chatMessages.value.push({
        text: newChatMessage.value,
        time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    })
    newChatMessage.value = ''
    
    // Auto reply mock
    setTimeout(() => {
        showToast('Driver received your message')
    }, 1500)
}

function handleFileUpload(event) {
    const file = event.target.files[0]
    if (!file) return
    
    // Create a mock chat message with the file
    chatMessages.value.push({
        text: `📎 Attached: ${file.name}`,
        time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    })
    
    // Reset file input
    event.target.value = ''
    showToast('File attached successfully')
}

function submitSupport() {
    if (!selected.value || !supportMessage.value.trim()) return
    store.addTicket({
        subject: `Support needed for ${selected.value.id}`,
        description: supportMessage.value,
        orderId: selected.value.id,
        priority: 'Medium'
    })
    showSupportModal.value = false
    supportMessage.value = ''
    showToast('Support ticket created successfully')
}

// Analytics Charts (Chart.js)
const primaryColor = '#3b82f6' // blue-500

const spendChartData = computed(() => {
  const months = store.analyticsData.monthly.map(m => m.month)
  const spends = store.analyticsData.monthly.map(m => m.spend)
  return {
    labels: months,
    datasets: [{
      label: 'Monthly Spend (₹)',
      data: spends,
      backgroundColor: primaryColor + '40', // 25% opacity
      borderColor: primaryColor,
      borderWidth: 2,
      borderRadius: 4,
      hoverBackgroundColor: primaryColor + '80'
    }]
  }
})

const spendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1f2937',
      padding: 10,
      cornerRadius: 4,
      displayColors: false,
      callbacks: {
        label: (context) => `₹${context.raw.toLocaleString()}`
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: 'rgba(156, 163, 175, 0.1)' },
      ticks: {
        callback: (value) => '₹' + (value / 1000) + 'k',
        font: { size: 10 }
      }
    },
    x: {
      grid: { display: false },
      ticks: { font: { size: 10 } }
    }
  }
}

const volumeChartData = computed(() => {
  const monthly = store.analyticsData.monthly
  return {
    labels: monthly.map(m => m.month),
    datasets: [{
        label: 'Orders',
        data: monthly.map(m => m.orders),
        borderColor: primaryColor,
        backgroundColor: primaryColor + '20',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: primaryColor,
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
    }]
  }
})

const mapAlertCount = computed(() =>
    store.overdueInvoices.length + store.shipments.filter(s => s.statusKey === 'cancelled').length
)

const topRoutes = computed(() => {
    const map = {}
    store.shipments.forEach(s => {
        if (s.origin && s.destination) {
            const key = `${s.origin} → ${s.destination}`
            if (!map[key]) map[key] = { route: key, count: 0, delivered: 0 }
            map[key].count++
            if (s.statusKey === 'delivered') map[key].delivered++
        }
    })
    return Object.values(map)
        .sort((a, b) => b.count - a.count)
        .slice(0, 3)
        .map((r, i) => ({
            ...r,
            rank: String(i + 1).padStart(2, '0'),
            onTime: r.count > 0 ? Math.round((r.delivered / r.count) * 100) : 0,
        }))
})

const volumeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: '#1f2937',
            padding: 10,
            displayColors: false
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: { color: 'rgba(156, 163, 175, 0.1)' },
            ticks: { font: { size: 10 } }
        },
        x: {
            grid: { display: false },
            ticks: { font: { size: 10 } }
        }
    }
}

const filteredShipments = computed(() => {
    let list = store.shipments
    if (statusFilter.value !== 'all') list = list.filter(s => s.statusKey === statusFilter.value)
    if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(s => s.id.toLowerCase().includes(q) || s.destination.toLowerCase().includes(q) || s.route.toLowerCase().includes(q))
    }
    return list
})

const statusClass = k => ({
    pending: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    warehouse: 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
    transit: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    delivery: 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-400',
    delivered: 'bg-green-500/20 text-green-600 dark:text-green-400',
    cancelled: 'bg-red-500/20 text-red-600 dark:text-red-400',
}[k] || 'bg-gray-500/20 text-gray-500')

const severityClass = sev => ({
    Low: 'border-yellow-500 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
    Medium: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400',
    High: 'border-red-500 bg-red-500/10 text-red-600 dark:text-red-400',
}[sev])

async function updateAddress() {
    if (!selected.value || !newAddress.value.trim()) return
    await store.updateShipmentAddress(selected.value.id, newAddress.value.trim())
    showAddressModal.value = false
    newAddress.value = ''
    showToast('Address updated successfully')
}

async function reschedule() {
    if (!selected.value || !newDate.value) return
    const formatted = new Date(newDate.value).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
    await store.rescheduleShipment(selected.value.id, formatted)
    showRescheduleModal.value = false
    newDate.value = ''
    rescheduleReason.value = ''
    showToast('Delivery rescheduled')
}

async function handleCancel() {
    if (!selected.value) return
    if (confirm(`Cancel shipment ${selected.value.id}? This action cannot be undone.`)) {
        await store.cancelShipment(selected.value.id)
        showToast('Shipment cancelled')
    }
}

async function submitDamage() {
    if (!selected.value || !damageForm.description.trim()) return
    await store.reportDamage(selected.value.id, { ...damageForm, photos: [] })
    showDamageModal.value = false
    damageForm.severity = 'Medium'
    damageForm.description = ''
    showToast('Damage report submitted — reverse logistics ticket created')
}

function openVendorRatingModal(shipment = selected.value) {
    if (!shipment) return
    Object.assign(vendorRatingModal, {
        show: true,
        order: shipment,
        selected: Number(shipment.customerRating || 0),
        hover: 0,
        feedback: shipment.customerFeedback || '',
    })
}

async function submitVendorRating() {
    if (!vendorRatingModal.selected || !vendorRatingModal.order?.backendId) return
    const result = await store.submitCustomerRating(
        vendorRatingModal.order.backendId,
        vendorRatingModal.selected,
        vendorRatingModal.feedback || null
    )
    vendorRatingModal.show = false
    showToast(
        result.success ? 'Thanks for rating your driver!' : (result.message || 'Failed to submit rating.'),
        result.success ? 'success' : 'error'
    )
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    const bg = type === 'error' ? 'bg-red-500' : 'bg-green-500'
    t.className = `fixed right-4 bottom-4 z-[9999] ${bg} text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}


</script>
