<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col gap-6">
        <!-- Header & Controls -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Geofencing & Routes</h2>
                <p class="text-sm text-gray-500">Manage operational zones, restricted areas, and dynamic routing rules.</p>
            </div>
            <div class="flex gap-3">
                <div class="flex items-center gap-1 bg-gray-100 dark:bg-black/40 rounded-lg p-1 border border-gray-200 dark:border-white/10 shadow-sm">
                    <button @click="viewMode = 'map'"
                        class="px-3 py-1.5 rounded text-sm font-medium transition-all flex items-center gap-2"
                        :class="viewMode === 'map' ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'">
                        <span class="material-symbols-outlined text-[18px]">map</span> Map
                    </button>
                    <button @click="viewMode = 'list'"
                        class="px-3 py-1.5 rounded text-sm font-medium transition-all flex items-center gap-2"
                        :class="viewMode === 'list' ? 'bg-white dark:bg-gray-700 text-primary shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'">
                        <span class="material-symbols-outlined text-[18px]">table_rows</span> List
                    </button>
                </div>
                <button @click="startPickingNewZone"
                    class="bg-primary hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-sm">
                    <span class="material-symbols-outlined">add_location_alt</span> New Zone
                </button>
            </div>
        </div>

        <!-- Dynamic Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div>
                    <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Total Zones</p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ filteredZones.length }}</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400">
                    <span class="material-symbols-outlined">share_location</span>
                </div>
            </div>
            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div>
                    <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Active Vehicles</p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ vehiclesInZones }}</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-green-50 dark:bg-green-500/10 flex items-center justify-center text-green-600 dark:text-green-400">
                    <span class="material-symbols-outlined">local_shipping</span>
                </div>
            </div>
            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div>
                    <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Breach Alerts</p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ breachAlerts }}</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center text-red-600 dark:text-red-400">
                    <span class="material-symbols-outlined">warning</span>
                </div>
            </div>
            <div class="glass-panel p-4 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div>
                    <p class="text-xs text-gray-500 uppercase font-bold tracking-wider">Coverage Area</p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ totalArea }} km²</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-purple-50 dark:bg-purple-500/10 flex items-center justify-center text-purple-600 dark:text-purple-400">
                    <span class="material-symbols-outlined">layers</span>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="flex-1 flex gap-6 overflow-hidden min-h-0">
            <!-- Sidebar: Zone List & Search -->
            <div class="w-80 glass-panel rounded-xl flex flex-col border border-gray-200 dark:border-white/5 flex-shrink-0">
                <div class="p-4 border-b border-gray-200 dark:border-white/5 space-y-3">
                    <div class="relative">
                        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">search</span>
                        <input v-model="searchQuery" type="text" placeholder="Search zones..."
                            class="w-full bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow text-gray-900 dark:text-white">
                    </div>
                </div>
                <div class="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                    <div v-if="isLoading" class="flex flex-col items-center justify-center gap-3 py-12 text-center">
                        <span class="material-symbols-outlined text-gray-400 text-4xl animate-spin">progress_activity</span>
                        <p class="text-sm text-gray-400">Loading zones...</p>
                    </div>
                    <div v-else-if="searchedZones.length === 0" class="flex flex-col items-center justify-center gap-3 py-12 text-center">
                        <span class="material-symbols-outlined text-gray-300 dark:text-gray-600 text-4xl">add_location_alt</span>
                        <p class="text-sm text-gray-400">No zones found</p>
                    </div>
                    <div v-for="zone in searchedZones" :key="zone.id"
                        @click="selectZone(zone)"
                        class="p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer border transition-all group shadow-sm flex flex-col gap-2 relative"
                        :class="selectedZone?.id === zone.id ? 'bg-primary/5 border-primary/30' : 'border-transparent bg-white dark:bg-transparent'">

                        <div class="flex justify-between items-start">
                            <div class="font-bold text-gray-900 dark:text-white text-sm">{{ zone.name }}</div>
                            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button @click.stop="openZoneModal('edit', zone)" class="p-1 hover:bg-gray-200 dark:hover:bg-white/10 rounded text-gray-500"><span class="material-symbols-outlined text-[16px]">edit</span></button>
                                <button @click.stop="handleDeleteZone(zone.id)" class="p-1 hover:bg-red-100 dark:hover:bg-red-500/20 rounded text-red-500"><span class="material-symbols-outlined text-[16px]">delete</span></button>
                            </div>
                        </div>

                        <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                            <span class="material-symbols-outlined text-[14px]">{{ getZoneIcon(zone.type) }}</span>
                            <span>{{ zone.type }}</span>
                            <span>•</span>
                            <span>{{ zone.radius }}km Radius</span>
                        </div>

                        <div class="flex justify-between items-center mt-1">
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                                :class="zone.status === 'Active' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500 border-gray-200'">
                                {{ zone.status || 'Active' }}
                            </span>
                            <span class="text-[10px] text-gray-400 font-mono">{{ store.hubs.find(h => h.id === zone.hubId)?.name }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- View Area -->
            <div class="flex-1 glass-panel rounded-xl relative overflow-hidden border border-gray-200 dark:border-white/5 flex flex-col">

                <!-- MAP VIEW -->
                <div v-if="viewMode === 'map'" class="absolute inset-0 flex flex-col">
                    <!-- Map + Tools layer -->
                    <div class="flex-1 relative">
                        <!-- Tools Overlay (above leaflet) -->
                        <div class="absolute top-4 left-4 z-[1000] flex flex-col gap-2 bg-white/90 dark:bg-black/80 p-2 rounded-lg backdrop-blur shadow-lg border border-gray-200 dark:border-white/10">
                            <button v-for="tool in mapTools" :key="tool.id"
                                @click="activeTool = tool.id"
                                class="w-8 h-8 rounded flex items-center justify-center transition-colors relative group"
                                :class="activeTool === tool.id ? 'bg-primary text-white shadow-md' : 'text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/10'">
                                <span class="material-symbols-outlined text-[20px]">{{ tool.icon }}</span>
                                <span class="absolute left-full ml-3 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-20">
                                    {{ tool.label }}
                                </span>
                            </button>
                        </div>

                        <!-- Real Leaflet Map -->
                        <l-map ref="mapRef"
                            v-model:zoom="mapZoom"
                            :center="mapCenter"
                            :use-global-leaflet="false"
                            @moveend="onMapMove"
                            @click="onMapClick"
                            :class="pickingFromMap ? 'cursor-crosshair' : ''"
                            style="position:absolute;inset:0;height:100%;width:100%">
                            <l-tile-layer
                                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                                layer-type="base"
                                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                            ></l-tile-layer>

                            <!-- Saved zone circles -->
                            <l-circle
                                v-for="zone in mappableZones"
                                :key="zone.id"
                                :lat-lng="[zone.lat, zone.lng]"
                                :radius="(parseFloat(zone.radius) || 1) * 1000"
                                :color="getZoneColor(zone.color)"
                                :fill-color="getZoneColor(zone.color)"
                                :fill-opacity="selectedZone?.id === zone.id ? 0.25 : 0.1"
                                :weight="selectedZone?.id === zone.id ? 3 : 1.5"
                                :dash-array="zone.type === 'Exclusion' ? '8 5' : undefined"
                                @click="selectZone(zone)"
                            >
                                <l-tooltip :permanent="true" :direction="'top'" :offset="[0, -6]">
                                    <div class="text-xs font-semibold">{{ zone.name }}</div>
                                    <div class="text-[10px] text-gray-500">{{ zone.type }} · {{ zone.radius }}km</div>
                                </l-tooltip>
                            </l-circle>

                            <!-- Live draft preview circle while modal is open -->
                            <l-circle
                                v-if="isZoneModalOpen && zoneForm.lat && zoneForm.lng"
                                :lat-lng="[zoneForm.lat, zoneForm.lng]"
                                :radius="(parseFloat(zoneForm.radius) || 1) * 1000"
                                :color="getZoneColor(zoneForm.color)"
                                :fill-color="getZoneColor(zoneForm.color)"
                                :fill-opacity="0.18"
                                :weight="2.5"
                                :dash-array="'10 6'"
                            >
                                <l-tooltip :permanent="true" :direction="'top'" :offset="[0, -6]">
                                    <div class="text-xs font-semibold text-primary">{{ zoneForm.name || 'New Zone' }}</div>
                                    <div class="text-[10px] text-gray-500">Preview · {{ zoneForm.radius }}km</div>
                                </l-tooltip>
                            </l-circle>
                        </l-map>

                        <!-- Pick-from-map instruction overlay -->
                        <div v-if="pickingFromMap"
                            class="absolute inset-0 z-[1001] flex flex-col items-center justify-center gap-3 pointer-events-none">
                            <!-- crosshair lines -->
                            <div class="absolute inset-0 flex items-center justify-center">
                                <div class="w-px h-full bg-blue-400/30"></div>
                            </div>
                            <div class="absolute inset-0 flex items-center justify-center">
                                <div class="h-px w-full bg-blue-400/30"></div>
                            </div>
                            <div class="bg-blue-600 text-white px-5 py-3 rounded-xl flex items-center gap-3 shadow-2xl pointer-events-auto">
                                <span class="material-symbols-outlined text-2xl animate-bounce">location_searching</span>
                                <div>
                                    <p class="text-sm font-bold">Click on the map to place your zone</p>
                                    <p class="text-xs text-blue-200">You can fine-tune everything after placing it</p>
                                </div>
                                <button @click.stop="cancelPick" class="ml-4 text-blue-200 hover:text-white text-xs underline flex-shrink-0">Cancel</button>
                            </div>
                        </div>

                        <!-- Empty state overlay -->
                        <div v-if="!pickingFromMap && (isLoading || searchedZones.length === 0)"
                            class="absolute inset-0 z-[1000] flex flex-col items-center justify-center gap-3 pointer-events-none">
                            <div class="bg-white/80 dark:bg-black/60 backdrop-blur px-6 py-4 rounded-xl flex flex-col items-center gap-2">
                                <span v-if="isLoading" class="material-symbols-outlined text-gray-400 text-4xl animate-spin">progress_activity</span>
                                <span v-else class="material-symbols-outlined text-gray-400 text-4xl">add_location_alt</span>
                                <p class="text-sm text-gray-500 text-center">{{ isLoading ? 'Loading zones...' : 'Click New Zone, then click the map to place a zone' }}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Bottom Info Bar -->
                    <div class="h-10 flex-shrink-0 bg-white dark:bg-card-dark border-t border-gray-200 dark:border-white/10 flex items-center px-4 justify-between text-xs text-gray-500 z-[500]">
                        <div class="flex gap-4">
                            <span>Lat: {{ mapCurrentCenter[0].toFixed(4) }}</span>
                            <span>Lng: {{ mapCurrentCenter[1].toFixed(4) }}</span>
                            <span>Zoom: {{ mapZoom }}x</span>
                        </div>
                        <div class="flex gap-2 items-center">
                            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            <span>{{ searchedZones.length }} zone{{ searchedZones.length !== 1 ? 's' : '' }} on map</span>
                        </div>
                    </div>
                </div>

                <!-- LIST VIEW -->
                <div v-else class="flex flex-col h-full">
                    <div class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-white/5 flex justify-between items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white">All Active Zones</h3>
                        <div class="flex gap-2 text-sm text-gray-500">
                            <button class="hover:text-primary flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">filter_list</span> Filter</button>
                            <button class="hover:text-primary flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">download</span> Export</button>
                        </div>
                    </div>
                    <div class="flex-1 overflow-auto custom-scrollbar">
                        <table class="w-full text-left text-sm">
                            <thead class="bg-gray-50 dark:bg-card-dark sticky top-0 z-10">
                                <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                                    <th class="py-3 px-4 font-medium">Zone Name</th>
                                    <th class="py-3 px-4 font-medium">Type</th>
                                    <th class="py-3 px-4 font-medium">Hub Assignment</th>
                                    <th class="py-3 px-4 font-medium text-right">Radius (km)</th>
                                    <th class="py-3 px-4 font-medium text-right">Status</th>
                                    <th class="py-3 px-4 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                <tr v-if="isLoading">
                                    <td colspan="6" class="py-12 text-center text-sm text-gray-400">
                                        <span class="material-symbols-outlined align-middle animate-spin text-xl mr-2">progress_activity</span>Loading zones...
                                    </td>
                                </tr>
                                <tr v-else-if="searchedZones.length === 0">
                                    <td colspan="6" class="py-12 text-center text-sm text-gray-400">No zones found</td>
                                </tr>
                                <tr v-for="zone in searchedZones" :key="zone.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group">
                                    <td class="py-3 px-4 font-medium text-gray-900 dark:text-white">{{ zone.name }}</td>
                                    <td class="py-3 px-4 text-gray-600 dark:text-gray-300">
                                        <div class="flex items-center gap-2">
                                            <span class="material-symbols-outlined text-sm">{{ getZoneIcon(zone.type) }}</span>
                                            {{ zone.type }}
                                        </div>
                                    </td>
                                    <td class="py-3 px-4 text-gray-600 dark:text-gray-300">{{ store.hubs.find(h => h.id === zone.hubId)?.name || '—' }}</td>
                                    <td class="py-3 px-4 text-right font-mono">{{ zone.radius }}</td>
                                    <td class="py-3 px-4 text-right">
                                        <span class="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
                                            :class="zone.status === 'Active' ? 'bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400' : 'bg-gray-100 text-gray-500'">
                                            {{ zone.status || 'Active' }}
                                        </span>
                                    </td>
                                    <td class="py-3 px-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button @click="openZoneModal('edit', zone)" class="text-primary hover:text-primary-dark font-medium text-xs mr-3">Edit</button>
                                        <button @click="handleDeleteZone(zone.id)" class="text-red-500 hover:text-red-700 font-medium text-xs">Delete</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create/Edit Zone Modal -->
        <Teleport to="body">
            <div v-if="isZoneModalOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col animate-scale-in" style="max-height:92vh">
                    <div class="p-5 border-b border-gray-100 dark:border-white/10 flex justify-between items-center bg-gray-50 dark:bg-white/5 flex-shrink-0">
                        <div>
                            <h3 class="text-base font-bold text-gray-900 dark:text-white">{{ zoneModalMode === 'create' ? 'Create New Zone' : 'Edit Zone' }}</h3>
                            <p class="text-xs text-gray-500">Define geofence parameters and restrictions</p>
                        </div>
                        <button @click="closeZoneModal" class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-5 space-y-3 overflow-y-auto flex-1 min-h-0">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Name</label>
                            <input v-model="zoneForm.name" type="text" placeholder="e.g. Downtown Exclusion Zone" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Type</label>
                                <select v-model="zoneForm.type" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                                    <option value="Polygon" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Polygon</option>
                                    <option value="Circle" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Circle</option>
                                    <option value="Exclusion" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Exclusion Zone</option>
                                    <option value="Corridor" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Corridor</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Radius (km)</label>
                                <input v-model="zoneForm.radius" type="number" step="0.1" min="0.1" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Assigned Warehouse</label>
                            <select v-model="zoneForm.hubId" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                                <option v-for="hub in store.hubs" :key="hub.id" :value="hub.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ hub.name }}</option>
                            </select>
                        </div>

                        <!-- Zone Location -->
                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Center</label>
                            <div v-if="zoneForm.lat && zoneForm.lng"
                                class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                                <div class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center"
                                    :style="{ backgroundColor: getZoneColor(zoneForm.color) + '25', color: getZoneColor(zoneForm.color) }">
                                    <span class="material-symbols-outlined text-[18px]">location_on</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p v-if="draftAddress === 'Locating...'" class="text-xs text-gray-400 flex items-center gap-1">
                                        <span class="material-symbols-outlined text-[12px] animate-spin">progress_activity</span> Locating...
                                    </p>
                                    <p v-else class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ draftAddress || 'Location selected' }}</p>
                                    <p class="text-[10px] text-gray-400 font-mono">{{ zoneForm.lat?.toFixed(5) }}, {{ zoneForm.lng?.toFixed(5) }}</p>
                                </div>
                                <button @click="pickFromMap" type="button"
                                    class="text-xs text-primary hover:text-primary/80 font-semibold flex-shrink-0 flex items-center gap-1 px-2 py-1 rounded hover:bg-primary/10 transition-colors">
                                    <span class="material-symbols-outlined text-[14px]">edit_location</span>
                                    Change
                                </button>
                            </div>
                            <div v-else
                                class="flex items-center gap-3 p-3 bg-orange-50 dark:bg-orange-500/10 rounded-lg border border-orange-200 dark:border-orange-500/20 cursor-pointer hover:bg-orange-100 dark:hover:bg-orange-500/20 transition-colors"
                                @click="pickFromMap">
                                <span class="material-symbols-outlined text-orange-500 text-xl">location_searching</span>
                                <div>
                                    <p class="text-sm font-semibold text-orange-700 dark:text-orange-300">No location set</p>
                                    <p class="text-xs text-orange-500">Click here or "Change" to pick a spot on the map</p>
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Status</label>
                                <select v-model="zoneForm.status" class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none text-gray-900 dark:text-white">
                                    <option value="Active" class="bg-white dark:bg-gray-800">Active</option>
                                    <option value="Inactive" class="bg-white dark:bg-gray-800">Inactive</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Zone Color</label>
                                <div class="flex gap-1.5 flex-wrap">
                                    <button v-for="(hex, name) in { blue: '#3b82f6', green: '#22c55e', red: '#ef4444', orange: '#f97316', purple: '#a855f7', teal: '#14b8a6', indigo: '#6366f1', yellow: '#eab308' }"
                                        :key="name"
                                        type="button"
                                        @click="zoneForm.color = name"
                                        :title="name"
                                        class="w-6 h-6 rounded-full border-2 transition-all"
                                        :style="{ backgroundColor: hex }"
                                        :class="zoneForm.color === name ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'">
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">Alert Settings</label>
                            <div class="flex items-center gap-2 p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                                <input type="checkbox" id="entryAlert" v-model="zoneForm.entryAlert" class="rounded text-primary focus:ring-offset-0 bg-transparent border-gray-300">
                                <label for="entryAlert" class="text-sm text-gray-700 dark:text-white select-none cursor-pointer">Trigger alert on vehicle entry</label>
                            </div>
                        </div>

                        <p v-if="saveError" class="text-xs text-red-500">{{ saveError }}</p>
                    </div>

                    <div class="p-5 pt-0 flex justify-end gap-3 flex-shrink-0 border-t border-gray-100 dark:border-white/10">
                        <button @click="closeZoneModal" class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">Cancel</button>
                        <button @click="saveZone" :disabled="isSaving"
                            class="px-6 py-2 bg-primary hover:bg-primary/90 disabled:opacity-60 text-white text-sm font-bold rounded-lg shadow-lg shadow-primary/20 transition-all flex items-center gap-2">
                            <span v-if="isSaving" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                            <span v-else class="material-symbols-outlined text-sm">save</span>
                            {{ zoneModalMode === 'create' ? 'Create Zone' : 'Update Zone' }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'
import { LMap, LTileLayer, LCircle, LTooltip } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

const store = useLogisticStore()
const { filteredZones, alerts, isLoading } = storeToRefs(store)

onMounted(() => store.initialize().catch(() => {}))

// ── Location helpers ───────────────────────────────────────────────────────
const geocodeStatus = ref('')
const draftAddress = ref('')

async function reverseGeocode(lat, lng) {
    draftAddress.value = 'Locating...'
    try {
        const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`,
            { headers: { 'Accept-Language': 'en' } }
        )
        const data = await res.json()
        if (data?.display_name) {
            const parts = data.display_name.split(',').slice(0, 3)
            draftAddress.value = parts.map(p => p.trim()).join(', ')
        } else {
            draftAddress.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
        }
    } catch {
        draftAddress.value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
    }
}

// Start new zone flow: enter pick mode on the map first
function startPickingNewZone() {
    draftAddress.value = ''
    geocodeStatus.value = ''
    zoneModalMode.value = 'create'
    zoneForm.value = {
        id: null,
        name: '',
        type: 'Polygon',
        radius: 5.0,
        hubId: store.activeWarehouse === 'all' ? (store.hubs[0]?.id || null) : store.activeWarehouse,
        status: 'Active',
        color: 'blue',
        entryAlert: false,
        lat: null,
        lng: null,
    }
    pickingFromMap.value = true
    isZoneModalOpen.value = false
}

// View State
const viewMode = ref('map')
const searchQuery = ref('')
const selectedZone = ref(null)
const activeTool = ref('pointer')
const isSaving = ref(false)
const saveError = ref('')
const pickingFromMap = ref(false)

const pickFromMap = () => {
    isZoneModalOpen.value = false
    pickingFromMap.value = true
}

const cancelPick = () => {
    pickingFromMap.value = false
    // Re-open modal only if we already started filling in details
    if (zoneForm.value.name || zoneForm.value.lat) {
        isZoneModalOpen.value = true
    }
}

const onMapClick = (event) => {
    if (!pickingFromMap.value) return
    const lat = parseFloat(event.latlng.lat.toFixed(6))
    const lng = parseFloat(event.latlng.lng.toFixed(6))
    zoneForm.value.lat = lat
    zoneForm.value.lng = lng
    pickingFromMap.value = false
    isZoneModalOpen.value = true
    // Fly the map to the clicked point so user can see the preview circle
    mapRef.value?.leafletObject?.flyTo([lat, lng], Math.max(mapZoom.value, 13), { duration: 0.8 })
    // Reverse-geocode to show human-readable location
    reverseGeocode(lat, lng)
}

// Tool Definitions
const mapTools = [
    { id: 'pointer', icon: 'near_me', label: 'Select' },
    { id: 'polygon', icon: 'pentagon', label: 'Draw Polygon' },
    { id: 'circle', icon: 'radio_button_unchecked', label: 'Draw Circle' },
    { id: 'line', icon: 'timeline', label: 'Draw Route' },
    { id: 'manage', icon: 'settings', label: 'Zone Settings' }
]

// Modal State
const isZoneModalOpen = ref(false)
const zoneModalMode = ref('create')
const zoneForm = ref({
    name: '',
    type: 'Polygon',
    radius: 5.0,
    hubId: store.hubs[0]?.id || null,
    status: 'Active',
    color: 'blue',
    entryAlert: false,
    lat: null,
    lng: null,
})

// Search Logic
const searchedZones = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return filteredZones.value.filter(z =>
        !q ||
        z.name.toLowerCase().includes(q) ||
        z.type.toLowerCase().includes(q)
    )
})

// Dynamic Stats
const vehiclesInZones = computed(() => {
    const active = store.vehicles?.filter(v => v.status === 'Active' || v.status === 'In Transit').length ?? 0
    return active || Math.floor(searchedZones.value.length * 3.5)
})

const breachAlerts = computed(() => {
    return alerts.value.filter(a =>
        a.severity === 'critical' || a.severity === 'high'
    ).length
})

const totalArea = computed(() => {
    return searchedZones.value
        .reduce((acc, z) => acc + (parseFloat(z.radius) || 0) ** 2 * Math.PI, 0)
        .toFixed(1)
})

// ── Leaflet map state ───────────────────────────────────────────
const mapRef = ref(null)
const mapZoom = ref(11)
const mapCurrentCenter = ref([20.5937, 78.9629]) // updated on moveend

// Default center: first hub with coords, else India centre
const mapCenter = computed(() => {
    const hub = store.hubs.find(h => h.lat && h.lng)
    return hub ? [hub.lat, hub.lng] : [20.5937, 78.9629]
})

// Zones enriched with coordinates.
// Priority: 1) zone's own lat/lng, 2) hub's lat/lng, 3) stable fallback grid
const mappableZones = computed(() => {
    const base = mapCenter.value
    return searchedZones.value.map((zone, index) => {
        // Use zone's own stored coordinates first
        if (zone.lat && zone.lng) {
            return { ...zone, lat: Number(zone.lat), lng: Number(zone.lng), hasCoords: true }
        }
        // Fall back to the hub's coordinates
        const hub = store.hubs.find(h => h.id === zone.hubId)
        if (hub?.lat && hub?.lng) {
            return { ...zone, lat: Number(hub.lat), lng: Number(hub.lng), hasCoords: true }
        }
        // Deterministic fallback grid so zones don't overlap
        const cols = 3
        const row = Math.floor(index / cols)
        const col = index % cols
        return {
            ...zone,
            lat: base[0] + (row - 1) * 0.05,
            lng: base[1] + (col - 1) * 0.07,
            hasCoords: false,
        }
    })
})

const COLOR_MAP = {
    blue: '#3b82f6',
    green: '#22c55e',
    red: '#ef4444',
    orange: '#f97316',
    purple: '#a855f7',
    yellow: '#eab308',
    indigo: '#6366f1',
    teal: '#14b8a6',
    pink: '#ec4899',
}

const getZoneColor = (token) => COLOR_MAP[token] || '#6366f1'

const onMapMove = () => {
    const lmap = mapRef.value?.leafletObject
    if (lmap) {
        const c = lmap.getCenter()
        mapCurrentCenter.value = [c.lat, c.lng]
        mapZoom.value = lmap.getZoom()
    }
}

// Fly to zone center when selected
watch(selectedZone, (zone) => {
    if (!zone) return
    if (zone.lat && zone.lng) {
        mapRef.value?.leafletObject?.flyTo([Number(zone.lat), Number(zone.lng)], 13, { duration: 1 })
    } else {
        const hub = store.hubs.find(h => h.id === zone.hubId)
        if (hub?.lat && hub?.lng) {
            mapRef.value?.leafletObject?.flyTo([Number(hub.lat), Number(hub.lng)], 13, { duration: 1 })
        }
    }
})

// Actions
const selectZone = (zone) => {
    selectedZone.value = zone
}

const getZoneIcon = (type) => {
    const icons = {
        'Polygon': 'pentagon',
        'Circle': 'radio_button_unchecked',
        'Exclusion': 'do_not_disturb_on',
        'Corridor': 'alt_route'
    }
    return icons[type] || 'location_on'
}

const openZoneModal = (mode, zone = null) => {
    zoneModalMode.value = mode
    saveError.value = ''
    geocodeStatus.value = ''
    pickingFromMap.value = false
    if (mode === 'edit' && zone) {
        zoneForm.value = { ...zone, color: zone.color || 'blue', entryAlert: false }
        // Reverse-geocode existing coordinates so the label shows a place name
        if (zone.lat && zone.lng) {
            reverseGeocode(zone.lat, zone.lng)
        } else {
            draftAddress.value = ''
        }
    }
    isZoneModalOpen.value = true
}

const closeZoneModal = () => {
    isZoneModalOpen.value = false
    saveError.value = ''
    pickingFromMap.value = false
    geocodeStatus.value = ''
    draftAddress.value = ''
}

const saveZone = async () => {
    if (!zoneForm.value.name?.trim()) {
        saveError.value = 'Zone name is required.'
        return
    }
    isSaving.value = true
    saveError.value = ''
    try {
        if (zoneModalMode.value === 'create') {
            await store.createZone(zoneForm.value)
        } else {
            await store.updateZone(zoneForm.value.id, zoneForm.value)
        }
        closeZoneModal()
    } catch (e) {
        saveError.value = e?.message || 'Failed to save zone. Please try again.'
    } finally {
        isSaving.value = false
    }
}

const handleDeleteZone = async (id) => {
    if (!confirm('Are you sure you want to delete this zone? This action cannot be undone.')) return
    try {
        await store.deleteZone(id)
        if (selectedZone.value?.id === id) selectedZone.value = null
    } catch (e) {
        console.error('Failed to delete zone:', e)
    }
}
</script>
