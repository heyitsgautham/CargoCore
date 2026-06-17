<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Driver Management</h2>
            <div class="flex gap-2">
                <button @click="openSlipPicker('vehicleSafetyChecklist')"
                    class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">health_and_safety</span> Safety Checklist
                </button>
                <button @click="openSlipPicker('assetCheckout')"
                    class="bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">inventory_2</span> Asset Checkout
                </button>
                <button @click="showBroadcast = true"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">message</span> Broadcast
                </button>
            </div>
        </div>

        <!-- Overview Stats -->
        <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ totalDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Total Drivers</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-green-400">{{ activeDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Active Now</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-yellow-500">{{ onBreakDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">On Break</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-red-500">{{ offlineDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Maintenance/Off</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-orange-400">{{ hosWarnings }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">HOS Warning</div>
            </div>
            <div class="glass-panel p-4 rounded-xl text-center">
                <div class="text-2xl font-bold text-cyan-400">{{ authorizedDrivers }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Authorized</div>
            </div>
        </div>

        <!-- HOS Compliance Alert -->
        <div v-if="hosWarningDriver" class="p-4 bg-orange-100 dark:bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-center gap-3">
            <span class="material-symbols-outlined text-orange-500 dark:text-orange-400 animate-pulse">warning</span>
            <div class="flex-1">
                <div class="text-sm font-bold text-orange-600 dark:text-orange-400">Hours-of-Service Compliance Alert</div>
                <div class="text-xs text-orange-700 dark:text-orange-300">{{ hosWarningDriver.name }} has logged {{ hosWarningDriver.hours }}h of {{ hosWarningDriver.maxHours }}h max continuous driving. Break required soon. System will block new assignments at limit.</div>
            </div>
            <button @click="showHOS = !showHOS" class="text-xs bg-orange-100 dark:bg-orange-500/20 hover:bg-orange-200 dark:hover:bg-orange-500/30 text-orange-700 dark:text-orange-400 px-3 py-1.5 rounded-lg font-bold transition-colors whitespace-nowrap border border-orange-300 dark:border-orange-500/30 flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">{{ showHOS ? 'visibility_off' : 'visibility' }}</span>
                {{ showHOS ? 'Hide HOS' : 'View HOS' }}
            </button>
        </div>
        <div v-if="showHOS" class="glass-panel p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 text-lg">HOS Compliance Overview</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto pr-2">
                <div v-for="d in drivers" :key="d.id" class="p-4 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/10">
                    <div class="flex items-center justify-between mb-2">
                        <div class="text-sm font-bold text-gray-900 dark:text-white truncate">{{ d.name }}</div>
                        <span v-if="d.suspended" class="text-[9px] px-1.5 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/20 font-bold ml-2 shrink-0">SUSP</span>
                    </div>
                    <div class="space-y-2">
                        <div class="flex items-center gap-2">
                            <div class="flex-1 h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div class="h-full rounded-full transition-all duration-500"
                                    :class="getHOSBarClass(d.hours, d.maxHours)"
                                    :style="{ width: (d.hosPct ?? 0) + '%' }"></div>
                            </div>
                            <span class="text-xs font-mono font-bold" :class="getHOSTextClass(d.hours, d.maxHours)">{{ d.hours }}h</span>
                        </div>
                        <div class="text-xs font-semibold" :class="getHOSStatusClass(d.hours, d.maxHours)">
                            {{ d.hours === 0 ? 'Not on shift' : getHOSStatus(d.hours, d.maxHours) }}
                        </div>
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 pt-1 flex justify-between">
                            <span>Max: {{ d.maxHours }}h</span>
                            <span>{{ d.stops }} active order{{ d.stops !== 1 ? 's' : '' }}</span>
                            <span v-if="d.totalWeightKg > 0">{{ d.totalWeightKg }} kg</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Drivers List -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex gap-4">
                <input v-model="driverSearch" type="text" placeholder="Search driver by name, ID, or vehicle..."
                    class="flex-1 bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 px-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                <select v-model="statusFilter" class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 text-gray-900 dark:text-white">
                    <option class="bg-white dark:bg-gray-800" value="">All Statuses</option>
                    <option class="bg-white dark:bg-gray-800" value="On Route">Active</option>
                    <option class="bg-white dark:bg-gray-800" value="Offline">Inactive</option>
                    <option class="bg-white dark:bg-gray-800" value="HOS">HOS Warning</option>
                </select>
                <select v-model="authFilter" class="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg px-4 text-gray-900 dark:text-white">
                    <option class="bg-white dark:bg-gray-800" value="">All Auth Status</option>
                    <option class="bg-white dark:bg-gray-800" value="authorized">Authorized</option>
                    <option class="bg-white dark:bg-gray-800" value="suspended">Suspended</option>
                    <option class="bg-white dark:bg-gray-800" value="expired">License Expired</option>
                </select>
            </div>

            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-400 uppercase text-[10px] tracking-wider">
                    <tr>
                        <th class="p-4">Driver</th>
                        <th class="p-4">Status</th>
                        <th class="p-4">Authorization</th>
                        <th class="p-4">Vehicle</th>
                        <th class="p-4">Current Load</th>
                        <th class="p-4">HOS Compliance</th>
                        <th class="p-4">Shift Stats</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-white/5">
                    <tr v-for="driver in filteredDrivers" :key="driver.id" class="hover:bg-gray-100 dark:hover:bg-white/5 transition-colors group">
                        <td class="p-4">
                            <div class="flex items-center gap-3">
                                <img :src="driver.avatar" class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700">
                                <div>
                                    <div class="font-bold text-gray-900 dark:text-white">{{ driver.name }}</div>
                                    <div class="text-xs text-gray-500">{{ driver.phone }}</div>
                                </div>
                            </div>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-1 rounded text-[10px] font-bold border" :class="driver.statusClass">
                                {{ driver.status }}
                            </span>
                        </td>
                        <td class="p-4">
                            <div class="space-y-1">
                                <div class="flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[12px]" :class="driver.authorized ? 'text-green-400' : 'text-red-400'">
                                        {{ driver.authorized ? 'check_circle' : 'cancel' }}
                                    </span>
                                    <span class="text-[10px]" :class="driver.authorized ? 'text-green-400' : 'text-red-400'">
                                        {{ driver.authorized ? 'Authorized' : 'Not Auth.' }}
                                    </span>
                                </div>
                                <div class="flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[12px]" :class="driver.licenseValid ? 'text-green-400' : 'text-red-400'">
                                        {{ driver.licenseValid ? 'verified' : 'gpp_bad' }}
                                    </span>
                                    <span class="text-[10px]" :class="driver.licenseValid ? 'text-gray-400' : 'text-red-400'">
                                        License {{ driver.licenseValid ? 'Valid' : 'Expired' }}
                                    </span>
                                </div>
                                <div v-if="driver.suspended" class="flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[12px] text-red-400">block</span>
                                    <span class="text-[10px] text-red-400">Suspended</span>
                                </div>
                                <div v-if="driver.maintenance" class="flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[12px] text-yellow-400">build</span>
                                    <span class="text-[10px] text-yellow-400">Vehicle in Maint.</span>
                                </div>
                            </div>
                        </td>
                        <!-- Vehicle -->
                        <td class="p-4 text-gray-600 dark:text-gray-300 text-xs">{{ driver.vehicle || '—' }}</td>

                        <!-- Current Load — real order weight / count -->
                        <td class="p-4">
                            <div class="space-y-1">
                                <div class="flex items-center gap-2">
                                    <div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div class="h-full rounded-full transition-all duration-500"
                                            :class="driver.load > 85 ? 'bg-red-500' : driver.load > 60 ? 'bg-orange-400' : 'bg-primary'"
                                            :style="`width: ${driver.load}%`"></div>
                                    </div>
                                    <span class="text-xs font-mono"
                                        :class="driver.load > 85 ? 'text-red-400' : driver.load > 60 ? 'text-orange-400' : 'text-gray-400'">
                                        {{ driver.load }}%
                                    </span>
                                </div>
                                <!-- Show weight if real orders present, else efficiency note -->
                                <div class="text-[9px] text-gray-500">
                                    <template v-if="driver.stops > 0 && driver.totalWeightKg > 0">
                                        {{ driver.totalWeightKg }} kg · {{ driver.stops }} order{{ driver.stops !== 1 ? 's' : '' }}
                                    </template>
                                    <template v-else-if="driver.stops > 0">
                                        {{ driver.stops }} active order{{ driver.stops !== 1 ? 's' : '' }}
                                    </template>
                                    <template v-else>
                                        Standby · eff. {{ driver.efficiency ?? 0 }}%
                                    </template>
                                </div>
                            </div>
                        </td>

                        <!-- HOS Compliance — real shift hours from order timestamps -->
                        <td class="p-4">
                            <div class="space-y-1">
                                <div class="flex items-center gap-1.5">
                                    <div class="w-14 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div class="h-full rounded-full transition-all duration-500"
                                            :class="getHOSBarClass(driver.hours, driver.maxHours)"
                                            :style="`width: ${driver.hosPct ?? 0}%`"></div>
                                    </div>
                                    <span class="text-[10px] font-mono" :class="getHOSTextClass(driver.hours, driver.maxHours)">
                                        {{ driver.hours }}h / {{ driver.maxHours }}h
                                    </span>
                                </div>
                                <div class="text-[10px]" :class="getHOSStatusClass(driver.hours, driver.maxHours)">
                                    <template v-if="driver.hours === 0">Not on shift</template>
                                    <template v-else>{{ getHOSStatus(driver.hours, driver.maxHours) }}</template>
                                </div>
                                <div v-if="driver.breakDue" class="text-[10px] text-orange-400 flex items-center gap-1">
                                    <span class="material-symbols-outlined text-[10px]">coffee</span>
                                    Break in {{ driver.breakDueIn }}
                                </div>
                            </div>
                        </td>

                        <!-- Shift Stats — real hours + active order count -->
                        <td class="p-4">
                            <div class="space-y-0.5">
                                <div class="text-xs font-mono"
                                    :class="driver.hours > 0 ? 'text-gray-300' : 'text-gray-500'">
                                    {{ driver.hours > 0 ? driver.hours + 'h logged' : '—' }}
                                </div>
                                <div class="text-xs text-gray-400">
                                    {{ driver.stops }} order{{ driver.stops !== 1 ? 's' : '' }} active
                                </div>
                                <div v-if="driver.stops === 0" class="text-[9px] text-gray-600">Standby</div>
                            </div>
                        </td>
                        <td class="p-4">
                            <div class="flex gap-1">
                                <button @click="chatDriver(driver)" class="text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-primary/10 p-1.5 rounded-lg transition-colors" title="Chat"><span
                                        class="material-symbols-outlined text-[18px]">chat</span></button>
                                <button @click="toggleMoreMenu(driver)" class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-white/10 p-1.5 rounded-lg transition-colors relative" title="More">
                                    <span class="material-symbols-outlined text-[18px]">more_vert</span>
                                    <div v-if="moreMenuDriver === driver.id" class="absolute right-0 top-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl z-20 w-40 py-1">
                                        <button @click.stop="promptSuspend(driver)" class="block w-full text-left px-3 py-2 text-sm font-semibold text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">{{ driver.suspended ? 'Unsuspend' : 'Suspend' }}</button>
                                        <button @click.stop="viewDriverProfile(driver)" class="block w-full text-left px-3 py-2 text-sm font-semibold text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">View Profile</button>
                                    </div>
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- HOS Detail -->

        <!-- Broadcast Modal -->
        <Teleport to="body">
        <div v-if="showBroadcast" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showBroadcast = false">
            <div class="bg-white dark:bg-card-dark shadow-2xl border border-gray-200 dark:border-white/10 rounded-2xl p-6 w-full max-w-md m-4">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4">Broadcast Message</h3>
                <textarea v-model="broadcastMsg" rows="3" placeholder="Type message for all drivers..."
                    class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none mb-3"></textarea>
                <div class="flex gap-2">
                    <button @click="sendBroadcast" class="flex-1 bg-primary text-black font-bold py-2 rounded-lg text-sm">Send to All</button>
                    <button @click="showBroadcast = false" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">Cancel</button>
                </div>
                <div v-if="broadcastSent" class="mt-2 text-center text-xs text-green-400 font-bold">✓ Broadcast sent to {{ totalDrivers }} drivers</div>
            </div>
        </div>
        </Teleport>

        <!-- Driver Chat Modal — real thread via dispatcherContacts -->
        <Teleport to="body">
        <div v-if="showDriverChat" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverChat = false">
            <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl w-full max-w-sm m-4 flex flex-col overflow-hidden" style="height:420px">
                <!-- Header -->
                <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between flex-shrink-0">
                    <div class="flex items-center gap-2">
                        <img :src="chatTargetDriver?.avatar" class="w-8 h-8 rounded-full bg-gray-700 flex-shrink-0">
                        <div>
                            <div class="text-sm font-bold text-white">{{ chatTargetDriver?.name }}</div>
                            <div class="flex items-center gap-1.5">
                                <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" :class="chatTargetDriver?.suspended ? 'bg-red-500' : 'bg-green-500'"></span>
                                <span class="text-[10px] text-gray-400">{{ chatTargetDriver?.status }}</span>
                                <span v-if="chatThreadId" class="text-[9px] text-primary/70 ml-1">• Live</span>
                            </div>
                        </div>
                    </div>
                    <button @click="showDriverChat = false" class="text-gray-500 hover:text-white transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>

                <!-- No thread warning -->
                <div v-if="!chatLoading && !chatThreadId" class="mx-4 mt-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-2 flex-shrink-0">
                    <span class="material-symbols-outlined text-yellow-400 text-[14px]">warning</span>
                    <span class="text-[10px] text-yellow-300">No chat thread found — message will be sent once a thread is created.</span>
                </div>

                <!-- Loading state -->
                <div v-if="chatLoading" class="flex-1 flex items-center justify-center">
                    <span class="material-symbols-outlined text-primary animate-spin text-[28px]">progress_activity</span>
                </div>

                <!-- Messages -->
                <div v-else ref="chatMsgEl" class="flex-1 overflow-y-auto no-scrollbar px-4 py-3 space-y-2">
                    <div v-if="driverChatMessages.length === 0" class="text-center py-8 text-gray-500 text-xs">No messages yet. Start the conversation.</div>
                    <div v-for="msg in driverChatMessages" :key="msg.id"
                        class="flex flex-col max-w-[80%] text-xs"
                        :class="msg.from === 'dispatch' ? 'ml-auto items-end' : 'mr-auto items-start'">
                        <span class="text-[9px] text-gray-500 mb-0.5 px-1">{{ msg.from === 'dispatch' ? 'You' : chatTargetDriver?.name }}</span>
                        <div class="px-3 py-2 rounded-xl"
                            :class="msg.from === 'dispatch' ? 'bg-primary text-black font-medium rounded-br-none' : 'bg-white/10 text-gray-200 rounded-bl-none'">
                            {{ msg.text }}
                        </div>
                        <span v-if="msg.time" class="text-[9px] text-gray-600 mt-0.5 px-1">{{ msg.time }}</span>
                    </div>
                </div>

                <!-- Input -->
                <div class="px-4 py-3 border-t border-white/10 flex gap-2 flex-shrink-0">
                    <input v-model="driverChatMsg" @keyup.enter="sendDriverChatMsg" type="text" placeholder="Message driver..."
                        class="flex-1 bg-white/5 border border-white/10 focus:border-primary/50 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none transition-colors">
                    <button @click="sendDriverChatMsg" :disabled="!driverChatMsg.trim()"
                        class="bg-primary hover:bg-primary-dark text-black px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-1 disabled:opacity-40 disabled:cursor-not-allowed">
                        <span class="material-symbols-outlined text-[16px]">send</span>
                    </button>
                </div>
            </div>
        </div>
        </Teleport>

        <!-- Driver Profile Modal -->
        <Teleport to="body">
        <div v-if="showDriverProfile" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showDriverProfile = false">
            <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl p-6 w-full max-w-md m-4">
                <!-- Header -->
                <div class="flex items-center gap-4 mb-5">
                    <div class="relative">
                        <img :src="profileTargetDriver?.avatar" class="w-16 h-16 rounded-full bg-gray-700 ring-2 ring-primary/30">
                        <span class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-900 flex-shrink-0"
                            :class="profileTargetDriver?.suspended ? 'bg-red-500' : profileTargetDriver?.statusColor || 'bg-gray-500'"></span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-bold text-white truncate">{{ profileTargetDriver?.name }}</h3>
                        <p class="text-sm text-gray-400 truncate">{{ profileTargetDriver?.vehicle || 'No vehicle assigned' }}</p>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-xs px-2 py-0.5 rounded-full border font-bold" :class="profileTargetDriver?.statusClass">{{ profileTargetDriver?.status }}</span>
                            <span v-if="profileTargetDriver?.suspended" class="text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/25 font-bold">SUSPENDED</span>
                        </div>
                    </div>
                    <button @click="showDriverProfile = false" class="text-gray-500 hover:text-white transition-colors flex-shrink-0">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Stat cards -->
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Phone</div>
                        <div class="text-sm font-semibold text-white">{{ profileTargetDriver?.phone || '—' }}</div>
                    </div>
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Load Capacity</div>
                        <div class="text-sm font-semibold" :class="(profileTargetDriver?.load || 0) > 85 ? 'text-red-400' : 'text-white'">{{ profileTargetDriver?.load ?? 0 }}%</div>
                    </div>
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Hours Logged</div>
                        <div class="text-sm font-semibold text-white">{{ profileTargetDriver?.hours }}h / {{ profileTargetDriver?.maxHours }}h</div>
                    </div>
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Active Orders</div>
                        <div class="text-sm font-semibold text-white">{{ profileTargetDriver?.stops ?? 0 }}</div>
                    </div>
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Efficiency</div>
                        <div class="text-sm font-semibold text-primary">{{ profileTargetDriver?.efficiency ?? 0 }}%</div>
                    </div>
                    <div class="p-3 bg-white/5 rounded-xl border border-white/8">
                        <div class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Rating</div>
                        <div class="text-sm font-semibold text-yellow-400">{{ profileTargetDriver?.rating ?? '—' }} ★</div>
                    </div>
                </div>

                <!-- Authorization flags -->
                <div class="flex flex-wrap gap-2 mb-4">
                    <div class="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold" :class="profileTargetDriver?.authorized ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'">
                        <span class="material-symbols-outlined text-[12px]">{{ profileTargetDriver?.authorized ? 'verified' : 'cancel' }}</span>
                        {{ profileTargetDriver?.authorized ? 'Authorized' : 'Not Authorized' }}
                    </div>
                    <div class="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold" :class="profileTargetDriver?.licenseValid ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'">
                        <span class="material-symbols-outlined text-[12px]">badge</span>
                        License {{ profileTargetDriver?.licenseValid ? 'Valid' : 'Expired' }}
                    </div>
                    <div v-if="profileTargetDriver?.breakDue" class="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-orange-500/10 text-orange-400 border border-orange-500/20">
                        <span class="material-symbols-outlined text-[12px]">coffee</span>
                        Break Due
                    </div>
                </div>

                <div class="flex gap-2">
                    <button @click="chatDriver(profileTargetDriver); showDriverProfile = false"
                        class="flex-1 bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary py-2 rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">chat</span> Message
                    </button>
                    <button @click="showDriverProfile = false"
                        class="flex-1 bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-sm font-bold transition-colors">Close</button>
                </div>
            </div>
        </div>
        </Teleport>

    <!-- Suspend Confirm Modal -->
    <Teleport to="body">
    <div v-if="showSuspendConfirm" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showSuspendConfirm = false">
        <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl p-6 w-full max-w-sm m-4">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                    :class="suspendConfirmDriver?.suspended ? 'bg-green-500/15' : 'bg-red-500/15'">
                    <span class="material-symbols-outlined" :class="suspendConfirmDriver?.suspended ? 'text-green-400' : 'text-red-400'">
                        {{ suspendConfirmDriver?.suspended ? 'lock_open' : 'block' }}
                    </span>
                </div>
                <div>
                    <h3 class="font-bold text-white text-sm">{{ suspendConfirmDriver?.suspended ? 'Unsuspend Driver' : 'Suspend Driver' }}</h3>
                    <p class="text-[11px] text-gray-400">{{ suspendConfirmDriver?.name }}</p>
                </div>
            </div>
            <p class="text-[12px] text-gray-400 mb-5 leading-relaxed">
                <template v-if="suspendConfirmDriver?.suspended">
                    This will <strong class="text-green-400">restore access</strong> for {{ suspendConfirmDriver?.name }}. They will appear in the driver assignment list and can receive new orders.
                </template>
                <template v-else>
                    This will <strong class="text-red-400">block {{ suspendConfirmDriver?.name }}</strong> from receiving new order assignments. They will be excluded from dispatch until unsuspended.
                </template>
            </p>
            <div class="flex gap-2">
                <button @click="confirmSuspend"
                    class="flex-1 font-bold py-2 rounded-lg text-sm transition-colors"
                    :class="suspendConfirmDriver?.suspended ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-red-600 hover:bg-red-700 text-white'">
                    {{ suspendConfirmDriver?.suspended ? 'Yes, Unsuspend' : 'Yes, Suspend' }}
                </button>
                <button @click="showSuspendConfirm = false"
                    class="flex-1 bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-sm font-bold transition-colors">Cancel</button>
            </div>
        </div>
    </div>
    </Teleport>

    <!-- Slip Picker Modal -->
    <Teleport to="body">
    <div v-if="showSlipPickerModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showSlipPickerModal = false">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-sm m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">{{ slipPickerType === 'vehicleSafetyChecklist' ? 'health_and_safety' : 'inventory_2' }}</span>
                {{ slipPickerType === 'vehicleSafetyChecklist' ? 'Safety Checklist' : 'Asset Checkout' }} — Select Driver
            </h3>
            <div class="mb-4">
                <label class="text-xs text-gray-400 mb-1 block">Driver</label>
                <select v-model="slipPickerDriver" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option v-for="d in drivers" :key="d.id" :value="d" class="bg-white dark:bg-gray-800">{{ d.name }} — {{ d.vehicle || 'No vehicle' }}</option>
                </select>
            </div>
            <div class="flex gap-2">
                <button @click="confirmSlipOpen" :disabled="!slipPickerDriver"
                    class="flex-1 bg-primary text-black font-bold py-2 rounded-lg text-sm disabled:opacity-50 hover:bg-primary-dark transition-colors">
                    Generate Slip
                </button>
                <button @click="showSlipPickerModal = false" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">Cancel</button>
            </div>
        </div>
    </div>
    </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useDispatcherStore } from '@/stores/dispatcherStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlipWithData, prefetchSlips } = useSlipPrinter()

const store = useDispatcherStore()
onMounted(() => {
    store.initialize().catch(() => {})
    // Pre-fetch slip HTML so opens are synchronous (bypasses popup blocker)
    prefetchSlips(['vehicleSafetyChecklist', 'assetCheckout'])
})

const driverSearch = ref('')
const statusFilter = ref('')
const authFilter = ref('')
const showHOS = ref(false)
const showBroadcast = ref(false)
const showDriverChat = ref(false)
const showDriverProfile = ref(false)
const chatTargetDriver = ref(null)
const chatThreadId = ref(null)
const chatLoading = ref(false)
const profileTargetDriver = ref(null)
const driverChatMsg = ref('')
const driverChatMessages = ref([])
const broadcastMsg = ref('')
const broadcastSent = ref(false)
const moreMenuDriver = ref(null)
const showSlipPickerModal = ref(false)
const slipPickerType = ref('')
const slipPickerDriver = ref(null)
const suspendConfirmDriver = ref(null)
const showSuspendConfirm = ref(false)
const chatMsgEl = ref(null)

const drivers = computed(() => store.dispatcherDrivers)

const ACTIVE_STATUSES = ['active', 'on route', 'on_route']
const BREAK_STATUSES  = ['idle', 'on break', 'on_break']

const totalDrivers    = computed(() => drivers.value.length)
const activeDrivers   = computed(() => drivers.value.filter(d => ACTIVE_STATUSES.includes((d.status || '').toLowerCase())).length)
const onBreakDrivers  = computed(() => drivers.value.filter(d => BREAK_STATUSES.includes((d.status || '').toLowerCase())).length)
const offlineDrivers  = computed(() => drivers.value.filter(d => {
    const s = (d.status || '').toLowerCase()
    return !ACTIVE_STATUSES.includes(s) && !BREAK_STATUSES.includes(s)
}).length)
const hosWarnings     = computed(() => drivers.value.filter(d => d.breakDue).length)
const authorizedDrivers = computed(() => drivers.value.filter(d => d.authorized && !d.suspended).length)
const hosWarningDriver  = computed(() => drivers.value.find(d => d.breakDue) || null)

const filteredDrivers = computed(() => {
    return drivers.value.filter(d => {
        if (driverSearch.value) {
            const q = driverSearch.value.toLowerCase()
            if (!d.name.toLowerCase().includes(q) && !(d.phone || '').includes(q) && !(d.vehicle || '').toLowerCase().includes(q)) return false
        }
        if (statusFilter.value === 'HOS') return d.breakDue
        if (statusFilter.value === 'On Route' && d.statusColor !== 'bg-green-500') return false
        if (statusFilter.value === 'Offline' && d.statusColor !== 'bg-gray-500') return false
        if (authFilter.value === 'authorized' && !d.authorized) return false
        if (authFilter.value === 'suspended' && !d.suspended) return false
        if (authFilter.value === 'expired' && d.licenseValid) return false
        return true
    })
})

// ── Real chat via dispatcherContacts (same as ServiceMoves contactCrew) ──────
async function chatDriver(driver) {
    chatTargetDriver.value = driver
    chatThreadId.value = null
    chatLoading.value = true
    driverChatMsg.value = ''
    driverChatMessages.value = []
    showDriverChat.value = true

    // Look up the contact by driver id or name
    const contact = store.dispatcherContacts.find(c => c.id === String(driver.id))
        || store.dispatcherContacts.find(c => c.name === driver.name)

    if (contact?.threadId) {
        chatThreadId.value = String(contact.threadId)
        driverChatMessages.value = (contact.messages || []).map(m => ({
            id: m.id || Date.now(),
            from: m.from || m.sender || 'driver',
            text: m.text || '',
            time: m.time || '',
        }))
    } else if (contact) {
        // No thread yet — create one
        const thread = await store.createChatForContact(contact.name, contact.phone)
        if (thread?.id) chatThreadId.value = String(thread.id)
    }

    chatLoading.value = false
    await nextTick()
    scrollChatToBottom()
}

async function sendDriverChatMsg() {
    const text = driverChatMsg.value.trim()
    if (!text) return
    driverChatMsg.value = ''

    if (chatThreadId.value) {
        const updated = await store.sendDispatchMessage(chatThreadId.value, text)
        if (updated) {
            driverChatMessages.value = (updated.messages || []).map(m => ({
                id: m.id || Date.now(),
                from: m.from || m.sender || 'driver',
                text: m.text || '',
                time: m.time || '',
            }))
            await nextTick()
            scrollChatToBottom()
            return
        }
    }
    // Fallback: show locally if thread not yet established
    driverChatMessages.value.push({ id: Date.now(), from: 'dispatch', text, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) })
    await nextTick()
    scrollChatToBottom()
}

function scrollChatToBottom() {
    if (chatMsgEl.value) chatMsgEl.value.scrollTop = chatMsgEl.value.scrollHeight
}

// ── Suspend / Unsuspend ───────────────────────────────────────────────────────
function promptSuspend(driver) {
    suspendConfirmDriver.value = driver
    showSuspendConfirm.value = true
    moreMenuDriver.value = null
}

async function confirmSuspend() {
    if (!suspendConfirmDriver.value) return
    await store.toggleDriverSuspend(suspendConfirmDriver.value.id)
    showSuspendConfirm.value = false
    suspendConfirmDriver.value = null
}

// ── View Profile ──────────────────────────────────────────────────────────────
function viewDriverProfile(driver) {
    profileTargetDriver.value = driver
    showDriverProfile.value = true
    moreMenuDriver.value = null
}

function toggleMoreMenu(driver) { moreMenuDriver.value = moreMenuDriver.value === driver.id ? null : driver.id }

function sendBroadcast() {
    broadcastSent.value = true
    setTimeout(() => { showBroadcast.value = false; broadcastSent.value = false; broadcastMsg.value = '' }, 1500)
}

function getHOSBarClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'bg-red-500'
    if (pct >= 75) return 'bg-orange-500'
    return 'bg-green-500'
}

function getHOSTextClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'text-red-400'
    if (pct >= 75) return 'text-orange-400'
    return 'text-gray-400'
}

function getHOSStatus(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 100) return 'LIMIT REACHED — BLOCKED'
    if (pct >= 90) return 'CRITICAL — Near limit'
    if (pct >= 75) return 'Warning — Monitor'
    return 'Compliant'
}

function getHOSStatusClass(hours, maxHours) {
    const pct = (hours / maxHours) * 100
    if (pct >= 90) return 'text-red-400 font-bold'
    if (pct >= 75) return 'text-orange-400'
    return 'text-green-400'
}

function openSlipPicker(type) {
    slipPickerType.value = type
    slipPickerDriver.value = drivers.value[0] || null
    showSlipPickerModal.value = true
}

async function confirmSlipOpen() {
    const driver = slipPickerDriver.value
    if (!driver) return

    const vehicle = store.filteredVehicles.find(v =>
        v.id === driver.vehicleId ||
        v.code === driver.vehicle ||
        v.licensePlate === driver.vehicle ||
        v.model === driver.vehicle
    ) || {
        code: driver.vehicle || '—',
        type: driver.vehicle || 'Truck',
        model: driver.vehicle || 'Standard Vehicle'
    }

    await openSlipWithData(slipPickerType.value, driver, vehicle)
    showSlipPickerModal.value = false
}
</script>
