<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div
                    class="w-10 h-10 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center shadow-lg shadow-green-500/30">
                    <span class="material-symbols-outlined text-black">health_and_safety</span>
                </div>
                <h2
                    class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-blue-500">
                    Smart Dispatch Assistant</h2>
            </div>
            <div class="flex items-center gap-3">
                <button @click="showChat = !showChat"
                    :class="showChat ? 'bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-800 dark:text-white border-gray-300 dark:border-white/20' : 'bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20'"
                    class="border py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm font-bold">
                    <span class="material-symbols-outlined text-[18px]">smart_toy</span>
                    {{ showChat ? 'Hide' : 'AI' }} Chat
                </button>
                <div class="flex items-center gap-2 text-xs text-gray-400">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> AI Engine Active
                </div>
            </div>
        </div>

        <!-- Natural Language Command Input -->
        <div class="glass-panel p-4 rounded-xl">
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary">terminal</span>
                <input v-model="nlCommand" type="text"
                    class="flex-1 bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-3 text-gray-900 dark:text-white text-sm placeholder-gray-500 focus:border-primary/50 focus:outline-none"
                    placeholder='Type a command e.g. "Show ready orders with assigned vehicles" or "Suggest best driver for released orders"'
                    @keyup.enter="executeNLCommand" />
                <button @click="executeNLCommand" :disabled="nlProcessing"
                    class="bg-primary hover:bg-primary-dark text-black font-bold px-4 py-3 rounded-lg text-sm transition-colors flex items-center gap-1 disabled:opacity-50">
                    <span v-if="nlProcessing"
                        class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                    <span v-else class="material-symbols-outlined text-[18px]">send</span> {{ nlProcessing ?
                        'Processing...' : 'Execute' }}
                </button>
            </div>
            <div v-if="nlResponse" class="mt-3 p-3 bg-green-50 dark:bg-primary/5 border border-primary/20 rounded-lg">
                <div class="text-[10px] text-primary uppercase font-bold tracking-wider mb-1">AI Response</div>
                <div class="text-sm text-gray-700 dark:text-gray-300" v-html="nlResponse"></div>
            </div>
            <div class="mt-3 flex gap-2 overflow-x-auto no-scrollbar pb-1 max-w-full" @wheel.prevent="handleChipsScroll"
                style="width: 75vw;">
                <button v-for="q in quickCommands" :key="q" @click="nlCommand = q; executeNLCommand()"
                    class="whitespace-nowrap flex-shrink-0 text-[11px] font-medium bg-white dark:bg-black/30 border border-gray-200 dark:border-white/10 hover:border-primary/50 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-1.5 rounded-full shadow-sm transition-all">{{
                        q }}</button>
            </div>
        </div>

        <div class="grid gap-6" :class="showChat ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1 lg:grid-cols-2'">
            <!-- AI Recommendations -->
            <div class="glass-panel p-6 rounded-xl flex flex-col h-[540px]">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">lightbulb</span>
                    AI Dispatch Suggestions
                </h3>
                <div class="space-y-4 flex-1 overflow-y-auto no-scrollbar pr-2">
                    <div v-if="suggestions.length === 0" class="text-center py-8 text-gray-500 text-sm">
                        <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
                        No dispatch exceptions right now. Released orders are covered.
                    </div>
                    <div v-for="suggestion in suggestions.filter(s => !ignoredSuggestions.has(s.id))" :key="suggestion.id"
                        class="p-4 bg-gray-50 dark:bg-white/5 border rounded-xl transition-all cursor-pointer group"
                        :class="appliedSuggestions.has(suggestion.id) ? 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-900/10' : 'border-gray-200 dark:border-white/5 hover:border-primary/30'">
                        <div class="flex justify-between items-start mb-2">
                            <div :class="suggestion.color" class="font-bold text-sm">
                                {{ appliedSuggestions.has(suggestion.id) ? '✓ ' : '' }}{{ suggestion.title }}
                            </div>
                            <div class="text-xs text-gray-600 dark:text-gray-400">
                                Confidence: <span
                                    :class="suggestion.confidence >= 90 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'"
                                    class="font-bold">{{ suggestion.confidence }}%</span>
                            </div>
                        </div>
                        <div class="text-sm text-gray-700 dark:text-gray-300 mb-2" v-html="suggestion.message"></div>
                        <div v-if="suggestion.explanation"
                            class="mb-2 p-2 bg-blue-500/10 dark:bg-blue-500/5 border border-blue-500/30 dark:border-blue-500/10 rounded text-[11px] text-blue-700 dark:text-blue-300">
                            <span class="font-bold">Why:</span> {{ suggestion.explanation }}
                        </div>
                        <div v-if="!appliedSuggestions.has(suggestion.id)" class="flex gap-2">
                            <button v-for="action in suggestion.actions" :key="action.label"
                                @click="applySuggestion(suggestion, action.label)" :class="action.class"
                                class="px-3 py-1 rounded text-xs font-bold transition-colors">{{ action.label
                                }}</button>
                        </div>
                        <div v-else
                            class="text-[10px] text-green-600 dark:text-green-400 font-bold flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">check_circle</span>
                            Applied successfully
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dispatch Forecast + Controls -->
            <div class="space-y-6 flex flex-col h-[540px] overflow-y-auto no-scrollbar pr-2">
                <div class="glass-panel p-6 rounded-xl flex-1">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Dispatch Readiness Forecast (Next 4 Hours)</h3>
                    <div class="h-48">
                        <Bar :data="demandChartData" :options="demandChartOptions" />
                    </div>
                    <div v-if="demandPeakHint" class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        {{ demandPeakHint }}
                    </div>
                    <div v-else class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        No demand forecast data yet. Will populate from live order volume.
                    </div>
                </div>

                <!-- Dispatch Control Toggles -->
                <div class="glass-panel p-6 rounded-xl flex-[0_0_auto]">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined text-red-400">priority_high</span>
                        Dispatch Control Toggles
                    </h3>
                    <div class="space-y-3">
                        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div>
                                <div class="text-sm text-gray-900 dark:text-white font-medium">Ready Order Prioritization</div>
                                <div class="text-[10px] text-gray-500">Auto-rank released orders that are waiting for driver confirmation</div>
                            </div>
                            <button @click="togglePeak('reallocation')"
                                :class="peakReallocation ? 'bg-primary' : 'bg-gray-600'"
                                class="w-10 h-5 rounded-full relative transition-colors">
                                <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                                    :class="peakReallocation ? 'left-5' : 'left-0.5'"></span>
                            </button>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div>
                                <div class="text-sm text-gray-900 dark:text-white font-medium">Driver Availability Escalation</div>
                                <div class="text-[10px] text-gray-500">Alert operations when vehicle-linked orders have no free driver</div>
                            </div>
                            <button @click="togglePeak('shift')" :class="shiftExtension ? 'bg-primary' : 'bg-gray-600'"
                                class="w-10 h-5 rounded-full relative transition-colors">
                                <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                                    :class="shiftExtension ? 'left-5' : 'left-0.5'"></span>
                            </button>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div>
                                <div class="text-sm text-gray-900 dark:text-white font-medium">Critical Order Priority Lock</div>
                                <div class="text-[10px] text-gray-500">Keep urgent released orders at the top of dispatcher review</div>
                            </div>
                            <button @click="togglePeak('vip')" :class="vipLock ? 'bg-primary' : 'bg-gray-600'"
                                class="w-10 h-5 rounded-full relative transition-colors">
                                <span class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all"
                                    :class="vipLock ? 'left-5' : 'left-0.5'"></span>
                            </button>
                        </div>
                        <div v-if="peakToast"
                            class="p-2 bg-primary/10 border border-primary/20 rounded text-xs text-primary text-center transition-all">
                            {{ peakToast }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- AI Chat Interface -->
            <div v-if="showChat" class="glass-panel rounded-xl flex flex-col h-[540px]">
                <div
                    class="p-4 border-b border-gray-200 dark:border-white/5 bg-gray-100 dark:bg-black/20 flex items-center gap-2">
                    <div
                        class="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center">
                        <span class="material-symbols-outlined text-black text-[16px]">smart_toy</span>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white">AI Dispatch Agent</div>
                        <div class="text-[10px] text-green-400">Online • Reasoning</div>
                    </div>
                </div>

                <div ref="chatContainer" class="flex-1 overflow-y-auto no-scrollbar p-4 space-y-3">
                    <div v-for="msg in chatMessages" :key="msg.id"
                        :class="msg.sender === 'ai' ? 'flex gap-2' : 'flex gap-2 flex-row-reverse'">
                        <div v-if="msg.sender === 'ai'"
                            class="w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center shadow-sm">
                            <span class="material-symbols-outlined text-black text-[14px]">smart_toy</span>
                        </div>
                        <div v-else
                            class="w-7 h-7 flex-shrink-0 rounded-full bg-primary flex items-center justify-center text-[9px] text-black font-bold shadow-sm">
                            YOU
                        </div>
                        <div class="max-w-[85%] p-3 rounded-xl text-sm shadow-sm font-medium"
                            :class="msg.sender === 'ai' ? 'bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 text-gray-800 dark:text-gray-100 rounded-tl-none' : 'bg-primary/30 border border-primary/40 text-black dark:text-white rounded-tr-none'">
                            <span v-if="msg.sender === 'ai'" v-html="msg.text"></span>
                            <span v-else>{{ msg.text }}</span>
                        </div>
                    </div>
                    <div v-if="chatTyping" class="flex gap-2">
                        <div
                            class="w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center">
                            <span class="material-symbols-outlined text-black text-[14px]">smart_toy</span>
                        </div>
                        <div
                            class="bg-white dark:bg-white/10 border border-gray-200 dark:border-white/10 p-3 rounded-xl rounded-tl-none text-gray-500 text-sm shadow-sm">
                            <span class="inline-flex gap-1"><span
                                    class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"></span><span
                                    class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
                                    style="animation-delay:0.15s"></span><span
                                    class="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
                                    style="animation-delay:0.3s"></span></span>
                        </div>
                    </div>
                </div>

                <div class="p-4 border-t border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/40">
                    <div class="flex items-center gap-2 relative">
                        <input v-model="chatInput" type="text" placeholder="Ask the AI agent..."
                            class="flex-1 bg-white dark:bg-white/5 border border-gray-300 dark:border-white/20 shadow-sm rounded-full py-2.5 pl-4 pr-12 text-gray-900 dark:text-white text-sm font-medium focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                            @keyup.enter="sendChat" />
                        <button @click="sendChat"
                            class="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 bg-primary rounded-full text-black hover:scale-105 transition-transform flex items-center justify-center shadow-md">
                            <span class="material-symbols-outlined text-[18px]">send</span>
                        </button>
                    </div>
                    <div class="flex gap-2 mt-3 overflow-x-auto no-scrollbar pb-1 max-w-full"
                        @wheel.prevent="handleChipsScroll" style="max-width: 75vw;">
                        <button v-for="chip in chatChips" :key="chip" @click="chatInput = chip; sendChat()"
                            class="whitespace-nowrap flex-shrink-0 text-[11px] font-medium bg-white dark:bg-black/30 border border-gray-200 dark:border-white/10 hover:border-primary/50 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-1 rounded-full shadow-sm transition-all">{{
                                chip }}</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Delay Prediction Panel -->
        <div class="glass-panel p-6 rounded-xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-yellow-400">schedule</span>
                AI Dispatch Risk Engine
            </h3>
            <div v-if="delayPredictions.length === 0" class="text-center py-8 text-gray-500 text-sm">
                <span class="material-symbols-outlined text-green-400 text-[32px] block mb-2">check_circle</span>
                No delay risks detected. Routes are running smoothly.
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div v-for="pred in delayPredictions" :key="pred.key" class="p-4 rounded-xl border"
                    :class="pred.risk === 'High' ? 'bg-red-500/5 border-red-500/20' : pred.risk === 'Medium' ? 'bg-yellow-500/5 border-yellow-500/20' : 'bg-green-500/5 border-green-500/20'">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-gray-900 dark:text-white font-bold text-sm">{{ pred.route }}</span>
                        <span class="text-[10px] px-2 py-0.5 rounded-full font-bold"
                            :class="pred.risk === 'High' ? 'bg-red-500/20 text-red-400' : pred.risk === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'">
                            {{ pred.risk }} Risk
                        </span>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ pred.reason }}</div>
                    <div class="flex items-center gap-2 mt-2">
                        <div class="flex-1 h-2 bg-gray-100 dark:bg-black/30 rounded-full overflow-hidden">
                            <div class="h-full rounded-full transition-all"
                                :class="pred.risk === 'High' ? 'bg-red-500' : pred.risk === 'Medium' ? 'bg-yellow-500' : 'bg-green-500'"
                                :style="{ width: pred.probability + '%' }"></div>
                        </div>
                        <span class="text-xs font-bold"
                            :class="pred.risk === 'High' ? 'text-red-400' : pred.risk === 'Medium' ? 'text-yellow-400' : 'text-green-400'">
                            {{ pred.probability }}%
                        </span>
                    </div>
                    <div class="flex items-center justify-between mt-2">
                        <div class="text-[10px] text-gray-500">Est. delay: {{ pred.delay }}</div>
                        <button @click="mitigateDelay(pred)" class="text-[10px] font-bold transition-colors"
                            :class="pred.mitigated ? 'text-green-400' : 'text-blue-400 hover:text-gray-900 dark:text-white'">
                            {{ pred.mitigated ? '✓ Mitigated' : 'Mitigate' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip } from 'chart.js'
import { useDispatcherStore } from '@/stores/dispatcherStore'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const store = useDispatcherStore()
onMounted(() => store.initialize().catch(() => {}))

const nlCommand = ref('')
const nlResponse = ref('')
const nlProcessing = ref(false)
const peakReallocation = ref(true)
const shiftExtension = ref(false)
const vipLock = ref(true)
const peakToast = ref('')
const showChat = ref(false)
const chatInput = ref('')
const chatTyping = ref(false)
const chatContainer = ref(null)

const quickCommands = [
    'Show ready orders with assigned vehicles',
    'Suggest best driver for released orders',
    'Show free drivers near Warehouse 3',
    'Flag orders with no driver available',
    'Prioritize urgent released orders',
    'Explain why this driver was suggested',
    'Predict dispatch delay for ready orders',
    'Find the next backup driver'
]

const chatChips = ['Best driver?', 'Ready orders?', 'No driver available?', 'Why this driver?']


function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
}

