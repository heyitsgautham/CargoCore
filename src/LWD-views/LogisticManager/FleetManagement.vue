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

        <!-- Tab Content: Active Drivers -->
        <div v-if="activeTab === 'Active Drivers'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <!-- Driver Scorecard -->
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Driver Roster & Performance</h3>
                <div class="space-y-4 overflow-y-auto pr-2 flex-grow custom-scrollbar">
                    <div v-for="driver in searchedDrivers" :key="driver.id"
                        class="flex items-center gap-4 p-3 rounded-lg border transition-colors shadow-sm"
                        :class="driver.dispatcherSuspended
                            ? 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/20'
                            : 'bg-gray-50 dark:bg-white/5 border-transparent'">
                        <!-- Avatar with suspended ring -->
                        <div class="relative shrink-0">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm"
                                :class="driver.dispatcherSuspended ? 'bg-red-700 opacity-60' : driver.avatarColor">
                                {{ driver.name.charAt(0) }}
                            </div>
                            <span v-if="driver.dispatcherSuspended"
                                class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-red-500 border-2 border-white dark:border-gray-900 flex items-center justify-center"
                                title="Suspended by Dispatcher">
                                <span class="material-symbols-outlined text-white" style="font-size:8px">block</span>
                            </span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between items-center gap-2">
                                <span class="font-bold text-sm truncate"
                                    :class="driver.dispatcherSuspended ? 'text-red-700 dark:text-red-400' : 'text-gray-900 dark:text-white'">
                                    {{ driver.name }}
                                </span>
                                <div class="flex items-center gap-1.5 shrink-0">
                                    <!-- Dispatcher suspended badge -->
                                    <span v-if="driver.dispatcherSuspended"
                                        class="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400 border border-red-300 dark:border-red-500/30 flex items-center gap-1">
                                        <span class="material-symbols-outlined" style="font-size:10px">block</span>
                                        Suspended
                                    </span>
                                    <!-- Normal status badge -->
                                    <span v-else class="text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wider"
                                        :class="driver.status === 'active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-400'">
                                        {{ driver.status }}
                                    </span>
                                </div>
                            </div>
                            <div class="text-xs mt-0.5 flex items-center gap-2 flex-wrap"
                                :class="driver.dispatcherSuspended ? 'text-red-400/70 dark:text-red-400/50' : 'text-gray-500 dark:text-gray-400'">
                                <span v-if="driver.dispatcherSuspended" class="font-semibold text-red-500 dark:text-red-400/80">Blocked from dispatch</span>
                                <template v-else>
                                    <span class="font-medium text-green-600 dark:text-green-400">{{ driver.efficiency }}% eff.</span>
                                    <span v-if="driver.rating" class="text-yellow-500">★ {{ Number(driver.rating).toFixed(1) }}</span>
                                    <span class="text-gray-300 dark:text-gray-600">•</span>
                                    <span class="font-medium text-primary truncate">{{ store.hubs.find(h => h.id === driver.hubId)?.name || 'Main Hub' }}</span>
                                    <span class="text-gray-300 dark:text-gray-600">•</span>
                                    <span class="truncate">{{ driver.currentJob || 'Standby' }}</span>
                                </template>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Top Driver Stats -->
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Top Leaderboard</h3>
                <div class="space-y-4 overflow-y-auto pr-2 flex-grow custom-scrollbar">
                    <div v-for="driver in searchedTopDrivers" :key="driver.id"
                        class="flex items-center gap-4 p-3 rounded-lg border transition-colors shadow-sm"
                        :class="driver.dispatcherSuspended
                            ? 'bg-red-50 dark:bg-red-500/5 border-red-200 dark:border-red-500/20'
                            : 'bg-gray-50 dark:bg-white/5 border-transparent'">
                        <!-- Avatar -->
                        <div class="relative shrink-0">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm"
                                :class="driver.dispatcherSuspended ? 'bg-red-700 opacity-60' : (driver.avatarColor || 'bg-gray-600')">
                                {{ (driver.name || '?').charAt(0) }}
                            </div>
                            <span v-if="driver.dispatcherSuspended"
                                class="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-red-500 border-2 border-white dark:border-gray-900 flex items-center justify-center">
                                <span class="material-symbols-outlined text-white" style="font-size:8px">block</span>
                            </span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between items-center gap-2">
                                <span class="font-bold text-sm truncate"
                                    :class="driver.dispatcherSuspended ? 'text-red-700 dark:text-red-400' : 'text-gray-900 dark:text-white'">
                                    {{ driver.name }}
                                </span>
                                <!-- Suspended overrides rating badge -->
                                <span v-if="driver.dispatcherSuspended"
                                    class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400 border border-red-300 dark:border-red-500/30 shrink-0 flex items-center gap-1">
                                    <span class="material-symbols-outlined" style="font-size:10px">block</span>
                                    Suspended
                                </span>
                                <span v-else
                                    class="text-yellow-500 dark:text-yellow-400 font-bold text-sm bg-yellow-50 dark:bg-yellow-500/10 px-2 py-0.5 rounded-full border border-yellow-200 dark:border-yellow-500/20 shrink-0">
                                    ★ {{ driver.rating }}
                                </span>
                            </div>
                            <div class="text-xs mt-1"
                                :class="driver.dispatcherSuspended ? 'text-red-400/70 dark:text-red-400/50' : 'text-gray-500 dark:text-gray-400'">
                                <span v-if="driver.dispatcherSuspended" class="font-semibold text-red-500 dark:text-red-400/80">Blocked from dispatch</span>
                                <template v-else>
                                    {{ driver.trips }} trips •
                                    <span class="font-medium"
                                        :class="driver.ontime > 95 ? 'text-green-500 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                                        {{ driver.ontime }}% On-time
                                    </span>
                                </template>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab Content: Fleet Vehicles -->
        <div v-if="activeTab === 'Fleet Vehicles'" class="flex flex-col gap-6">
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">Vehicle Roster</h3>
                <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                            <tr
                                class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                <th class="py-2 px-2 font-medium">Vehicle ID</th>
                                <th class="py-2 font-medium">Warehouse</th>
                                <th class="py-2 font-medium">Type / Model</th>
                                <th class="py-2 font-medium">Driver</th>
                                <th class="py-2 font-medium text-right">Status</th>
                                <th class="py-2 px-2 text-right"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="vehicle in searchedVehicles" :key="vehicle.id"
                                @click.stop="openVehicleProfile(vehicle)"
                                class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer relative">
                                <td class="py-3 px-2 text-gray-700 dark:text-white font-mono font-medium">{{ vehicle.id
                                }}<br /><span class="text-[10px] text-gray-500">{{ vehicle.licensePlate }}</span>
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                    {{ store.hubs.find(h => h.id === vehicle.hubId)?.name || 'Main Hub' }}
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300">{{ vehicle.type }}<br /><span
                                        class="text-xs text-gray-400">{{ vehicle.model }} ({{ vehicle.year }})</span>
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium">{{ vehicle.driver }}</td>
                                <td class="py-3 text-right">
                                    <span
                                        class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
                                        :class="vehicle.status === 'Active' ? 'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-500' :
                                            (vehicle.status === 'In Shop' ? 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-500' : 'bg-yellow-50 border-yellow-200 text-yellow-600 dark:bg-yellow-500/10 dark:border-yellow-500/20 dark:text-yellow-500')">
                                        {{ vehicle.status }}
                                    </span>
                                </td>
                                <td class="py-3 px-2 text-right relative">
                                    <button @click.stop="toggleVehicleDropdown(vehicle.id)"
                                        class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white cursor-pointer transition-colors p-1 rounded-full hover:bg-gray-100 dark:hover:bg-white/10">
                                        <span class="material-symbols-outlined">more_vert</span>
                                    </button>

                                    <!-- Action Dropdown for Vehicles -->
                                    <div v-if="activeDropdown === vehicle.id" @click.stop
                                        class="absolute right-6 top-10 w-40 bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-xl shadow-lg z-50 py-1 overflow-hidden">
                                        <button @click="openVehicleModal('edit', vehicle); activeDropdown = null"
                                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                                            <span class="material-symbols-outlined text-[18px]">edit</span> Edit Details
                                        </button>
                                        <button
                                            @click="store.updateVehicleStatus(vehicle.id, vehicle.status === 'Active' ? 'In Shop' : 'Active'); activeDropdown = null"
                                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                                            <span class="material-symbols-outlined text-[18px]">engineering</span>
                                            Toggle Status
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Maintenance Alerts -->
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden">
                <div class="absolute top-0 right-0 p-6 opacity-5 dark:opacity-10 pointer-events-none">
                </div>
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0 z-10">Pending Maintenance</h3>
                <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar z-10">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                            <tr
                                class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                <th class="py-2 px-2 font-medium">Vehicle ID</th>
                                <th class="py-2 font-medium">Issue / Description</th>
                                <th class="py-2 font-medium">Warehouse</th>
                                <th class="py-2 font-medium">Type / Model</th>
                                <th class="py-2 font-medium text-right">Approx Cost</th>
                                <th class="py-2 font-medium text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="issue in searchedMaintenance" :key="issue.id"
                                class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer relative"
                                @click="openVehicleProfile(store.filteredVehicles.find(v => v.id === issue.id), 'history')">
                                <td class="py-3 px-2 text-gray-700 dark:text-white font-mono font-medium">
                                    {{ store.filteredVehicles.find(v => v.id === issue.id)?.code || store.filteredVehicles.find(v => v.id === issue.id)?.id || issue.id }}<br />
                                    <span class="text-[10px] text-gray-500">
                                        {{ store.filteredVehicles.find(v => v.id === issue.id)?.licensePlate || 'N/A' }}
                                    </span>
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium">
                                    {{ issue.issue }}
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                    {{ store.hubs.find(h => h.id === issue.hubId)?.name || 'Main Hub' }}
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300">
                                    <div class="font-medium text-gray-900 dark:text-white">
                                        {{ store.filteredVehicles.find(v => v.id === issue.id)?.type || '—' }}
                                    </div>
                                    <div class="text-[10px] text-gray-500">
                                        {{ store.filteredVehicles.find(v => v.id === issue.id)?.model || '—' }}
                                        <template v-if="store.filteredVehicles.find(v => v.id === issue.id)?.year">({{ store.filteredVehicles.find(v => v.id === issue.id)?.year }})</template>
                                    </div>
                                </td>
                                <td class="py-3 text-right text-gray-600 dark:text-gray-300 font-mono">
                                    {{ maintenanceCost(issue.id) }}
                                </td>
                                <td class="py-3 text-right">
                                    <span
                                        class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
                                        :class="issue.statusClass">{{ issue.status }}</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Tab Content: Fuel Logs (New) -->
        <!-- Tab Content: Fleet Logs (Dynamic) -->
        <div v-if="activeTab === 'Fleet Logs'" class="grid grid-cols-1 lg:grid-cols-3 gap-6 text-sm">
            <!-- Left Panel: Dynamic Stats & Selector -->
            <div class="glass-panel rounded-xl p-6 lg:col-span-1 border border-gray-200 dark:border-white/5 h-[500px] flex flex-col">
                <div class="mb-6">
                    <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Select Log Category</label>
                    <div class="relative">
                        <select v-model="activeLogType" class="w-full appearance-none bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white font-bold rounded-lg py-3 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow cursor-pointer">
                            <option v-for="type in logTypes" :key="type" :value="type" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ type }}</option>
                        </select>
                        <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">expand_more</span>
                    </div>
                </div>

                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2 flex-shrink-0">
                    <span class="material-symbols-outlined" :class="`text-${logStats.color}-500`">{{ logStats.icon }}</span>
                    {{ logStats.title }}
                </h3>
                
                <div class="space-y-4 overflow-y-auto custom-scrollbar pr-2">
                    <div class="p-4 rounded-xl border" 
                        :class="`bg-${logStats.color}-50 dark:bg-${logStats.color}-500/10 border-${logStats.color}-100 dark:border-${logStats.color}-500/20`">
                        <p class="text-xs uppercase font-bold tracking-wider mb-1" :class="`text-${logStats.color}-600 dark:text-${logStats.color}-400`">Total Cost (This Month)</p>
                        <p class="text-2xl font-bold text-gray-900 dark:text-white">₹{{ logStats.totalCost.toLocaleString(undefined, {minimumFractionDigits: 2}) }}</p>
                        <p class="text-xs mt-1 opacity-80" :class="`text-${logStats.color}-600 dark:text-${logStats.color}-400`">↑ 2.4% vs last month</p>
                    </div>

                     <div class="grid grid-cols-2 gap-4">
                        <div v-for="(tile, idx) in logStats.tiles" :key="idx" class="bg-gray-50 dark:bg-white/5 p-4 rounded-xl">
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">{{ tile.label }}</p>
                            <p class="text-lg font-bold text-gray-900 dark:text-white">{{ tile.value }}</p>
                        </div>
                    </div>
                    
                    <div class="p-4 border-t border-gray-100 dark:border-white/5 mt-4">
                        <p class="text-xs text-gray-500 uppercase font-bold tracking-wider mb-2">{{ logStats.trend.label }}</p>
                        <div class="w-full bg-gray-200 dark:bg-white/10 rounded-full h-2 mb-1">
                            <div class="h-2 rounded-full" :class="`bg-${logStats.color}-500`" :style="`width: ${logStats.trend.pct}%`"></div>
                        </div>
                        <div class="flex justify-between text-xs text-gray-500">
                            <span>{{ logStats.trend.value }}</span>
                            <span>Target: {{ logStats.trend.target }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Panel: Data Table -->
            <div class="glass-panel rounded-xl p-6 lg:col-span-2 border border-gray-200 dark:border-white/5 h-[500px] flex flex-col relative overflow-hidden">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex-shrink-0">{{ activeLogType }} Overview</h3>
                <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                            <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                <th class="py-2 px-2 font-medium">Date</th>
                                <th class="py-2 font-medium">Vehicle ID</th>
                                <th class="py-2 font-medium">Warehouse</th>
                                
                                <!-- Dynamic Headers -->
                                <th v-if="activeLogType === 'Fuel Logs'" class="py-2 font-medium">Station</th>
                                <th v-if="activeLogType === 'Fuel Logs'" class="py-2 font-medium text-right">Gallons</th>
                                
                                <th v-if="activeLogType === 'Service Logs'" class="py-2 font-medium">Service</th>
                                <th v-if="activeLogType === 'Service Logs'" class="py-2 font-medium">Provider</th>

                                <th v-if="activeLogType === 'Maintenance Logs'" class="py-2 font-medium">Issue</th>
                                <th v-if="activeLogType === 'Maintenance Logs'" class="py-2 font-medium">Mechanic</th>

                                <th v-if="activeLogType === 'Cleaning Logs'" class="py-2 font-medium">Type</th>
                                <th v-if="activeLogType === 'Cleaning Logs'" class="py-2 font-medium">Provider</th>

                                <th class="py-2 font-medium text-right">Cost</th>
                                <th class="py-2 font-medium text-right">Status</th>
                            </tr>
                        </thead>
                       <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="log in searchedLogs" :key="log.id" 
                                class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
                                @click="openVehicleProfile(store.filteredVehicles.find(v => v.id === log.vehicleId), 'history')">
                                
                                <td class="py-3 px-2 text-gray-600 dark:text-gray-300 font-mono">{{ log.date }}</td>
                                <td class="py-3 text-gray-900 dark:text-white font-medium">{{ log.vehicleId }}</td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                    {{ store.hubs.find(h => h.id === log.hubId)?.name || 'Main Hub' }}
                                </td>

                                <!-- Dynamic Cells -->
                                <td v-if="activeLogType === 'Fuel Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.station }}</td>
                                <td v-if="activeLogType === 'Fuel Logs'" class="py-3 text-gray-600 dark:text-gray-300 text-right">{{ log.gallons }}</td>

                                <td v-if="activeLogType === 'Service Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.service }}</td>
                                <td v-if="activeLogType === 'Service Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.provider }}</td>

                                <td v-if="activeLogType === 'Maintenance Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.issue }}</td>
                                <td v-if="activeLogType === 'Maintenance Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.mechanic }}</td>

                                <td v-if="activeLogType === 'Cleaning Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.type }}</td>
                                <td v-if="activeLogType === 'Cleaning Logs'" class="py-3 text-gray-600 dark:text-gray-300">{{ log.provider }}</td>

                                <td class="py-3 text-gray-900 dark:text-white font-bold text-right">₹{{ log.cost }}</td>
                                <td class="py-3 text-right">
                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border" 
                                        :class="log.status === 'Completed' || log.status === 'Verified' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400'">
                                        {{ log.alert ? 'Anomaly' : (log.status || 'Verified') }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Tab Content: Vehicle Documents -->
        <div v-if="activeTab === 'Vehicle Documents'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden col-span-2">
                <div class="flex justify-between items-center mb-4 flex-shrink-0">
                <h3 class="font-bold text-gray-900 dark:text-white">Vehicle Documentation & Compliance</h3>
                <button @click="openUploadModal('VEHICLE')" class="bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-md shadow-primary/20 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">upload_file</span> Upload Doc
                </button>
            </div>
                <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                    <table class="w-full text-left text-sm">
                         <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                            <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                <th class="py-2 px-2 font-medium">Vehicle ID</th>
                                <th class="py-2 font-medium">Warehouse</th>
                                <th class="py-2 font-medium">Doc Types</th>
                                <th class="py-2 font-medium">Next Expiry</th>
                                <th class="py-2 font-medium">Status Overview</th>
                                <th class="py-2 px-2 text-right">View</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <template v-for="(docs, vehicleId) in groupedVehicleDocs" :key="vehicleId">
                                <!-- Parent Row -->
                                <tr class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer" @click="toggleDocExpand(vehicleId)">
                                    <td class="py-3 px-2 text-gray-900 dark:text-white font-mono font-medium flex items-center gap-2">
                                        <span class="material-symbols-outlined text-gray-400 text-sm transition-transform duration-200" :class="expandedDocs.includes(vehicleId) ? 'rotate-90' : ''">chevron_right</span>
                                        {{ docs[0]?.vehicleCode && docs[0].vehicleCode !== 'N/A' ? docs[0].vehicleCode : vehicleId }}
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                        {{ store.hubs.find(h => h.id === docs[0]?.hubId)?.name || 'Main Hub' }}
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300">
                                        <div class="flex flex-wrap gap-1">
                                            <span v-for="type in [...new Set(docs.map(d => d.type))].slice(0, 2)" :key="type" class="text-[10px] bg-gray-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300">
                                                {{ type }}
                                            </span>
                                            <span v-if="[...new Set(docs.map(d => d.type))].length > 2" class="text-[10px] text-gray-400">+{{ [...new Set(docs.map(d => d.type))].length - 2 }}</span>
                                        </div>
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300 font-mono text-xs">
                                        {{ docs.map(d => d.expiry).sort((a,b) => new Date(a) - new Date(b))[0] }}
                                    </td>
                                    <td class="py-3">
                                        <div class="flex gap-2 items-center">
                                            <span v-if="docs.some(d => new Date(d.expiry) < new Date())" class="w-2 h-2 rounded-full bg-red-500" title="Expired Doc"></span>
                                            <span v-else-if="docs.some(d => d.status === 'Expiring Soon')" class="w-2 h-2 rounded-full bg-yellow-500" title="Expiring Soon"></span>
                                            <span v-else class="w-2 h-2 rounded-full bg-green-500" title="All Good"></span>
                                            <span class="text-xs text-gray-500 dark:text-gray-400">
                                                {{ docs.some(d => new Date(d.expiry) < new Date()) ? 'Action Required' : (docs.some(d => d.status === 'Expiring Soon') ? 'Renew Soon' : 'Compliant') }}
                                            </span>
                                        </div>
                                    </td>
                                    <td class="py-3 px-2 text-right">
                                        <button @click.stop="toggleDocExpand(vehicleId)" class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white p-1 rounded-full transition-colors hover:bg-gray-100 dark:hover:bg-white/10">
                                            <span class="material-symbols-outlined">expand_circle_down</span>
                                        </button>
                                    </td>
                                </tr>
                                <!-- Child Rows (Dropdown) -->
                                <tr v-if="expandedDocs.includes(vehicleId)" class="bg-gray-50/50 dark:bg-white/5">
                                    <td colspan="5" class="p-0">
                                        <div class="px-4 py-2 border-l-2 border-primary ml-6 my-2 space-y-2">
                                            <div v-for="doc in docs" :key="doc.id" class="flex justify-between items-center p-2 rounded-lg hover:bg-white dark:hover:bg-white/5 border border-transparent hover:border-gray-200 dark:hover:border-white/10 transition-colors">
                                                <div class="flex items-center gap-3">
                                                    <span class="material-symbols-outlined text-gray-400">description</span>
                                                    <div>
                                                        <p class="text-sm font-medium text-gray-900 dark:text-white">{{ doc.type }}</p>
                                                        <p class="text-[10px] text-gray-500">Exp: {{ doc.expiry }}</p>
                                                    </div>
                                                </div>
                                                <div class="flex items-center gap-4">
                                                     <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border"
                                                        :class="doc.status === 'Active' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : (doc.status === 'Expiring Soon' ? 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400' : (doc.status === 'Pending Verification' ? 'bg-orange-50 text-orange-600 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400' : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400'))">
                                                        {{ doc.status }}
                                                    </span>
                                                    <button @click.stop="openDocModal(doc)" class="text-primary hover:text-primary/80 font-medium text-xs flex items-center gap-1 bg-primary/10 px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors">
                                                        <span class="material-symbols-outlined text-[14px]">visibility</span> View
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Tab Content: Driver Documents -->
        <div v-if="activeTab === 'Driver Documents'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden col-span-2">
            <div class="flex justify-between items-center mb-4 flex-shrink-0">
                <h3 class="font-bold text-gray-900 dark:text-white">Driver Personnel Files</h3>
                <button @click="openUploadModal('DRIVER')" class="bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-md shadow-primary/20 flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">upload_file</span> Upload Doc
                </button>
            </div>
                 <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                    <table class="w-full text-left text-sm">
                         <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                            <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                <th class="py-2 px-2 font-medium">Driver Name</th>
                                <th class="py-2 font-medium">Warehouse</th>
                                <th class="py-2 font-medium">Files on Record</th>
                                <th class="py-2 font-medium">Next Expiry</th>
                                <th class="py-2 font-medium">Compliance Status</th>
                                <th class="py-2 px-2 text-right">View</th>
                            </tr>
                        </thead>
                       <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <template v-for="driverGroup in groupedDriverDocs" :key="driverGroup.id">
                                <!-- Parent Row -->
                                <tr class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer" @click="toggleDocExpand(driverGroup.id)">
                                    <td class="py-3 px-2 flex items-center gap-3">
                                        <span class="material-symbols-outlined text-gray-400 text-sm transition-transform duration-200" :class="expandedDocs.includes(driverGroup.id) ? 'rotate-90' : ''">chevron_right</span>
                                        <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-600 dark:text-gray-300">
                                            {{ driverGroup.name.charAt(0) }}
                                        </div>
                                        <span class="text-gray-900 dark:text-white font-medium">{{ driverGroup.name }}</span>
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                        {{ store.hubs.find(h => h.id === driverGroup.docs[0]?.hubId)?.name || 'Main Hub' }}
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300">
                                        <div class="flex flex-wrap gap-1">
                                            <span v-for="doc in driverGroup.docs.slice(0, 2)" :key="doc.id" class="text-[10px] bg-gray-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300 truncate max-w-[100px]">
                                                {{ doc.type }}
                                            </span>
                                            <span v-if="driverGroup.docs.length > 2" class="text-[10px] text-gray-400">+{{ driverGroup.docs.length - 2 }}</span>
                                        </div>
                                    </td>
                                    <td class="py-3 text-gray-600 dark:text-gray-300 text-xs">
                                        {{ driverGroup.docs.map(d => d.expiry).sort((a,b) => new Date(a) - new Date(b))[0] }}
                                    </td>
                                    <td class="py-3">
                                          <div class="flex gap-2 items-center">
                                            <span v-if="driverGroup.docs.some(d => new Date(d.expiry) < new Date())" class="w-2 h-2 rounded-full bg-red-500" title="Expired Doc"></span>
                                            <span v-else-if="driverGroup.docs.some(d => d.status === 'Expiring Soon')" class="w-2 h-2 rounded-full bg-yellow-500" title="Expiring Soon"></span>
                                            <span v-else class="w-2 h-2 rounded-full bg-green-500" title="All Good"></span>
                                            <span class="text-xs text-gray-500 dark:text-gray-400">
                                                {{ driverGroup.docs.some(d => new Date(d.expiry) < new Date()) ? 'Action Required' : (driverGroup.docs.some(d => d.status === 'Expiring Soon') ? 'Renew Soon' : 'Compliant') }}
                                            </span>
                                        </div>
                                    </td>
                                    <td class="py-3 px-2 text-right">
                                         <button @click.stop="toggleDocExpand(driverGroup.id)" class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white p-1 rounded-full transition-colors hover:bg-gray-100 dark:hover:bg-white/10">
                                            <span class="material-symbols-outlined">expand_circle_down</span>
                                        </button>
                                    </td>
                                </tr>
                                <!-- Child Rows -->
                                <tr v-if="expandedDocs.includes(driverGroup.id)" class="bg-gray-50/50 dark:bg-white/5">
                                    <td colspan="5" class="p-0">
                                        <div class="px-4 py-2 border-l-2 border-primary ml-10 my-2 space-y-2">
                                            <div v-for="doc in driverGroup.docs" :key="doc.id" class="flex justify-between items-center p-2 rounded-lg hover:bg-white dark:hover:bg-white/5 border border-transparent hover:border-gray-200 dark:hover:border-white/10 transition-colors">
                                                <div class="flex items-center gap-3">
                                                    <span class="material-symbols-outlined text-gray-400">badge</span>
                                                    <div>
                                                        <p class="text-sm font-medium text-gray-900 dark:text-white">{{ doc.type }}</p>
                                                        <p class="text-[10px] text-gray-500">ID: {{ doc.licenseNo }}</p>
                                                    </div>
                                                </div>
                                                <div class="flex items-center gap-4">
                                                    <div class="text-right">
                                                        <p class="text-[10px] text-gray-400">Expiry</p>
                                                        <p class="text-xs font-medium" :class="new Date(doc.expiry) < new Date() ? 'text-red-500' : 'text-gray-900 dark:text-white'">{{ doc.expiry }}</p>
                                                    </div>
                                                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border"
                                                        :class="doc.status === 'Active' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : (doc.status === 'Expiring Soon' ? 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400' : (doc.status === 'Pending Verification' ? 'bg-orange-50 text-orange-600 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400' : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400'))">
                                                        {{ doc.status }}
                                                    </span>
                                                    <button @click.stop="openDocModal(doc)" class="text-primary hover:text-primary/80 font-medium text-xs flex items-center gap-1 bg-primary/10 px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors">
                                                        <span class="material-symbols-outlined text-[14px]">visibility</span> View
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Tab Content: Live Locations -->
        <div v-if="activeTab === 'Live Locations'" class="flex flex-col gap-4">

            <!-- Driver List -->
            <div class="glass-panel rounded-xl p-5 border border-gray-200 dark:border-white/5">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm">Active Driver Locations</h3>
                    <span class="text-xs text-gray-500">{{ wsConnected ? 'Live via WebSocket' : 'Polling every 30s' }}</span>
                </div>
                <div v-if="liveDrivers.length === 0" class="text-center py-8 text-gray-400 text-sm">
                    <span class="material-symbols-outlined block text-3xl mb-2">signal_disconnected</span>
                    No live GPS data. Drivers need to start a shift on the driver app.
                </div>
                <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div v-for="d in liveDrivers" :key="d.driver_id"
                        class="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-white/5 border border-transparent hover:border-primary/30 transition-colors cursor-pointer"
                        @click="selectedFleetDriver = d">
                        <div class="w-9 h-9 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                            <span class="material-symbols-outlined text-green-500 text-[18px]">local_shipping</span>
                        </div>
                        <div class="min-w-0 flex-1">
                            <p class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ d.driver_name }}</p>
                            <p class="text-[10px] text-gray-500">{{ d.vehicle_code || 'No vehicle' }}</p>
                            <p class="text-[10px] text-primary truncate">
                                {{ liveDriverLocation(d) }}
                            </p>
                        </div>
                        <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase flex-shrink-0"
                            :class="d.status === 'in-transit' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400' : 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400'">
                            {{ d.status }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ======================= MODALS AND SLIDEOVERS ======================= -->

        <!-- Add/Edit Vehicle Modal -->
        <Teleport to="body">
            <div v-if="isVehicleModalOpen"
                class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
                @click.self="closeVehicleModal">
                <div :class="vehicleModalMode === 'add' ? 'max-w-[800px]' : 'max-w-md'"
                    class="lm-vehicle-modal bg-slate-950/98 w-full rounded-2xl shadow-2xl border border-white/10 overflow-hidden flex flex-col max-h-[90vh] backdrop-blur-xl">
                    <div
                        class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                        <h3 class="text-lg font-bold text-white">{{ vehicleModalMode === 'add' ? `Add
                            New Vehicle` : `Edit Vehicle` }}</h3>
                        <button @click="closeVehicleModal"
                            class="text-gray-400 hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-6 overflow-y-auto bg-slate-950/95 text-slate-200" :class="vehicleModalMode === 'add' ? 'grid grid-cols-1 md:grid-cols-2 gap-8' : 'space-y-4'">
                        <!-- Left Column: Vehicle Details -->
                        <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Vehicle
                                    ID</label>
                                <input v-model="vehicleFormData.id" :disabled="vehicleModalMode === 'edit'"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 disabled:opacity-50">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">License
                                    Plate</label>
                                <input v-model="vehicleFormData.licensePlate"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type /
                                Model</label>
                            <input v-model="vehicleFormData.model" placeholder="e.g. Ford Transit (2022)"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                        </div>

                        <div v-if="vehicleModalMode === 'add'">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hub
                                Assignment</label>
                            <div class="relative">
                                <select v-model="vehicleFormData.hubId"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                                    <option value="all" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Global (All Warehouses)</option>
                                    <option v-for="h in store.hubs" :key="h.id" :value="h.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ h.name }}</option>
                                </select>
                            </div>
                        </div>

                        </div> <!-- End Left Column -->

                        <!-- Right Column: Required Documentation Section -->
                        <div v-if="vehicleModalMode === 'add'" class="space-y-6 bg-slate-900/70 p-5 rounded-2xl border border-white/10">
                            <h4 class="text-xs font-bold text-slate-300 uppercase tracking-wider">Required Documents</h4>
                            
                            <!-- Insurance Policy -->
                            <div class="space-y-3">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-gray-400 text-sm">verified_user</span>
                                    <p class="text-sm font-medium text-gray-900 dark:text-white">Insurance Policy</p>
                                </div>
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <label class="block text-xs font-medium text-slate-300 mb-1">Expiry Date</label>
                                        <input type="date" v-model="vehicleFormData.insuranceExpiry" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-xs font-medium text-slate-300 mb-1">Policy Document</label>
                                        <label class="w-full flex items-center justify-center gap-2 cursor-pointer bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg px-3 py-2 text-xs font-bold text-primary transition-colors h-[38px]">
                                            <span class="material-symbols-outlined text-[16px]">cloud_upload</span>
                                            <span class="truncate">{{ vehicleFormData.insuranceFileName || 'Upload PDF/IMG' }}</span>
                                            <input type="file" class="hidden" accept="image/*,.pdf" @change="e => handleVehicleDocUpload(e, 'insurance')">
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <!-- Vehicle Registration -->
                            <div class="space-y-3">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-gray-400 text-sm">assignment</span>
                                    <p class="text-sm font-medium text-gray-900 dark:text-white">Vehicle Registration</p>
                                </div>
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <label class="block text-xs font-medium text-slate-300 mb-1">Expiry Date</label>
                                        <input type="date" v-model="vehicleFormData.registrationExpiry" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-xs font-medium text-slate-300 mb-1">Registration Document</label>
                                        <label class="w-full flex items-center justify-center gap-2 cursor-pointer bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg px-3 py-2 text-xs font-bold text-primary transition-colors h-[38px]">
                                            <span class="material-symbols-outlined text-[16px]">cloud_upload</span>
                                            <span class="truncate">{{ vehicleFormData.registrationFileName || 'Upload PDF/IMG' }}</span>
                                            <input type="file" class="hidden" accept="image/*,.pdf" @change="e => handleVehicleDocUpload(e, 'registration')">
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div
                        class="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/90">
                        <button @click="closeVehicleModal"
                            class="px-4 py-2 rounded-lg font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 dark:bg-white/10 dark:border-white/10 dark:text-gray-200 dark:hover:bg-white/15 transition-colors shadow-sm">Cancel</button>
                        <button @click="submitVehicle" :disabled="isSubmitting"
                            class="px-4 py-2 rounded-lg font-medium text-white flex items-center justify-center gap-2 min-w-[120px] bg-primary hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-75 disabled:cursor-not-allowed">
                            <span v-if="isSubmitting" class="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin"></span>
                            <span>{{ vehicleModalMode === 'add' ? (isSubmitting ? 'Uploading...' : 'Add Vehicle') : 'Save Changes' }}</span>
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>


        <!-- Vehicle Profile Modal -->
        <Teleport to="body">
            <div v-if="activeVehicleProfile"
                class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
                @click.self="closeVehicleProfile">
                <div
                    class="bg-white dark:bg-card-dark w-full max-w-2xl rounded-2xl shadow-2xl border border-gray-200 dark:border-white/10 overflow-hidden flex flex-col">
                    <div
                        class="px-6 py-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-gray-400">local_shipping</span>
                            <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ activeVehicleProfile.id }}
                                Overview</h3>
                        </div>
                        <button @click="closeVehicleProfile"
                            class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-6">
                        <div v-if="activeVehicleProfile.viewMode === 'full'">
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                                <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                    <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Status</p>
                                    <span class="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider"
                                        :class="activeVehicleProfile.status === 'Active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-500' : 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-500'">
                                        {{ activeVehicleProfile.status }}
                                    </span>
                                </div>
                                <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                    <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Model /
                                        Year</p>
                                    <p class="text-sm font-bold text-gray-900 dark:text-white">{{ activeVehicleProfile.model
                                    }} ({{ activeVehicleProfile.year }})</p>
                                </div>
                                <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                    <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Current
                                        Odometer</p>
                                    <p class="text-sm font-bold text-gray-900 dark:text-white">{{
                                        activeVehicleProfile.mileage.toLocaleString() }} mi</p>
                                </div>
                                <div class="bg-gray-50 dark:bg-black/20 rounded-xl p-4">
                                    <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Assigned
                                        Driver</p>
                                    <p class="text-sm font-bold text-gray-900 dark:text-white">{{
                                        activeVehicleProfile.driver }}</p>
                                </div>
                            </div>


                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <!-- Left: Spec & Metrics -->
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white mb-3">Vehicle Metrics</h4>
                                    <div class="space-y-3">
                                        <div
                                            class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                            <span class="text-gray-500">License Plate</span>
                                            <span class="font-medium text-gray-900 dark:text-white">{{
                                                activeVehicleProfile.licensePlate }}</span>
                                        </div>
                                        <div
                                            class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                            <span class="text-gray-500">Vehicle Type</span>
                                            <span class="font-medium text-gray-900 dark:text-white">{{
                                                activeVehicleProfile.type }}</span>
                                        </div>
                                        <div
                                            class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                            <span class="text-gray-500">Avg Fuel Efficiency</span>
                                            <span class="font-medium text-gray-900 dark:text-white">{{
                                                activeVehicleProfile.fuelEfficiency }}</span>
                                        </div>
                                        <div
                                            class="flex justify-between text-sm py-2 border-b border-gray-100 dark:border-white/5">
                                            <span class="text-gray-500">Total Repair Expense</span>
                                            <span class="font-medium text-gray-900 dark:text-white">
                                                ₹{{ activeVehicleProfile.totalMaintenanceCost.toLocaleString() }} (YTD)
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Right: Service Logs -->
                                <div>
                                    <div class="flex justify-between items-center mb-3">
                                        <h4 class="font-bold text-gray-900 dark:text-white">Recent Service</h4>
                                        <span class="text-xs text-primary font-bold">Next: {{
                                            activeVehicleProfile.nextService }}</span>
                                    </div>
                                    <div class="space-y-3">
                                        <div v-for="log in activeVehicleProfile.serviceHistory.slice(0, 2)" :key="log.id" class="p-3 border border-gray-200 dark:border-white/10 rounded-lg">
                                            <div class="flex justify-between items-center mb-1">
                                                <span class="text-sm font-bold text-gray-900 dark:text-white">{{ log.service }}</span>
                                                <span class="text-xs text-gray-500">{{ log.date }}</span>
                                            </div>
                                            <div class="flex justify-between items-center">
                                                <span
                                                    class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300">{{ log.type }}</span>
                                                <span class="text-xs font-mono font-bold text-gray-900 dark:text-white">₹{{ log.cost }}</span>
                                            </div>
                                        </div>
                                        <button @click="activeVehicleProfile.viewMode = 'history'" class="w-full text-center text-xs text-primary hover:underline mt-2">View Full History</button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- History Mode View -->
                        <div v-else-if="activeVehicleProfile.viewMode === 'history'" class="flex flex-col h-full">
                            <div class="flex items-center justify-between mb-4">
                                <h4 class="font-bold text-gray-900 dark:text-white">Full Service Ledger</h4>
                                <div class="bg-gray-100 dark:bg-white/5 px-3 py-1 rounded-lg">
                                    <span class="text-xs text-gray-500 uppercase font-bold mr-2">Total Cost</span>
                                    <span class="font-mono font-bold text-gray-900 dark:text-white">₹{{ activeVehicleProfile.totalMaintenanceCost.toLocaleString() }}</span>
                                </div>
                            </div>
                            
                            <div class="overflow-y-auto max-h-[400px] border rounded-lg border-gray-200 dark:border-white/10">
                                <table class="w-full text-left text-sm">
                                    <thead class="bg-gray-50 dark:bg-white/5 sticky top-0 backdrop-blur-md">
                                        <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                            <th class="py-2 px-3 font-medium">Date</th>
                                            <th class="py-2 px-3 font-medium">Service Performed</th>
                                            <th class="py-2 px-3 font-medium">Description</th>
                                            <th class="py-2 px-3 font-medium text-right">Cost</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                        <tr v-for="item in activeVehicleProfile.serviceHistory" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                            <td class="py-3 px-3 text-gray-600 dark:text-gray-300 font-mono text-xs">{{ item.date }}</td>
                                            <td class="py-3 px-3 text-gray-900 dark:text-white font-medium">{{ item.service }}</td>
                                            <td class="py-3 px-3">
                                                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider" 
                                                    :class="item.type === 'Routine' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-500' : 'bg-yellow-50 text-yellow-600 dark:bg-yellow-500/10 dark:text-yellow-500'">
                                                    {{ item.type }}
                                                </span>
                                            </td>
                                            <td class="py-3 px-3 text-right text-gray-900 dark:text-white font-mono font-bold">₹{{ item.cost.toFixed(2) }}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <button @click="activeVehicleProfile.viewMode = 'full'" class="mt-4 flex items-center gap-2 text-primary hover:underline text-sm font-medium">
                                <span class="material-symbols-outlined text-sm">arrow_back</span> Back to Overview
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Document Viewer Modal -->
        <Teleport to="body">
            <div v-if="activeDoc"
                class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
                @click.self="closeDocModal">
                <div class="bg-white dark:bg-card-dark w-full max-w-3xl rounded-2xl shadow-2xl border border-gray-200 dark:border-white/10 overflow-hidden flex flex-col h-[80vh]">
                    <div class="px-6 py-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-primary">description</span>
                            <div>
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ activeDoc.type }}</h3>
                                <p class="text-xs text-gray-500">
                                    {{ activeDoc.vehicleId ? `Vehicle: ${activeDoc.vehicleId}` : `Driver: ${activeDoc.driver}` }}
                                </p>
                            </div>
                        </div>
                        <button @click="closeDocModal"
                            class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    
                    <div class="flex-1 bg-gray-100 dark:bg-black/50 overflow-hidden relative flex items-center justify-center p-4">
                        <!-- Mock Doc Viewer -->
                        <div class="bg-white shadow-lg p-2 max-h-full overflow-y-auto">
                            <img :src="activeDoc.url" class="max-w-full object-contain" alt="Document Preview"/>
                        </div>
                        <div class="absolute bottom-6 bg-black/60 backdrop-blur-md px-4 py-2 rounded-full text-white text-sm flex gap-4">
                            <button @click="downloadDoc(activeDoc)" class="hover:text-primary transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">download</span> Download</button>
                            <span class="w-px h-4 bg-white/20 my-auto"></span>
                            <button @click="printDoc(activeDoc)" class="hover:text-primary transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">print</span> Print</button>
                            <span class="w-px h-4 bg-white/20 my-auto"></span>
                            <button @click="openShareModal" class="hover:text-primary transition-colors flex items-center gap-1" ref="shareButton"><span class="material-symbols-outlined text-[16px]">share</span> Share</button>
                        
                            <!-- Share Popover -->
                            <div v-if="isShareModalOpen" class="absolute bottom-12 right-0 bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-xl shadow-xl w-72 overflow-hidden animate-fade-in-up z-[130]">
                                <div class="p-3 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                                    <h4 class="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider">Share Document</h4>
                                    <button @click.stop="isShareModalOpen = false" class="text-gray-400 hover:text-gray-900 dark:hover:text-white"><span class="material-symbols-outlined text-sm">close</span></button>
                                </div>
                                <div v-if="shareStep === 'select'" class="p-2 grid grid-cols-1 gap-1">
                                    <button @click="shareVia('whatsapp')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                        <div class="w-8 h-8 rounded-full bg-[#25D366]/10 flex items-center justify-center text-[#25D366]"><span class="material-symbols-outlined text-lg">chat</span></div>
                                        <div>
                                            <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-[#25D366]">WhatsApp</p>
                                            <p class="text-[10px] text-gray-500">Share via link</p>
                                        </div>
                                    </button>
                                    <button @click="shareVia('telegram')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                        <div class="w-8 h-8 rounded-full bg-[#0088cc]/10 flex items-center justify-center text-[#0088cc]"><span class="material-symbols-outlined text-lg">send</span></div>
                                        <div>
                                            <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-[#0088cc]">Telegram</p>
                                            <p class="text-[10px] text-gray-500">Share via message</p>
                                        </div>
                                    </button>
                                    <button @click="shareVia('cargocore')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                        <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-lg">local_shipping</span></div>
                                        <div>
                                            <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary">CargoCore Messenger</p>
                                            <p class="text-[10px] text-gray-500">Internal secure share</p>
                                        </div>
                                    </button>
                                </div>

                                <!-- CargoCore Share Form -->
                                <div v-if="shareStep === 'form'" class="p-4 space-y-3">
                                    <div class="bg-primary/5 rounded-lg p-2 flex items-center gap-2 border border-primary/10">
                                        <span class="material-symbols-outlined text-primary text-sm">picture_as_pdf</span>
                                        <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate max-w-[150px]">{{ activeDoc.type }}.pdf</span>
                                    </div>
                                    
                                    <div>
                                        <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Assigned Warehouse</label>
                                        <div class="w-full text-xs bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded px-2 py-2 text-gray-500 dark:text-gray-400 font-mono">
                                            {{ store.hubs.find(h => h.id === shareFormData.hubId)?.name || 'Unknown Hub' }}
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Recipient Role</label>
                                        <div class="flex gap-2">
                                            <button @click="shareFormData.role = 'dispatcher'" 
                                                class="flex-1 py-1.5 text-xs rounded border transition-colors font-medium"
                                                :class="shareFormData.role === 'dispatcher' ? 'bg-primary text-white border-primary' : 'bg-slate-100 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-slate-200 dark:hover:bg-white/10'">
                                                Dispatcher
                                            </button>
                                            <button @click="shareFormData.role = 'manager'" 
                                                class="flex-1 py-1.5 text-xs rounded border transition-colors font-medium"
                                                :class="shareFormData.role === 'manager' ? 'bg-primary text-white border-primary' : 'bg-slate-100 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-slate-200 dark:hover:bg-white/10'">
                                                Manager
                                            </button>
                                        </div>
                                    </div>

                                    <div>
                                        <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Message (Optional)</label>
                                        <textarea v-model="shareFormData.message" rows="2" placeholder="Add a note..." class="w-full text-xs bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 focus:border-primary focus:outline-none text-gray-900 dark:text-white resize-none"></textarea>
                                    </div>

                                    <button @click="submitShare" class="w-full bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                                        <span class="material-symbols-outlined text-sm">send</span> Send Document
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="px-6 py-4 border-t border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-white/5 grid grid-cols-3 gap-4">
                        <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Expiry Date</p>
                            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ activeDoc.expiry }}</p>
                        </div>
                        <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Status</p>
                            <p class="text-sm font-bold" :class="activeDoc.status === 'Active' ? 'text-green-600' : 'text-red-500'">{{ activeDoc.status }}</p>
                        </div>
                         <div>
                            <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Verified By</p>
                            <p class="text-sm font-medium text-gray-900 dark:text-white">Admin System (Auto)</p>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import { storeToRefs } from 'pinia'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { apiUrl, API_BASE_URL } from '@/config/api'
import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix Leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
    iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
    shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

const { openSlip, openSlipWithData } = useSlipPrinter()

const store = useLogisticStore()
const authStore = useAuthStore()
const { filteredTopDrivers, filteredMaintenance, filteredVehicles } = storeToRefs(store)

// Dispatcher store — shared reactive suspend state (same Pinia instance, no localStorage polling needed)
const dispatcherStore = useDispatcherStore()

// ── Live Tracking (WebSocket + REST fallback) ──────────────────────────────────
const liveDrivers = ref([])
const fleetLoading = ref(false)
const wsConnected = ref(false)
const liveLocationsMap = ref(null)

let fleetWs = null
let wsReconnectTimer = null
let wsReconnectDelay = 2000
let pollFallbackTimer = null

function buildWsUrl() {
    const token = localStorage.getItem('auth_token') || ''
    const wsBase = API_BASE_URL.replace(/^http/, 'ws')
    return `${wsBase}/ws/fleet?token=${encodeURIComponent(token)}`
}

function liveDriverLocation(d) {
    // Try to get a human-readable location from the store driver record
    const storeDriver = store.drivers.find(sd =>
        String(sd.id) === String(d.driver_id) ||
        String(sd.name || '').trim().toLowerCase() === String(d.driver_name || '').trim().toLowerCase()
    )
    if (storeDriver?.location) return storeDriver.location
    const hub = store.hubs.find(h => h.id === storeDriver?.hubId)
    if (hub?.name) return hub.name
    if (d.last_updated) {
        return 'Updated ' + new Date(d.last_updated).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    }
    return 'Location updating…'
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
        wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000)
    }, wsReconnectDelay)
}

