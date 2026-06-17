<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Picking & Packing</h2>
            <div class="flex flex-wrap gap-2">
                <div
                    class="px-4 py-2 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white text-sm">
                    Active Pickers: <span class="text-green-600 dark:text-green-400 font-bold">{{ activePickers }}</span>
                </div>
                <div v-if="autoRefreshEnabled"
                    class="px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-600 dark:text-green-400 text-xs flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    Live {{ autoRefreshCountdown }}s
                </div>
                <button @click="toggleAutoRefresh"
                    class="px-3 py-2 rounded-lg text-xs font-bold transition-colors flex items-center gap-1"
                    :class="autoRefreshEnabled ? 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400' : 'bg-primary/20 text-primary'">
                    <span class="material-symbols-outlined text-[14px]">{{ autoRefreshEnabled ? 'pause' : 'play_arrow' }}</span>
                    {{ autoRefreshEnabled ? 'Pause' : 'Auto' }}
                </button>
                <button @click="openMasterPickList"
                    class="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[18px]">checklist</span>
                    Pick List
                </button>
                <button @click="refreshData"
                    class="bg-primary hover:bg-primary-dark text-background-dark font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-1">
                    <span class="material-symbols-outlined text-[18px]">refresh</span>
                    Refresh
                </button>
            </div>
        </div>

        <!-- Search & Filter Bar -->
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex flex-col md:flex-row gap-3">
                <div class="flex-1 relative">
                    <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-[18px]">search</span>
                    <input v-model="searchQuery" type="text" placeholder="Search by Order ID, Type..."
                        class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg pl-10 pr-4 py-2 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-primary/50" />
                </div>
                <div class="flex flex-wrap gap-2">
                    <button v-for="filter in statusFilters" :key="filter.value"
                        @click="toggleStatusFilter(filter.value)"
                        class="px-3 py-2 rounded-lg text-xs font-bold transition-all border"
                        :class="activeStatusFilters.includes(filter.value)
                            ? 'bg-primary text-background-dark border-primary'
                            : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-white/10 hover:border-primary/50'">
                        {{ filter.label }}
                    </button>
                    <select v-model="priorityFilter"
                        class="px-3 py-2 bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white text-xs focus:outline-none focus:border-primary/50">
                        <option value="">All Priorities</option>
                        <option value="EXPRESS">🔥 Express</option>
                        <option value="STANDARD">📦 Standard</option>
                        <option value="ECONOMY">🐢 Economy</option>
                    </select>
                    <button v-if="hasActiveFilters" @click="clearFilters"
                        class="px-3 py-2 bg-red-500/10 text-red-500 rounded-lg text-xs font-bold hover:bg-red-500/20 transition-colors">
                        Clear
                    </button>
                </div>
            </div>
        </div>

        <!-- Undo Toast -->
        <Transition name="slide-up">
            <div v-if="undoAction"
                class="fixed bottom-20 left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-6 py-3 rounded-xl shadow-2xl flex items-center gap-4 z-50">
                <span class="text-sm">{{ undoAction.message }}</span>
                <button @click="performUndo"
                    class="bg-primary text-background-dark px-3 py-1 rounded-lg text-xs font-bold hover:bg-primary-dark transition-colors">
                    Undo
                </button>
                <button @click="dismissUndo" class="text-gray-400 hover:text-white">
                    <span class="material-symbols-outlined text-[18px]">close</span>
                </button>
            </div>
        </Transition>

        <!-- Prerequisite Warnings -->
        <div v-if="prerequisiteWarnings.length > 0"
            class="glass-panel p-4 rounded-xl border border-amber-500/40 bg-amber-500/5">
            <div class="flex items-center gap-2 mb-3">
                <span class="material-symbols-outlined text-amber-500 text-[22px]">warning</span>
                <span class="font-bold text-amber-600 dark:text-amber-400 text-sm">Picking Prerequisites Not Met</span>
            </div>
            <ul class="space-y-2 mb-3">
                <li v-for="(warning, idx) in prerequisiteWarnings" :key="idx"
                    class="flex items-start gap-2 text-xs text-amber-700 dark:text-amber-300">
                    <span class="material-symbols-outlined text-[14px] mt-0.5 shrink-0">error_outline</span>
                    {{ warning }}
                </li>
            </ul>
            <p class="text-xs text-amber-600 dark:text-amber-400 font-medium">
                Orders cannot be moved to picking until all prerequisites above are resolved.
            </p>
        </div>

        <!-- Order Fulfillment Pipeline -->
        <div class="glass-panel p-4 rounded-xl">
            <div class="text-xs text-gray-600 dark:text-gray-400 uppercase font-semibold mb-3">Order Fulfillment
                Pipeline</div>
            <div v-if="pipelineLoading" class="flex items-center justify-center py-4">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
            </div>
            <div v-else class="flex items-center justify-between gap-2">
                <div v-for="(step, idx) in pipelineSteps" :key="step.label"
                    class="flex-1 flex flex-col items-center relative group">
                    <div class="w-full flex items-center">
                        <div class="flex-1 h-1 rounded-full"
                            :class="idx === 0 ? 'bg-transparent' : step.active ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'">
                        </div>
                        <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all"
                            :class="step.active ? 'bg-primary text-background-dark shadow-lg shadow-primary/30' : 'bg-gray-50 dark:bg-white/5 text-gray-500 border border-gray-200 dark:border-white/10'">
                            <span class="material-symbols-outlined text-[18px]">{{ step.icon }}</span>
                        </div>
                        <div class="flex-1 h-1 rounded-full"
                            :class="idx === pipelineSteps.length - 1 ? 'bg-transparent' : pipelineSteps[idx + 1]?.active ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'">
                        </div>
                    </div>
                    <div class="text-[10px] mt-2 font-bold text-center"
                        :class="step.active ? 'text-primary' : 'text-gray-500'">{{ step.label }}</div>
                    <div class="text-[10px] text-gray-600 text-center">{{ step.count }} orders</div>
                </div>
            </div>
        </div>

        <!-- Dispatcher-Assigned Direct Transport Notifications -->
        <TransitionGroup name="slide-up" tag="div" class="space-y-2">
            <div v-for="order in dispatcherAssignedOrders" :key="order.rawId"
                class="flex items-start gap-3 px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/30">
                <span class="material-symbols-outlined text-blue-400 text-[20px] shrink-0 mt-0.5">local_shipping</span>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-sm font-bold text-blue-300">Dispatcher assigned a driver to {{ order.id }}</span>
                        <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-bold border border-blue-500/20">No WM Action</span>
                    </div>
                    <div class="text-xs text-blue-300/70 mt-0.5">
                        <span class="font-semibold text-blue-300">{{ order.driverName }}</span> will pick up directly from {{ order.pickupAddr || 'the pickup location' }}. No warehouse picking or packing required.
                    </div>
                </div>
                <button @click="dismissDispatcherOrder(order.rawId)"
                    class="shrink-0 text-blue-400/60 hover:text-blue-300 transition-colors mt-0.5"
                    title="Dismiss">
                    <span class="material-symbols-outlined text-[18px]">close</span>
                </button>
            </div>
        </TransitionGroup>

        <!-- Active Pick Waves - Clean Tab Layout -->
        <div class="glass-panel rounded-xl overflow-hidden">
            <!-- Header with Status Tabs -->
            <div class="border-b border-gray-100 dark:border-white/5">
                <div class="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Active Pick Waves</h3>
                    <div class="text-xs text-gray-500">
                        {{ filteredWaves.length }} orders
                        <span v-if="hasActiveFilters" class="text-primary">(filtered)</span>
                    </div>
                </div>

                <!-- Status Tabs -->
                <div class="flex overflow-x-auto px-4 gap-1 pb-0">
                    <button @click="selectedStatusTab = 'ALL'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'ALL'
                            ? 'border-primary text-primary bg-primary/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        All
                        <span class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-gray-200 dark:bg-white/10">
                            {{ waves.length }}
                        </span>
                    </button>
                    <button @click="selectedStatusTab = 'ON_HOLD'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'ON_HOLD'
                            ? 'border-red-500 text-red-600 dark:text-red-400 bg-red-500/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        <span class="inline-flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-red-500"></span>
                            On Hold
                        </span>
                        <span v-if="wavesByStatus.ON_HOLD?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-red-500/20 text-red-600 dark:text-red-400">
                            {{ wavesByStatus.ON_HOLD.length }}
                        </span>
                    </button>
                    <button @click="selectedStatusTab = 'AWAITING_PICK'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'AWAITING_PICK'
                            ? 'border-yellow-500 text-yellow-600 dark:text-yellow-400 bg-yellow-500/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        <span class="inline-flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-yellow-500"></span>
                            Awaiting
                        </span>
                        <span v-if="wavesByStatus.AWAITING_PICK?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-yellow-500/20 text-yellow-600 dark:text-yellow-400">
                            {{ wavesByStatus.AWAITING_PICK.length }}
                        </span>
                    </button>
                    <button @click="selectedStatusTab = 'PICKING'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'PICKING'
                            ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-500/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        <span class="inline-flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                            Picking
                        </span>
                        <span v-if="wavesByStatus.PICKING?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-blue-500/20 text-blue-600 dark:text-blue-400">
                            {{ wavesByStatus.PICKING.length }}
                        </span>
                    </button>
                    <button @click="selectedStatusTab = 'PICKED'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'PICKED'
                            ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-cyan-500/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        <span class="inline-flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-cyan-500"></span>
                            Picked
                        </span>
                        <span v-if="wavesByStatus.PICKED?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-600 dark:text-cyan-400">
                            {{ wavesByStatus.PICKED.length }}
                        </span>
                    </button>
                    <button @click="selectedStatusTab = 'PACKING'"
                        class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
                        :class="selectedStatusTab === 'PACKING'
                            ? 'border-green-500 text-green-600 dark:text-green-400 bg-green-500/5'
                            : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white'">
                        <span class="inline-flex items-center gap-1">
                            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            Packing
                        </span>
                        <span v-if="wavesByStatus.PACKING?.length" class="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-green-500/20 text-green-600 dark:text-green-400">
                            {{ wavesByStatus.PACKING.length }}
                        </span>
                    </button>
                </div>
            </div>

            <!-- Loading -->
            <div v-if="loading" class="p-8 text-center">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                <div class="mt-2 text-xs text-gray-500">Loading pick waves...</div>
            </div>

            <!-- Orders Grid -->
            <div v-else class="p-4">
                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    <div v-for="wave in filteredWavesByTab" :key="wave.id"
                        class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-white/10 transition-all cursor-pointer group"
                        @click="openPickList(wave)">
                        <!-- Header -->
                        <div class="flex justify-between items-start mb-3">
                            <div>
                                <div class="font-mono text-primary font-bold">{{ wave.id }}</div>
                                <div class="flex items-center gap-2 mt-1">
                                    <span :class="getPriorityBadgeClass(wave.priority)" class="px-2 py-0.5 rounded text-[10px] font-bold">
                                        {{ getPriorityIcon(wave.priority) }} {{ wave.priority || 'Standard' }}
                                    </span>
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border" :class="wave.statusClass">
                                        {{ wave.status === 'ON_HOLD' ? 'ON HOLD' : wave.status }}
                                    </span>
                                </div>
                            </div>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ wave.items }} items</span>
                        </div>

                        <!-- Labour Info (for ON_HOLD orders) -->
                        <div v-if="wave.status === 'ON_HOLD'"
                            class="mb-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                            <div class="flex items-center gap-2 text-red-600 dark:text-red-400">
                                <span class="material-symbols-outlined text-[16px]">warning</span>
                                <span class="text-xs font-medium">
                                    Need {{ wave.laborRequired }} labourer(s) — {{ wave.laborAssigned?.length || 0 }} assigned
                                </span>
                            </div>
                        </div>

                        <!-- Labour Badge (for other orders) -->
                        <div v-else-if="wave.laborRequired > 0" class="mb-3">
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-gray-500">Labour:</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                                    :class="(wave.laborAssigned?.length || 0) >= wave.laborRequired
                                        ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                                        : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                                    {{ wave.laborAssigned?.length || 0 }}/{{ wave.laborRequired }}
                                </span>
                                <div v-if="wave.laborAssigned?.length" class="flex -space-x-1">
                                    <span v-for="(l, idx) in wave.laborAssigned.slice(0, 3)" :key="l.id"
                                        class="w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center text-[9px] font-bold border border-white dark:border-gray-800">
                                        {{ (l.name || 'L')[0] }}
                                    </span>
                                    <span v-if="wave.laborAssigned.length > 3"
                                        class="w-5 h-5 rounded-full bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-300 flex items-center justify-center text-[9px] font-bold border border-white dark:border-gray-800">
                                        +{{ wave.laborAssigned.length - 3 }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Direct Transport Notice -->
                        <div v-if="isDirectTransport(wave)"
                            class="mb-3 p-2.5 rounded-lg flex items-start gap-2"
                            :class="wave.isDispatcherAssigned
                                ? 'bg-blue-500/10 border border-blue-500/30'
                                : 'bg-teal-500/10 border border-teal-500/30'">
                            <span class="material-symbols-outlined text-[16px] shrink-0 mt-0.5"
                                :class="wave.isDispatcherAssigned ? 'text-blue-400' : 'text-teal-400'">local_shipping</span>
                            <div>
                                <div class="text-[11px] font-bold"
                                    :class="wave.isDispatcherAssigned ? 'text-blue-400' : 'text-teal-400'">
                                    Direct Transport Order
                                </div>
                                <template v-if="wave.isDispatcherAssigned">
                                    <div class="text-[10px] text-blue-300/70 mt-0.5 leading-snug">
                                        Dispatcher assigned <span class="font-bold text-blue-300">{{ wave.assignedDriverName || 'a driver' }}</span> — driver will handle pickup directly. No warehouse action required.
                                    </div>
                                </template>
                                <template v-else>
                                    <div class="text-[10px] text-teal-300/70 mt-0.5 leading-snug">No packing service selected — driver handles pickup directly. No warehouse processing needed.</div>
                                </template>
                            </div>
                        </div>

                        <!-- Details -->
                        <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                            <span>{{ formatCurrency(wave.value) }}</span>
                            <span class="font-mono" :class="isOverdue(wave.deadline) ? 'text-red-500 font-bold' : ''">
                                {{ wave.deadline }}
                                <span v-if="isOverdue(wave.deadline)">⚠️</span>
                            </span>
                        </div>

                        <!-- Action Button -->
                        <div v-if="isDirectTransport(wave)" class="text-center text-xs py-2 border rounded-lg"
                            :class="wave.isDispatcherAssigned
                                ? 'text-blue-400/80 border-blue-500/20 bg-blue-500/5'
                                : 'text-teal-400/70 border-teal-500/20 bg-teal-500/5'">
                            {{ wave.isDispatcherAssigned
                                ? 'Driver assigned by Dispatcher — no warehouse action required'
                                : 'Awaiting Dispatcher — driver assignment pending' }}
                        </div>
                        <div v-else-if="wave.status === 'ON_HOLD'" class="flex gap-2">
                            <button @click.stop="openAssignLabourers(wave)"
                                class="flex-1 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">group_add</span>
                                Assign Labourers
                            </button>
                        </div>
                        <div v-else-if="hasAction(wave)" class="flex gap-2">
                            <button @click.stop="handleWaveAction(wave)"
                                :disabled="isStartPickingBlocked(wave) || isWaveActionPending(wave)"
                                :title="isWaveActionPending(wave) ? 'Action in progress...' : (isStartPickingBlocked(wave) ? 'Prerequisites not met — see warnings above' : '')"
                                class="flex-1 py-2 rounded-lg text-xs font-bold transition-colors"
                                :class="(isStartPickingBlocked(wave) || isWaveActionPending(wave))
                                    ? 'bg-gray-200 dark:bg-white/10 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                                    : 'bg-primary hover:bg-primary-dark text-background-dark'">
                                {{ isWaveActionPending(wave) ? 'Working...' : getActionLabel(wave) }}
                            </button>
                            <button v-if="wave.canUndo" @click.stop="undoWaveStatus(wave)"
                                class="px-3 py-2 bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-300 dark:hover:bg-white/20 transition-colors"
                                title="Undo">
                                <span class="material-symbols-outlined text-[14px]">undo</span>
                            </button>
                        </div>
                        <div v-else class="text-center text-xs text-gray-400 py-2">
                            Awaiting QC / Dispatch
                        </div>
                    </div>
                </div>

                <!-- Empty State -->
                <div v-if="filteredWavesByTab.length === 0" class="text-center py-12 text-gray-500">
                    <span class="material-symbols-outlined text-5xl mb-3 opacity-30">inventory_2</span>
                    <p class="font-medium">No orders in this category</p>
                    <p class="text-xs mt-1 text-gray-400">Orders will appear here when they match this status</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

            <!-- Packing Station View + Quality Check -->
            <div class="space-y-6">
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Packing Stations</h3>
                    <div v-if="stations.length === 0"
                        class="rounded-lg border border-dashed border-gray-200 dark:border-white/10 p-4 text-center text-sm text-gray-500">
                        No packing stations configured yet. A station will appear here once the warehouse starts packing orders.
                    </div>
                    <div v-else class="space-y-4">
                        <div v-for="station in stations" :key="station.id"
                            class="p-4 bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-lg">
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-bold text-gray-900 dark:text-white">{{ station.name }}</span>
                                <span class="w-2 h-2 rounded-full"
                                    :class="station.active ? 'bg-green-500 animate-pulse' : 'bg-gray-500'"></span>
                            </div>
                            <div class="text-xs text-gray-600 dark:text-gray-400 mb-2">{{ station.packer }}</div>
                            <div class="flex justify-between items-end text-sm">
                                <div>
                                    <div class="text-gray-500 text-[10px] uppercase">Throughput</div>
                                    <div class="text-gray-900 dark:text-white font-bold">{{ station.rate }} / hr</div>
                                </div>
                                <button @click="monitorStation(station)"
                                    class="bg-gray-100 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 text-gray-900 dark:text-white px-2 py-1 rounded text-xs transition-colors"
                                    :class="showStationMonitor && monitoredStation?.id === station.id ? 'ring-1 ring-primary bg-primary/20 text-primary' : ''">
                                    {{ showStationMonitor && monitoredStation?.id === station.id ? '● Live' : 'Monitor' }}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quality Check Panel -->
                <div class="glass-panel p-6 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined text-green-600 dark:text-green-400">verified</span>
                        Quality Verification
                    </h3>
                    <div class="space-y-3">
                        <div v-for="check in qualityChecks" :key="check.orderId"
                            class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-mono text-primary text-xs font-bold">{{ check.orderId }}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                                    :class="check.isPassed ? 'bg-green-500/20 text-green-600 dark:text-green-400' : check.verified ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                                    {{ check.isPassed ? 'Passed' : check.verified ? 'Ready' : 'Pending' }}
                                </span>
                            </div>
                            <div class="space-y-1 text-xs">
                                <div v-for="(field, fIdx) in checkFields" :key="fIdx"
                                    @click="toggleCheck(check, field.key)"
                                    class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:bg-white/5 rounded p-0.5 transition-colors">
                                    <span class="material-symbols-outlined text-[14px]"
                                        :class="check[field.key] ? 'text-green-600 dark:text-green-400' : 'text-gray-600'">{{
                                            check[field.key] ? 'check_circle' : 'radio_button_unchecked' }}</span>
                                    <span class="text-gray-600 dark:text-gray-300">{{ field.label }}</span>
                                </div>
                            </div>
                            <button v-if="check.isPassed"
                                class="mt-3 w-full py-2 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-xs font-bold cursor-default opacity-70">
                                Dispatch Queue Updated
                            </button>
                            <button v-else-if="check.verified" @click="triggerDispatch(check)"
                                class="mt-3 w-full py-2 bg-green-500/20 hover:bg-green-500/30 text-green-600 dark:text-green-400 rounded text-xs font-bold transition-colors flex items-center justify-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">send</span> Ready for Dispatch
                            </button>
                            <button v-else
                                class="mt-3 w-full py-2 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded text-xs font-bold cursor-not-allowed opacity-50">
                                Complete all checks first
                            </button>
                        </div>
                        <div v-if="qualityChecks.length === 0" class="text-center text-xs text-gray-500 py-4">
                            No orders pending quality check
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Dispatch Toast -->
        <div v-if="dispatchToast"
            class="fixed bottom-6 right-6 bg-green-500/90 text-white px-6 py-4 rounded-xl shadow-2xl shadow-green-500/30 flex items-center gap-3 z-50 animate-bounce">
            <span class="material-symbols-outlined">check_circle</span>
            <div>
                <div class="font-bold">{{ dispatchToast }}</div>
                <div class="text-xs opacity-80">Notification sent to Dispatcher</div>
            </div>
        </div>
        <div v-if="actionToast"
            class="fixed bottom-6 left-6 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce max-w-md"
            :class="actionToast.startsWith('⚠') ? 'bg-amber-500/95 shadow-amber-500/30' : 'bg-blue-500/90 shadow-blue-500/30'">
            <span class="material-symbols-outlined shrink-0">{{ actionToast.startsWith('⚠') ? 'warning' : 'inventory' }}</span>
            <div class="font-bold text-sm leading-tight">{{ actionToast }}</div>
        </div>

        <!-- Pick List Modal -->
        <Teleport to="body">
            <div v-if="showPickListModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showPickListModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-4xl border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0">
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                                <span class="material-symbols-outlined text-primary">list_alt</span>
                                Pick List — {{ selectedWave?.id }}
                            </h3>
                            <p class="text-xs text-gray-500 mt-1">Item-by-item picking locations</p>
                        </div>
                        <button @click="showPickListModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 overflow-y-auto flex-1">
                        <div v-if="pickListLoading" class="flex items-center justify-center py-8">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                        <div v-else-if="pickListItems.length === 0" class="text-center py-8 text-gray-500">
                            <span class="material-symbols-outlined text-4xl mb-2 opacity-50">inventory_2</span>
                            <p>No items found for this order</p>
                        </div>
                        <div v-else class="space-y-3">
                            <div v-for="(item, idx) in pickListItems" :key="getPickItemKey(item)"
                                class="p-4 rounded-xl border transition-all"
                                :class="item.is_complete
                                    ? 'bg-green-500/10 border-green-500/30'
                                    : getItemPickedQuantity(item) > 0
                                        ? 'bg-blue-500/10 border-blue-500/30'
                                        : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5'">
                                <div class="flex justify-between items-start">
                                    <div class="flex items-start gap-4">
                                        <div class="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
                                            {{ idx + 1 }}
                                        </div>
                                        <div>
                                            <div class="font-bold text-gray-900 dark:text-white">{{ item.item_name || item.name }}</div>
                                            <div class="text-xs text-gray-500 font-mono">SKU: {{ item.sku }}</div>
                                            <div class="mt-2 flex gap-4 text-xs">
                                                <span class="text-gray-600 dark:text-gray-400">
                                                    <strong class="text-primary">{{ item.required_quantity || item.quantity }}</strong> {{ item.unit || 'pcs' }} required
                                                </span>
                                                <span v-if="getItemPickedQuantity(item) > 0"
                                                    class="font-bold"
                                                    :class="item.is_complete ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                                                    Picked: {{ getItemPickedQuantity(item) }} / {{ getItemRequiredQuantity(item) }}
                                                </span>
                                                <span v-if="item.shortage_quantity > 0" class="text-red-500 font-bold">
                                                    ⚠ Shortage: {{ item.shortage_quantity }}
                                                </span>
                                            </div>
                                            <div v-if="item.picker_name" class="mt-2 text-[11px] text-gray-500">
                                                Last confirmed by {{ item.picker_name }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-bold mb-2">
                                            {{ item.location_path || formatLocation(item) }}
                                        </div>
                                        <div class="text-[10px] text-gray-500 font-mono">
                                            Scan: {{ item.scan_code || item.sku }}
                                        </div>
                                    </div>
                                </div>
                                <div class="mt-3 flex items-center justify-between">
                                    <div class="flex gap-2 text-[10px] text-gray-500">
                                        <span v-if="item.zone" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Zone: {{ item.zone }}</span>
                                        <span v-if="item.aisle" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Aisle: {{ item.aisle }}</span>
                                        <span v-if="item.rack" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Rack: {{ item.rack }}</span>
                                        <span v-if="item.shelf" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Shelf: {{ item.shelf }}</span>
                                        <span v-if="item.bin" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Bin: {{ item.bin }}</span>
                                    </div>
                                    <div class="flex gap-2">
                                        <button @click="requestItemScan(item)"
                                            :disabled="!canConfirmPickItem(item)"
                                            class="px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1"
                                            :class="canConfirmPickItem(item)
                                                ? 'bg-primary/15 text-primary hover:bg-primary/25'
                                                : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                            <span class="material-symbols-outlined text-[14px]">qr_code_scanner</span>
                                            Scan to Confirm
                                        </button>
                                        <button @click="toggleItemPicked(item)"
                                            :disabled="!canConfirmPickItem(item)"
                                            class="px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1"
                                            :class="item.is_complete
                                                ? 'bg-green-500/30 text-green-600 dark:text-green-400 cursor-not-allowed'
                                                : getItemPickedQuantity(item) > 0
                                                    ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 hover:bg-blue-500/30'
                                                    : 'bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-primary/20 hover:text-primary'">
                                            <span class="material-symbols-outlined text-[14px]">
                                                {{ item.syncing ? 'sync' : item.is_complete ? 'check_circle' : getItemPickedQuantity(item) > 0 ? 'inventory_2' : 'radio_button_unchecked' }}
                                            </span>
                                            {{ getPickActionLabel(item) }}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 border-t border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0 bg-gray-50 dark:bg-black/20">
                        <div class="text-sm text-gray-600 dark:text-gray-400">
                            {{ pickedCount }} / {{ pickListItems.length }} items picked
                        </div>
                        <div class="flex gap-2">
                            <button @click="printPickList" class="px-4 py-2 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/20 transition-colors flex items-center gap-2">
                                <span class="material-symbols-outlined text-[18px]">print</span>
                                Print List
                            </button>
                            <button @click="completePickList" :disabled="pickListActionDisabled"
                                class="px-4 py-2 bg-primary text-background-dark rounded-lg text-sm font-bold transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                                <span class="material-symbols-outlined text-[18px]">check</span>
                                {{ selectedWave ? (getActionLabel(selectedWave) || 'Proceed with Order') : 'Proceed with Order' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Assign Picker Modal -->
        <Teleport to="body">
            <div v-if="showAssignPickerModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showAssignPickerModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                                <span class="material-symbols-outlined text-primary">person_add</span>
                                Assign Picker
                            </h3>
                            <p class="text-xs text-gray-500 mt-1">Order: {{ selectedWave?.id }}</p>
                        </div>
                        <button @click="showAssignPickerModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6">
                        <div v-if="labourersLoading" class="flex items-center justify-center py-4">
                            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                        </div>
                        <div v-else>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Select Available Picker</label>
                            <div class="space-y-2 max-h-64 overflow-y-auto">
                                <div v-for="labourer in availableLabourers" :key="labourer.id"
                                    @click="selectedLabourer = labourer"
                                    class="p-3 rounded-lg border cursor-pointer transition-all"
                                    :class="selectedLabourer?.id === labourer.id ? 'bg-primary/20 border-primary' : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5 hover:border-primary/50'">
                                    <div class="flex justify-between items-center">
                                        <div class="flex items-center gap-3">
                                            <div class="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold">
                                                {{ (labourer.name || labourer.full_name || '?')[0].toUpperCase() }}
                                            </div>
                                            <div>
                                                <div class="font-bold text-gray-900 dark:text-white text-sm">{{ labourer.name || labourer.full_name }}</div>
                                                <div class="text-xs text-gray-500">{{ labourer.skill_tags?.join(', ') || 'Warehouse Picker' }}</div>
                                            </div>
                                        </div>
                                        <span v-if="!labourer.assigned_order_id || labourer.assigned_order_id === selectedWave?.rawId" class="px-2 py-0.5 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-[10px] font-bold">Available</span>
                                        <span v-else class="px-2 py-0.5 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded text-[10px] font-bold">Assigned</span>
                                    </div>
                                </div>
                                <div v-if="availableLabourers.length === 0" class="text-center py-4 text-gray-500 text-sm">
                                    No labourers available
                                </div>
                            </div>
                            <button @click="assignPicker" :disabled="!selectedLabourer || assigningPicker"
                                class="mt-4 w-full py-3 bg-primary text-background-dark rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                                <span v-if="assigningPicker" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                                <span>{{ assigningPicker ? 'Assigning...' : 'Assign Picker' }}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Multi-Labourer Assignment Modal (for orders requiring multiple labourers) -->
        <Teleport to="body">
            <div v-if="showMultiLabourerModal"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="showMultiLabourerModal = false">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                                <span class="material-symbols-outlined text-primary">group_add</span>
                                Assign Labourers
                            </h3>
                            <p class="text-xs text-gray-500 mt-1">
                                Order: {{ multiLabourerWave?.id }} requires
                                <span class="text-primary font-bold">{{ multiLabourerWave?.laborRequired || 1 }}</span> labourer(s)
                            </p>
                        </div>
                        <button @click="showMultiLabourerModal = false" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6">
                        <div v-if="labourersLoading" class="flex items-center justify-center py-4">
                            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                        </div>
                        <div v-else>
                            <!-- Selection Counter -->
                            <div class="flex items-center justify-between mb-4 p-3 rounded-lg"
                                :class="selectedLabourers.length >= (multiLabourerWave?.laborRequired || 1)
                                    ? 'bg-green-500/20 border border-green-500/30'
                                    : 'bg-yellow-500/20 border border-yellow-500/30'">
                                <span class="text-sm font-medium"
                                    :class="selectedLabourers.length >= (multiLabourerWave?.laborRequired || 1)
                                        ? 'text-green-600 dark:text-green-400'
                                        : 'text-yellow-600 dark:text-yellow-400'">
                                    {{ selectedLabourers.length }} / {{ multiLabourerWave?.laborRequired || 1 }} labourers selected
                                </span>
                                <span v-if="selectedLabourers.length >= (multiLabourerWave?.laborRequired || 1)"
                                    class="material-symbols-outlined text-green-500 text-[18px]">check_circle</span>
                                <span v-else class="material-symbols-outlined text-yellow-500 text-[18px]">info</span>
                            </div>

                            <!-- Selected Labourers -->
                            <div v-if="selectedLabourers.length > 0" class="mb-4">
                                <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Selected:</label>
                                <div class="flex flex-wrap gap-2">
                                    <span v-for="labourer in selectedLabourers" :key="labourer.id"
                                        class="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/20 text-primary rounded-full text-sm font-medium">
                                        {{ labourer.name || labourer.full_name }}
                                        <button @click="toggleLabourerSelection(labourer)" class="hover:text-red-500">
                                            <span class="material-symbols-outlined text-[14px]">close</span>
                                        </button>
                                    </span>
                                </div>
                            </div>

                            <!-- Available Labourers List -->
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-2 block">Available Labourers:</label>
                            <div class="space-y-2 max-h-64 overflow-y-auto">
                                <div v-for="labourer in availableLabourersForMulti" :key="labourer.id"
                                    @click="toggleLabourerSelection(labourer)"
                                    class="p-3 rounded-lg border cursor-pointer transition-all"
                                    :class="isLabourerSelected(labourer)
                                        ? 'bg-primary/20 border-primary'
                                        : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5 hover:border-primary/50'">
                                    <div class="flex justify-between items-center">
                                        <div class="flex items-center gap-3">
                                            <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                                                :class="isLabourerSelected(labourer)
                                                    ? 'bg-primary text-white'
                                                    : 'bg-primary/20 text-primary'">
                                                {{ (labourer.name || labourer.full_name || '?')[0].toUpperCase() }}
                                            </div>
                                            <div>
                                                <div class="font-bold text-gray-900 dark:text-white text-sm">
                                                    {{ labourer.name || labourer.full_name }}
                                                </div>
                                                <div class="text-xs text-gray-500">
                                                    {{ labourer.skill_tags?.join(', ') || 'Warehouse Labour' }}
                                                </div>
                                            </div>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <span class="px-2 py-0.5 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-[10px] font-bold">
                                                Available
                                            </span>
                                            <span v-if="isLabourerSelected(labourer)"
                                                class="material-symbols-outlined text-primary text-[18px]">check_circle</span>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="availableLabourersForMulti.length === 0" class="text-center py-8 text-gray-500">
                                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">group_off</span>
                                    <p class="text-sm">No available labourers</p>
                                    <p class="text-xs mt-1">All labourers are currently assigned to other orders</p>
                                </div>
                            </div>

                            <!-- Action Buttons -->
                            <div class="flex gap-2 mt-4">
                                <button @click="showMultiLabourerModal = false"
                                    class="flex-1 py-3 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg font-bold transition-colors hover:bg-gray-200 dark:hover:bg-white/20">
                                    Cancel
                                </button>
                                <button @click="assignMultipleLabourers"
                                    :disabled="selectedLabourers.length < (multiLabourerWave?.laborRequired || 1) || assigningPicker"
                                    class="flex-1 py-3 bg-primary text-background-dark rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                                    <span v-if="assigningPicker" class="animate-spin rounded-full h-4 w-4 border-b-2 border-background-dark"></span>
                                    <span>{{ assigningPicker ? 'Assigning...' : 'Assign & Continue' }}</span>
                                </button>
                            </div>

                            <p v-if="selectedLabourers.length < (multiLabourerWave?.laborRequired || 1)"
                                class="text-xs text-center text-yellow-600 dark:text-yellow-400 mt-3">
                                Select {{ (multiLabourerWave?.laborRequired || 1) - selectedLabourers.length }} more labourer(s) to proceed
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- Packing Station Live Monitor Modal -->
        <Teleport to="body">
            <div v-if="showStationMonitor"
                class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                @click.self="closeStationMonitor">
                <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-lg border border-gray-200 dark:border-white/10">
                    <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                                <span class="material-symbols-outlined text-green-500 animate-pulse">radio_button_checked</span>
                                Live Monitor — {{ monitoredStation?.name }}
                            </h3>
                            <p class="text-xs text-gray-500 mt-1">Real-time packing station activity</p>
                        </div>
                        <button @click="closeStationMonitor" class="text-gray-500 hover:text-gray-900 dark:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                                <div class="text-3xl font-bold text-primary">{{ monitoredStation?.rate || 0 }}</div>
                                <div class="text-xs text-gray-500 mt-1">Items Packed Today</div>
                            </div>
                            <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl text-center">
                                <div class="text-3xl font-bold" :class="monitoredStation?.active ? 'text-green-500' : 'text-gray-500'">
                                    {{ monitoredStation?.active ? 'Active' : 'Idle' }}
                                </div>
                                <div class="text-xs text-gray-500 mt-1">Station Status</div>
                            </div>
                        </div>
                        <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl">
                            <div class="text-xs text-gray-500 mb-2">Current Order</div>
                            <div v-if="monitoredStation?.currentOrderTracking" class="font-mono text-primary font-bold">
                                {{ monitoredStation.currentOrderTracking }}
                            </div>
                            <div v-else class="text-gray-500 text-sm">No order in progress</div>
                        </div>
                        <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl">
                            <div class="text-xs text-gray-500 mb-2">Assigned Packer</div>
                            <div class="font-bold text-gray-900 dark:text-white">{{ monitoredStation?.packer || 'Unassigned' }}</div>
                        </div>
                        <div class="flex gap-2">
                            <button @click="refreshStationData" class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/20 transition-colors">
                                Refresh Data
                            </button>
                            <button @click="closeStationMonitor" class="flex-1 py-2 bg-primary text-background-dark rounded-lg text-sm font-bold">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { getEffectiveWarehouseSubstatus, patchWarehouseOrderUiState } from '@/utils/warehouseOrderState'
import { apiUrl } from '@/config/api'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlip, openSlipWithData } = useSlipPrinter()

const authStore = useAuthStore()
const openScanner = inject('openScanner', null)
const lastGlobalScan = inject('lastGlobalScan', ref(null))
const dispatchToast = ref('')
const actionToast = ref('')
const loading = ref(false)
const pipelineLoading = ref(false)
const waveActionPending = ref({})
// Prerequisite checks — null = not yet checked, 0 = empty/missing, >0 = ok
const inventoryCount = ref(null)
const floorPlanConfigured = ref(null) // null=checking, false=not set up, true=ok
const labourers = ref([])
const scannerTargetSku = ref('')
const scannerTargetItemKey = ref('')

// Search & Filter state
const searchQuery = ref('')
const activeStatusFilters = ref([])
const priorityFilter = ref('')
const statusFilters = [
    { label: 'Awaiting', value: 'AWAITING_PICK' },
    { label: 'Picking', value: 'PICKING' },
    { label: 'Picked', value: 'PICKED' },
    { label: 'Packing', value: 'PACKING' },
]

// Auto-refresh state
const autoRefreshEnabled = ref(true)
const autoRefreshCountdown = ref(30)
let autoRefreshInterval = null
let countdownInterval = null

// Undo state
const undoAction = ref(null)
const undoHistory = ref([]) // Stack of previous states
let undoTimeout = null

// Pick list modal state
const showPickListModal = ref(false)
const selectedWave = ref(null)
const pickListItems = ref([])
const pickListLoading = ref(false)

// Assign picker modal state
const showAssignPickerModal = ref(false)
const availableLabourers = ref([])
const selectedLabourer = ref(null)
const labourersLoading = ref(false)
const assigningPicker = ref(false)

// Multi-Labourer assignment modal state
const showMultiLabourerModal = ref(false)
const multiLabourerWave = ref(null)
const selectedLabourers = ref([])

// Kanban view state
const kanbanViewMode = ref('board') // 'board' or 'table'
const selectedStatusTab = ref('ALL') // ALL, ON_HOLD, AWAITING_PICK, PICKING, PICKED, PACKING

// Station monitor state
const showStationMonitor = ref(false)
const monitoredStation = ref(null)

const checkFields = [
    { key: 'goodsCorrect', label: 'Correct goods' },
    { key: 'countCorrect', label: 'Correct count' },
    { key: 'packagingOk', label: 'Packaging verified' },
    { key: 'laborConfirmed', label: 'Labor assigned' },
    { key: 'weightOk', label: 'Weight verified' },
    { key: 'labelAttached', label: 'Shipping label attached' },
]

// Dynamic data
const waves = ref([])
const qualityChecks = ref([])
// Dispatcher-assigned direct transport orders — shown as notification banners, not picking cards
const dispatcherAssignedOrders = ref([])
const dismissedDispatcherOrders = ref(new Set())
const pipelineSteps = ref([
    { label: 'Accepted', icon: 'task_alt', active: true, count: 0 },
    { label: 'Picking', icon: 'shopping_basket', active: false, count: 0 },
    { label: 'Packing', icon: 'package_2', active: false, count: 0 },
    { label: 'Quality Check', icon: 'verified', active: false, count: 0 },
    { label: 'Ready for Dispatch', icon: 'local_shipping', active: false, count: 0 },
])

// Packing stations - fetched from API
const stations = ref([])

// Track assigned labourers per order
const orderAssignments = ref({})

// Filtered waves computed
const filteredWaves = computed(() => {
    let result = waves.value

    // Search filter
    if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        result = result.filter(w =>
            w.id.toLowerCase().includes(query) ||
            (w.type || '').toLowerCase().includes(query) ||
            (w.priority || '').toLowerCase().includes(query) ||
            (w.assignedPicker || '').toLowerCase().includes(query)
        )
    }

    // Status filter
    if (activeStatusFilters.value.length > 0) {
        result = result.filter(w => activeStatusFilters.value.includes(w.status))
    }

    // Priority filter
    if (priorityFilter.value) {
        result = result.filter(w => (w.priority || 'STANDARD').toUpperCase() === priorityFilter.value)
    }

    return result
})

const hasActiveFilters = computed(() => searchQuery.value.trim() || activeStatusFilters.value.length > 0 || priorityFilter.value)

// Waves grouped by status for Kanban board
const wavesByStatus = computed(() => {
    const grouped = {
        ON_HOLD: [],
        AWAITING_PICK: [],
        PICKING: [],
        PICKED: [],
        PACKING: [],
    }

    for (const wave of waves.value) {
        // Put orders on hold if they don't have enough labourers assigned
        const laborRequired = wave.laborRequired ?? 0
        const laborAssigned = wave.laborAssigned?.length || 0

        if (laborAssigned < laborRequired && ['AWAITING_PICK', 'CONFIRMED'].includes(wave.status)) {
            grouped.ON_HOLD.push({ ...wave, status: 'ON_HOLD' })
        } else if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') {
            grouped.AWAITING_PICK.push(wave)
        } else if (wave.status === 'PICKING') {
            grouped.PICKING.push(wave)
        } else if (wave.status === 'PICKED') {
            grouped.PICKED.push(wave)
        } else if (wave.status === 'PACKING') {
            grouped.PACKING.push(wave)
        }
    }

    return grouped
})

// Available labourers for multi-selection modal
const availableLabourersForMulti = computed(() => {
    return labourers.value.filter(l =>
        l.is_active && !l.assigned_order_id
    )
})

// Filtered waves based on selected tab
const filteredWavesByTab = computed(() => {
    if (selectedStatusTab.value === 'ALL') {
        // Return all waves including ON_HOLD ones
        const allWaves = []
        for (const status of ['ON_HOLD', 'AWAITING_PICK', 'PICKING', 'PICKED', 'PACKING']) {
            allWaves.push(...(wavesByStatus.value[status] || []))
        }
        return allWaves
    }
    return wavesByStatus.value[selectedStatusTab.value] || []
})

// Active pickers: count real labourers currently attached to picking/packing orders
const activePickers = computed(() => {
    return labourers.value.filter(labourer =>
        labourer.is_active && ['PICKING', 'PACKING'].includes(labourer.assigned_order_substatus)
    ).length
})

// INDIVIDUAL (house-shift) orders require customers to select packing materials,
// so they need warehouse inventory stocked and a floor plan configured before picking.
// Small package / parcel orders (VENDOR etc.) are pre-packaged — no packing materials,
// no inventory tracking, no floor plan needed. Only a labourer is required for all types.
function isHouseShift(wave) {
    return wave.laborRequired > 0
}

// Direct transport orders have packing_amount == 0, meaning the customer did NOT request
// packing services. The driver goes straight to the pickup location — no warehouse
// picking, packing, or loading dock processing is needed.
function isDirectTransport(wave) {
    return wave.packingAmount === 0
}

const prerequisiteWarnings = computed(() => {
    const warnings = []
    const hasHouseShiftOrders = waves.value.some(w => isHouseShift(w))
    if (hasHouseShiftOrders && inventoryCount.value === 0) {
        warnings.push('No inventory items configured — go to Inventory to add stock before picking.')
    }
    if (hasHouseShiftOrders && floorPlanConfigured.value === false) {
        warnings.push('Floor plan not configured — set up warehouse layout in Floor Plan before picking.')
    }
    if (labourers.value.length === 0) {
        warnings.push('No labourers registered — add labourers in Labour Management before assigning to orders.')
    }
    return warnings
})

function isStartPickingBlocked(wave) {
    if (wave.status !== 'AWAITING_PICK' && wave.status !== 'CONFIRMED') return false
    if (isHouseShift(wave)) {
        return inventoryCount.value === 0 || floorPlanConfigured.value === false || labourers.value.length === 0
    }
    // Small package / parcel — no inventory, floor plan, or labour required
    return false
}

const PICK_CONFIRMED_STATUSES = ['PICKED', 'PACKING', 'PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH', 'ON_DOCK', 'DISPATCHED']

// Computed for pick list
const pickedCount = computed(() => pickListItems.value.filter(item => item.is_complete).length)
const allPickListItemsComplete = computed(() =>
    pickListItems.value.length > 0 && pickListItems.value.every(item => item.is_complete)
)
const pickListActionDisabled = computed(() => {
    if (pickListLoading.value || !selectedWave.value) return true
    if (selectedWave.value.status === 'PICKING') return !allPickListItemsComplete.value
    return false
})

// ==================
// Filter Functions
// ==================

function toggleStatusFilter(status) {
    const idx = activeStatusFilters.value.indexOf(status)
    if (idx >= 0) {
        activeStatusFilters.value.splice(idx, 1)
    } else {
        activeStatusFilters.value.push(status)
    }
}

function clearFilters() {
    searchQuery.value = ''
    activeStatusFilters.value = []
    priorityFilter.value = ''
}

// ==================
// Priority Helpers
// ==================

function getPriorityIcon(priority) {
    const p = (priority || 'STANDARD').toUpperCase()
    if (p === 'EXPRESS' || p === 'URGENT') return '🔥'
    if (p === 'ECONOMY' || p === 'LOW') return '🐢'
    return '📦'
}

function getPriorityBadgeClass(priority) {
    const p = (priority || 'STANDARD').toUpperCase()
    if (p === 'EXPRESS' || p === 'URGENT') return 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
    if (p === 'ECONOMY' || p === 'LOW') return 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30'
    return 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border border-gray-500/30'
}

function isOverdue(deadline) {
    if (!deadline || deadline === 'N/A') return false
    try {
        const deadlineDate = new Date(deadline)
        return deadlineDate < new Date()
    } catch {
        return false
    }
}

// ==================
// Auto-Refresh
// ==================

function toggleAutoRefresh() {
    autoRefreshEnabled.value = !autoRefreshEnabled.value
    if (autoRefreshEnabled.value) {
        startAutoRefresh()
    } else {
        stopAutoRefresh()
    }
}

function startAutoRefresh() {
    stopAutoRefresh()
    autoRefreshCountdown.value = 30

    countdownInterval = setInterval(() => {
        autoRefreshCountdown.value--
        if (autoRefreshCountdown.value <= 0) {
            autoRefreshCountdown.value = 30
        }
    }, 1000)

    autoRefreshInterval = setInterval(async () => {
        if (!loading.value) {
            await fetchPickingData()
        }
        autoRefreshCountdown.value = 30
    }, 30000)
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval)
        autoRefreshInterval = null
    }
    if (countdownInterval) {
        clearInterval(countdownInterval)
        countdownInterval = null
    }
}