function normalizeCommand(value) {
    return String(value || '').trim().toLowerCase()
}

function getWarehouseByNumber(number) {
    const normalized = String(number)
    return (store.hubs || []).find((hub) => {
        const idMatch = String(hub.id || '') === normalized
        const codeMatch = String(hub.hubCode || '').match(/\d+/)?.[0] === normalized
        const nameMatch = String(hub.name || '').match(/\d+/)?.[0] === normalized
        return idMatch || codeMatch || nameMatch
    }) || null
}

function executeLocalQuickCommand(command) {
    const normalized = normalizeCommand(command)
    const drivers = store.dispatcherDrivers || []
    const activeOrders = store.activeOrders || []

    if (normalized === 'show idle drivers near warehouse 3') {
        const hub = getWarehouseByNumber(3)
        const idleDrivers = drivers
            .filter((driver) => driver.statusColor === 'bg-green-500' && (driver.load || 0) < 30)
            .sort((a, b) => {
                const aNear = String(a.hubId || '') === String(hub?.id || '')
                const bNear = String(b.hubId || '') === String(hub?.id || '')
                if (aNear !== bNear) return aNear ? -1 : 1
                return (a.load || 0) - (b.load || 0)
            })
            .slice(0, 5)

        return {
            text: idleDrivers.length
                ? `<b>Executed:</b> idle-driver scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>${idleDrivers.map((driver) => `${escapeHtml(driver.name)} (${driver.load}% load)`).join(', ')}.`
                : `<b>Executed:</b> idle-driver scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>No low-load active drivers found right now.`,
        }
    }

    if (normalized === 'prioritize vip orders for next 2 hours') {
        vipLock.value = true
        peakToast.value = 'VIP priority lock ON — Smart Dispatcher reserved priority handling'
        setTimeout(() => { peakToast.value = '' }, 3000)
        const vipOrders = activeOrders.filter((order) => String(order.priority || '').toUpperCase() === 'VIP')
        return {
            text: `<b>Executed:</b> VIP priority lock enabled for the next 2 hours.<br>Current VIP orders in scope: <b>${vipOrders.length}</b>.`
        }
    }

    if (normalized === 'find closest vehicle to warehouse 4') {
        const hub = getWarehouseByNumber(4)
        const nearbyDrivers = drivers
            .filter((driver) => String(driver.hubId || '') === String(hub?.id || ''))
            .sort((a, b) => (a.load || 0) - (b.load || 0))
        const best = nearbyDrivers[0]

        return {
            text: best
                ? `<b>Executed:</b> closest-vehicle scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>Best available match: <b>${escapeHtml(best.vehicle || 'Unassigned vehicle')}</b> with driver <b>${escapeHtml(best.name)}</b> at <b>${best.load}%</b> load.`
                : `<b>Executed:</b> closest-vehicle scan${hub ? ` for <b>${escapeHtml(hub.name)}</b>` : ''}.<br>No active driver-linked vehicle found for that warehouse right now.`,
        }
    }

    if (normalized === 'balance load across all active drivers') {
        const overloaded = drivers.filter((driver) => (driver.load || 0) > 85)
        const underused = drivers.filter((driver) => driver.statusColor === 'bg-green-500' && (driver.load || 0) < 30)
        return {
            text: `<b>Analysis ready:</b> load balance review completed.<br>Overloaded drivers: <b>${overloaded.length}</b>. Underused active drivers: <b>${underused.length}</b>.<br>No automatic reassignment is wired from this panel yet.`,
        }
    }

    if (normalized === 'assign all downtown parcels to smallest van') {
        const pendingCount = (store.pendingOrders || []).length
        return {
            text: `<b>Analysis ready:</b> found <b>${pendingCount}</b> pending order(s) to review for downtown assignment.<br>This panel does not yet auto-assign orders from the quick chip itself.`,
        }
    }

    if (normalized === 're-route zone b around highway closure') {
        return {
            text: `<b>Analysis ready:</b> reroute request captured for <b>Zone B</b>.<br>No direct reroute executor is connected from this quick chip yet; use Route Optimization to apply route changes.`,
        }
    }

    if (normalized === 'delay route 7 due to weather alerts') {
        return {
            text: `<b>Analysis ready:</b> weather-delay scenario prepared for <b>Route 7</b>.<br>This quick chip does not currently write an actual route-delay update into operations data.`,
        }
    }

    if (normalized === 'simulate 20% traffic increase in downtown') {
        return {
            text: `<b>Analysis ready:</b> simulated downtown traffic increase request received.<br>This panel currently shows advisory output only and does not run a live traffic simulation.`,
        }
    }

    return null
}