function disconnectFleetWs() {
    clearTimeout(wsReconnectTimer)
    clearInterval(pollFallbackTimer)
    if (fleetWs) {
        fleetWs.onclose = null
        fleetWs.close()
        fleetWs = null
    }
    wsConnected.value = false
}

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
        if (liveDrivers.value.length > 0 && liveLocationsMap.value?.leafletObject) {
            const bounds = L.latLngBounds(liveDrivers.value.map(d => [d.latitude, d.longitude]))
            liveLocationsMap.value.leafletObject.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 })
        }
    } catch (e) { /* silent */ } finally {
        fleetLoading.value = false
    }
}

// Center map on first active driver, fallback to India center
const fleetMapCenter = computed(() => {
    if (liveDrivers.value.length > 0) {
        const first = liveDrivers.value[0]
        return [first.latitude, first.longitude]
    }
    return [20.5937, 78.9629]
})

// Selected driver for zoom-to focus on live map
const selectedFleetDriver = ref(null)

const tabs = ['Active Drivers', 'Fleet Vehicles', 'Fleet Logs', 'Vehicle Documents', 'Driver Documents', 'Live Locations']
const activeTab = ref('Active Drivers')
const activeDropdown = ref(null)
const searchQuery = ref('') // Search State

// Log Management State
const logTypes = ['Fuel Logs', 'Service Logs', 'Maintenance Logs', 'Cleaning Logs']
const activeLogType = ref('Fuel Logs')