// ==================
// Undo Functionality
// ==================

function saveUndoState(wave, previousStatus, newStatus) {
    undoHistory.value.push({
        orderId: wave.rawId,
        waveId: wave.id,
        previousStatus,
        newStatus,
        timestamp: Date.now()
    })

    // Keep only last 5 undo actions
    if (undoHistory.value.length > 5) {
        undoHistory.value.shift()
    }

    // Show undo toast
    undoAction.value = {
        message: `${wave.id} moved to ${newStatus.replace(/_/g, ' ')}`,
        orderId: wave.rawId,
        previousStatus,
        newStatus
    }

    // Auto-dismiss after 10 seconds
    if (undoTimeout) clearTimeout(undoTimeout)
    undoTimeout = setTimeout(() => {
        undoAction.value = null
    }, 10000)
}

async function performUndo() {
    if (!undoAction.value) return

    const { orderId, previousStatus, newStatus } = undoAction.value
    const warehouseId = getWarehouseId()

    if (!warehouseId) return

    const headers = { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }

    // Map newStatus → revert endpoint (uses the reverse transitions added to the state machine)
    const revertEndpoints = {
        'PICKING': `api/v1/warehouses/${warehouseId}/operations/orders/${orderId}/revert-picking`,
    }
    const revertUrl = revertEndpoints[newStatus]

    if (revertUrl) {
        try {
            const res = await fetch(apiUrl(revertUrl), { method: 'POST', headers })
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                actionToast.value = err.detail || `Failed to undo: ${res.status}`
                setTimeout(() => { actionToast.value = '' }, 3000)
                undoAction.value = null
                if (undoTimeout) clearTimeout(undoTimeout)
                return
            }
        } catch (e) {
            actionToast.value = 'Network error during undo'
            setTimeout(() => { actionToast.value = '' }, 3000)
            return
        }
    }

    patchWarehouseOrderUiState(warehouseId, orderId, {
        accepted: true,
        warehouse_substatus: previousStatus,
    })

    notifyOrdersUpdated()
    await fetchPickingData()

    actionToast.value = `Reverted to ${previousStatus.replace(/_/g, ' ')}`
    setTimeout(() => { actionToast.value = '' }, 2500)

    undoAction.value = null
    if (undoTimeout) clearTimeout(undoTimeout)
}

