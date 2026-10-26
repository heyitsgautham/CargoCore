<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { driverManagementPageKey } from './driverManagementPageContext'

const { chatDriver, profileTargetDriver, showDriverProfile } = inject(driverManagementPageKey)
</script>
