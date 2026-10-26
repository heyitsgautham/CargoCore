<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { serviceMovesPageKey } from './serviceMovesPageContext'

const {
    cancelMove,
    completeMove,
    contactCrew,
    loading,
    moveMenu,
    serviceMoves,
    toggleMoveMenu,
    trackMove,
    trackingLoading,
    trackingMove,
} = inject(serviceMovesPageKey)
</script>