function dismissUndo() {
    undoAction.value = null
    if (undoTimeout) clearTimeout(undoTimeout)
}

async function undoWaveStatus(wave) {
    // Find the last undo state for this wave
    const lastState = undoHistory.value.filter(h => h.orderId === wave.rawId).pop()
    if (!lastState) return

    const warehouseId = getWarehouseId()
    if (!warehouseId) return

    patchWarehouseOrderUiState(warehouseId, wave.rawId, {
        accepted: true,
        warehouse_substatus: lastState.previousStatus,
    })

    notifyOrdersUpdated()
    await fetchPickingData()

    actionToast.value = `${wave.id} reverted to ${lastState.previousStatus.replace(/_/g, ' ')}`
    setTimeout(() => { actionToast.value = '' }, 2500)

    // Remove this from history
    const idx = undoHistory.value.indexOf(lastState)
    if (idx >= 0) undoHistory.value.splice(idx, 1)
}

function formatCurrency(value) {
    if (!value) return '₹0'
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value)
}

function formatDate(dateString) {
    if (!dateString) return 'N/A'
    try {
        return new Date(dateString).toLocaleDateString('en-IN', {
            month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
        })
    } catch {
        return 'N/A'
    }
}

function formatLocation(item) {
    const parts = []
    if (item.zone) parts.push(item.zone)
    if (item.aisle) parts.push(`A${item.aisle}`)
    if (item.rack) parts.push(`R${item.rack}`)
    if (item.shelf) parts.push(`S${item.shelf}`)
    if (item.bin) parts.push(`B${item.bin}`)
    return parts.length > 0 ? parts.join('-') : 'Location TBD'
}