// Vehicle Management state
const isVehicleModalOpen = ref(false)
const vehicleModalMode = ref('add') // 'add' or 'edit'
const isSubmitting = ref(false)
const vehicleFormData = ref({})

// Driver Management state

// Document Viewing State
const activeDoc = ref(null)
const expandedDocs = ref([]) // IDs of expanded rows


// Document Upload State
const isUploadModalOpen = ref(false)
const uploadMode = ref('VEHICLE') // 'VEHICLE' or 'DRIVER'
const uploadFormData = ref({
    entityId: '',
    docType: '',
    expiryDate: '',
    fileBase64: null,
    fileName: ''
})

const openUploadModal = (mode) => {
    uploadMode.value = mode
    uploadFormData.value = {
        entityId: '',
        docType: '',
        expiryDate: '',
        fileBase64: null,
        fileName: ''
    }
    isUploadModalOpen.value = true
}

const closeUploadModal = () => {
    isUploadModalOpen.value = false
}

const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
        uploadFormData.value.fileName = file.name
        const reader = new FileReader()
        reader.onload = (e) => {
            uploadFormData.value.fileBase64 = e.target.result
        }
        reader.readAsDataURL(file)
    }
}

const submitDocument = async () => {
    if (!uploadFormData.value.entityId || !uploadFormData.value.docType) return
    
    await store.uploadDocument({
        entity_type: uploadMode.value,
        entity_id: uploadFormData.value.entityId,
        hub_id: store.activeWarehouse === 'all' ? null : store.activeWarehouse,
        doc_type: uploadFormData.value.docType,
        document_url: uploadFormData.value.fileBase64 || `https://placehold.co/400x500?text=${uploadFormData.value.docType.replace(/ /g, '+')}+Upload`,
        expiry_date: uploadFormData.value.expiryDate ? new Date(uploadFormData.value.expiryDate).toISOString() : null
    })
    closeUploadModal()
}

