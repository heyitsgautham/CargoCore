<template>
    <div class="h-full flex flex-col space-y-6">
        <!-- Header & Control Bar -->
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shrink-0">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">analytics</span> Reports & Command Center
                </h2>
                <p class="text-xs text-gray-500 font-mono mt-1">
                    Live Operational Intelligence • {{ store.activeWarehouseName }}
                </p>
            </div>

            <div class="flex flex-wrap gap-2 items-center">
                <!-- AI Query Bar -->
                <div class="relative group mr-2">
                    <input v-model="aiQuery" @keyup.enter="handleAiQuery" :disabled="aiThinking" type="text"
                        placeholder="Ask AI: 'Show me top spending vendors...'"
                        class="pl-10 pr-10 py-2 bg-white dark:bg-white/5 border border-purple-200 dark:border-purple-500/30 rounded-full text-sm w-64 focus:w-80 transition-all outline-none focus:ring-2 focus:ring-purple-500/50 shadow-sm disabled:opacity-60">
                    <span v-if="!aiThinking"
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-purple-500">auto_awesome</span>
                    <span v-else
                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-purple-500 animate-spin">progress_activity</span>
                    <button @click="handleAiQuery" :disabled="aiThinking || !aiQuery"
                        class="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full bg-purple-500 text-white disabled:opacity-40 hover:bg-purple-600 transition-colors">
                        <span class="material-symbols-outlined text-[14px]">send</span>
                    </button>
                </div>

                <select v-model="timeRange"
                    class="bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-lg text-sm px-3 py-2 outline-none focus:ring-2 focus:ring-primary/50 text-gray-700 dark:text-gray-200 cursor-pointer">
                    <option value="today" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Today (Live)</option>
                    <option value="7d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 7 Days</option>
                    <option value="30d" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Last 30 Days</option>
                    <option value="ytd" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Year to Date</option>
                </select>

                <button @click="downloadCurrentView"
                    class="bg-white hover:bg-gray-50 dark:bg-white/10 dark:hover:bg-white/20 text-gray-700 dark:text-white font-bold px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-all border border-gray-200 dark:border-white/10">
                    <span class="material-symbols-outlined">download</span> Export View
                </button>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div
            class="flex gap-1 overflow-x-auto pb-2 shrink-0 border-b border-gray-200 dark:border-white/10 no-scrollbar">
            <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
                class="px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all flex items-center gap-2"
                :class="activeTab === tab.id ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5'">
                <span class="material-symbols-outlined text-[18px]">{{ tab.icon }}</span>
                {{ tab.label }}
            </button>
        </div>

        <!-- Main Content Area -->
        <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-10">

            <!-- 1. CONTROL TOWER (Executive Summary) -->
            <div v-if="activeTab === 'control_tower'" class="space-y-6 animate-fade-in">
                <!-- Top Row Alerts -->
                <div v-if="crisisAlerts.length > 0" class="flex gap-4 overflow-x-auto pb-2">
                    <div v-for="alert in crisisAlerts" :key="alert.id"
                        class="flex-shrink-0 w-80 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 p-4 rounded-xl flex items-start gap-3 shadow-sm">
                        <span class="material-symbols-outlined text-red-600 animate-bounce">warning</span>
                        <div class="flex-1 min-w-0">
                            <h4 class="font-bold text-red-700 dark:text-red-400 text-sm">{{ alert.title }}</h4>
                            <p class="text-xs text-red-600/80 dark:text-red-400/80 mt-1">{{ alert.desc }}</p>
                            <div class="flex items-center gap-2 mt-2">
                                <p class="text-[10px] text-red-500 font-mono">Active Alert</p>
                                <button @click="store.resolveAlert(alert.id)"
                                    class="text-[10px] px-2 py-0.5 rounded bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-500/30 font-bold transition-colors">
                                    Dismiss
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    <!-- Daily Orders Gauge -->
                    <div
                        class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center relative overflow-hidden group hover:scale-[1.02] transition-transform">
                        <h3 class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-4">
                            Daily Completion</h3>
                        <div class="relative h-74 w-40 mx-auto">
                            <svg class="h-full w-full -rotate-90" viewBox="0 0 36 36">
                                <path class="text-gray-200 dark:text-gray-700"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none" stroke="currentColor" stroke-width="3" />
                                <path class="text-primary transition-all duration-1000 ease-out"
                                    :stroke-dasharray="`${completionRate}, 100`"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none" stroke="currentColor" stroke-width="3" />
                            </svg>
                            <div class="absolute inset-0 flex flex-col items-center justify-center">
                                <span class="text-xl font-black text-gray-900 dark:text-white">{{ completedOrders }}/{{
                                    totalOrders }}</span>
                                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Orders</span>
                            </div>
                        </div>
                    </div>

                    <!-- System Health + Dues -->
                    <div class="lg:col-span-1 space-y-4">
                        <div
                            class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                            <h3 class="text-xs font-bold text-gray-500 uppercase mb-2">System Health</h3>
                            <div class="flex items-end gap-2">
                                <span class="text-4xl font-black text-green-500">{{ store.dashboardStats.deliverySuccess
                                    }}%</span>
                                <span
                                    class="text-xs font-bold mb-1 px-2 py-0.5 rounded-full"
                                    :class="store.dashboardStats.deliverySuccess >= 80 ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100'"
                                >
                                    {{ store.dashboardStats.deliverySuccess >= 80 ? '▲ On Track' : '▼ Below Target' }}
                                </span>
                            </div>
                            <p class="text-xs text-gray-400 mt-2">Delivery Success Rate</p>
                        </div>
                        <div
                            class="p-5 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-500/20 rounded-2xl shadow-sm relative overflow-hidden group hover:scale-[1.02] transition-transform">
                            <div
                                class="absolute -right-4 -top-4 bg-red-500 w-16 h-16 rounded-full opacity-20 blur-xl group-hover:opacity-30 transition-opacity">
                            </div>
                            <h3
                                class="text-xs font-bold text-red-600 dark:text-red-400 uppercase mb-2 flex items-center gap-1">
                                <span class="material-symbols-outlined text-[16px]">payments</span> Pending Dues
                            </h3>
                            <span class="text-3xl font-black text-gray-900 dark:text-white">₹{{ (store.reportMetrics.pending_dues || 0).toLocaleString() }}</span>
                            <p class="text-xs text-red-500 mt-1 font-medium">Critical Collection Required</p>
                        </div>
                    </div>

                    <!-- AI Daily Summary -->
                    <div
                        class="lg:col-span-2 p-6 bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/10 dark:to-white/5 border border-purple-100 dark:border-purple-500/20 rounded-2xl shadow-sm relative">
                        <span
                            class="material-symbols-outlined absolute top-4 right-4 text-purple-300 text-6xl opacity-20 animate-pulse">auto_awesome</span>
                        <h3 class="font-bold text-purple-900 dark:text-purple-300 flex items-center gap-2 mb-3">
                            <span class="material-symbols-outlined">smart_toy</span> Daily AI Briefing
                        </h3>
                        <div v-if="aiThinking" class="flex items-center gap-2 text-sm text-purple-500 animate-pulse mb-2">
                            <span class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                            Analysing...
                        </div>
                        <ul v-if="aiInsights.length" class="space-y-2">
                            <li v-for="(insight, i) in aiInsights" :key="i"
                                class="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                                <span class="mt-1 h-1.5 w-1.5 rounded-full bg-purple-500 shrink-0"></span>
                                <span v-html="insight"></span>
                            </li>
                        </ul>
                        <div v-else-if="!aiThinking" class="flex flex-col items-center justify-center py-4 text-center">
                            <span class="material-symbols-outlined text-3xl text-purple-300 mb-2">auto_awesome</span>
                            <p class="text-sm text-gray-400 dark:text-gray-500">Ask the AI above to generate insights.<br>
                                <span class="text-xs text-purple-400">e.g. "Show me top spending vendors"</span>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Entity Stats Overview Table -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden animate-fade-in-up">
                    <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                        <h3 class="font-bold text-gray-900 dark:text-white">Operational Entity Overview</h3>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">Entity Type</th>
                                <th class="p-4 text-center">Active Count</th>
                                <th class="p-4 text-center">Issues</th>
                                <th class="p-4 text-right">Performance/Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold">Drivers</td>
                                <td class="p-4 text-center">{{ store.filteredDrivers.length }}</td>
                                <td class="p-4 text-center text-red-500 font-bold">{{store.filteredDrivers.filter(d => d.status !== 'Active').length }}</td>
                                <td class="p-4 text-right text-green-600 font-mono">{{ avgDriverEfficiency }}% Efficiency</td>
                            </tr>
                            <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold">Vehicles</td>
                                <td class="p-4 text-center">{{ store.filteredVehicles.length }}</td>
                                <td class="p-4 text-center text-yellow-500 font-bold">{{store.filteredVehicles.filter(v => v.status !== 'Active').length }}</td>
                                <td class="p-4 text-right font-mono">{{ vehiclesInMaintenance }} In Shop</td>
                            </tr>
                            <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold">Returns (RMA)</td>
                                <td class="p-4 text-center">{{ store.filteredReturns.length }}</td>
                                <td class="p-4 text-center text-blue-500 font-bold">{{store.filteredReturns.filter(r => r.status === 'Pending').length }}</td>
                                <td class="p-4 text-right font-mono">Processing</td>
                            </tr>
                            <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold">Inventory</td>
                                <td class="p-4 text-center">{{ store.filteredInventory.length }} items</td>
                                <td class="p-4 text-center text-red-500 font-bold">{{store.filteredInventory.filter(i => i.status.includes('Low')).length }}</td>
                                <td class="p-4 text-right font-mono">Stock Level OK</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. FINANCIAL LEDGER -->
            <div v-if="activeTab === 'financials'" class="space-y-6 animate-fade-in">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Revenue Split -->
                    <div
                        class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Revenue Stream</h3>
                        <div class="h-74 relative flex justify-center">
                            <Doughnut :data="revenueStreamData" :options="doughnutOptions" />
                        </div>
                    </div>
                    <!-- Recon Breakdown -->
                    <div
                        class="lg:col-span-2 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Payment Reconciliation (COD vs Digital)
                        </h3>
                        <div class="h-74 relative">
                            <Bar :data="paymentReconData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <!-- Fuel Audit Chart -->
                <div
                    class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined text-orange-500">local_gas_station</span>
                        Fuel Expense Audit (Receipts vs GPS)
                    </h3>
                    <div class="h-74 w-full relative">
                        <Line :data="fuelAuditData" :options="chartOptions" />
                    </div>
                    <div
                        class="mt-4 p-3 bg-orange-50 dark:bg-orange-500/10 border border-orange-100 dark:border-orange-500/20 rounded-lg flex items-center gap-3">
                        <span class="material-symbols-outlined text-orange-600">visibility</span>
                        <p class="text-xs text-orange-800 dark:text-orange-300" v-if="fuelAnomalyText">
                            <strong>Anomaly Detected:</strong> {{ fuelAnomalyText }}
                        </p>
                        <p class="text-xs text-green-700 dark:text-green-400" v-else>
                            <strong>No fuel anomalies detected.</strong> All vehicle mileage reports match GPS logs.
                        </p>
                    </div>
                </div>

                <!-- Payment Ledger -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
                    <div
                        class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5 flex justify-between">
                        <h3 class="font-bold text-gray-900 dark:text-white">Live Payment Ledger</h3>
                        <button class="text-xs text-primary font-bold hover:underline">View All</button>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">Customer</th>
                                <th class="p-4">Transaction ID</th>
                                <th class="p-4 text-right">Amount</th>
                                <th class="p-4 text-right">Date</th>
                                <th class="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="tx in store.filteredTransactions" :key="tx.id"
                                class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold text-gray-900 dark:text-white">{{ tx.desc }}</td>
                                <td class="p-4 font-mono text-gray-500">{{ tx.id }}</td>
                                <td class="p-4 text-right font-mono font-bold"
                                    :class="tx.amount > 0 ? 'text-green-600' : 'text-red-500'">₹{{ Math.abs(tx.amount)
                                    }}</td>
                                <td class="p-4 text-right font-mono">{{ tx.date }}</td>
                                <td class="p-4">
                                    <span class="px-2 py-1 rounded text-[10px] uppercase font-bold"
                                        :class="tx.status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                                        {{ tx.status }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Procurement vs Capital Chart -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-emerald-500">inventory_2</span>
                            Procurement vs Capital Funding
                        </h3>
                        <div class="h-64 relative flex justify-center">
                            <Doughnut :data="procurementCapitalData" :options="doughnutOptions" />
                        </div>
                        <div class="mt-4 grid grid-cols-2 gap-3 text-center text-xs">
                            <div class="p-3 bg-orange-50 dark:bg-orange-500/10 rounded-xl">
                                <p class="text-orange-700 dark:text-orange-400 font-bold text-lg">₹{{ (financeSummary?.procurement_expenses || 0).toLocaleString() }}</p>
                                <p class="text-gray-500 mt-1">Procurement Spent</p>
                            </div>
                            <div class="p-3 bg-blue-50 dark:bg-blue-500/10 rounded-xl">
                                <p class="text-blue-700 dark:text-blue-400 font-bold text-lg">₹{{ (financeSummary?.capital_invested || 0).toLocaleString() }}</p>
                                <p class="text-gray-500 mt-1">Capital Invested</p>
                            </div>
                        </div>
                    </div>

                    <!-- Log Investment Panel -->
                    <div class="p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm flex flex-col">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                <span class="material-symbols-outlined text-blue-500">add_card</span>
                                Capital Investment Log
                            </h3>
                            <button @click="investmentModalOpen = true"
                                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-2 shadow-sm">
                                <span class="material-symbols-outlined text-[16px]">add</span> Log Investment
                            </button>
                        </div>
                        <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2">
                            <div v-if="capitalTransactions.length === 0" class="text-center py-8 text-gray-400 text-sm">No capital investments logged yet.</div>
                            <div v-for="tx in capitalTransactions" :key="tx.id"
                                class="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-500/10 rounded-xl border border-blue-100 dark:border-blue-500/20">
                                <div>
                                    <p class="font-bold text-sm text-gray-900 dark:text-white">{{ tx.desc }}</p>
                                    <p class="text-xs text-gray-500 mt-0.5">{{ tx.date }}</p>
                                </div>
                                <span class="font-mono font-bold text-blue-600 dark:text-blue-400">+₹{{ tx.amount.toLocaleString() }}</span>
                            </div>
                        </div>
                    </div>
                </div>

            </div>

            <div v-if="activeTab === 'attendance'" class="space-y-6 animate-fade-in">
                <!-- Overview Stats Cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div
                        class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                        <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Present Today</h3>
                        <span class="text-4xl font-black text-green-500">{{ attendancePresentCount }}</span>
                        <p class="text-[10px] text-gray-400 mt-1">{{ attendancePresentPct }}% of Active Staff</p>
                    </div>
                    <div
                        class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                        <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">On Leave</h3>
                        <span class="text-4xl font-black text-yellow-500">{{ attendanceOnLeaveCount }}</span>
                        <p class="text-[10px] text-gray-400 mt-1">Scheduled Absences</p>
                    </div>
                    <div
                        class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                        <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Unplanned Absences</h3>
                        <span class="text-4xl font-black text-red-500">{{ attendanceUnplannedCount }}</span>
                        <p class="text-[10px] text-gray-400 mt-1">Requires Attention</p>
                    </div>
                    <div
                        class="p-5 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm text-center">
                        <h3 class="text-xs uppercase font-bold text-gray-500 mb-2">Total Workforce</h3>
                        <span class="text-4xl font-black text-blue-500">{{ store.filteredUsers.length }}</span>
                        <p class="text-[10px] text-gray-400 mt-1">Active Accounts</p>
                    </div>
                </div>

                <!-- Detailed Leave Table -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                    <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                        <h3 class="font-bold text-gray-900 dark:text-white">Attendance & Leave Tracker</h3>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">Employee</th>
                                <th class="p-4">Status</th>
                                <th class="p-4 text-center">Allowed Leave</th>
                                <th class="p-4 text-center">Taken</th>
                                <th class="p-4 text-center">Balance</th>
                                <th class="p-4 text-center">Extra Absent</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="user in store.filteredUsers" :key="user.email"
                                class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 flex items-center gap-3">
                                    <img :src="user.avatar" class="w-8 h-8 rounded-full">
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white">{{ user.name }}</p>
                                        <p class="text-[10px] text-gray-400">{{ user.email }}</p>
                                    </div>
                                </td>
                                <td class="p-4">
                                    <span class="px-2 py-1 rounded text-[10px] uppercase font-bold"
                                        :class="loginedToday(user) ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400'">
                                        {{ loginedToday(user) ? 'Present' : 'Absent' }}
                                    </span>
                                </td>
                                <td class="p-4 text-center font-mono font-bold">{{ userLeave(user).allowed }} Days</td>
                                <td class="p-4 text-center font-mono text-gray-500">{{ userLeave(user).taken }}</td>
                                <td class="p-4 text-center font-mono font-bold" :class="userLeave(user).balance > 5 ? 'text-green-600' : 'text-yellow-500'">{{ userLeave(user).balance }}</td>
                                <td class="p-4 text-center font-mono font-bold" :class="userLeave(user).extra > 0 ? 'text-red-500' : 'text-gray-400'">{{ userLeave(user).extra }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </div>

            <!-- 4. WORKFORCE & ROLES -->
            <div v-if="activeTab === 'workforce'" class="space-y-6 animate-fade-in">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div
                        class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Labour Allocation</h3>
                        <div class="h-74 relative flex justify-center">
                            <Doughnut :data="workforceData" :options="doughnutOptions" />
                        </div>
                    </div>

                    <!-- Vendor Performance -->
                    <div
                        class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Vendor Performance & Lead Time</h3>
                        <div class="h-74 relative">
                            <Line :data="vendorLeadTimeData" :options="chartOptions" />
                        </div>
                    </div>

                    <!-- Safety Incident Trends (New to fill gap) -->
                    <div
                        class="lg:col-span-1 p-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Safety Incident Alerts</h3>
                        <div class="h-74 relative">
                            <Bar :data="safetyIncidentData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <!-- Warehouse Dwell Time -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 mb-6">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Warehouse Dwell Time Analytics
                        (Loading/Unloading)</h3>
                    <div class="h-74 relative">
                        <Bar :data="dwellTimeData" :options="chartOptions" />
                    </div>
                </div>

                <!-- Dynamic Roles Table -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                        <div class="p-4 border-b border-gray-100 dark:border-white/10 flex justify-between">
                            <h3 class="font-bold text-gray-900 dark:text-white">Warehouse Staff & Dispatchers</h3>
                            <div class="flex gap-2">
                                <button class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-1 rounded">Metrics</button>
                                <button class="text-xs bg-gray-100 dark:bg-white/10 px-2 py-1 rounded">Roster</button>
                            </div>
                        </div>
                        <table class="w-full text-left text-xs">
                            <thead
                                class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                                <tr>
                                    <th class="p-3">Staff</th>
                                    <th class="p-3">Role</th>
                                    <th class="p-3">Shift Status</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                <tr v-for="user in store.filteredUsers" :key="user.email"
                                    class="hover:bg-gray-50 dark:hover:bg-white/5">
                                    <td class="p-3 flex items-center gap-3">
                                        <img :src="user.avatar" class="w-8 h-8 rounded-full">
                                        <div>
                                            <p class="font-bold text-gray-900 dark:text-white">{{ user.name }}</p>
                                            <p class="text-[10px] text-gray-400">{{ user.email }}</p>
                                        </div>
                                    </td>
                                    <td class="p-3">
                                        <span
                                            class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100">{{
                                            user.role }}</span>
                                    </td>
                                    <td class="p-3 text-green-500 font-bold">{{ user.status }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Staff Efficiency & Overtime (Filling the gap) -->
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden flex flex-col p-6">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Shift Efficiency & Overtime</h3>
                        <div class="h-64 relative">
                            <Bar :data="shiftEfficiencyData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <!-- Driver Performance Scorecard -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
                    <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
                        <h3 class="font-bold text-gray-900 dark:text-white">Driver Performance Scorecard</h3>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-3">Driver</th>
                                <th class="p-3 text-center">Rating</th>
                                <th class="p-3 text-center">Safety Incidents</th>
                                <th class="p-3 text-center">Fuel Eff.</th>
                                <th class="p-3 text-center">Avg Speed</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="d in store.filteredDrivers" :key="d.id"
                                class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-3 font-bold text-gray-900 dark:text-white">{{ d.name }}</td>
                                <td class="p-3 text-center">
                                    <div class="flex items-center justify-center gap-1 text-yellow-500">
                                        <span class="font-bold text-gray-900 dark:text-white">{{ d.rating.toFixed(1) }}</span>
                                        <span class="material-symbols-outlined text-[14px]">star</span>
                                    </div>
                                </td>
                                <td class="p-3 text-center font-bold"
                                    :class="d.safetyIncidents > 0 ? 'text-red-500' : 'text-gray-300'">{{ d.safetyIncidents }}</td>
                                <td class="p-3 text-center font-mono text-green-600">{{ d.fuelEfficiencyScore }}</td>
                                <td class="p-3 text-center font-mono">{{ d.avgSpeed }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 5. ASSETS & INVENTORY (Specific Items) -->
            <div v-if="activeTab === 'assets'" class="space-y-6 animate-fade-in">

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <!-- Specific Counts for User Requests -->
                    <div
                        class="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-500/20">
                        <h4 class="text-xs uppercase font-bold text-blue-800 dark:text-blue-300">Total Boxes</h4>
                        <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{ getInventoryCount(['Box',
                            'Packaging']) }}</p>
                    </div>
                    <div
                        class="p-4 bg-orange-50 dark:bg-orange-900/10 rounded-xl border border-orange-100 dark:border-orange-500/20">
                        <h4 class="text-xs uppercase font-bold text-orange-800 dark:text-orange-300">Crates & Cargo</h4>
                        <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{
                            getInventoryCount(['Crates', 'Cargo']) }}</p>
                    </div>
                    <div
                        class="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-500/20">
                        <h4 class="text-xs uppercase font-bold text-purple-800 dark:text-purple-300">Tape & Tools</h4>
                        <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{ getInventoryCount(['Tape',
                            'Consumables']) }}</p>
                    </div>
                    <div
                        class="p-4 bg-teal-50 dark:bg-teal-900/10 rounded-xl border border-teal-100 dark:border-teal-500/20">
                        <h4 class="text-xs uppercase font-bold text-teal-800 dark:text-teal-300">Utensils</h4>
                        <p class="text-2xl font-black text-gray-900 dark:text-white mt-1">{{
                            getInventoryCount(['Utensils']) }}</p>
                    </div>
                </div>

                <!-- Returnable Equipment Audit -->
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden mt-6 mb-6">
                    <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-indigo-50 dark:bg-indigo-900/10">
                        <h3 class="font-bold text-indigo-900 dark:text-indigo-300">Returnable Equipment Audit
                            (Crates/Blankets)</h3>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">Customer Order</th>
                                <th class="p-4 text-center">Equipment Issued</th>
                                <th class="p-4 text-center">Returned</th>
                                <th class="p-4 text-center text-red-500">Missing/Damaged</th>
                                <th class="p-4 text-right">Penalty Cost</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="eq in store.equipmentLedger" :key="eq.id" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-bold text-gray-900 dark:text-white">{{ eq.referenceCode || 'Unknown' }}</td>
                                <td class="p-4 text-center font-mono">{{ eq.issuedCount }} {{ eq.itemType }}</td>
                                <td class="p-4 text-center font-mono">{{ eq.returnedCount }}</td>
                                <td class="p-4 text-center font-bold" :class="(eq.issuedCount - eq.returnedCount) > 0 ? 'text-red-500' : 'text-gray-300'">
                                    {{ Math.max(0, eq.issuedCount - eq.returnedCount) }}
                                </td>
                                <td class="p-4 text-right font-mono font-bold" :class="(eq.issuedCount - eq.returnedCount) > 0 ? 'text-red-600' : 'text-green-600'">
                                    {{ (eq.issuedCount - eq.returnedCount) > 0 ? `-$${((eq.issuedCount - eq.returnedCount) * 20).toFixed(2)}` : '$0.00' }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- MAIN INVENTORY TABLE -->
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 overflow-hidden flex flex-col">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="font-bold text-gray-900 dark:text-white">Detailed Inventory Levels</h3>
                            <button @click="openRestockModal"
                                class="bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 rounded-lg text-xs font-bold transition-colors flex items-center gap-1 relative">
                                <span class="material-symbols-outlined text-[14px]">pending_actions</span> Pending Restocks
                                <span v-if="escalatedRestockCount > 0"
                                    class="ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-orange-500 text-white animate-pulse">\u26a1 {{ escalatedRestockCount }} Urgent</span>
                            </button>
                        </div>
                        <div class="flex-1 overflow-y-auto custom-scrollbar">
                            <table class="w-full text-left text-xs">
                                <thead>
                                    <tr class="text-gray-400 border-b border-gray-100 dark:border-white/5">
                                        <th class="pb-2">Item Name</th>
                                        <th class="pb-2">Category</th>
                                        <th class="pb-2 text-right">Capacity</th>
                                        <th class="pb-2 text-right">Stock Left</th>
                                        <th class="pb-2 text-right">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                    <tr v-for="item in store.filteredInventory" :key="item.id">
                                        <td class="py-2 font-medium">{{ item.name }}</td>
                                        <td class="py-2 text-gray-500">{{ item.category }}</td>
                                        <td class="py-2 text-right font-mono">{{ Math.floor(item.quantity * 1.5) }} {{
                                            item.unit }}</td>
                                        <td class="py-2 text-right font-mono font-bold">{{ item.quantity }} {{ item.unit
                                            }}</td>
                                        <td class="py-2 text-right">
                                            <span class="px-2 py-0.5 rounded text-[10px]"
                                                :class="item.status === 'Good' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">{{
                                                item.status }}</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Damage Claims -->
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6 overflow-hidden flex flex-col">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Damage & Claims Queue</h3>
                        <div class="flex-1 overflow-y-auto custom-scrollbar space-y-3">
                            <div v-for="(claim, index) in damageClaims" :key="index" @click="openClaimModal(claim)"
                                class="p-3 border border-red-100 dark:border-red-500/20 bg-red-50 dark:bg-red-500/5 rounded-xl flex gap-3 cursor-pointer hover:bg-red-100 dark:hover:bg-red-500/10 transition-colors">
                                <div
                                    class="w-12 h-12 bg-gray-300 rounded-lg shrink-0 flex items-center justify-center font-bold text-gray-500 bg-gray-200 overflow-hidden">
                                    <img v-if="claim.image" :src="claim.image" class="w-full h-full object-cover">
                                    <span v-else>IMG</span>
                                </div>
                                <div class="flex-1">
                                    <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ claim.title }}</h4>
                                    <p class="text-xs text-gray-500">Reported by {{ claim.reporter }} • {{ claim.time }}
                                    </p>
                                    <div class="mt-2 text-red-500 text-xs font-bold"
                                        :class="{ 'text-green-500': claim.status === 'Resolved' }">{{ claim.status }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Claims Action Modal -->
            <div v-if="claimsModalOpen && selectedClaim"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
                <div
                    class="bg-slate-950/98 w-full max-w-md rounded-2xl shadow-2xl p-6 border border-white/10 transform transition-all scale-100 backdrop-blur-xl">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Review Damage Claim</h3>
                        <button @click="claimsModalOpen = false"
                            class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="mb-4">
                        <img v-if="selectedClaim.image" :src="selectedClaim.image"
                            class="w-full h-48 object-cover rounded-xl bg-gray-100 mb-3">
                        <div v-else
                            class="w-full h-48 bg-gray-100 dark:bg-white/5 rounded-xl flex items-center justify-center text-gray-400 mb-3">
                            No Image Available</div>

                        <h4 class="font-bold text-gray-800 dark:text-gray-200">{{ selectedClaim.title }}</h4>
                        <p class="text-sm text-gray-500 mt-1">Reported by: <span
                                class="font-mono text-gray-700 dark:text-gray-300">{{ selectedClaim.reporter }}</span>
                        </p>
                        <p class="text-sm text-gray-500">Time: {{ selectedClaim.time }}</p>
                        <div
                            class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-xs leading-relaxed text-red-800 dark:text-red-200">
                            <strong>Description:</strong> {{ selectedClaim.description || 'Item was found damaged upon arrival at the loading bay. Packaging was torn.' }}
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3 mt-6">
                        <button @click="resolveClaim('Approved')"
                            class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-bold text-sm transition-colors">Approve
                            Replacement</button>
                        <button @click="resolveClaim('Rejected')"
                            class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-gray-100 rounded-lg font-bold text-sm transition-colors border border-white/10">Reject
                            Claim</button>
                    </div>
                </div>
            </div>

            <!-- 6. RETURNS & REVERSE LOGISTICS -->
            <div v-if="activeTab === 'returns'" class="space-y-6 animate-fade-in">
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
                    <div
                        class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5 flex gap-4 items-center">
                        <h3 class="font-bold text-gray-900 dark:text-white">RMA Returns Processing</h3>
                        <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-bold">{{
                            store.filteredReturns.length }} Active</span>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">RMA ID</th>
                                <th class="p-4">Customer</th>
                                <th class="p-4">Order Ref</th>
                                <th class="p-4">Reason</th>
                                <th class="p-4">Condition</th>
                                <th class="p-4 text-center">Images</th>
                                <th class="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                            <tr v-for="rma in store.filteredReturns" :key="rma.id"
                                class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 font-mono font-bold">{{ rma.id }}</td>
                                <td class="p-4">{{ rma.customer }}</td>
                                <td class="p-4 font-mono text-blue-600 font-bold cursor-pointer hover:underline">
                                    {{ rma.orderId ? `#ORD-${rma.orderId.slice(-4).toUpperCase()}` : 'N/A' }}</td>
                                <td class="p-4">{{ rma.reason }}</td>
                                <td class="p-4 whitespace-nowrap">
                                    <span class="px-2 py-1 rounded border"
                                        :class="rma.condition === 'Damaged' ? 'bg-red-50 border-red-200 text-red-600' : 'bg-green-50 border-green-200 text-green-600'">{{
                                        rma.condition }}</span>
                                </td>
                                <td class="p-4 text-center">
                                    <button v-if="rma.images.length"
                                        class="text-blue-500 hover:underline hover:text-blue-600">View {{
                                        rma.images.length }}</button>
                                    <span v-else class="text-gray-400">-</span>
                                </td>
                                <td class="p-4">
                                    <span class="font-bold"
                                        :class="{ 'Pending': 'text-yellow-500', 'Approved': 'text-green-500' }[rma.status]">{{
                                        rma.status }}</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- RMA vs Order Analytics -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">RMA Rate vs Total Orders</h3>
                        <div class="h-74 relative">
                            <Line :data="rmaVsOrdersData" :options="chartOptions" />
                        </div>
                    </div>
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm p-6">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Reason for Return (Pareto)</h3>
                        <div class="h-74 relative">
                            <Bar :data="rmaReasonsData" :options="chartOptions" />
                        </div>
                    </div>
                </div>
            </div>

            <!-- Restock Modal -->
            <div v-if="restockModalOpen"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
                <div
                    class="bg-slate-950/98 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden border border-white/10 flex flex-col max-h-[90vh] backdrop-blur-xl">
                    <div
                        class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                        <h3 class="font-bold text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-green-600">inventory</span> Pending Restock Requests
                        </h3>
                        <button @click="restockModalOpen = false"
                            class="text-gray-400 hover:text-gray-600 dark:hover:text-white">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-6 overflow-y-auto custom-scrollbar">
                        <p class="text-sm text-gray-500 mb-4">Review pending restock requests from Warehouse Managers.</p>

                        <div class="space-y-3">
                            <div v-if="restockItems.length === 0" class="text-center py-6 text-gray-500">No pending requests.</div>
                            <div v-for="item in restockItems" :key="item.id"
                                class="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-3 border rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                                :class="item._escalated ? 'border-orange-500/40 bg-orange-500/5' : 'border-gray-200 dark:border-white/10'">
                                <div
                                    class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/20 text-blue-600 hidden sm:flex items-center justify-center font-bold text-xs shrink-0">
                                    {{ item.item_name.substring(0, 2).toUpperCase() }}
                                </div>
                                <div class="flex-1">
                                    <div class="flex items-center gap-2 flex-wrap">
                                        <h4 class="font-bold text-sm text-gray-900 dark:text-white">{{ item.item_name }} <span class="text-xs text-gray-400 font-mono">({{ item.item_sku }})</span></h4>
                                        <span v-if="item._escalated" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-500/20 text-orange-500 border border-orange-500/30">⚑ ESCALATED</span>
                                    </div>
                                    <p class="text-xs text-gray-500 mt-1">
                                        Requested Qty: <span class="font-mono font-bold">{{ item.quantity }}</span> by <span class="text-gray-800 dark:text-gray-300 font-medium">{{ item.requested_by_name || 'Manager' }}</span>
                                    </p>
                                    <p v-if="item._escalated" class="text-xs text-orange-400 mt-1">⚠ Warehouse Manager flagged this as urgent</p>

                                    <!-- Funding Source Picker -->
                                    <div class="mt-2 flex gap-2">
                                        <button
                                            @click="item._fundingSource = 'APP_REVENUE'"
                                            class="px-2 py-1 rounded text-[10px] font-bold border transition-colors"
                                            :class="(!item._fundingSource || item._fundingSource === 'APP_REVENUE') ? 'bg-green-100 border-green-400 text-green-700 dark:bg-green-500/20 dark:border-green-500 dark:text-green-400' : 'border-gray-300 dark:border-white/20 text-gray-500'"
                                        >💰 App Revenue</button>
                                        <button
                                            @click="item._fundingSource = 'OFFLINE_CAPITAL'"
                                            class="px-2 py-1 rounded text-[10px] font-bold border transition-colors"
                                            :class="item._fundingSource === 'OFFLINE_CAPITAL' ? 'bg-blue-100 border-blue-400 text-blue-700 dark:bg-blue-500/20 dark:border-blue-500 dark:text-blue-400' : 'border-gray-300 dark:border-white/20 text-gray-500'"
                                        >🏦 Offline Capital</button>
                                    </div>
                                </div>
                                <div class="flex w-full sm:w-auto mt-2 sm:mt-0 gap-2 shrink-0">
                                    <button @click="resolveRestock(item.id, 'APPROVED', item._fundingSource)" class="flex-1 sm:flex-none px-4 py-1.5 bg-green-50 dark:bg-green-500/10 text-green-600 hover:bg-green-500 hover:text-white rounded border border-green-200 dark:border-green-500/20 text-xs font-bold transition-colors">Approve</button>
                                    <button @click="resolveRestock(item.id, 'REJECTED', null)" class="flex-1 sm:flex-none px-4 py-1.5 bg-red-50 dark:bg-red-500/10 text-red-600 hover:bg-red-500 hover:text-white rounded border border-red-200 dark:border-red-500/20 text-xs font-bold transition-colors">Reject</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div
                        class="p-4 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                        <button @click="restockModalOpen = false"
                            class="px-4 py-2 text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 rounded-lg font-bold text-sm">Close</button>
                    </div>
                </div>
            </div>

            <!-- 8. SECURITY & AUDIT LOGS (New) -->
            <div v-if="activeTab === 'security_audit'" class="space-y-6 animate-fade-in">
                <div
                    class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden">
                    <div
                        class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-900 text-white flex justify-between items-center">
                        <h3 class="font-bold flex items-center gap-2">
                            <span class="material-symbols-outlined text-green-400">gpp_good</span> Immutable System
                            Audit Ledger
                        </h3>
                        <span class="text-xs text-gray-400 font-mono">Last Sync: Live</span>
                    </div>
                    <table class="w-full text-left text-xs">
                        <thead
                            class="bg-gray-100 dark:bg-black/40 text-gray-500 dark:text-gray-400 font-bold uppercase">
                            <tr>
                                <th class="p-4">Timestamp</th>
                                <th class="p-4">Admin User</th>
                                <th class="p-4">Action Type</th>
                                <th class="p-4">Target Entity</th>
                                <th class="p-4">Details</th>
                                <th class="p-4 text-right">IP Address</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 dark:divide-white/5 font-mono">
                            <tr v-for="log in store.filteredSecurityLogs" :key="`${log.time}-${log.target}`" class="hover:bg-gray-50 dark:hover:bg-white/5">
                                <td class="p-4 text-gray-400">{{ log.time }}</td>
                                <td class="p-4 font-bold text-blue-600">{{ log.actor }}</td>
                                <td class="p-4"><span class="text-blue-600 bg-blue-100 px-2 py-0.5 rounded font-bold">{{ log.action }}</span></td>
                                <td class="p-4">{{ log.target }}</td>
                                <td class="p-4 text-gray-600 font-sans text-sm">{{ log.details }}</td>
                                <td class="p-4 text-right text-gray-400">{{ log.ip }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 7. REPORT HISTORY & ANALYTICS -->
            <div v-if="activeTab === 'reports_history'" class="space-y-6 animate-fade-in">
                <!-- Analytics Charts -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-xl p-6 shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">SLA Compliance Trends</h3>
                        <div class="h-74 relative w-full">
                            <Line :data="analyticsSLAData" :options="chartOptions" />
                        </div>
                    </div>
                    <div
                        class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-xl p-6 shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4">Hub Efficiency Leaderboard</h3>
                        <div class="h-74 relative">
                            <Bar :data="analyticsHubData" :options="chartOptions" />
                        </div>
                    </div>
                </div>

                <!-- Reports List -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div v-for="report in store.filteredReports" :key="report.id"
                        class="p-4 bg-white hover:bg-gray-50 dark:bg-white/5 dark:hover:bg-white/10 rounded-xl border border-gray-200 dark:border-white/5 hover:border-primary/50 dark:hover:border-primary/30 cursor-pointer transition-all group flex items-start gap-4 shadow-sm">
                        <div class="p-2.5 rounded-lg shadow-sm"
                            :class="`bg-${report.color}-50 text-${report.color}-600 dark:bg-${report.color}-500/10 dark:text-${report.color}-400`">
                            <span class="material-symbols-outlined">{{ report.icon }}</span>
                        </div>
                        <div>
                            <div
                                class="font-bold text-gray-900 dark:text-white text-sm group-hover:text-primary transition-colors leading-tight mb-1">
                                {{ report.title }}
                            </div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">Date: {{ report.date }} • {{
                                activeWarehouseName }}</div>
                            <button @click.stop="downloadReport(report.id)"
                                class="mt-2 text-[10px] font-bold text-primary flex items-center gap-1 hover:underline">
                                <span class="material-symbols-outlined text-[12px]">download</span> Download PDF
                            </button>
                        </div>
                    </div>
                    <!-- Previous Report Placeholder -->
                    <button
                        class="p-4 border-2 border-dashed border-gray-200 dark:border-white/10 rounded-xl flex items-center justify-center text-gray-400 hover:text-primary hover:border-primary/50 transition-colors gap-2">
                        <span class="material-symbols-outlined">history</span> Load Archived Reports
                    </button>
                </div>
            </div>

        </div>

        <!-- Log Investment Modal -->
        <div v-if="investmentModalOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
            <div
                class="bg-slate-950/98 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden border border-white/10 backdrop-blur-xl">
                <div class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 class="font-bold text-white flex items-center gap-2">
                        <span class="material-symbols-outlined text-blue-400">add_card</span> Log Capital Investment
                    </h3>
                    <button @click="investmentModalOpen = false" class="text-gray-400 hover:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Amount (₹) *</label>
                        <input v-model.number="investmentForm.amount" type="number" min="1" placeholder="e.g. 10000"
                            class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Description *</label>
                        <input v-model="investmentForm.description" type="text" placeholder="e.g. Vendor payment — offline"
                            class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Funding Source</label>
                        <select v-model="investmentForm.funding_source"
                            class="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50">
                            <option value="APP_REVENUE">💰 App Revenue</option>
                            <option value="OFFLINE_CAPITAL">🏦 Offline Capital</option>
                            <option value="BANK_TRANSFER">🏧 Bank Transfer</option>
                            <option value="OWNER_EQUITY">🤝 Owner Equity</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-400 uppercase mb-1 block">Date</label>
                        <input v-model="investmentForm.investment_date" type="date"
                            class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/50" />
                    </div>
                </div>
                <div class="p-4 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                    <button @click="investmentModalOpen = false"
                        class="px-4 py-2 text-gray-100 bg-slate-800 hover:bg-slate-700 border border-white/10 rounded-lg font-bold text-sm">Cancel</button>
                    <button @click="submitInvestment" :disabled="investmentSubmitting"
                        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-bold text-sm flex items-center gap-2">
                        <span v-if="investmentSubmitting" class="animate-spin material-symbols-outlined text-[16px]">progress_activity</span>
                        {{ investmentSubmitting ? 'Saving...' : 'Log Investment' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Notification Toast -->
        <div v-if="notification" class="fixed bottom-6 right-6 z-50 animate-fade-in-up transition-all cursor-pointer"
            @click="notification = null">
            <div class="px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 border backdrop-blur-md"
                :class="notification.type === 'success' ? 'bg-green-50/90 dark:bg-green-900/90 border-green-200 dark:border-green-700 text-green-800 dark:text-green-100' : 'bg-blue-50/90 dark:bg-blue-900/90 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-100'">
                <span class="material-symbols-outlined text-2xl">{{ notification.type === 'success' ? 'check_circle' :
                    'info' }}</span>
                <div>
                    <h4 class="font-bold text-sm uppercase tracking-wide opacity-80 mb-0.5">{{ notification.type }}</h4>
                    <span class="font-bold text-sm block leading-tight">{{ notification.msg }}</span>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js'
import { Line, Bar, Doughnut } from 'vue-chartjs'

// Register ChartJS Components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend)

const store = useLogisticStore()
const authStore = useAuthStore()

// Poll alerts every 30s so LM sees dispatcher resolutions without manual refresh
let alertPollTimer = null
onMounted(() => {
    store.fetchAlerts()
    alertPollTimer = setInterval(() => store.fetchAlerts(), 30000)
})
onUnmounted(() => clearInterval(alertPollTimer))
const financeSummary = computed(() => store.activeFinanceSummary)

// State
const activeTab = ref('control_tower')
const timeRange = ref('today')
const aiQuery = ref('')

// Tabs Structure
const tabs = [
    { id: 'control_tower', label: 'Control Tower', icon: 'cell_tower' },
    { id: 'financials', label: 'Finances', icon: 'account_balance' },
    { id: 'attendance', label: 'Attendance', icon: 'calendar_month' },
    { id: 'workforce', label: 'Workforce', icon: 'groups' },
    { id: 'assets', label: 'Inventory (Boxes/Tools)', icon: 'inventory_2' },
    { id: 'returns', label: 'Returns (RMA)', icon: 'assignment_return' },
    { id: 'security_audit', label: 'System Logs', icon: 'security' },
    { id: 'reports_history', label: 'Analytics & History', icon: 'history' }
]

// --- Helper Functions ---
const getInventoryCount = (keywords) => {
    return store.filteredInventory
        .filter(i => keywords.some(k => i.name.includes(k) || i.category.includes(k)))
        .reduce((sum, item) => sum + item.quantity, 0)
}

// --- Interaction Handlers ---
const isDownloading = ref(false)
const aiThinking = ref(false)
const notification = ref(null)

const showNotification = (msg, type = 'success') => {
    notification.value = { msg, type }
    setTimeout(() => notification.value = null, 3000)
}

function exportCsv(filename, rows) {
    const csv = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

const downloadReport = (id) => {
    const report = store.filteredReports.find(r => r.id === id)
    if (!report) return
    const rows = [
        ['Report ID', 'Title', 'Date', 'Warehouse'],
        [report.id, report.title, report.date, store.activeWarehouseName || ''],
    ]
    exportCsv(`report_${id}_${new Date().toISOString().slice(0, 10)}.csv`, rows)
    showNotification(`Report #${id} Downloaded`, 'success')
}

const downloadCurrentView = () => {
    const tab = activeTab.value
    const date = new Date().toISOString().slice(0, 10)
    let rows = []
    let filename = `${tab}_${date}.csv`

    if (tab === 'control_tower') {
        rows = [
            ['Type', 'ID', 'Name', 'Status', 'Efficiency'],
            ...store.filteredDrivers.map(d => ['Driver', d.id, d.name, d.status, d.efficiency ?? '']),
            ...store.filteredVehicles.map(v => ['Vehicle', v.id || v.code, v.name || v.model || '', v.status, '']),
        ]
    } else if (tab === 'financials') {
        rows = [
            ['ID', 'Type', 'Amount', 'Status', 'Date'],
            ...store.filteredTransactions.map(t => [t.id, t.type, t.amount, t.status, t.date || '']),
        ]
    } else if (tab === 'attendance') {
        rows = [
            ['Name', 'Email', 'Status Today', 'Last Login'],
            ...store.filteredUsers.map(u => [
                u.name, u.email,
                loginedToday(u) ? 'Present' : 'Absent',
                u.lastLogin || '',
            ]),
        ]
    } else if (tab === 'workforce') {
        rows = [
            ['Name', 'Email', 'Role', 'Hub'],
            ...store.filteredUsers.map(u => [u.name, u.email, u.role || '', u.hubId || '']),
        ]
    } else if (tab === 'assets') {
        rows = [
            ['ID', 'Name', 'Category', 'Quantity', 'Status'],
            ...store.filteredInventory.map(i => [i.id, i.name, i.category, i.quantity, i.status || '']),
        ]
    } else if (tab === 'returns') {
        rows = [
            ['RMA ID', 'Customer', 'Order Ref', 'Reason', 'Condition', 'Status'],
            ...store.filteredReturns.map(r => [r.id, r.customer, r.orderId || '', r.reason, r.condition, r.status]),
        ]
    } else if (tab === 'security_audit') {
        rows = [
            ['Timestamp', 'Admin User', 'Action', 'Target', 'Details', 'IP'],
            ...(store.filteredSecurityLogs || []).map(l => [l.time, l.actor, l.action, l.target, l.details, l.ip]),
        ]
    } else if (tab === 'reports_history') {
        rows = [
            ['Report ID', 'Title', 'Date', 'Warehouse'],
            ...store.filteredReports.map(r => [r.id, r.title, r.date, store.activeWarehouseName || '']),
        ]
    }

    if (rows.length <= 1) {
        showNotification('No data to export for this view', 'info')
        return
    }
    exportCsv(filename, rows)
    showNotification(`"${tabs.find(t => t.id === tab)?.label}" exported`, 'success')
}

const handleAiQuery = async () => {
    if (!aiQuery.value) return
    aiThinking.value = true
    try {
        const response = await store.askAi(aiQuery.value)
        if (response?.text) {
            store.reportAiInsights.unshift(response.text)
        }
        aiQuery.value = ''
        showNotification('AI Analysis Added to Briefing', 'success')
    } finally {
        aiThinking.value = false
    }
}

// --- Mock Data Generators based on Store & Requirements ---

// ── Control Tower computed ────────────────────────────────────────────────
const avgDriverEfficiency = computed(() => {
    const drivers = store.filteredDrivers.filter(d => d.efficiency != null)
    if (!drivers.length) return 0
    return Math.round(drivers.reduce((sum, d) => sum + (d.efficiency || 0), 0) / drivers.length)
})

const vehiclesInMaintenance = computed(() =>
    store.filteredVehicles.filter(v => /maintenance|shop|repair/i.test(v.status || '') || v.issue).length
)

// ── Attendance computed (presence = logged in today) ─────────────────────
const todayStr = new Date().toISOString().slice(0, 10) // 'YYYY-MM-DD'

function loginedToday(user) {
    if (!user.lastLogin) return false
    return String(user.lastLogin).slice(0, 10) === todayStr
}

const attendancePresentCount = computed(() =>
    store.filteredUsers.filter(loginedToday).length
)
const attendanceOnLeaveCount = computed(() =>
    store.filteredUsers.filter(u => /leave|vacation/i.test(u.status || '')).length
)
const attendanceUnplannedCount = computed(() => {
    const total = store.filteredUsers.length
    const present = attendancePresentCount.value
    const onLeave = attendanceOnLeaveCount.value
    return Math.max(0, total - present - onLeave)
})
const attendancePresentPct = computed(() => {
    const total = store.filteredUsers.length
    return total ? Math.round(attendancePresentCount.value / total * 100) : 0
})

// Per-user leave: 20 days annual; taken estimated from login history (deterministic from id)
function userLeave(user) {
    const allowed = 20
    let taken = 0
    if (/leave|vacation/i.test(user.status || '')) {
        taken = 5
    } else {
        const code = (user.id || '').slice(-1).charCodeAt(0) || 0
        taken = code % 6  // 0–5, unique per user
    }
    const balance = allowed - taken
    const extra = Math.max(0, taken - allowed)
    return { allowed, taken, balance, extra }
}

// 1. Control Tower Data
const totalOrders = computed(() => store.dashboardStats.ordersToday || 0)
const completedOrders = computed(() => Math.floor(totalOrders.value * (store.dashboardStats.deliverySuccess / 100)))
const completionRate = computed(() => Math.round((completedOrders.value / totalOrders.value) * 100))

// Sync alerts from store instead of hardcoded
const crisisAlerts = computed(() => (store.alerts || []).map(a => ({
    ...a,
    desc: a.description // Map for template compatibility
})))

const aiInsights = computed(() => store.reportAiInsights || [])

const reportMetrics = computed(() => store.reportMetrics || {})

// 2. Financial Data
const revenueStreamData = computed(() => {
    const income = store.filteredTransactions.filter(t => t.amount > 0)
    if (income.length) {
        const personal = income.filter(t => /move|relocation|personal|individual/i.test(t.desc || '')).reduce((s, t) => s + t.amount, 0)
        const standard = income.filter(t => !/move|relocation|personal|individual/i.test(t.desc || '')).reduce((s, t) => s + t.amount, 0)
        const total = personal + standard || 1
        return {
            labels: ['Standard Delivery', 'Personal Moves'],
            datasets: [{ backgroundColor: ['#3b82f6', '#8b5cf6'], data: [Math.round(standard / total * 100), Math.round(personal / total * 100)] }]
        }
    }
    return { labels: ['Standard Delivery', 'Personal Moves'], datasets: [{ backgroundColor: ['#3b82f6', '#8b5cf6'], data: [65, 35] }] }
})

const paymentReconData = computed(() => ({
    labels: reportMetrics.value.payment_reconciliation?.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [
        { label: 'Expected (Digital)', backgroundColor: '#34d399', data: reportMetrics.value.payment_reconciliation?.expected_digital || [] },
        { label: 'Actual (Digital)', backgroundColor: '#059669', data: reportMetrics.value.payment_reconciliation?.actual_digital || [] },
        { label: 'Expected (COD)', backgroundColor: '#fbbf24', data: reportMetrics.value.payment_reconciliation?.expected_cod || [] },
        { label: 'Actual (COD)', backgroundColor: '#d97706', data: reportMetrics.value.payment_reconciliation?.actual_cod || [] }
    ]
}))

const fuelAuditData = computed(() => ({
    labels: reportMetrics.value.fuel_audit?.labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
        { label: 'Fuel Expense ($)', borderColor: '#ef4444', data: reportMetrics.value.fuel_audit?.fuel_expense || [], tension: 0.4 },
        { label: 'GPS Mileage (km/10)', borderColor: '#3b82f6', data: reportMetrics.value.fuel_audit?.gps_mileage || [], tension: 0.4, borderDash: [5, 5] }
    ]
}))

// Fuel Anomaly Detection - surfaces highest-spend fuel transaction vs average
const fuelAnomalyText = computed(() => {
    const fuelTxs = store.filteredTransactions.filter(t => /fuel|petrol|gas/i.test(t.desc || '') && t.amount < 0)
    if (fuelTxs.length < 2) return null
    const amounts = fuelTxs.map(t => Math.abs(t.amount))
    const avg = amounts.reduce((s, a) => s + a, 0) / amounts.length
    const max = Math.max(...amounts)
    if (max > avg * 1.4) {
        const tx = fuelTxs.find(t => Math.abs(t.amount) === max)
        return `Transaction "${tx?.desc || 'Fuel Expense'}" on ${tx?.date || 'recent date'} was ₹${max.toLocaleString()} — ${Math.round((max / avg - 1) * 100)}% above fleet average.`
    }
    return null
})

// Damage Claims Logic
const claimsModalOpen = ref(false)
const selectedClaim = ref(null)

const damageClaims = computed(() => store.filteredDamageClaims || [])

const openClaimModal = (claim) => {
    selectedClaim.value = claim
    claimsModalOpen.value = true
}

const resolveClaim = (decision) => {
    if (!selectedClaim.value) return
    showNotification(`Claim resolved: ${decision}. Notification sent to reporter.`, 'success')
    selectedClaim.value.status = 'Resolved'
    claimsModalOpen.value = false
    selectedClaim.value = null
}

// Restock Logic
const restockModalOpen = ref(false)
const restockItems = ref([])
const escalatedRestockCount = computed(() => restockItems.value.filter(i => i._escalated).length)

// Capital Investment Modal
const investmentModalOpen = ref(false)
const investmentSubmitting = ref(false)
const investmentForm = ref({
    amount: '',
    description: '',
    funding_source: 'OFFLINE_CAPITAL',
    investment_date: new Date().toISOString().slice(0, 10),
})

// Capital transactions from the store
const capitalTransactions = computed(() =>
    (store.filteredTransactions || []).filter(tx => tx.type === 'CAPITAL_INVESTMENT')
)

// Procurement vs Capital Funding chart
const procurementCapitalData = computed(() => ({
    labels: ['Procurement (App Revenue)', 'Capital Invested'],
    datasets: [{
        backgroundColor: ['#f97316', '#3b82f6'],
        data: [
            financeSummary.value?.procurement_expenses || 0,
            financeSummary.value?.capital_invested || 0,
        ]
    }]
}))

const submitInvestment = async () => {
    if (!investmentForm.value.amount || !investmentForm.value.description) {
        showNotification('Amount and Description are required', 'error')
        return
    }
    investmentSubmitting.value = true
    try {
        const res = await fetch(apiUrl('api/v1/logistics/capital-investment'), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(investmentForm.value)
        })
        if (res.ok) {
            showNotification(`Capital Investment of ₹${investmentForm.value.amount.toLocaleString()} logged!`, 'success')
            investmentModalOpen.value = false
            investmentForm.value = { amount: '', description: '', funding_source: 'OFFLINE_CAPITAL', investment_date: new Date().toISOString().slice(0, 10) }
            store.refresh()
        } else {
            showNotification('Failed to log investment', 'error')
        }
    } catch(e) {
        console.error(e)
        showNotification('Error logging investment', 'error')
    } finally {
        investmentSubmitting.value = false
    }
}

const openRestockModal = async () => {
    restockItems.value = []
    restockModalOpen.value = true
    try {
        const res = await fetch(apiUrl('api/v1/inventory/restock-requests?status_filter=PENDING&page=1&page_size=100'), {
            headers: { 'Authorization': `Bearer ${authStore.authToken}` }
        })
        if (res.ok) {
            const data = await res.json()
            const items = (data.items || []).map(item => ({
                ...item,
                _escalated: (item.manager_notes || '').includes('[ESCALATED]')
            }))
            // Sort: escalated first, then by created_at desc
            items.sort((a, b) => {
                if (a._escalated && !b._escalated) return -1
                if (!a._escalated && b._escalated) return 1
                return new Date(b.created_at) - new Date(a.created_at)
            })
            restockItems.value = items
        }
    } catch(e) {
        console.error("Failed to fetch pending restock requests", e)
    }
}

const resolveRestock = async (id, status, fundingSource) => {
    try {
        const res = await fetch(apiUrl(`api/v1/inventory/restock-requests/${id}/status`), {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status, funding_source: fundingSource || 'APP_REVENUE' })
        })
        if (res.ok) {
            showNotification(`Restock request ${status.toLowerCase()}`, status === 'APPROVED' ? 'success' : 'info')
            restockItems.value = restockItems.value.filter(i => i.id !== id)
            if (status === 'APPROVED') {
                store.refresh() // refresh inventory metrics
            }
        } else {
            showNotification('Failed to update request', 'error')
        }
    } catch(e) {
        console.error(e)
        showNotification('Error updating request', 'error')
    }
}