function getStatusClass(status) {
    const map = {
        'ON_HOLD': 'bg-red-500/10 text-red-500 border-red-500/20',
        'AWAITING_PICK': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        'PICKING': 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        'PICKED': 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
        'PACKING': 'bg-green-500/10 text-green-500 border-green-500/20',
        'PACKED': 'bg-teal-500/10 text-teal-500 border-teal-500/20',
        'QC_PASSED': 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
        'READY_FOR_DISPATCH': 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        'ON_DOCK': 'bg-orange-500/10 text-orange-500 border-orange-500/20',
        'CONFIRMED': 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    }
    return map[status] || 'bg-gray-500/10 text-gray-500 border-gray-500/20'
}

function dedupeOrders(orders) {
    const seen = new Set()
    return orders.filter(order => {
        const key = order.id || order.tracking_code
        if (!key || seen.has(key)) return false
        seen.add(key)
        return true
    })
}

function getWarehouseId() {
    return authStore.currentWarehouse?.id || authStore.currentUser?.warehouse_id
}

function isWaveActionPending(wave) {
    return Boolean(wave?.rawId && waveActionPending.value[wave.rawId])
}

function getActionLabel(wave) {
    if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') return 'Start Picking'
    if (wave.status === 'PICKING') return 'Complete Picking'
    if (wave.status === 'PICKED') return 'Start Packing'
    if (wave.status === 'PACKING') return 'Complete Packing'
    return ''
}