const verifyDocumentStatus = async (docId, status) => {
    await store.updateDocumentStatus(docId, status)
    activeDoc.value = null // Close the viewer
}

// Share Modal State

const isShareModalOpen = ref(false)
const shareStep = ref('select') // 'select' or 'form'
const shareFormData = ref({
    activeDocId: null,
    hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
    role: 'dispatcher', // dispatcher or manager
    message: ''
})

// Profile Viewers state
const activeDriverProfile = ref(null)
const activeVehicleProfile = ref(null)
const chatInput = ref('')
const managerChatLoading = ref(false)
const LM_SENDERS = new Set(['me', 'manager', 'logistics manager'])

const activeDriverMessages = computed(() => {
    const threadId = activeDriverProfile.value?.managerThreadId
    if (!threadId) return []
    const thread = store.chats.find(c => c.id === threadId)
    return thread?.messages || []
})

const isDriverSuspendedInFleet = (driver) => {
    const id = String(driver?.id || '')
    const status = String(driver?.status || '').toLowerCase()
    if (status === 'suspended') return true
    if (id && dispatcherStore.isDriverSuspended(id)) return true
    return store.drivers.some((item) =>
        String(item.id) === id && String(item.status || '').toLowerCase() === 'suspended'
    )
}

// ── Computed properties for Search & Grouping
const searchedDrivers = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return store.filteredDrivers
        .filter(d =>
            !q ||
            d.name.toLowerCase().includes(q) ||
            String(d.vehicle || '').toLowerCase().includes(q) ||
            String(d.currentJob || '').toLowerCase().includes(q) ||
            String(d.status || '').toLowerCase().includes(q)
        )
        .map(d => ({ ...d, dispatcherSuspended: isDriverSuspendedInFleet(d) }))
})