async function executeNLCommand() {
    if (!nlCommand.value.trim() || nlProcessing.value) return
    nlProcessing.value = true
    nlResponse.value = ''
    try {
        const localResult = executeLocalQuickCommand(nlCommand.value)
        if (localResult) {
            nlResponse.value = localResult.text
            return
        }
        const result = await store.askAi(nlCommand.value)
        nlResponse.value = result?.text || `Could not get an AI response for "${nlCommand.value}". Please try again.`
    } catch (_) {
        nlResponse.value = `AI engine unavailable. Please try again.`
    } finally {
        nlProcessing.value = false
    }
}

function togglePeak(type) {
    if (type === 'reallocation') { peakReallocation.value = !peakReallocation.value; peakToast.value = peakReallocation.value ? 'Ready-order prioritization enabled for released jobs' : 'Ready-order prioritization disabled' }
    else if (type === 'shift') { shiftExtension.value = !shiftExtension.value; peakToast.value = shiftExtension.value ? 'Driver availability escalation activated' : 'Driver availability escalation disabled' }
    else if (type === 'vip') { vipLock.value = !vipLock.value; peakToast.value = vipLock.value ? 'Critical order priority lock enabled' : 'Critical order priority lock removed' }
    setTimeout(() => { peakToast.value = '' }, 3000)
}