function hasAction(wave) {
    return Boolean(getActionLabel(wave))
}

function hasCompletedPicking(status) {
    return PICK_CONFIRMED_STATUSES.includes(status)
}

function getPickItemKey(item) {
    return [item.sku, item.location_path || formatLocation(item), item.required_quantity || item.quantity_required || item.quantity || 0].join('::')
}

function getItemRequiredQuantity(item) {
    return Number(item.quantity_required ?? item.required_quantity ?? item.quantity ?? 0) || 0
}

function getItemPickedQuantity(item) {
    return Math.max(0, Number(item.quantity_picked ?? 0) || 0)
}

function getItemRemainingQuantity(item) {
    return Math.max(0, getItemRequiredQuantity(item) - getItemPickedQuantity(item))
}

function canConfirmPickItem(item) {
    return selectedWave.value?.status === 'PICKING' && !item.syncing && getItemRemainingQuantity(item) > 0
}

function getPickActionLabel(item) {
    if (item.syncing) return 'Saving...'
    if (item.is_complete) return 'Picked'
    if (getItemPickedQuantity(item) > 0) return 'Mark Remaining Picked'
    return 'Mark Picked'
}

function notifyOrdersUpdated() {
    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('warehouse-orders-updated'))
    }
}

function dismissDispatcherOrder(rawId) {
    dismissedDispatcherOrders.value.add(rawId)
    dispatcherAssignedOrders.value = dispatcherAssignedOrders.value.filter(o => o.rawId !== rawId)
}

// ==================
// Backend Data Helpers
// ==================

async function readResponseError(response, fallbackMessage) {
    try {
        const errorData = await response.json()
        return errorData.detail || errorData.message || fallbackMessage
    } catch {
        return fallbackMessage
    }
}

function mergePickListWithProgress(items = [], progressItems = [], status = selectedWave.value?.status) {
    const progressBySku = new Map((progressItems || []).map(progressItem => [progressItem.sku, progressItem]))
    const inferCompletedPick = hasCompletedPicking(status)

    return items.map(item => {
        const progressItem = progressBySku.get(item.sku)
        const requiredQuantity = Number(
            progressItem?.quantity_required ?? item.quantity_required ?? item.required_quantity ?? item.quantity ?? 0
        ) || 0
        const quantityPicked = Math.min(
            requiredQuantity,
            Number(progressItem?.quantity_picked ?? (inferCompletedPick ? requiredQuantity : 0)) || 0
        )
        const isComplete = Boolean(progressItem?.is_complete) || (inferCompletedPick && requiredQuantity > 0)

        return {
            ...item,
            quantity_required: requiredQuantity,
            required_quantity: requiredQuantity,
            quantity_picked: quantityPicked,
            picked_by: progressItem?.picked_by || null,
            picker_name: progressItem?.picker_name || null,
            picked_record_id: progressItem?.id || null,
            is_complete: isComplete,
            picked: isComplete,
            syncing: false,
        }
    })
}

async function fetchPickListItems(orderId) {
    const response = await fetch(apiUrl(`api/v1/inventory/pick-list/${orderId}`), {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
    })

    if (response.ok) {
        const data = await response.json()
        return data.items || []
    }

    const orderRes = await fetch(apiUrl(`api/v1/orders/${orderId}`), {
        headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
    })

    if (!orderRes.ok) {
        const pickListError = await readResponseError(response, `Unable to load pick list (${response.status})`)
        throw new Error(pickListError)
    }

    const orderData = await orderRes.json()
    return (orderData.items || []).map((item, idx) => ({
        sku: item.sku || `ITEM-${idx + 1}`,
        item_name: item.name || item.description || 'Item',
        required_quantity: item.quantity || 1,
        available_quantity: item.quantity || 1,
        shortage_quantity: 0,
        unit: item.unit || 'pcs',
        scan_code: item.sku || `SCAN-${idx + 1}`,
        zone: null,
        aisle: null,
        shelf: null,
        bin: null,
        location_path: 'Location TBD',
    }))
}