const searchedTopDrivers = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return filteredTopDrivers.value
        .filter(d => !q || d.name.toLowerCase().includes(q))
        .map(d => ({ ...d, dispatcherSuspended: isDriverSuspendedInFleet(d) }))
})

const searchedVehicles = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return store.filteredVehicles.filter(v => 
        !q || 
        v.id.toLowerCase().includes(q) || 
        v.type.toLowerCase().includes(q) || 
        v.model.toLowerCase().includes(q) ||
        v.driver.toLowerCase().includes(q) ||
        v.status.toLowerCase().includes(q)
    )
})

const searchedMaintenance = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return filteredMaintenance.value.filter(m => 
        !q || 
        m.id.toLowerCase().includes(q) || 
        m.issue.toLowerCase().includes(q) || 
        m.status.toLowerCase().includes(q)
    )
})

const searchedLogs = computed(() => {
    let logs = store.fleetLogs[activeLogType.value] || []

    const q = searchQuery.value.toLowerCase()
    
    // Generic filter across all fields for simplicity
    return logs.filter(l => 
        (store.activeWarehouse === 'all' || l.hubId === store.activeWarehouse) &&
        (!q || Object.values(l).some(val => String(val).toLowerCase().includes(q)))
    )
})

const logStats = computed(() => {
    // Dynamic Stats Calculator based on current Log Type
    const logs = searchedLogs.value
    const totalCost = logs.reduce((sum, log) => sum + (log.cost || 0), 0)
    
    if (activeLogType.value === 'Fuel Logs') {
        const totalVolume = logs.reduce((sum, log) => sum + (log.gallons || 0), 0)
        const avgPrice = totalVolume > 0 ? (totalCost / totalVolume).toFixed(2) : 0
        const completedCount = logs.filter(l => l.status === 'Completed' || l.status === 'Verified').length
        const trendPct = logs.length ? Math.round((completedCount / logs.length) * 100) : 0
        return {
            title: 'Fuel Consumption',
            icon: 'local_gas_station',
            color: 'orange',
            tiles: [
                { label: 'Avg Price/Gal', value: `₹${avgPrice}` },
                { label: 'Total Volume', value: `${totalVolume.toLocaleString()} L` }
            ],
            trend: { label: 'Verified Logs', value: `${completedCount} / ${logs.length}`, target: `${logs.length}`, pct: trendPct },
            totalCost
        }
    } else if (activeLogType.value === 'Service Logs') {
        const completedCount = logs.filter(l => l.status === 'Completed').length
        const trendPct = logs.length ? Math.round((completedCount / logs.length) * 100) : 0
        return {
            title: 'Service Metrics',
            icon: 'car_repair',
            color: 'blue',
            tiles: [
                { label: 'Total Services', value: logs.length },
                { label: 'Avg Cost', value: `₹${logs.length ? (totalCost / logs.length).toFixed(0) : 0}` }
            ],
            trend: { label: 'Completion Rate', value: `${completedCount} / ${logs.length}`, target: `${logs.length}`, pct: trendPct },
            totalCost
        }
    } else if (activeLogType.value === 'Maintenance Logs') {
        const resolvedCount = logs.filter(l => l.status === 'Resolved').length
        const trendPct = logs.length ? Math.round((resolvedCount / logs.length) * 100) : 0
        return {
            title: 'Maintenance Costs',
            icon: 'build',
            color: 'red',
            tiles: [
                { label: 'Active Repairs', value: logs.filter(l => l.status !== 'Resolved').length },
                { label: 'Avg Repair Cost', value: `₹${logs.length ? (totalCost / logs.length).toFixed(0) : 0}` }
            ],
            trend: { label: 'Resolved', value: `${resolvedCount} / ${logs.length}`, target: `${logs.length}`, pct: trendPct },
            totalCost
        }
    } else {
        const completedCount = logs.filter(l => l.status === 'Completed').length
        const trendPct = logs.length ? Math.round((completedCount / logs.length) * 100) : 0
        return {
           title: 'Fleet Hygiene',
            icon: 'cleaning_services',
            color: 'teal',
            tiles: [
                { label: 'Total Washes', value: logs.length },
                { label: 'Avg Wash Cost', value: `₹${logs.length ? (totalCost / logs.length).toFixed(0) : 0}` }
            ],
            trend: { label: 'Completed', value: `${completedCount} / ${logs.length}`, target: `${logs.length}`, pct: trendPct },
            totalCost
        }
    }
})