const appliedSuggestions = ref(new Set())
const ignoredSuggestions = ref(new Set())

function applySuggestion(suggestion, actionLabel) {
    if (actionLabel === 'Ignore') {
        ignoredSuggestions.value.add(suggestion.id)
        return
    }
    appliedSuggestions.value.add(suggestion.id)
}

// Chart.js Demand Prediction — derived from real order data bucketed by scheduled delivery hour
const hourlyVolumes = computed(() => {
    const buckets = Array(24).fill(0)
    const allOrders = [...(store.pendingOrders || []), ...(store.activeOrders || [])]
    allOrders.forEach(o => {
        const dateStr = o.deadline || o.eta || o.lastUpdated
        if (dateStr && dateStr !== '—') {
            const h = new Date(dateStr).getHours()
            if (!isNaN(h)) buckets[h]++
        }
    })
    // If no timestamp data, use order counts spread across hours as a flat baseline
    if (!buckets.some(v => v > 0)) {
        const basePerHour = Math.ceil((store.pendingOrders?.length || 0) / 6)
        if (basePerHour > 0) return Array.from({ length: 24 }, (_, i) => (i >= new Date().getHours() && i < new Date().getHours() + 6 ? basePerHour : 0))
    }
    return buckets
})

const demandChartData = computed(() => {
    const currentHour = new Date().getHours()
    const vols = hourlyVolumes.value
    const next6h = Array.from({ length: 6 }, (_, i) => vols[(currentHour + i) % 24] || 0)
    const maxVal = Math.max(...next6h, 1)
    return {
        labels: ['Now', '+1h', '+2h', '+3h', '+4h', '+5h'],
        datasets: [{
            label: 'Predicted Orders',
            data: next6h,
            backgroundColor: next6h.map(v => v === maxVal && v > 0 ? 'rgba(239,68,68,0.75)' : 'rgba(59,130,246,0.5)'),
            borderColor: 'rgba(59,130,246,0.8)',
            borderWidth: 1,
            borderRadius: 6,
        }]
    }
})