async function fetchPickProgress(orderId) {
    const warehouseId = getWarehouseId()
    if (!warehouseId) return null

    const response = await fetch(
        apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${orderId}/pick-progress`),
        {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        }
    )

    if (!response.ok) return null
    return await response.json()
}

async function fetchLabourers(warehouseId) {
    if (!warehouseId) {
        labourers.value = []
        orderAssignments.value = {}
        return
    }

    try {
        const response = await fetch(apiUrl(`api/v1/labourers?warehouse_id=${warehouseId}&page_size=100`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        if (!response.ok) {
            labourers.value = []
            orderAssignments.value = {}
            return
        }

        const data = await response.json()
        labourers.value = data.items || []
        orderAssignments.value = labourers.value.reduce((map, labourer) => {
            if (labourer.assigned_order_id) {
                map[labourer.assigned_order_id] = {
                    labourerId: labourer.id,
                    labourerName: labourer.name || labourer.email || 'Assigned labourer'
                }
            }
            return map
        }, {})
    } catch (error) {
        console.error('Failed to fetch labourers:', error)
        labourers.value = []
        orderAssignments.value = {}
    }
}

async function checkPrerequisites(warehouseId) {
    if (!warehouseId) return

    // Check inventory exists in this warehouse
    try {
        const invRes = await fetch(apiUrl(`api/v1/inventory?warehouse_id=${warehouseId}&page_size=1`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })
        if (invRes.ok) {
            const invData = await invRes.json()
            inventoryCount.value = invData.total ?? invData.count ?? (invData.items?.length ?? 0)
        } else {
            inventoryCount.value = 0
        }
    } catch {
        inventoryCount.value = 0
    }

    // Check floor plan is configured
    try {
        const fpRes = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/floor-plan`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })
        if (fpRes.ok) {
            const fpData = await fpRes.json()
            floorPlanConfigured.value = (
                (fpData.sections?.length ?? 0) > 0 ||
                (fpData.racks?.length ?? 0) > 0 ||
                (fpData.groups?.length ?? 0) > 0
            )
        } else if (fpRes.status === 404) {
            floorPlanConfigured.value = false
        } else {
            floorPlanConfigured.value = true // don't block on unexpected API errors
        }
    } catch {
        floorPlanConfigured.value = true // don't block on network errors
    }
}

async function fetchQualityChecks(warehouseId) {
    if (!warehouseId) return []

    try {
        const response = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/quality-checks`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        if (!response.ok) return []
        const data = await response.json()
        return data.items || []
    } catch (error) {
        console.error('Failed to fetch quality checks:', error)
        return []
    }
}

async function ensureQualityCheckRecord(check) {
    if (check.checkId) return check.checkId

    const warehouseId = getWarehouseId()
    if (!warehouseId || !check.rawId) {
        throw new Error('Missing warehouse or order for quality check')
    }

    const createResponse = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${check.rawId}/quality-check`), {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
    })

    if (createResponse.ok) {
        const data = await createResponse.json()
        check.checkId = data.id
        return check.checkId
    }

    if (createResponse.status === 409) {
        const existingResponse = await fetch(
            apiUrl(`api/v1/warehouses/${warehouseId}/operations/quality-checks?order_id=${check.rawId}`),
            { headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' } }
        )

        if (existingResponse.ok) {
            const data = await existingResponse.json()
            const existingCheck = data.items?.[0]
            if (existingCheck) {
                check.checkId = existingCheck.id
                return check.checkId
            }
        }
    }

    throw new Error(`Unable to create quality check (${createResponse.status})`)
}

async function persistQualityCheck(check) {
    const warehouseId = getWarehouseId()
    const checkId = await ensureQualityCheckRecord(check)
    const response = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/quality-checks/${checkId}`), {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
            goods_correct: check.goodsCorrect,
            count_correct: check.countCorrect,
            packaging_verified: check.packagingOk,
            labor_assigned: check.laborConfirmed,
            weight_verified: check.weightOk,
            label_attached: check.labelAttached,
        })
    })

    if (!response.ok) {
        throw new Error(`Unable to persist quality check (${response.status})`)
    }

    const data = await response.json()
    check.checkId = data.id
    check.verified = Boolean(data.is_passed) || (
        check.goodsCorrect &&
        check.countCorrect &&
        check.packagingOk &&
        check.laborConfirmed &&
        check.weightOk &&
        check.labelAttached
    )
    check.isPassed = Boolean(data.is_passed)
}

function requestItemScan(item) {
    if (!canConfirmPickItem(item)) {
        actionToast.value = selectedWave.value?.status === 'PICKING'
            ? `${item.sku} is already fully confirmed`
            : 'Start picking before confirming items'
        setTimeout(() => { actionToast.value = '' }, 2500)
        return
    }

    if (!openScanner) {
        actionToast.value = 'Scanner is unavailable in this layout'
        setTimeout(() => { actionToast.value = '' }, 2500)
        return
    }

    scannerTargetSku.value = (item.scan_code || item.sku || '').toLowerCase()
    scannerTargetItemKey.value = getPickItemKey(item)
    openScanner('scan')
}

watch(lastGlobalScan, async (scanValue) => {
    if (!scanValue || !scannerTargetSku.value) return

    const scannedCode = String(scanValue).trim().toLowerCase()
    const item = pickListItems.value.find(candidate => getPickItemKey(candidate) === scannerTargetItemKey.value)

    if (item && scannedCode === scannerTargetSku.value) {
        await toggleItemPicked(item, 'scan')
    } else {
        actionToast.value = `Scanned code "${scanValue}" does not match ${scannerTargetSku.value.toUpperCase()}`
        setTimeout(() => { actionToast.value = '' }, 2500)
    }

    scannerTargetSku.value = ''
    scannerTargetItemKey.value = ''
    if (lastGlobalScan?.value !== undefined) {
        lastGlobalScan.value = null
    }
})

// ==================
// Pick List Modal
// ==================

async function openPickList(wave) {
    selectedWave.value = wave
    showPickListModal.value = true
    pickListLoading.value = true
    pickListItems.value = []

    try {
        const [items, progress] = await Promise.all([
            fetchPickListItems(wave.rawId),
            fetchPickProgress(wave.rawId),
        ])
        pickListItems.value = mergePickListWithProgress(items, progress?.items || [], wave.status)
    } catch (error) {
        console.error('Error fetching pick list:', error)
        actionToast.value = error.message || 'Unable to load pick list'
        setTimeout(() => { actionToast.value = '' }, 2500)
    } finally {
        pickListLoading.value = false
    }
}

async function toggleItemPicked(item, source = 'button') {
    if (!selectedWave.value) return

    const warehouseId = getWarehouseId()
    if (!warehouseId) return

    if (selectedWave.value.status !== 'PICKING') {
        actionToast.value = 'Start picking before confirming items'
        setTimeout(() => { actionToast.value = '' }, 2500)
        return
    }

    const quantityToConfirm = getItemRemainingQuantity(item)
    if (quantityToConfirm <= 0) {
        actionToast.value = `${item.sku} is already fully confirmed`
        setTimeout(() => { actionToast.value = '' }, 2500)
        return
    }

    item.syncing = true

    try {
        const response = await fetch(
            apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${selectedWave.value.rawId}/pick-item`),
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sku: item.sku,
                    quantity_picked: quantityToConfirm,
                    location: item.location_path || formatLocation(item),
                    notes: null
                })
            }
        )

        if (!response.ok) {
            const errorMessage = await readResponseError(response, `Failed to confirm pick (${response.status})`)
            throw new Error(errorMessage)
        }

        const data = await response.json()
        item.quantity_required = data.quantity_required ?? getItemRequiredQuantity(item)
        item.required_quantity = data.quantity_required ?? getItemRequiredQuantity(item)
        item.quantity_picked = data.quantity_picked
        item.picked_by = data.picked_by
        item.picker_name = data.picker_name
        item.picked_record_id = data.id
        item.is_complete = Boolean(data.is_complete)
        item.picked = item.is_complete
        item.location_path = data.location || item.location_path
        actionToast.value = source === 'scan' ? `${item.sku} scan confirmed` : `${item.sku} marked picked`
        setTimeout(() => { actionToast.value = '' }, 2500)
    } catch (error) {
        console.error('Error confirming pick:', error)
        actionToast.value = error.message || 'Unable to confirm pick'
        setTimeout(() => { actionToast.value = '' }, 2500)
    } finally {
        item.syncing = false
    }
}

/** Top-level "Pick List" button — master overview of all active waves */
async function openMasterPickList() {
    await fetchPickingData()   // get fresh order items before building the slip
    await openSlipWithData('digitalPickList', { waves: waves.value })
}

/** Per-wave "Print" button inside the pick list modal */
async function printPickList() {
    const items = pickListItems.value.map(item => ({
        ...item,
        location_path: item.location_path || formatLocation(item),
    }))
    await openSlipWithData('digitalPickList', { wave: selectedWave.value, items })
}

async function completePickList() {
    if (!selectedWave.value) return

    const warehouseId = getWarehouseId()
    if (!warehouseId) return

    try {
        if (selectedWave.value.status === 'PICKING') {
            const progress = await fetchPickProgress(selectedWave.value.rawId)
            if (progress?.items) {
                pickListItems.value = mergePickListWithProgress(
                    pickListItems.value,
                    progress.items,
                    selectedWave.value.status
                )
            }

            if (progress && !progress.is_complete) {
                actionToast.value = `${progress.picked_items}/${progress.total_items} items confirmed. Complete all items first.`
                setTimeout(() => { actionToast.value = '' }, 3000)
                return
            }

            if (!progress && !allPickListItemsComplete.value) {
                actionToast.value = 'Please mark all items as picked before completing'
                setTimeout(() => { actionToast.value = '' }, 2500)
                return
            }
        }

        const actionSucceeded = await handleWaveAction(selectedWave.value)
        if (actionSucceeded) {
            showPickListModal.value = false
        }
    } catch (error) {
        console.error('Error checking pick progress:', error)
        actionToast.value = error.message || 'Unable to complete pick list'
        setTimeout(() => { actionToast.value = '' }, 3000)
    }
}

// ==================
// Assign Picker
// ==================

async function openAssignPicker(wave) {
    selectedWave.value = wave
    selectedLabourer.value = null
    showAssignPickerModal.value = true
    labourersLoading.value = true

    try {
        const warehouseId = getWarehouseId()
        const url = warehouseId
            ? apiUrl(`api/v1/labourers?warehouse_id=${warehouseId}&page_size=50`)
            : apiUrl('api/v1/labourers?page_size=50')

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        if (response.ok) {
            const data = await response.json()
            availableLabourers.value = (data.items || []).filter(labourer =>
                labourer.is_active && (!labourer.assigned_order_id || labourer.assigned_order_id === wave.rawId)
            )
        }
    } catch (error) {
        console.error('Error fetching labourers:', error)
    } finally {
        labourersLoading.value = false
    }
}