const groupedVehicleDocs = computed(() => {
    // 1. Filter by active warehouse
    let docs = store.filteredVehicleDocuments
    if (store.activeWarehouse !== 'all') {
        docs = docs.filter(d => d.hubId === store.activeWarehouse)
    }
    
    // 2. Filter by Search
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        docs = docs.filter(d => 
            d.vehicleId.toLowerCase().includes(q) || 
            d.type.toLowerCase().includes(q) || 
            d.status.toLowerCase().includes(q)
        )
    }
    
    // 3. Group by Vehicle ID
    const groups = {}
    docs.forEach(doc => {
        if (!groups[doc.vehicleId]) {
            groups[doc.vehicleId] = []
        }
        groups[doc.vehicleId].push(doc)
    })
    return groups
})

const groupedDriverDocs = computed(() => {
    // 1. Filter by active warehouse
    let docs = store.filteredDriverDocuments
    if (store.activeWarehouse !== 'all') {
        docs = docs.filter(d => d.hubId === store.activeWarehouse)
    }

    // 2. Filter by Search
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        docs = docs.filter(d => 
            d.driver.toLowerCase().includes(q) || 
            d.type.toLowerCase().includes(q) || 
            d.licenseNo.toLowerCase().includes(q) ||
            d.status.toLowerCase().includes(q)
        )
    }

    // 3. Group by Driver Name/ID
    const groups = {}
    docs.forEach(doc => {
        if (!groups[doc.driverId]) {
            groups[doc.driverId] = {
                id: doc.driverId,
                name: doc.driver,
                docs: []
            }
        }
        groups[doc.driverId].docs.push(doc)
    })
    return Object.values(groups)
})