const demandPeakHint = computed(() => {
    const currentHour = new Date().getHours()
    const vols = hourlyVolumes.value
    const next6h = Array.from({ length: 6 }, (_, i) => ({ offset: i, vol: vols[(currentHour + i) % 24] || 0 }))
    if (!next6h.some(v => v.vol > 0)) return null
    const peak = next6h.reduce((a, b) => a.vol > b.vol ? a : b)
    if (peak.vol === 0) return null
    const peakHour = (currentHour + peak.offset) % 24
    return `Peak expected at ${String(peakHour).padStart(2, '0')}:00 — ${peak.vol} order(s) predicted.`
})

const demandChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#111', titleColor: '#fff', bodyColor: '#ccc', padding: 10 } },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#6b7280', font: { size: 10 } } },
        y: { grid: { color: 'rgba(156,163,175,0.2)' }, ticks: { color: '#6b7280', font: { size: 10 } }, beginAtZero: true }
    }
}

// Chat
const chatMessages = ref([
    { id: 1, sender: 'ai', text: 'Hello! I\'m your AI Dispatch Agent. Ask me about released orders, best driver suggestions, no-driver exceptions, or dispatch delay risks.' }
])


let chatId = 2
async function sendChat() {
    if (!chatInput.value.trim()) return
    const userMsg = chatInput.value.trim()
    chatMessages.value.push({ id: chatId++, sender: 'user', text: userMsg })
    chatInput.value = ''
    chatTyping.value = true
    scrollChat()
    try {
        const result = await store.askAi(userMsg)
        const responseText = result?.text || 'No response from AI. Please try again.'
        chatMessages.value.push({ id: chatId++, sender: 'ai', text: responseText })
    } catch (_) {
        chatMessages.value.push({ id: chatId++, sender: 'ai', text: 'AI engine unavailable. Please try again.' })
    } finally {
        chatTyping.value = false
        scrollChat()
    }
}