async function assignPicker() {
    if (!selectedLabourer.value || !selectedWave.value) return

    assigningPicker.value = true

    try {
        const response = await fetch(
            apiUrl(`api/v1/labourers/${selectedLabourer.value.id}/assign/${selectedWave.value.rawId}`),
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
            }
        )

        if (!response.ok) {
            throw new Error(`Failed to assign picker (${response.status})`)
        }

        showAssignPickerModal.value = false
        actionToast.value = `${selectedLabourer.value.name || selectedLabourer.value.full_name} assigned to ${selectedWave.value.id}`
        await fetchPickingData()
        setTimeout(() => { actionToast.value = '' }, 2500)
    } catch (error) {
        console.error('Error assigning picker:', error)
        actionToast.value = error.message || 'Unable to assign picker'
        setTimeout(() => { actionToast.value = '' }, 2500)
    } finally {
        assigningPicker.value = false
    }
}

// ==================
// Multi-Labourer Assignment
// ==================

function openAssignLabourers(wave) {
    multiLabourerWave.value = wave
    selectedLabourers.value = wave.laborAssigned ? [...wave.laborAssigned] : []
    showMultiLabourerModal.value = true
    fetchAvailableLabourersForMulti()
}

async function fetchAvailableLabourersForMulti() {
    labourersLoading.value = true
    const warehouseId = getWarehouseId()

    if (!warehouseId) {
        labourersLoading.value = false
        return
    }

    try {
        await fetchLabourers(warehouseId)
    } finally {
        labourersLoading.value = false
    }
}

function isLabourerSelected(labourer) {
    return selectedLabourers.value.some(l => l.id === labourer.id)
}

function toggleLabourerSelection(labourer) {
    const idx = selectedLabourers.value.findIndex(l => l.id === labourer.id)
    if (idx >= 0) {
        selectedLabourers.value.splice(idx, 1)
    } else {
        selectedLabourers.value.push(labourer)
    }
}

async function assignMultipleLabourers() {
    if (!multiLabourerWave.value || selectedLabourers.value.length < (multiLabourerWave.value.laborRequired || 1)) {
        return
    }

    assigningPicker.value = true

    try {
        // Assign each selected labourer to the order
        for (const labourer of selectedLabourers.value) {
            const response = await fetch(
                apiUrl(`api/v1/labourers/${labourer.id}/assign/${multiLabourerWave.value.rawId}`),
                {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
                }
            )

            if (!response.ok) {
                console.warn(`Failed to assign labourer ${labourer.id}`)
            }
        }

        showMultiLabourerModal.value = false
        actionToast.value = `${selectedLabourers.value.length} labourer(s) assigned to ${multiLabourerWave.value.id}`
        await fetchPickingData()
        setTimeout(() => { actionToast.value = '' }, 2500)
    } catch (error) {
        console.error('Error assigning labourers:', error)
        actionToast.value = error.message || 'Unable to assign labourers'
        setTimeout(() => { actionToast.value = '' }, 2500)
    } finally {
        assigningPicker.value = false
    }
}

// ==================
// Station Monitor
// ==================

function monitorStation(station) {
    monitoredStation.value = { ...station }
    showStationMonitor.value = true
}

function closeStationMonitor() {
    showStationMonitor.value = false
    monitoredStation.value = null
}

async function refreshStationData() {
    const warehouseId = getWarehouseId()
    if (!warehouseId || !monitoredStation.value) return

    await fetchPackingStations(warehouseId)
    const updated = stations.value.find(s => s.id === monitoredStation.value.id)
    if (updated) {
        monitoredStation.value = { ...updated }
    }
}

// ==================
// Data Fetching
// ==================

async function refreshData() {
    await fetchPickingData()
}