const vehicleLocationData = computed(() => {
    const data = filteredVehicles.value.map(vehicle => {
        // Find assigned driver from store.drivers (we use store.filteredDrivers but need to ensure we catch all if needed, 
        // though filteredDrivers fits the current view context)
        const driver = store.drivers.find(d => d.name === vehicle.driver)
        
        // Find driver license from local driverDocs
        let licenseNo = 'N/A'
        if (driver) {
            const doc = store.driverDocuments.find(d => d.driverId === driver.id && d.type.includes('License'))
            if (doc) licenseNo = doc.licenseNo
        }

        return {
            ...vehicle,
            driverId: driver ? driver.id : null,
            licenseNo: licenseNo,
            currentLocation: driver ? driver.location : 'Depot (Parked)',
            currentJob: driver ? driver.currentJob : 'Idle',
            speed: driver && driver.status?.toLowerCase() === 'active' ? `${35 + (driver.efficiency % 18)} mph` : '0 mph',
            gps: driver ? `${34.05 + ((driver.efficiency || 0) / 1000)}, -118.24` : '34.0522, -118.2437',
            lastUpdate: 'Just now'
        }
    })

    // Search Filter for Locations
    const q = searchQuery.value.toLowerCase()
    if (!q) return data

    return data.filter(v => 
        String(v.id || '').toLowerCase().includes(q) || 
        String(v.type || '').toLowerCase().includes(q) || 
        String(v.licensePlate || '').toLowerCase().includes(q) || 
        String(v.driver || '').toLowerCase().includes(q) || 
        String(v.driverId || '').toLowerCase().includes(q) || 
        String(v.currentLocation || '').toLowerCase().includes(q) ||
        String(v.currentJob || '').toLowerCase().includes(q)
    )
})

// Report & Doc Actions
const openSafetyChecklist = () => {
    const vehicle = store.filteredVehicles[0] || null
    const driver = store.filteredDrivers.find(d => vehicle && d.vehicle === vehicle.code) || store.filteredDrivers[0] || null
    if (driver || vehicle) {
        openSlipWithData('vehicleSafetyChecklist', driver, vehicle)
    } else {
        openSlip('vehicleSafetyChecklist')
    }
}

const openSafetyChecklistForVehicle = (vehicle) => {
    const driver = store.filteredDrivers.find(d => d.vehicle === vehicle.code) || null
    openSlipWithData('vehicleSafetyChecklist', driver, vehicle)
}

const openSafetyChecklistForDriver = (driver) => {
    const vehicle = store.filteredVehicles.find(v => v.code === driver.vehicle) || null
    openSlipWithData('vehicleSafetyChecklist', driver, vehicle)
}