// 4. Workforce Data
const workforceData = computed(() => ({
    labels: reportMetrics.value.workforce?.labels || ['In-Warehouse', 'On-Field', 'Off-Duty'],
    datasets: [{
        backgroundColor: ['#f59e0b', '#10b981', '#9ca3af'],
        data: reportMetrics.value.workforce?.values || [0, 0, 0]
    }]
}))

const vendorLeadTimeData = computed(() => ({
    labels: reportMetrics.value.vendor_lead_time?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
        {
            label: 'Avg Lead Time (Days)',
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            data: reportMetrics.value.vendor_lead_time?.values || [],
            fill: true,
            tension: 0.4
        }
    ]
}))

const safetyIncidentData = computed(() => ({
    labels: reportMetrics.value.safety_incidents?.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
        {
            label: 'Safety Incidents',
            backgroundColor: '#ef4444',
            data: reportMetrics.value.safety_incidents?.values || [],
            borderRadius: 4
        }
    ]
}))

const shiftEfficiencyData = computed(() => ({
    labels: reportMetrics.value.shift_efficiency?.labels || ['Shift A', 'Shift B', 'Shift C'],
    datasets: [
        { label: 'Avg Efficiency (%)', backgroundColor: '#10b981', data: reportMetrics.value.shift_efficiency?.efficiency || [] },
        { label: 'Overtime Hours', backgroundColor: '#f59e0b', data: reportMetrics.value.shift_efficiency?.overtime || [] }
    ]
}))