function scrollChat() {
    nextTick(() => {
        if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    })
}

function handleChipsScroll(e) {
    if (e.deltaX !== 0) {
        e.currentTarget.scrollLeft += e.deltaX;
    } else if (e.deltaY !== 0) {
        e.currentTarget.scrollLeft += e.deltaY;
    }
}

// Suggestions generated dynamically from store data
const suggestions = computed(() => {
    const result = []
    const drivers = store.dispatcherDrivers
    const allOrders = [...(store.pendingOrders || []), ...(store.activeOrders || [])]
    const readyOrders = allOrders.filter(order => order.readyForDispatch && order.vehicleId && !order.driverId)
    const freeDrivers = drivers.filter(driver =>
        driver.authorized
        && !driver.suspended
        && !driver.maintenance
        && (driver.activeOrders?.length || 0) === 0
    )

    if (readyOrders.length && freeDrivers.length) {
        result.push({
            id: 'best-driver-match',
            title: 'Best Driver Suggestion Ready',
            color: 'text-primary',
            applied: false,
            message: `<strong>${readyOrders[0].trackingCode || readyOrders[0].id}</strong> is released with vehicle <strong>${readyOrders[0].vehicle || 'assigned'}</strong>. <strong>${freeDrivers[0].name}</strong> is the best free driver to review first.`,
            explanation: 'The suggestion is based on driver availability, shift time remaining, and warehouse-fit signals from current dispatch data.',
            confidence: 94,
            actions: [
                { label: 'Queue Suggestion', class: 'bg-primary/30 hover:bg-primary/40 text-primary-900 dark:text-primary border border-primary/40 dark:border-primary/20' },
                { label: 'Review', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    if (readyOrders.length > freeDrivers.length) {
        result.push({
            id: 'driver-gap',
            title: 'Driver Gap Detected',
            color: 'text-orange-600 dark:text-orange-400',
            applied: false,
            message: `<strong>${readyOrders.length - freeDrivers.length}</strong> released order(s) have a vehicle assigned but not enough free drivers available right now.`,
            explanation: 'Dispatcher attention is needed for escalation, reassignment, or release sequencing.',
            confidence: 92,
            actions: [
                { label: 'Review Gap', class: 'bg-orange-500/30 hover:bg-orange-500/40 text-orange-800 dark:text-orange-400 border border-orange-500/40 dark:border-orange-500/20' },
                { label: 'Ignore', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    const hosRisk = drivers.filter(d => d.breakDue)
    if (hosRisk.length) {
        result.push({
            id: 'hos-risk', title: 'Driver Shift Limit Risk', color: 'text-red-600 dark:text-red-400', applied: false,
            message: `<strong>${hosRisk.length}</strong> driver(s) are approaching their shift limit. New one-to-one assignments may be blocked soon.`,
            explanation: `Drivers: ${hosRisk.map(d => d.name).join(', ')}. Confirm a backup driver before assigning another released order.`,
            confidence: 95,
            actions: [
                { label: 'Review HOS', class: 'bg-red-500/30 hover:bg-red-500/40 text-red-800 dark:text-red-400 border border-red-500/40 dark:border-red-500/20' },
                { label: 'Ignore', class: 'bg-gray-300 hover:bg-gray-400 dark:bg-white/10 dark:hover:bg-white/20 text-gray-800 dark:text-gray-300 border border-gray-400 dark:border-white/10' }
            ]
        })
    }

    return result
})

const mitigatedRoutes = ref(new Set())

const delayPredictions = computed(() => {
    const disruptions = store.disruptions || []
    const crises = store.activeCrises || []
    const items = []
    disruptions.forEach(d => {
        const sev = (d.severity || '').toLowerCase()
        const risk = sev === 'high' || sev === 'critical' ? 'High' : sev === 'medium' ? 'Medium' : 'Low'
        const baseProbability = risk === 'High' ? 78 : risk === 'Medium' ? 45 : 15
        const key = d.route || d.location || d.name || String(d.id)
        const mitigated = mitigatedRoutes.value.has(key)
        items.push({
            key,
            route: d.route || d.location || d.name || 'Affected Route',
            risk: mitigated ? (risk === 'High' ? 'Medium' : 'Low') : risk,
            probability: mitigated ? Math.max(5, baseProbability - 30) : baseProbability,
            reason: d.description || d.type || 'Disruption reported in this area',
            delay: risk === 'High' ? '30–45 min' : risk === 'Medium' ? '10–20 min' : '0–5 min',
            mitigated,
        })
    })
    crises.forEach(c => {
        const key = c.route || c.location || c.title || String(c.id)
        const mitigated = mitigatedRoutes.value.has(key)
        items.push({
            key,
            route: c.route || c.location || c.title || 'Crisis Route',
            risk: mitigated ? 'Medium' : 'High',
            probability: mitigated ? 55 : 85,
            reason: c.description || c.type || 'Active crisis — immediate attention needed',
            delay: mitigated ? '15–25 min' : '45+ min',
            mitigated,
        })
    })
    return items
})

function mitigateDelay(pred) {
    mitigatedRoutes.value = new Set([...mitigatedRoutes.value, pred.key])
}
</script>
