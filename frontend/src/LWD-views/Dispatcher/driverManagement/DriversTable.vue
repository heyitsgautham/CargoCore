<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { driverManagementPageKey } from './driverManagementPageContext'

const {
    authFilter,
    chatDriver,
    driverSearch,
    filteredDrivers,
    getHOSBarClass,
    getHOSStatus,
    getHOSStatusClass,
    getHOSTextClass,
    moreMenuDriver,
    promptSuspend,
    statusFilter,
    toggleMoreMenu,
    viewDriverProfile,
} = inject(driverManagementPageKey)
</script>