const generateMaintenanceReport = () => {
    const vehicles = store.filteredVehicles
    if (!vehicles.length) {
        window.alert('No vehicle data available to download.')
        return
    }
    const rows = [
        ['Vehicle ID', 'License Plate', 'Type', 'Model', 'Year', 'Driver', 'Status', 'Warehouse', 'Fuel Efficiency', 'Current Location'],
        ...vehicles.map(v => [
            v.id, v.licensePlate || '—', v.type || '—', v.model || '—', v.year || '—',
            v.driver || '—', v.status || '—',
            store.hubs.find(h => h.id === v.hubId)?.name || 'Main Hub',
            v.fuelEfficiency || '—', v.currentLocation || '—'
        ])
    ]
    const csv = rows.map(r => r.map(c => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fleet_maintenance_report_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

const downloadDoc = (doc) => {
    window.alert(`Starting download for ${doc.type}.pdf...`)
}

const printDoc = (doc) => {
    window.print()
}

const openShareModal = () => {
    isShareModalOpen.value = !isShareModalOpen.value
    // Reset form if opening fresh
    if (isShareModalOpen.value) {
        shareStep.value = 'select'
        shareFormData.value = {
            activeDocId: activeDoc.value.id,
            hubId: activeDoc.value.hubId || (store.activeWarehouse === 'all' ? 1 : store.activeWarehouse),
            role: 'dispatcher',
            message: `Please review attached ${activeDoc.value.type} for ${activeDoc.value.vehicleId || activeDoc.value.driver}.`
        }
    }
}

const shareVia = (platform) => {
    if (platform === 'whatsapp') {
        window.open(`https://wa.me/?text=Check this document: ${activeDoc.value.url}`, '_blank')
        isShareModalOpen.value = false
    } else if (platform === 'telegram') {
        window.open(`https://t.me/share/url?url=${activeDoc.value.url}&text=Check this document`, '_blank')
        isShareModalOpen.value = false
    } else if (platform === 'cargocore') {
        shareStep.value = 'form'
    }
}

const submitShare = () => {
    // Mock API call to internal messaging system
    console.log('Sending CargoCore Message:', {
        docId: shareFormData.value.activeDocId,
        hubId: shareFormData.value.hubId,
        role: shareFormData.value.role,
        message: shareFormData.value.message
    })
    
    // Simulate success
    window.alert(`Document sent to ${shareFormData.value.role === 'dispatcher' ? 'Dispatch Team' : 'Warehouse Manager'} successfully!`)
    isShareModalOpen.value = false
}

// Dropdowns logic
const toggleVehicleDropdown = (id) => {
    activeDropdown.value = activeDropdown.value === id ? null : id
}

const toggleDocExpand = (id) => {
    if (expandedDocs.value.includes(id)) {
        expandedDocs.value = expandedDocs.value.filter(e => e !== id)
    } else {
        expandedDocs.value.push(id)
    }
}

const openDocModal = (doc) => {
    activeDoc.value = doc
}

const closeDocModal = () => {
    activeDoc.value = null
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


// Vehicle form helpers
const openVehicleModal = (mode, vehicle = null) => {
    vehicleModalMode.value = mode
    if (mode === 'edit' && vehicle) {
        // Find the driver currently assigned to this vehicle
        const assignedDriver = store.filteredDrivers.find(d => d.vehicle === vehicle.code || d.vehicle === vehicle.id)
        vehicleFormData.value = { ...vehicle, driverId: assignedDriver?.id || null }
    } else {
        vehicleFormData.value = {
            id: `VH-${Math.floor(Math.random() * 9000) + 1000}`,
            licensePlate: '',
            model: '',
            type: 'Delivery Van',
            hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
            year: new Date().getFullYear(),
            driverId: null,
        }
    }
    isVehicleModalOpen.value = true
}


const handleVehicleDocUpload = (event, docType) => {
    const file = event.target.files[0]
    if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
            if (docType === 'insurance') {
                vehicleFormData.value.insuranceFile = e.target.result
                vehicleFormData.value.insuranceFileName = file.name
            } else if (docType === 'registration') {
                vehicleFormData.value.registrationFile = e.target.result
                vehicleFormData.value.registrationFileName = file.name
            }
        }
        reader.readAsDataURL(file)
    }
}

const closeVehicleModal = () => {
    isVehicleModalOpen.value = false
    vehicleFormData.value = {}
}

const submitVehicle = async () => {
    try {
        isSubmitting.value = true
        if (vehicleModalMode.value === 'add') {
            await store.addVehicle({ ...vehicleFormData.value })
            
            let targetHub = vehicleFormData.value.hubId
            if (targetHub === 'all' || targetHub === 1) targetHub = null

            if (vehicleFormData.value.insuranceFile && vehicleFormData.value.insuranceExpiry) {
                await store.uploadDocument({
                    entity_type: 'VEHICLE',
                    entity_id: vehicleFormData.value.id,
                    hub_id: targetHub,
                    doc_type: 'Insurance Policy',
                    document_url: vehicleFormData.value.insuranceFile,
                    expiry_date: new Date(vehicleFormData.value.insuranceExpiry).toISOString()
                })
            }
            
            if (vehicleFormData.value.registrationFile && vehicleFormData.value.registrationExpiry) {
                await store.uploadDocument({
                    entity_type: 'VEHICLE',
                    entity_id: vehicleFormData.value.id,
                    hub_id: targetHub,
                    doc_type: 'Vehicle Registration',
                    document_url: vehicleFormData.value.registrationFile,
                    expiry_date: new Date(vehicleFormData.value.registrationExpiry).toISOString()
                })
            }
        } else {
            await store.updateVehicle(vehicleFormData.value.id, {
                model: vehicleFormData.value.model,
                license_plate: vehicleFormData.value.licensePlate,
                assigned_driver_id: vehicleFormData.value.driverId || null,
            })
        }
    } finally {
        isSubmitting.value = false
        closeVehicleModal()
    }
}

// Get cost for a maintenance item from fleet logs
const maintenanceCost = (vehicleId) => {
    const vehicle = store.filteredVehicles.find(v => v.id === vehicleId)
    if (!vehicle) return '—'
    const log = (store.fleetLogs['Maintenance Logs'] || []).find(l => l.vehicleId === vehicle.code)
    return log?.cost != null ? `₹${log.cost.toLocaleString()}` : '—'
}

// Helper: get performance stats from topDrivers list
const driverStats = (driver) => {
    if (!driver) return {}
    const top = store.topDrivers.find(d => d.id === driver.id || d.name === driver.name)
    return {
        trips: top?.trips ?? null,
        rating: top?.rating ?? null,
        ontime: top?.ontime ?? null,
    }
}

// Profiles logic
const openDriverProfile = async (driver) => {
    const dispatcherSuspended = isDriverSuspendedInFleet(driver)
    // Merge fields without injecting fake/static data
    activeDriverProfile.value = {
        ...driver,
        dispatcherSuspended,
        id: driver.id || null,
        phone: driver.phone || null,
        status: dispatcherSuspended ? 'Suspended' : (driver.status || 'active'),
        efficiency: driver.efficiency ?? null,
        vehicle: driver.vehicle || 'Company Fleet',
        currentJob: dispatcherSuspended ? 'Blocked from dispatch' : (driver.currentJob || 'On Route'),
        location: driver.location || null,
        avatarColor: driver.avatarColor || 'bg-blue-600',
        managerThreadId: null,
    }
    managerChatLoading.value = true
    try {
        const thread = await store.ensureManagerDriverThread(activeDriverProfile.value)
        activeDriverProfile.value = {
            ...activeDriverProfile.value,
            managerThreadId: String(thread.id),
        }
    } finally {
        managerChatLoading.value = false
    }
}
const closeDriverProfile = () => {
    activeDriverProfile.value = null
    chatInput.value = ''
}

const forceEndDriverShift = async (driver) => {
    // 1. Resolve warehouse coords to snap driver location back to hub
    const hub = store.hubs.find(h => h.id === driver.hubId)
    const warehouseLocation = (hub?.lat && hub?.lng) ? `${hub.lat},${hub.lng}` : null

    // 2. Set driver Off-Duty + reset location to warehouse in one call
    const updatePayload = { status: 'Off-Duty', current_job: null }
    if (warehouseLocation) updatePayload.current_location = warehouseLocation

    await fetch(`http://localhost:8000/api/v1/logistics/drivers/${driver.id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${authStore.token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(updatePayload),
    }).catch(() => {})

    // 3. Release the vehicle assigned to this driver
    const byName = store.filteredVehicles.find(v => v.driver === driver.name)
    if (byName) {
        await store.updateVehicle(byName.id, { assigned_driver_id: null, status: 'Active' })
    } else {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/logistics/vehicles`, {
                headers: { 'Authorization': `Bearer ${authStore.token}` }
            })
            if (res.ok) {
                const list = await res.json()
                const veh = (Array.isArray(list) ? list : list.items || [])
                    .find(v => String(v.assigned_driver_id) === String(driver.id))
                if (veh) await store.updateVehicle(veh.id, { assigned_driver_id: null, status: 'Active' })
            }
        } catch (_) { /* best-effort */ }
    }

    await store.refresh()

    // 4. Update the open profile badge reactively
    if (activeDriverProfile.value?.id === driver.id) {
        activeDriverProfile.value = { ...activeDriverProfile.value, status: 'Off-Duty' }
    }
}
const sendChat = async () => {
    if (!chatInput.value.trim() || !activeDriverProfile.value?.managerThreadId) return
    const text = chatInput.value.trim()
    chatInput.value = ''
    await store.sendChatMessage(activeDriverProfile.value.managerThreadId, text)
}

const isLmOutgoing = (msg) => {
    return LM_SENDERS.has(String(msg?.sender || '').toLowerCase())
}

const openVehicleProfile = (vehicle, viewMode = 'full') => {
    const history = [
        ...(store.fleetLogs['Service Logs'] || []).filter(item => item.vehicleId === vehicle.id).map(item => ({
            id: item.id,
            service: item.service,
            date: item.date,
            type: 'Routine',
            cost: item.cost,
        })),
        ...(store.fleetLogs['Maintenance Logs'] || []).filter(item => item.vehicleId === vehicle.id).map(item => ({
            id: item.id,
            service: item.issue,
            date: item.date,
            type: 'Repair',
            cost: item.cost,
        })),
    ]

    activeVehicleProfile.value = { 
        ...vehicle, 
        viewMode: viewMode,
        serviceHistory: history,
        totalMaintenanceCost: history.reduce((sum, item) => sum + item.cost, 0)
    }
}
const closeVehicleProfile = () => {
    activeVehicleProfile.value = null
}
</script>

<style scoped>
.lm-vehicle-modal {
    color: #e2e8f0;
}

.lm-vehicle-modal :deep(label) {
    color: #cbd5e1 !important;
}

.lm-vehicle-modal :deep(input),
.lm-vehicle-modal :deep(select),
.lm-vehicle-modal :deep(textarea) {
    background-color: rgba(15, 23, 42, 0.92) !important;
    color: #f8fafc !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color-scheme: dark;
}

.lm-vehicle-modal :deep(input::placeholder),
.lm-vehicle-modal :deep(textarea::placeholder) {
    color: #94a3b8 !important;
}

.lm-vehicle-modal :deep(option) {
    background-color: rgb(15 23 42) !important;
    color: #f8fafc !important;
}

.lm-vehicle-modal :deep(.text-gray-400),
.lm-vehicle-modal :deep(.text-gray-500) {
    color: #94a3b8 !important;
}

.lm-vehicle-modal :deep(input[type='date']::-webkit-calendar-picker-indicator) {
    filter: invert(1);
    opacity: 0.85;
}
</style>