async function fetchPickingData() {
    loading.value = true
    pipelineLoading.value = true
    await authStore.ensureWarehouseContext()
    const warehouseId = getWarehouseId()

    try {
        // Fetch orders (include backend search when query is set)
        const searchParam = searchQuery.value.trim() ? `&search=${encodeURIComponent(searchQuery.value.trim())}` : ''
        const response = await fetch(apiUrl(`api/v1/orders?page=1&page_size=100${searchParam}`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        let awaitingPickOrders = []
        let pickingOrders = []
        let pickedOrders = []
        let packingOrders = []
        let packedOrders = []

        if (response.ok) {
            const data = await response.json()
            const warehouseOrders = (data.items || []).filter(order =>
                warehouseId ? order.warehouse_id === warehouseId : true
            )

            awaitingPickOrders = warehouseOrders.filter(order => {
                const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
                return order.status === 'CONFIRMED' && substatus === 'AWAITING_PICK'
            }).map(order => ({
                ...order,
                warehouse_substatus: 'AWAITING_PICK'
            }))

            // Direct transport order (packing_amount == 0) routing logic:
            //
            // Case A — normal WM flow: WM assigned a vehicle first → keep in picking
            //   (vehicle already set means WM owns this order; dispatcher will be called later)
            //
            // Case B — dispatcher-direct flow: CONFIRMED + no vehicle → WM has nothing to do yet.
            //   Remove from WM Picking; dispatcher handles driver assignment via Order Clustering.
            //
            // Case C — dispatcher already assigned driver (ASSIGNED status, no vehicle):
            //   Surface as an info-only card so WM knows a driver is inbound but no action is needed.
            const warehousePickOrders = awaitingPickOrders.filter(o => Number(o.packing_amount ?? 0) > 0)
            const wmOwnedDirectTransport = awaitingPickOrders.filter(o =>
                Number(o.packing_amount ?? 0) === 0 && o.assigned_vehicle_id != null
            )
            // Case C orders are surfaced as notification banners, NOT picking cards.
            // We update the ref here so the banner stays visible across refreshes.
            const dispatcherAssignedDirect = warehouseOrders.filter(order =>
                order.status === 'ASSIGNED' &&
                Number(order.packing_amount ?? 0) === 0 &&
                order.assigned_driver_id != null &&
                order.assigned_vehicle_id == null
            )
            dispatcherAssignedOrders.value = dispatcherAssignedDirect
                .filter(order => !dismissedDispatcherOrders.value.has(order.id))
                .map(order => ({
                    id: order.tracking_code || String(order.id).slice(0, 8).toUpperCase(),
                    rawId: order.id,
                    driverName: order.assigned_driver_name || 'a driver',
                    pickupAddr: order.pickup_addr || '',
                    value: order.total_amount || 0,
                }))
            awaitingPickOrders = [...warehousePickOrders, ...wmOwnedDirectTransport]
            pickingOrders = warehouseOrders.filter(order => order.status !== 'CANCELLED' && getEffectiveWarehouseSubstatus(order, warehouseId) === 'PICKING')
                .map(order => ({ ...order, warehouse_substatus: 'PICKING' }))
            pickedOrders = warehouseOrders.filter(order => order.status !== 'CANCELLED' && getEffectiveWarehouseSubstatus(order, warehouseId) === 'PICKED')
                .map(order => ({ ...order, warehouse_substatus: 'PICKED' }))
            packingOrders = warehouseOrders.filter(order => order.status !== 'CANCELLED' && getEffectiveWarehouseSubstatus(order, warehouseId) === 'PACKING')
                .map(order => ({ ...order, warehouse_substatus: 'PACKING' }))
            packedOrders = warehouseOrders.filter(order => {
                if (order.status === 'CANCELLED') return false
                const substatus = getEffectiveWarehouseSubstatus(order, warehouseId)
                return ['PACKED', 'QC_PASSED', 'READY_FOR_DISPATCH'].includes(substatus)
            }).map(order => ({
                ...order,
                warehouse_substatus: getEffectiveWarehouseSubstatus(order, warehouseId)
            }))
        }

        await fetchLabourers(warehouseId)
        await checkPrerequisites(warehouseId)
        const qcItems = await fetchQualityChecks(warehouseId)

        // Build a map of labourers assigned to each order
        const labourersByOrder = {}
        for (const labourer of labourers.value) {
            if (labourer.assigned_order_id) {
                if (!labourersByOrder[labourer.assigned_order_id]) {
                    labourersByOrder[labourer.assigned_order_id] = []
                }
                labourersByOrder[labourer.assigned_order_id].push({
                    id: labourer.id,
                    name: labourer.name || labourer.full_name || labourer.email || 'Labourer',
                    skill_tags: labourer.skill_tags
                })
            }
        }

        const allActiveOrders = dedupeOrders([...awaitingPickOrders, ...pickingOrders, ...pickedOrders, ...packingOrders])
        waves.value = allActiveOrders.map(order => {
            const assignment = orderAssignments.value[order.id]
            const hasUndoHistory = undoHistory.value.some(h => h.orderId === order.id)
            const laborAssigned = labourersByOrder[order.id] || []

            return {
                id: order.tracking_code || order.id?.slice(0, 8).toUpperCase(),
                type: order.order_type || 'Standard',
                priority: order.priority || order.shipping_priority || 'STANDARD',
                items: (order.items || []).reduce((sum, item) => sum + Number(item.quantity || 0), 0) || order.item_count || 0,
                value: order.total_amount || 0,
                deadline: formatDate(order.scheduled_at),
                status: order.warehouse_substatus || order.status,
                statusClass: getStatusClass(order.warehouse_substatus || order.status),
                rawId: order.id,
                assignedPicker: assignment?.labourerName || null,
                canUndo: hasUndoHistory,
                laborRequired: order.labor_count ?? order.laborCount ?? 0,
                laborAssigned: laborAssigned,
                materialsAmount: Number(order.materials_amount ?? 0),
                packingAmount: Number(order.packing_amount ?? 0),
                assignedDriverId: order.assigned_driver_id || null,
                assignedDriverName: order.assigned_driver_name || null,
                assignedVehicleId: order.assigned_vehicle_id || null,
                // Dispatcher-direct flow: driver assigned by dispatcher, no WM vehicle yet
                isDispatcherAssigned: !!order.assigned_driver_id && !order.assigned_vehicle_id && Number(order.packing_amount ?? 0) === 0
            }
        })
        const warehouseAwaitingCount = awaitingPickOrders.filter(o => Number(o.packing_amount ?? 0) > 0).length
        pipelineSteps.value[0].count = warehouseAwaitingCount
        pipelineSteps.value[0].active = warehouseAwaitingCount > 0
        pipelineSteps.value[1].count = pickingOrders.length + pickedOrders.length
        pipelineSteps.value[1].active = pipelineSteps.value[1].count > 0
        pipelineSteps.value[2].count = packingOrders.length
        pipelineSteps.value[2].active = packingOrders.length > 0
        pipelineSteps.value[3].count = packedOrders.length
        pipelineSteps.value[3].active = packedOrders.length > 0
        pipelineSteps.value[4].count = packedOrders.filter(order =>
            ['QC_PASSED', 'READY_FOR_DISPATCH'].includes(order.warehouse_substatus)
        ).length
        pipelineSteps.value[4].active = pipelineSteps.value[4].count > 0

        const qcByOrderId = new Map(qcItems.map(item => [item.order_id, item]))
        qualityChecks.value = packedOrders.map(order => {
            const orderId = order.tracking_code || order.id?.slice(0, 8)
            const existingCheck = qcByOrderId.get(order.id)
            return {
                orderId,
                rawId: order.id,
                checkId: existingCheck?.id || null,
                goodsCorrect: Boolean(existingCheck?.goods_correct),
                countCorrect: Boolean(existingCheck?.count_correct),
                packagingOk: Boolean(existingCheck?.packaging_verified),
                laborConfirmed: Boolean(existingCheck?.labor_assigned || orderAssignments.value[order.id]),
                weightOk: Boolean(existingCheck?.weight_verified),
                labelAttached: Boolean(existingCheck?.label_attached),
                verified: Boolean(existingCheck?.is_passed) || (
                    Boolean(existingCheck?.goods_correct) &&
                    Boolean(existingCheck?.count_correct) &&
                    Boolean(existingCheck?.packaging_verified) &&
                    Boolean(existingCheck?.labor_assigned || orderAssignments.value[order.id]) &&
                    Boolean(existingCheck?.weight_verified) &&
                    Boolean(existingCheck?.label_attached)
                ),
                isPassed: Boolean(existingCheck?.is_passed)
            }
        })

        // Fetch packing stations from API
        if (warehouseId) {
            await fetchPackingStations(warehouseId)
        } else {
            stations.value = []
        }

    } catch (error) {
        console.error('Error fetching picking data:', error)
    } finally {
        loading.value = false
        pipelineLoading.value = false
    }
}

async function fetchPackingStations(warehouseId) {
    try {
        const response = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/packing-stations`), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        if (response.ok) {
            const data = await response.json()
            if (data.items && data.items.length > 0) {
                stations.value = data.items.map(station => ({
                    id: station.id,
                    name: station.station_number,
                    packer: station.assigned_labourer_name || (station.status === 'ACTIVE' ? 'Active' : '-- Idle --'),
                    rate: station.items_packed_today || 0,
                    active: station.status === 'ACTIVE',
                    currentOrderId: station.current_order_id,
                    currentOrderTracking: station.current_order_tracking
                }))
            } else {
                stations.value = []
            }
        } else {
            stations.value = []
        }
    } catch (error) {
        console.error('Error fetching packing stations:', error)
        stations.value = []
    }
}

async function updateWaveStatus(wave, targetStatus, request, options = {}) {
    const warehouseId = getWarehouseId()
    if (!warehouseId) {
        actionToast.value = 'Warehouse not linked'
        setTimeout(() => { actionToast.value = '' }, 2500)
        return false
    }
    if (!wave?.rawId) {
        actionToast.value = 'Order action is missing an order id'
        setTimeout(() => { actionToast.value = '' }, 2500)
        return false
    }
    if (waveActionPending.value[wave.rawId]) {
        return false
    }

    waveActionPending.value = {
        ...waveActionPending.value,
        [wave.rawId]: true,
    }

    try {
        const response = await fetch(request.url, request.options)
        if (!response.ok) {
            const errorMsg = await readResponseError(response, `Failed warehouse action: ${response.status}`)
            throw new Error(errorMsg)
        }

        if (typeof options.onSuccess === 'function') {
            options.onSuccess()
        }

        // Only update UI state if backend call succeeds
        patchWarehouseOrderUiState(warehouseId, wave.rawId, {
            accepted: true,
            warehouse_substatus: targetStatus,
        })
        notifyOrdersUpdated()
        actionToast.value = `${wave.id} moved to ${targetStatus.replaceAll('_', ' ')}`
        await fetchPickingData()
        setTimeout(() => { actionToast.value = '' }, 2500)
        return true
    } catch (error) {
        console.error('Warehouse action error:', error)
        actionToast.value = error.message || 'Unable to update order status'
        setTimeout(() => { actionToast.value = '' }, 3500)
        // Refresh to get accurate state from backend
        await fetchPickingData()
        return false
    } finally {
        const nextPending = { ...waveActionPending.value }
        delete nextPending[wave.rawId]
        waveActionPending.value = nextPending
    }
}

async function handleWaveAction(wave) {
    const warehouseId = getWarehouseId()
    const headers = { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
    const previousStatus = wave.status

    if (wave.status === 'AWAITING_PICK' || wave.status === 'CONFIRMED') {
        if (isHouseShift(wave) && inventoryCount.value === 0) {
            actionToast.value = 'Cannot start picking — no inventory configured. Add inventory items first.'
            setTimeout(() => { actionToast.value = '' }, 5000)
            return false
        }
        if (isHouseShift(wave) && floorPlanConfigured.value === false) {
            actionToast.value = 'Cannot start picking — floor plan not configured. Set up the warehouse layout first.'
            setTimeout(() => { actionToast.value = '' }, 5000)
            return false
        }
        if (labourers.value.length === 0) {
            actionToast.value = 'Cannot start picking — no labourers registered. Add labourers in Labour Management first.'
            setTimeout(() => { actionToast.value = '' }, 5000)
            return false
        }
        const assignment = orderAssignments.value[wave.rawId]
        return updateWaveStatus(wave, 'PICKING', {
            url: apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${wave.rawId}/start-picking`),
            options: { method: 'POST', headers, body: JSON.stringify({ labourer_id: assignment?.labourerId || null }) }
        }, {
            onSuccess: () => saveUndoState(wave, previousStatus, 'PICKING')
        })
    }

    if (wave.status === 'PICKING') {
        return updateWaveStatus(wave, 'PICKED', {
            url: apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${wave.rawId}/complete-picking`),
            options: { method: 'POST', headers }
        }, {
            onSuccess: () => saveUndoState(wave, previousStatus, 'PICKED')
        })
    }

    if (wave.status === 'PICKED') {
        return updateWaveStatus(wave, 'PACKING', {
            url: apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${wave.rawId}/start-packing`),
            options: { method: 'POST', headers, body: JSON.stringify({}) }
        }, {
            onSuccess: () => saveUndoState(wave, previousStatus, 'PACKING')
        })
    }

    if (wave.status === 'PACKING') {
        // Check if this order has real packing materials that need issuance.
        // Cross-reference order items against actual WM inventory to avoid
        // phantom items from old default form values (boxes:10, blankets:4, etc.)
        try {
            const [catalogRes, orderItemsRes] = await Promise.all([
                fetch(apiUrl('api/v1/inventory/packing-catalog'), { headers }),
                fetch(apiUrl(`api/v1/orders/${wave.rawId}/items`), { headers })
            ])

            if (catalogRes.ok && orderItemsRes.ok) {
                const catalog = await catalogRes.json()
                const realSkus = new Set(catalog.map(c => c.sku).filter(Boolean))

                const orderItems = await orderItemsRes.json()
                // Only items whose SKU actually exists in this WM's inventory count
                const realMaterialItems = (orderItems || []).filter(i =>
                    i.quantity > 0 && realSkus.has(i.sku)
                )

                if (realMaterialItems.length > 0) {
                    // Customer selected real materials — verify they were issued
                    const movRes = await fetch(
                        apiUrl(`api/v1/inventory/movements?reference_order_id=${wave.rawId}&page_size=50`),
                        { headers }
                    )
                    if (movRes.ok) {
                        const movements = await movRes.json()
                        const issued = movements.filter(m =>
                            (m.movement_type || '').toUpperCase() === 'ISSUE'
                        )
                        if (issued.length === 0) {
                            actionToast.value = '⚠ Packing materials not issued! Go to Packing Materials → Issue to Order before completing packing.'
                            setTimeout(() => { actionToast.value = '' }, 6000)
                            return false
                        }
                    }
                }
            }
        } catch (e) {
            // Network error — allow to proceed
        }

        return updateWaveStatus(wave, 'PACKED', {
            url: apiUrl(`api/v1/warehouses/${warehouseId}/operations/orders/${wave.rawId}/complete-packing`),
            options: { method: 'POST', headers }
        }, {
            onSuccess: () => saveUndoState(wave, previousStatus, 'PACKED')
        })
    }

    return false
}

async function toggleCheck(check, key) {
    if (check.isPassed) return

    const previous = {
        goodsCorrect: check.goodsCorrect,
        countCorrect: check.countCorrect,
        packagingOk: check.packagingOk,
        laborConfirmed: check.laborConfirmed,
        weightOk: check.weightOk,
        labelAttached: check.labelAttached,
        verified: check.verified,
    }

    check[key] = !check[key]
    check.verified = check.goodsCorrect && check.countCorrect && check.packagingOk && check.laborConfirmed && check.weightOk && check.labelAttached

    try {
        await persistQualityCheck(check)
    } catch (error) {
        Object.assign(check, previous)
        console.error('Error persisting quality check:', error)
        actionToast.value = error.message || 'Unable to save quality check'
        setTimeout(() => { actionToast.value = '' }, 2500)
    }
}

async function triggerDispatch(check) {
    const warehouseId = getWarehouseId()
    if (!warehouseId || !check.rawId) {
        dispatchToast.value = 'Cannot dispatch - missing warehouse or order'
        setTimeout(() => { dispatchToast.value = '' }, 3000)
        return
    }

    try {
        const checkId = await ensureQualityCheckRecord(check)
        await persistQualityCheck(check)

        const passResponse = await fetch(apiUrl(`api/v1/warehouses/${warehouseId}/operations/quality-checks/${checkId}/pass`), {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authStore.authToken}`, 'Content-Type': 'application/json' }
        })

        if (!passResponse.ok) {
            throw new Error(`Unable to pass quality check (${passResponse.status})`)
        }

        patchWarehouseOrderUiState(warehouseId, check.rawId, {
            accepted: true,
            warehouse_substatus: 'QC_PASSED',
        })
        check.isPassed = true
        check.verified = true

        pipelineSteps.value[4].count++
        pipelineSteps.value[4].active = true
        pipelineSteps.value[3].count = Math.max(0, pipelineSteps.value[3].count - 1)
        dispatchToast.value = `${check.orderId} — Ready for Dispatch!`

        // Refresh data
        notifyOrdersUpdated()
        await fetchPickingData()
    } catch (error) {
        console.error('Error triggering dispatch:', error)
        dispatchToast.value = 'Error updating order status'
    }

    setTimeout(() => { dispatchToast.value = '' }, 3000)
}

// Debounced backend search when searchQuery changes
let searchDebounceTimer = null
watch(searchQuery, () => {
    clearTimeout(searchDebounceTimer)
    searchDebounceTimer = setTimeout(() => {
        fetchPickingData()
    }, 400)
})

onMounted(() => {
    window.addEventListener('warehouse-orders-updated', fetchPickingData)
    fetchPickingData()
    if (autoRefreshEnabled.value) {
        startAutoRefresh()
    }
})

onUnmounted(() => {
    window.removeEventListener('warehouse-orders-updated', fetchPickingData)
    stopAutoRefresh()
    if (undoTimeout) clearTimeout(undoTimeout)
    clearTimeout(searchDebounceTimer)
})
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
    transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
    transform: translate(-50%, 100%);
    opacity: 0;
}
</style>