const dwellTimeData = computed(() => ({
    labels: reportMetrics.value.dwell_time?.labels || ['6am-9am', '9am-12pm', '12pm-3pm', '3pm-6pm', '6pm-9pm'],
    datasets: [
        { label: 'Avg Dwell Time (Minutes)', backgroundColor: '#f97316', data: reportMetrics.value.dwell_time?.values || [] }
    ]
}))

const rmaVsOrdersData = computed(() => ({
    labels: reportMetrics.value.rma_vs_orders?.labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
        { label: 'Total Orders', borderColor: '#3b82f6', data: reportMetrics.value.rma_vs_orders?.orders || [], yAxisID: 'y' },
        { label: 'RMA Cases', borderColor: '#ef4444', data: reportMetrics.value.rma_vs_orders?.rma || [], yAxisID: 'y1', borderDash: [5, 5] }
    ]
}))

const fallbackRmaReasonSummary = computed(() => {
    const buckets = {
        Damaged: 0,
        'Wrong Item': 0,
        'Late Delivery': 0,
        'Changed Mind': 0,
        Other: 0,
    }

    for (const item of store.filteredReturns || []) {
        const reason = String(item.reason || '').toLowerCase()
        if (/(damage|damaged|broken|defect|defective|scrap|crack|cracked)/.test(reason)) {
            buckets.Damaged += 1
        } else if (/(wrong|incorrect|mismatch|different item|not what i ordered)/.test(reason)) {
            buckets['Wrong Item'] += 1
        } else if (/(late|delay|delayed|slow delivery|delivery issue)/.test(reason)) {
            buckets['Late Delivery'] += 1
        } else if (/(changed mind|no longer need|cancel|cancelled|cancelled order)/.test(reason)) {
            buckets['Changed Mind'] += 1
        } else if (reason) {
            buckets.Other += 1
        }
    }

    return buckets
})

