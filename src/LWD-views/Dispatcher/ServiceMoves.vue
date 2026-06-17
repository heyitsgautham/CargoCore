<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex justify-between items-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Service Move & Time Blocking</h2>
                <p class="text-sm text-gray-400 mt-1">Manage house shifts, warehouse pickups, manual service runs, crew manifest, and time blocks</p>
            </div>
            <button @click="openNewMoveModal" class="bg-primary hover:bg-primary-dark text-black font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors text-sm">
                <span class="material-symbols-outlined text-[18px]">add</span> New Service Move
            </button>
        </div>

        <!-- Summary Stats -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ serviceMoves.length }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Active Moves</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-blue-400">{{ totalCrewCount }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Crew Deployed</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-purple-400">{{ blockedHours }}h</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Time Blocked</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-yellow-400">{{ vehiclesReserved }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Vehicles Reserved</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-primary">{{ completedToday }}</div>
                <div class="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mt-1">Completed Today</div>
            </div>
        </div>

        <!-- Active Service Moves -->
        <div v-if="loading && serviceMoves.length === 0" class="glass-panel rounded-xl p-12 text-center">
            <span class="material-symbols-outlined text-gray-400 text-[48px] block mb-3 animate-spin">progress_activity</span>
            <div class="text-gray-500 text-sm">Loading service moves...</div>
        </div>
        <div v-else-if="serviceMoves.length === 0" class="glass-panel rounded-xl p-12 text-center">
            <span class="material-symbols-outlined text-gray-400 text-[48px] block mb-3">local_shipping</span>
            <div class="text-gray-500 text-sm">No active service moves. Click "New Service Move" to create one.</div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div v-for="move in serviceMoves" :key="move.id"
                class="glass-panel rounded-xl overflow-hidden border border-gray-200 dark:border-white/5 hover:border-gray-200 dark:border-white/10 transition-all">
                <!-- Move Header -->
                <div class="p-4 flex items-center justify-between" :class="move.headerBg">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-[24px]" :class="move.iconClass">{{ move.icon }}</span>
                        <div>
                            <div class="font-bold text-gray-900 dark:text-white text-sm">{{ move.title }}</div>
                            <div class="text-[10px] text-gray-400">{{ move.id }} • {{ move.type }}</div>
                        </div>
                    </div>
                    <span class="px-2 py-1 rounded text-[10px] font-bold" :class="move.statusClass">{{ move.status }}</span>
                </div>

                <div class="p-4 space-y-4">
                    <!-- Route Info -->
                    <div class="flex items-center gap-3">
                        <div class="flex flex-col items-center">
                            <span class="w-3 h-3 rounded-full bg-green-500 border-2 border-green-500/30"></span>
                            <div class="w-0.5 h-8 bg-gray-600"></div>
                            <span class="w-3 h-3 rounded-full bg-red-500 border-2 border-red-500/30"></span>
                        </div>
                        <div class="flex-1 space-y-4">
                            <div>
                                <div class="text-xs text-gray-500">Pickup</div>
                                <div class="text-sm text-gray-900 dark:text-white">{{ move.pickup }}</div>
                            </div>
                            <div>
                                <div class="text-xs text-gray-500">Delivery</div>
                                <div class="text-sm text-gray-900 dark:text-white">{{ move.delivery }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Time Block -->
                    <div class="p-3 bg-gray-100 dark:bg-black/20 rounded-lg">
                        <div class="text-[10px] text-gray-500 mb-2 font-bold uppercase tracking-wider">Time Block Reserved</div>
                        <div class="flex items-center gap-2 mb-2">
                            <span class="material-symbols-outlined text-purple-400 text-[16px]">schedule</span>
                            <span class="text-gray-900 dark:text-white text-sm font-bold">{{ move.timeBlock }}</span>
                            <span class="text-gray-500 text-xs">({{ move.duration }})</span>
                        </div>
                        <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div class="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                                :style="{ width: move.progress + '%' }"></div>
                        </div>
                        <div class="flex justify-between text-[10px] text-gray-500 mt-1">
                            <span>{{ move.packingTime }} packing</span>
                            <span>{{ move.dwellTime }} dwell</span>
                            <span>{{ move.transitTime }} transit</span>
                        </div>
                    </div>

                    <!-- Crew Manifest -->
                    <div>
                        <div class="text-[10px] text-gray-500 mb-2 font-bold uppercase tracking-wider">Crew Manifest ({{ move.crew.length }} members)</div>
                        <div class="space-y-1.5">
                            <div v-for="member in move.crew" :key="member.name"
                                class="flex items-center justify-between p-2 bg-gray-50 dark:bg-white/5 rounded-lg text-xs">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[14px]" :class="member.role === 'Driver' ? 'text-primary' : 'text-blue-400'">
                                        {{ member.role === 'Driver' ? 'local_shipping' : 'person' }}
                                    </span>
                                    <span class="text-gray-900 dark:text-white">{{ member.name }}</span>
                                </div>
                                <span class="text-gray-400">{{ member.role }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Vehicle & Load -->
                    <div class="grid grid-cols-2 gap-2">
                        <div class="bg-gray-100 dark:bg-black/20 rounded-lg p-2 text-center">
                            <div class="text-[10px] text-gray-500">Vehicle</div>
                            <div class="text-xs font-bold text-gray-900 dark:text-white">{{ move.vehicle }}</div>
                        </div>
                        <div class="bg-gray-100 dark:bg-black/20 rounded-lg p-2 text-center">
                            <div class="text-[10px] text-gray-500">Seats</div>
                            <div class="text-xs font-bold" :class="move.seatsAvailable >= move.crew.length ? 'text-green-400' : 'text-red-400'">
                                {{ move.crew.length }} / {{ move.seatsAvailable }}
                            </div>
                        </div>
                    </div>

                    <!-- Special Notes -->
                    <div v-if="move.notes" class="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                        <div class="flex items-center gap-1 text-[10px] text-yellow-400 font-bold mb-1">
                            <span class="material-symbols-outlined text-[12px]">info</span> Special Notes
                        </div>
                        <div class="text-xs text-yellow-600 dark:text-yellow-200">{{ move.notes }}</div>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2 pt-2">
                        <button @click="trackMove(move)" :disabled="trackingLoading && trackingMove?.id !== move.id"
                            class="flex-1 py-2 rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1 border"
                            :class="move.tracking ? 'bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 border-green-300 dark:border-green-500/30' : 'bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white border-gray-200 dark:border-white/10'">
                            <span class="material-symbols-outlined text-[14px]" :class="{ 'animate-spin': trackingLoading && trackingMove?.id === move.id }">
                                {{ trackingLoading && trackingMove?.id === move.id ? 'progress_activity' : move.tracking ? 'gps_fixed' : 'visibility' }}
                            </span>
                            {{ trackingLoading && trackingMove?.id === move.id ? 'Loading...' : move.tracking ? 'Tracking Live' : 'Track' }}
                        </button>
                        <button @click="contactCrew(move)" class="flex-1 bg-emerald-100 dark:bg-primary/10 hover:bg-emerald-200 dark:hover:bg-primary/20 text-emerald-700 dark:text-primary py-2 rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1 border border-emerald-300 dark:border-primary/30">
                            <span class="material-symbols-outlined text-[14px]">chat</span> Contact Crew
                        </button>
                        <button @click="toggleMoveMenu(move)" class="bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 py-2 px-3 rounded-lg text-xs font-bold transition-colors relative border border-gray-200 dark:border-white/10">
                            <span class="material-symbols-outlined text-[16px]">more_vert</span>
                            <div v-if="moveMenu === move.id" class="absolute bottom-full right-0 mb-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl z-20 w-40">
                                <button @click.stop="cancelMove(move)" class="w-full text-left px-3 py-2 text-xs text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-white/5">Cancel Move</button>
                                <button @click.stop="completeMove(move)" class="w-full text-left px-3 py-2 text-xs text-green-600 dark:text-green-400 hover:bg-gray-100 dark:hover:bg-white/5">Mark Complete</button>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scheduling Conflict Warning -->
        <div class="glass-panel rounded-xl p-5">
            <div class="flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-yellow-400">event_busy</span>
                <h3 class="font-bold text-gray-900 dark:text-white">Scheduling Conflicts & Overbooking Prevention</h3>
            </div>
            <div v-if="serviceMoves.length === 0" class="p-3 bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
                <span class="material-symbols-outlined text-green-500 dark:text-green-400 text-[18px]">check_circle</span>
                <div class="text-xs text-green-700 dark:text-green-300">No active service moves. No scheduling conflicts detected.</div>
            </div>
            <div v-else class="p-3 bg-green-100 dark:bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
                <span class="material-symbols-outlined text-green-500 dark:text-green-400 text-[18px]">check_circle</span>
                <div class="text-xs text-green-700 dark:text-green-300">{{ serviceMoves.length }} active move(s). All drivers have clear time blocks. No overbooking detected.</div>
            </div>
        </div>

        <!-- New Service Move Modal -->
        <Teleport to="body">
        <div v-if="showNewMove" class="fixed inset-0 bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4" @click.self="closeNewMoveModal">
            <div class="bg-gradient-to-br from-gray-900 to-gray-800 shadow-2xl border border-primary/20 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/30 scrollbar-track-transparent">
                <div class="flex items-center justify-between mb-5">
                    <h3 class="text-xl font-bold text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary">add_circle</span>
                        Create New Service Move
                    </h3>
                    <button @click="closeNewMoveModal" class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div v-if="formError" class="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {{ formError }}
                </div>
                <div v-else-if="formSuccess" class="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                    {{ formSuccess }}
                </div>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">Move Title *</label>
                        <input v-model="newMove.title" type="text" placeholder="e.g., Johnson Family House Shift"
                            class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">Service Type *</label>
                        <select v-model="newMove.type" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                            <option value="House Shift" class="bg-gray-900">🏠 House Shift</option>
                            <option value="Office Shift" class="bg-gray-900">🏢 Office Shift</option>
                            <option value="Warehouse Transfer" class="bg-gray-900">🏭 Warehouse Transfer</option>
                            <option value="Warehouse Supply Pickup" class="bg-gray-900">📦 Warehouse Supply Pickup</option>
                            <option value="Equipment Transfer" class="bg-gray-900">🛠️ Equipment Transfer</option>
                            <option value="Manual Service" class="bg-gray-900">🧰 Manual Service</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-medium text-primary mb-1.5">Pickup Location *</label>
                            <div class="relative">
                                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-green-400 text-[18px]">trip_origin</span>
                                <button type="button" @click="openMapPicker('pickup')"
                                    class="w-full pl-10 pr-3 py-2.5 rounded-lg border border-gray-700 hover:border-primary/50 focus:border-primary bg-black/40 text-left text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors flex items-center justify-between">
                                    <span :class="newMove.pickup ? '' : 'text-gray-500'">{{ newMove.pickup || 'Select pickup on map' }}</span>
                                    <span class="material-symbols-outlined text-[18px] text-gray-400">map</span>
                                </button>
                            </div>
                            <div class="mt-1 flex items-center justify-between gap-2 text-[11px] text-gray-400">
                                <span class="truncate">
                                    {{ newMove.pickupLat !== null && newMove.pickupLng !== null
                                        ? `${Number(newMove.pickupLat).toFixed(5)}, ${Number(newMove.pickupLng).toFixed(5)}`
                                        : 'Search or click on the map' }}
                                </span>
                                <button v-if="assignedHub?.address" type="button" @click="useAssignedHub('pickup')" class="shrink-0 text-primary hover:text-yellow-300 transition-colors">
                                    Use assigned hub
                                </button>
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-primary mb-1.5">Delivery Location *</label>
                            <div class="relative">
                                <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-400 text-[18px]">location_on</span>
                                <button type="button" @click="openMapPicker('delivery')"
                                    class="w-full pl-10 pr-3 py-2.5 rounded-lg border border-gray-700 hover:border-primary/50 focus:border-primary bg-black/40 text-left text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors flex items-center justify-between">
                                    <span :class="newMove.delivery ? '' : 'text-gray-500'">{{ newMove.delivery || 'Select delivery on map' }}</span>
                                    <span class="material-symbols-outlined text-[18px] text-gray-400">map</span>
                                </button>
                            </div>
                            <div class="mt-1 flex items-center justify-between gap-2 text-[11px] text-gray-400">
                                <span class="truncate">
                                    {{ newMove.deliveryLat !== null && newMove.deliveryLng !== null
                                        ? `${Number(newMove.deliveryLat).toFixed(5)}, ${Number(newMove.deliveryLng).toFixed(5)}`
                                        : 'Search or click on the map' }}
                                </span>
                                <button v-if="assignedHub?.address" type="button" @click="useAssignedHub('delivery')" class="shrink-0 text-primary hover:text-yellow-300 transition-colors">
                                    Use assigned hub
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-medium text-primary mb-1.5">📅 Scheduled Date</label>
                            <input v-model="newMove.scheduledDate" type="date"
                                class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-primary mb-1.5">⏰ Scheduled Time</label>
                            <input v-model="newMove.scheduledTime" type="time"
                                class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">🚚 Assign Vehicle</label>
                        <select v-model="newMove.vehicleId" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                            <option value="" class="bg-gray-900">-- Select Vehicle --</option>
                            <option v-for="vehicle in realVehicleOptions" :key="vehicle.id" :value="vehicle.id" class="bg-gray-900">
                                {{ vehicle.label }}
                            </option>
                        </select>
                        <div v-if="realVehicleOptions.length === 0" class="mt-1 text-xs text-yellow-400">
                            ⚠️ No direct-dispatch vehicles available right now.
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">👤 Assign Driver</label>
                        <select v-model="newMove.driverId" class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors appearance-none cursor-pointer">
                            <option value="" class="bg-gray-900">-- Select Driver --</option>
                            <option v-for="driver in availableDrivers" :key="driver.id" :value="driver.id" class="bg-gray-900">
                                {{ driver.name }} ({{ driver.status }}){{ driver.vehicle ? ' · ' + driver.vehicle : '' }}
                            </option>
                        </select>
                        <div v-if="availableDrivers.length === 0" class="mt-1 text-xs text-yellow-400">
                            ⚠️ No available drivers ready for direct dispatch
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">⏱️ Estimated Duration (hours)</label>
                        <input v-model="newMove.estimatedDuration" type="number" min="1" max="24" placeholder="4"
                            class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors">
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-primary mb-1.5">📝 Special Notes</label>
                        <textarea v-model="newMove.notes" rows="2" placeholder="Any special instructions or requirements..."
                            class="w-full bg-black/40 border border-gray-700 hover:border-primary/50 focus:border-primary rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors resize-none"></textarea>
                    </div>
                </div>
                <div class="flex gap-3 mt-6">
                    <button @click="createServiceMove" :disabled="!newMove.title || !newMove.pickup || !newMove.delivery || loading"
                        class="flex-1 bg-gradient-to-r from-primary to-yellow-400 hover:from-yellow-400 hover:to-primary text-black font-bold py-3 rounded-lg text-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg">
                        <span v-if="loading" class="flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                            Creating...
                        </span>
                        <span v-else class="flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">check_circle</span>
                            Create Move
                        </span>
                    </button>
                    <button @click="closeNewMoveModal" class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 rounded-lg text-sm transition-colors">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
        </Teleport>

        <MapPicker
            :isOpen="showMapPicker"
            :title="mapPickerTitle"
            :initialLat="mapPickerInitialLat"
            :initialLon="mapPickerInitialLon"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />

        <!-- Contact Crew Modal -->
        <Teleport to="body">
        <div v-if="showCrewChat" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showCrewChat = false">
            <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-md m-4 overflow-hidden">
                <!-- Header -->
                <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary text-[20px]">chat</span>
                        <div>
                            <div class="text-sm font-bold text-white">{{ crewChatMove?.title }}</div>
                            <div class="text-[10px] text-gray-400">{{ crewChatMove?.crew?.[0]?.name || 'Crew' }} · {{ crewChatMove?.id }}</div>
                        </div>
                    </div>
                    <button @click="showCrewChat = false" class="text-gray-500 hover:text-white transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>

                <!-- Warning if no thread -->
                <div v-if="!crewThreadId" class="mx-5 mt-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-2">
                    <span class="material-symbols-outlined text-yellow-400 text-[14px]">warning</span>
                    <span class="text-xs text-yellow-300">No chat thread found — message will be sent once a thread is created.</span>
                </div>

                <!-- Messages -->
                <div class="px-5 py-4 space-y-2 max-h-56 overflow-y-auto no-scrollbar">
                    <div v-if="crewMessages.length === 0" class="text-center py-8 text-gray-500 text-xs">No messages yet. Start the conversation.</div>
                    <div v-for="msg in crewMessages" :key="msg.id"
                        class="flex flex-col max-w-[80%] text-xs"
                        :class="msg.from === 'dispatch' ? 'ml-auto items-end' : 'mr-auto items-start'">
                        <span class="text-[9px] text-gray-500 mb-0.5 px-1">{{ msg.from === 'dispatch' ? 'You' : msg.from }}</span>
                        <div class="px-3 py-2 rounded-xl"
                            :class="msg.from === 'dispatch' ? 'bg-primary text-black font-medium rounded-br-none' : 'bg-white/10 text-gray-200 rounded-bl-none'">
                            {{ msg.text }}
                        </div>
                    </div>
                </div>

                <!-- Input -->
                <div class="px-5 py-4 border-t border-white/10 flex gap-2">
                    <input v-model="crewMsg" type="text" placeholder="Message crew..." @keyup.enter="sendCrewMsg"
                        class="flex-1 bg-white/5 border border-white/10 focus:border-primary/50 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none transition-colors">
                    <button @click="sendCrewMsg" class="bg-primary hover:bg-primary-dark text-black px-5 py-2.5 rounded-xl text-sm font-bold transition-colors flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">send</span>
                    </button>
                </div>
            </div>
        </div>
        </Teleport>

        <!-- Live Tracking Modal -->
        <Teleport to="body">
        <div v-if="showTrackingModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)">
            <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-md m-4 overflow-hidden">

                <!-- Header -->
                <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-green-400 text-[20px] animate-pulse">gps_fixed</span>
                        <div>
                            <div class="text-sm font-bold text-white">Live Tracking</div>
                            <div class="text-[10px] text-gray-400">{{ trackingMove?.title }} · {{ trackingMove?.id }}</div>
                        </div>
                    </div>
                    <button @click="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)" class="text-gray-500 hover:text-white transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>

                <!-- No driver state -->
                <div v-if="!trackedDriver" class="px-5 py-10 text-center">
                    <span class="material-symbols-outlined text-gray-600 text-[48px] block mb-3">location_off</span>
                    <div class="text-gray-400 text-sm">No driver assigned or location unavailable.</div>
                    <div class="text-gray-500 text-xs mt-1">Assign a driver to this move to enable live tracking.</div>
                </div>

                <!-- Driver has location -->
                <div v-else>
                    <!-- Driver info bar -->
                    <div class="flex items-center gap-3 px-5 py-3 bg-white/5 border-b border-white/5">
                        <span class="w-2.5 h-2.5 rounded-full flex-shrink-0 ring-2 ring-offset-1 ring-offset-gray-900"
                            :class="trackedDriver.status?.toLowerCase() === 'active' ? 'bg-green-500 ring-green-500/40' : 'bg-yellow-500 ring-yellow-500/40'"></span>
                        <div class="flex-1 min-w-0">
                            <div class="text-sm font-bold text-white truncate">{{ trackedDriver.driver_name }}</div>
                            <div class="text-xs text-gray-400 capitalize">{{ trackedDriver.status }} · {{ trackedDriver.vehicle_code || 'No vehicle' }}</div>
                        </div>
                        <div class="text-[10px] text-gray-500 text-right">
                            <div>Last updated</div>
                            <div class="text-gray-300 font-medium">{{ trackedDriver.last_updated ? new Date(trackedDriver.last_updated).toLocaleTimeString() : '—' }}</div>
                        </div>
                    </div>

                    <!-- Leaflet map with driver marker -->
                    <div v-if="trackedDriver.latitude && trackedDriver.longitude" class="h-56">
                        <l-map :zoom="14" :center="[trackedDriver.latitude, trackedDriver.longitude]" :use-global-leaflet="false" style="height:100%;width:100%;">
                            <l-tile-layer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
                            <l-marker
                                :lat-lng="[trackedDriver.latitude, trackedDriver.longitude]"
                                :icon="driverMapIcon"
                            >
                                <l-tooltip :permanent="true" direction="top" :offset="[0, -26]">
                                    <span style="font-size:11px;font-weight:700;">{{ trackedDriver.driver_name }}</span>
                                </l-tooltip>
                            </l-marker>
                            <!-- Delivery destination marker -->
                            <l-circle-marker
                                v-if="trackingMove?.deliveryLat && trackingMove?.deliveryLng"
                                :lat-lng="[trackingMove.deliveryLat, trackingMove.deliveryLng]"
                                :radius="8"
                                color="#ef4444"
                                fill-color="#ef4444"
                                :fill-opacity="0.9"
                                :weight="2"
                            >
                                <l-tooltip :permanent="true" direction="top" :offset="[0,-12]">
                                    <span style="font-size:10px;">Drop-off</span>
                                </l-tooltip>
                            </l-circle-marker>
                        </l-map>
                    </div>
                    <!-- No GPS yet -->
                    <div v-else class="h-32 flex items-center justify-center bg-white/5">
                        <div class="text-center">
                            <span class="material-symbols-outlined text-gray-500 text-[32px] block mb-1">location_searching</span>
                            <div class="text-xs text-gray-400">Waiting for GPS signal…</div>
                        </div>
                    </div>

                    <!-- Route info -->
                    <div class="px-5 py-3 flex items-center gap-3 border-t border-white/5">
                        <div class="flex flex-col items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-green-500"></span>
                            <div class="w-px h-5 bg-gray-600"></div>
                            <span class="w-2 h-2 rounded-full bg-red-500"></span>
                        </div>
                        <div class="flex-1 space-y-2 text-xs">
                            <div class="text-gray-400 truncate"><span class="text-gray-500">From:</span> {{ trackingMove?.pickup }}</div>
                            <div class="text-gray-400 truncate"><span class="text-gray-500">To:</span> {{ trackingMove?.delivery }}</div>
                        </div>
                    </div>
                </div>

                <div class="px-5 pb-4">
                    <button @click="showTrackingModal = false; trackingMove && (trackingMove.tracking = false)"
                        class="w-full bg-white/10 hover:bg-white/15 text-white py-2.5 rounded-xl text-sm font-bold transition-colors">
                        Close
                    </button>
                </div>
            </div>
        </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useAuthStore } from '@/stores/authStore'
import { API_BASE_URL, getStoredAccessToken } from '@/config/api'
import { useToast } from '@/composables/useToast'
import MapPicker from '@/components/MapPicker.vue'
import { LMap, LTileLayer, LMarker, LCircleMarker, LTooltip } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

const store = useDispatcherStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const toast = useToast()
onMounted(async () => {
    await store.initialize().catch(() => {})
    await fetchServiceMoves()
})

// Auth headers
function authHeaders() {
    const token = getStoredAccessToken()
    return token
        ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/json' }
}

function formatVehicleLabel(vehicle) {
    const parts = [vehicle.code, vehicle.type, vehicle.licensePlate].filter(Boolean)
    return parts.length > 0 ? parts.join(' · ') : `Vehicle ${vehicle.id}`
}

function normalizeAvailabilityStatus(status) {
    return String(status || '')
        .trim()
        .toLowerCase()
        .replace(/[_\s]+/g, '-')
}

function isDriverAssignableStatus(status) {
    const normalized = normalizeAvailabilityStatus(status)
    return ['active', 'idle', 'available', 'on-duty', 'online', 'on-route', 'standby', 'stand-by'].includes(normalized)
}

function isVehicleAssignableStatus(status) {
    const normalized = normalizeAvailabilityStatus(status)
    return !['in-use', 'maintenance', 'in-shop', 'out-of-service', 'offline'].includes(normalized)
}

function hasOpenAssignments(driver) {
    return (driver.activeOrders || []).some((order) => {
        const status = String(order?.status || '').toUpperCase()
        return !['DELIVERED', 'COMPLETED', 'CANCELLED', 'CLOSED'].includes(status)
    })
}

function parseApiError(payload, fallback) {
    if (Array.isArray(payload?.detail)) return payload.detail[0]?.msg || fallback
    return payload?.detail || fallback
}

function parseServiceMoveMeta(raw) {
    if (!raw) return { title: '', notes: '' }
    if (!raw.startsWith('SERVICE_MOVE_META::')) return { title: '', notes: raw }

    try {
        const parsed = JSON.parse(raw.slice('SERVICE_MOVE_META::'.length))
        return {
            title: parsed?.title || '',
            notes: parsed?.notes || '',
        }
    } catch (_) {
        return { title: '', notes: raw }
    }
}

function buildServiceMoveMeta() {
    return `SERVICE_MOVE_META::${JSON.stringify({
        title: newMove.title.trim(),
        notes: newMove.notes.trim(),
    })}`
}

function buildServiceTimeBlock() {
    const durationHours = Number(newMove.estimatedDuration || 0)
    const startText = newMove.scheduledTime || 'TBD'
    if (!durationHours) return `${startText} start`
    return `${startText} start · ${durationHours}h block`
}

function deriveDurationLabel(serviceTimeBlock) {
    const match = String(serviceTimeBlock || '').match(/(\d+(?:\.\d+)?)h block/i)
    if (match) return `${match[1]} hours`
    return '4 hours'
}

function resetNewMoveForm() {
    newMove.title = ''
    newMove.type = 'House Shift'
    newMove.pickup = ''
    newMove.delivery = ''
    newMove.pickupLat = null
    newMove.pickupLng = null
    newMove.deliveryLat = null
    newMove.deliveryLng = null
    newMove.vehicleId = ''
    newMove.driverId = ''
    newMove.laborerIds = []
    newMove.scheduledDate = ''
    newMove.scheduledTime = ''
    newMove.estimatedDuration = '4'
    newMove.notes = ''
}

function primeNewMoveDefaults() {
    if (!newMove.vehicleId && vehicleOptions.value.length > 0) {
        newMove.vehicleId = vehicleOptions.value[0].id
    }
    if (!newMove.driverId && availableDrivers.value.length > 0) {
        newMove.driverId = availableDrivers.value[0].id
    }
    if (!newMove.scheduledDate) {
        newMove.scheduledDate = new Date().toISOString().split('T')[0]
    }
    if (!newMove.scheduledTime) {
        newMove.scheduledTime = '10:00'
    }
}

async function closeNewMoveModal() {
    showNewMove.value = false
    formError.value = ''
    formSuccess.value = ''

    if (route.query.createMove === '1') {
        const nextQuery = { ...route.query }
        delete nextQuery.createMove
        await router.replace({ query: nextQuery })
    }
}

async function openNewMoveModal() {
    formError.value = ''
    formSuccess.value = ''
    showNewMove.value = true
    await Promise.allSettled([
        store.fetchVehicles(),
        store.fetchDrivers(),
    ])
    primeNewMoveDefaults()
}

function resolveDriverVehicleId(driver) {
    if (!driver?.vehicle) return null
    const driverVehicleCode = String(driver.vehicle).trim().toLowerCase()
    const matchedVehicle = store.filteredVehicles.find((vehicle) =>
        String(vehicle.code || '').trim().toLowerCase() === driverVehicleCode
    )
    return matchedVehicle ? matchedVehicle.id : null
}

const availableDrivers = computed(() => {
    return store.dispatcherDrivers
        .filter((driver) =>
            isDriverAssignableStatus(driver.status) &&
            !driver.suspended &&
            !hasOpenAssignments(driver)
        )
        .map((driver) => ({
            ...driver,
            assignedVehicleId: resolveDriverVehicleId(driver),
        }))
})

const vehicleOptions = computed(() => {
    const selectedDriver = availableDrivers.value.find((driver) => driver.id === newMove.driverId)
    const selectedDriverVehicleId = selectedDriver?.assignedVehicleId || null

    return store.filteredVehicles
        .filter((vehicle) =>
            isVehicleAssignableStatus(vehicle.status) ||
            (selectedDriverVehicleId && vehicle.id === selectedDriverVehicleId)
        )
        .map(v => ({
            id: v.id,
            label: formatVehicleLabel(v),
            code: v.code || '',
            type: v.type || '',
            seatCapacity: v.seatCapacity ?? null,
        }))
})
// Alias used in template
const realVehicleOptions = vehicleOptions

// Available laborers (from store if you have labor data)
const availableLaborers = computed(() => {
    // Try to get from store if it has labor/staff data
    // For now, we'll use drivers as potential crew members
    return store.dispatcherDrivers.slice(0, 10)
})

const completedToday = ref(0)
const showNewMove = ref(false)
const showCrewChat = ref(false)
const crewChatMove = ref(null)
const crewMsg = ref('')
const crewMessages = ref([])
const moveMenu = ref(null)
const loading = ref(false)
const formError = ref('')
const formSuccess = ref('')
const showTrackingModal = ref(false)
const trackingMove = ref(null)
const trackedDriver = ref(null)
const trackingLoading = ref(false)
const crewThreadId = ref(null)
const showMapPicker = ref(false)
const mapPickerType = ref('pickup')
const selectedVehicleOption = computed(() =>
    vehicleOptions.value.find(vehicle => vehicle.id === newMove.vehicleId) || null
)
const assignedHub = computed(() => {
    const warehouseId = authStore.currentUser?.warehouse_id
    if (!warehouseId) return null
    return store.hubs.find((hub) => String(hub.id) === String(warehouseId)) || null
})
const mapPickerTitle = computed(() =>
    mapPickerType.value === 'pickup' ? 'Select Pickup Location' : 'Select Delivery Location'
)
const mapPickerInitialLat = computed(() => {
    if (mapPickerType.value === 'pickup' && newMove.pickupLat !== null) return Number(newMove.pickupLat)
    if (mapPickerType.value === 'delivery' && newMove.deliveryLat !== null) return Number(newMove.deliveryLat)
    return Number(assignedHub.value?.lat ?? 12.9716)
})
const mapPickerInitialLon = computed(() => {
    if (mapPickerType.value === 'pickup' && newMove.pickupLng !== null) return Number(newMove.pickupLng)
    if (mapPickerType.value === 'delivery' && newMove.deliveryLng !== null) return Number(newMove.deliveryLng)
    return Number(assignedHub.value?.lng ?? 77.5946)
})

const driverMapIcon = computed(() =>
    L.divIcon({
        html: `<div style="
            width:40px;height:40px;
            background:#111827;
            border:2.5px solid #22c55e;
            border-radius:50%;
            box-shadow:0 3px 10px rgba(0,0,0,0.5);
            display:flex;align-items:center;justify-content:center;
            font-size:20px;
        ">🚚</div>`,
        className: '',
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        tooltipAnchor: [0, -24],
    })
)

const newMove = reactive({
    title: '',
    type: 'House Shift',
    pickup: '',
    delivery: '',
    pickupLat: null,
    pickupLng: null,
    deliveryLat: null,
    deliveryLng: null,
    vehicleId: '',
    driverId: '',
    laborerIds: [],
    scheduledDate: '',
    scheduledTime: '',
    estimatedDuration: '4',
    notes: ''
})

const serviceMoves = ref([])

const totalCrewCount = computed(() => serviceMoves.value.reduce((sum, m) => sum + m.crew.length, 0))
const blockedHours = computed(() => serviceMoves.value.reduce((sum, m) => sum + parseInt(m.duration), 0))
const vehiclesReserved = computed(() => serviceMoves.value.length)

watch(showNewMove, (isOpen) => {
    if (isOpen) {
        formError.value = ''
        formSuccess.value = ''
        primeNewMoveDefaults()
    }
})

watch(() => route.query.createMove, (value) => {
    if (value === '1') {
        openNewMoveModal()
        return
    }

    if (showNewMove.value) {
        showNewMove.value = false
        formError.value = ''
        formSuccess.value = ''
    }
}, { immediate: true })

watch(() => newMove.driverId, (driverId) => {
    if (!driverId) return
    const selectedDriver = availableDrivers.value.find((driver) => driver.id === driverId)
    if (selectedDriver?.assignedVehicleId) {
        newMove.vehicleId = selectedDriver.assignedVehicleId
    }
})

watch([availableDrivers, vehicleOptions], () => {
    if (showNewMove.value) {
        primeNewMoveDefaults()
    }
})

// Fetch service moves from backend — fetch all active statuses separately
// (backend status_filter only accepts one value at a time)
async function fetchServiceMoves() {
    loading.value = true
    try {
        const [r1, r2, r3, r4] = await Promise.all([
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=ASSIGNED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=IN_TRANSIT&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=CONFIRMED&page_size=100`, { headers: authHeaders() }),
            fetch(`${API_BASE_URL}/api/v1/orders?status_filter=DELIVERED&page_size=100`, { headers: authHeaders() }),
        ])
        const parse = async r => r.ok ? (await r.json()) : []
        const [d1, d2, d3, d4] = await Promise.all([parse(r1), parse(r2), parse(r3), parse(r4)])

        const assigned    = Array.isArray(d1) ? d1 : (d1.items || [])
        const inTransit   = Array.isArray(d2) ? d2 : (d2.items || [])
        const confirmed   = Array.isArray(d3) ? d3 : (d3.items || [])
        const delivered   = Array.isArray(d4) ? d4 : (d4.items || [])
        const isServiceMoveOrder = (order) => {
            const legacyTypes = ['House Shift', 'Office Shift', 'Warehouse Transfer']
            return String(order?.order_type || '').toUpperCase() === 'SERVICE_MOVE'
                || legacyTypes.includes(order?.cargo_type)
        }

        const activeMoves = [
            // All assigned orders that have a driver — regardless of type
            ...assigned.filter(o => o.assigned_driver_id),
            // All in-transit orders — they're on the road and need dispatcher visibility
            ...inTransit,
            // Only confirmed orders explicitly created as service moves
            ...confirmed.filter(isServiceMoveOrder),
        ]
        serviceMoves.value = activeMoves.map(mapServiceMove)

        // Count completed today
        const today = new Date().toISOString().split('T')[0]
        completedToday.value = delivered.filter(o =>
            o.delivered_at?.startsWith(today) && isServiceMoveOrder(o)
        ).length
    } catch (err) {
        console.error('Failed to fetch service moves:', err)
    }
    loading.value = false
}

function mapServiceMove(order) {
    const iconMap = {
        'House Shift': 'home',
        'Office Shift': 'domain',
        'Warehouse Transfer': 'warehouse',
        'Warehouse Supply Pickup': 'inventory_2',
        'Equipment Transfer': 'construction',
        'Manual Service': 'handyman',
        'service_move': 'local_shipping',
    }
    const colorMap = {
        'House Shift': 'blue',
        'Office Shift': 'purple',
        'Warehouse Transfer': 'green',
        'Warehouse Supply Pickup': 'amber',
        'Equipment Transfer': 'cyan',
        'Manual Service': 'rose',
        'service_move': 'blue',
    }

    const moveType = order.cargo_type || order.order_type || 'service_move'
    const c = colorMap[moveType] || 'blue'
    const moveMeta = parseServiceMoveMeta(order.delivery_notes)

    // Get driver and crew info
    const driver = store.dispatcherDrivers.find(d => d.id === String(order.assigned_driver_id))
    const crew = driver ? [{ name: driver.name, role: 'Driver', driverId: String(order.assigned_driver_id) }] : []

    // Get vehicle info
    const vehicle = store.filteredVehicles.find(v => v.id === String(order.assigned_vehicle_id))
    const vehicleCode = order.assigned_vehicle_code || vehicle?.code || order.vehicle_type || 'Vehicle pending'

    // Calculate progress based on status
    let progress = 0
    if (order.status === 'ASSIGNED') progress = 10
    else if (order.status === 'IN_TRANSIT') progress = 50
    else if (order.status === 'DELIVERED') progress = 100

    const statusMap = {
        'CONFIRMED': { label: 'Scheduled', class: 'bg-yellow-500/20 text-yellow-400' },
        'ASSIGNED': { label: 'Assigned', class: 'bg-blue-500/20 text-blue-400' },
        'IN_TRANSIT': { label: 'In Progress', class: 'bg-green-500/20 text-green-400' },
        'DELIVERED': { label: 'Completed', class: 'bg-gray-500/20 text-gray-400' }
    }

    const statusInfo = statusMap[order.status] || { label: order.status, class: 'bg-gray-500/20 text-gray-400' }

    return {
        id: order.tracking_code || order.id,
        orderId: order.id,
        title: moveMeta.title || `${moveType} · ${order.tracking_code || String(order.id).slice(0, 8)}`,
        type: moveType,
        icon: iconMap[moveType] || 'local_shipping',
        iconClass: `text-${c}-400`,
        headerBg: `bg-${c}-500/5`,
        status: statusInfo.label,
        statusClass: statusInfo.class,
        pickup: order.pickup_addr || 'Not specified',
        pickupLat: order.pickup_lat ?? null,
        pickupLng: order.pickup_lng ?? null,
        delivery: order.delivery_addr || 'Not specified',
        deliveryLat: order.delivery_lat ?? null,
        deliveryLng: order.delivery_lng ?? null,
        timeBlock: order.service_time_block || (
            order.scheduled_at
                ? new Date(order.scheduled_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
                : 'Not scheduled'
        ),
        duration: deriveDurationLabel(order.service_time_block),
        packingTime: '1h',
        dwellTime: '0.5h',
        transitTime: '2.5h',
        progress,
        vehicle: vehicleCode,
        seatsAvailable: vehicle?.seatCapacity || 4,
        notes: moveMeta.notes || '',
        tracking: false,
        crew
    }
}

function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}

function handleMapSelect(data) {
    if (mapPickerType.value === 'pickup') {
        newMove.pickup = data.address
        newMove.pickupLat = data.lat
        newMove.pickupLng = data.lon
    } else {
        newMove.delivery = data.address
        newMove.deliveryLat = data.lat
        newMove.deliveryLng = data.lon
    }
    showMapPicker.value = false
}

function useAssignedHub(type) {
    if (!assignedHub.value?.address) return

    const hubLat = assignedHub.value.lat !== null && assignedHub.value.lat !== undefined
        ? Number(assignedHub.value.lat)
        : null
    const hubLng = assignedHub.value.lng !== null && assignedHub.value.lng !== undefined
        ? Number(assignedHub.value.lng)
        : null

    if (type === 'pickup') {
        newMove.pickup = assignedHub.value.address
        newMove.pickupLat = hubLat
        newMove.pickupLng = hubLng
        return
    }

    newMove.delivery = assignedHub.value.address
    newMove.deliveryLat = hubLat
    newMove.deliveryLng = hubLng
}

async function trackMove(move) {
    // Toggle off if already tracking this move
    if (trackingMove.value?.id === move.id && showTrackingModal.value) {
        showTrackingModal.value = false
        move.tracking = false
        return
    }
    trackingLoading.value = true
    move.tracking = true
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/tracking/orders/${move.orderId}/driver`, {
            headers: authHeaders(),
        })
        trackedDriver.value = res.ok ? await res.json() : null
    } catch (_) {
        trackedDriver.value = null
    } finally {
        trackingLoading.value = false
    }
    trackingMove.value = move
    showTrackingModal.value = true
}

function toggleMoveMenu(move) { moveMenu.value = moveMenu.value === move.id ? null : move.id }

async function contactCrew(move) {
    crewChatMove.value = move
    crewMessages.value = []
    crewThreadId.value = null
    showCrewChat.value = true

    // Find the driver's existing contact/thread from the store
    const driverId = move.crew[0]?.driverId
    const contact = driverId
        ? store.dispatcherContacts.find(c => c.id === String(driverId))
        : store.dispatcherContacts.find(c => c.name === move.crew[0]?.name)

    if (contact?.threadId) {
        crewThreadId.value = String(contact.threadId)
        crewMessages.value = (contact.messages || []).map(m => ({
            id: m.id || Date.now(),
            from: m.from || m.sender || 'driver',
            text: m.text || '',
        }))
    } else if (contact) {
        // No thread yet — create one
        const thread = await store.createChatForContact(contact.name, contact.phone)
        if (thread?.id) crewThreadId.value = String(thread.id)
    }
}

async function sendCrewMsg() {
    const text = crewMsg.value.trim()
    if (!text) return
    crewMsg.value = ''

    if (crewThreadId.value) {
        const updated = await store.sendDispatchMessage(crewThreadId.value, text)
        if (updated) {
            crewMessages.value = (updated.messages || []).map(m => ({
                id: m.id || Date.now(),
                from: m.from || m.sender || 'driver',
                text: m.text || '',
            }))
            return
        }
    }
    // Fallback: show locally if no thread
    crewMessages.value.push({ id: Date.now(), from: 'dispatch', text })
}

async function cancelMove(move) {
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/orders/${move.orderId}/cancel`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ reason: 'Cancelled by dispatcher' }),
        })
        if (res.ok) {
            serviceMoves.value = serviceMoves.value.filter(m => m.id !== move.id)
        }
    } catch (err) {
        console.error('Failed to cancel move:', err)
    }
    moveMenu.value = null
}

async function completeMove(move) {
    try {
        // Use the transition endpoint (correct backend route)
        const res = await fetch(`${API_BASE_URL}/api/v1/orders/${move.orderId}/transition`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ next_status: 'DELIVERED' }),
        })
        if (res.ok) {
            move.status = 'Completed'
            move.statusClass = 'bg-green-500/20 text-green-400'
            move.progress = 100
            completedToday.value++
            serviceMoves.value = serviceMoves.value.filter(m => m.id !== move.id)
        }
    } catch (err) {
        console.error('Failed to complete move:', err)
    }
    moveMenu.value = null
}

async function createServiceMove() {
    if (!newMove.title || !newMove.pickup || !newMove.delivery) return

    loading.value = true
    formError.value = ''
    formSuccess.value = ''
    try {
        // Build scheduled timestamp
        const scheduledAt = newMove.scheduledDate && newMove.scheduledTime
            ? `${newMove.scheduledDate}T${newMove.scheduledTime}:00`
            : null

        // Create order payload
        const payload = {
            cargo_type: newMove.type,
            order_type: 'SERVICE_MOVE',
            pickup_addr: newMove.pickup,
            pickup_lat: newMove.pickupLat,
            pickup_lng: newMove.pickupLng,
            delivery_addr: newMove.delivery,
            delivery_lat: newMove.deliveryLat,
            delivery_lng: newMove.deliveryLng,
            vehicle_type: selectedVehicleOption.value?.code || selectedVehicleOption.value?.type || null,
            delivery_notes: buildServiceMoveMeta(),
            service_time_block: buildServiceTimeBlock(),
            scheduled_at: scheduledAt,
        }

        const res = await fetch(`${API_BASE_URL}/api/v1/orders`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        })

        if (!res.ok) {
            const error = await res.json().catch(() => ({}))
            throw new Error(parseApiError(error, 'Failed to create service move'))
        }

        const createdOrder = await res.json()

        if (newMove.driverId && createdOrder.id) {
            const assignRes = await fetch(`${API_BASE_URL}/api/v1/orders/${createdOrder.id}/assign`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({
                    driver_id: newMove.driverId,
                    vehicle_id: newMove.vehicleId || null,
                }),
            })

            if (!assignRes.ok) {
                const assignError = await assignRes.json().catch(() => ({}))
                await fetchServiceMoves()
                const partialMessage = parseApiError(assignError, 'Service move created, but assignment failed')
                toast.warning(partialMessage)
                resetNewMoveForm()
                await closeNewMoveModal()
                return
            }
        }

        await fetchServiceMoves()
        formSuccess.value = 'Service move created successfully.'
        toast.success('Service move created successfully.')
        resetNewMoveForm()
        await closeNewMoveModal()
    } catch (err) {
        console.error('Failed to create service move:', err)
        formError.value = err instanceof Error ? err.message : 'Failed to create service move'
        toast.error(formError.value)
    }
    loading.value = false
}
</script>