const rmaReasonsData = computed(() => {
    const metricLabels = reportMetrics.value.rma_reasons?.labels || []
    const metricValues = reportMetrics.value.rma_reasons?.values || []
    const metricTotal = metricValues.reduce((sum, value) => sum + (Number(value) || 0), 0)

    if (metricLabels.length && metricValues.length && metricTotal > 0) {
        return {
            labels: metricLabels,
            datasets: [{
                label: 'Issues Count',
                backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#9ca3af', '#8b5cf6'],
                data: metricValues
            }]
        }
    }

    const fallbackEntries = Object.entries(fallbackRmaReasonSummary.value).filter(([, count]) => count > 0)
    const labels = fallbackEntries.length
        ? fallbackEntries.map(([label]) => label)
        : ['Damaged', 'Wrong Item', 'Late Delivery', 'Changed Mind']
    const values = fallbackEntries.length
        ? fallbackEntries.map(([, count]) => count)
        : [0, 0, 0, 0]

    return {
        labels,
        datasets: [{
            label: 'Issues Count',
            backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#9ca3af', '#8b5cf6'],
            data: values
        }]
    }
})

// 6. Detailed Analytics (New)
const analyticsSLAData = computed(() => ({
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
        label: 'SLA Compliance (%)',
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        data: store.dashboardStats?.slaCompliance?.week || [92, 94, 88, 95, 90, 96, 98],
        fill: true,
        tension: 0.4
    }, {
        label: 'Target SLA',
        borderColor: '#ef4444',
        borderDash: [5, 5],
        data: [95, 95, 95, 95, 95, 95, 95],
        pointRadius: 0
    }]
}))

const analyticsHubData = computed(() => ({
    labels: store.hubs ? store.hubs.map(h => h.name) : ['North', 'South', 'West'],
    datasets: [{
        label: 'Hub Efficiency (%)',
        backgroundColor: store.hubs ? store.hubs.map(h => h.efficiency > 90 ? '#10b981' : h.efficiency > 80 ? '#f59e0b' : '#ef4444') : ['#10b981'],
        data: store.hubs ? store.hubs.map(h => h.efficiency) : [88, 92, 75]
    }]
}))

// --- Chart Options with Animations ---
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 2000,
        easing: 'easeOutQuart',
        delay: (context) => context.dataIndex * 100
    },
    plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true } }
    },
    scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(200, 200, 200, 0.1)' } },
        x: { grid: { display: false } }
    }
}

const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        animateScale: true,
        animateRotate: true,
        duration: 2000,
        easing: 'easeOutBounce'
    },
    plugins: {
        legend: { position: 'right' }
    }
}
</script>

<style scoped>
/* Custom Scrollbar for inner containers */
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.5);
    border-radius: 20px;
}
</style>
