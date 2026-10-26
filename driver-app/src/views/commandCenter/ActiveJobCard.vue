<template>
    <div class="rounded-3xl p-6 relative border"
        :class="isDark ? 'bg-surface-dark/60 border-white/10' : 'bg-white border-gray-100 shadow-xl'">
        <!-- Multiple Background Glows (contained in their own overflow-hidden layer) -->
        <div class="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
            <div class="absolute top-0 right-0 w-40 h-40 blur-3xl opacity-30"
                :class="jobStore.jobType === 'PARCEL_DELIVERY' ? 'bg-green-500' : jobStore.jobType === 'PARCEL_PICKUP' ? 'bg-blue-500' : 'bg-purple-500'">
            </div>
            <div class="absolute bottom-0 left-0 w-32 h-32 blur-3xl opacity-20 bg-primary"></div>
        </div>

        <div class="relative">
            <!-- Header Section -->
            <div class="flex items-start justify-between gap-3 mb-4">

                <!-- Icon Badge -->
                <div class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 ring-2 ring-offset-2"
                    :class="[
                        jobStore.jobType === 'PARCEL_DELIVERY'
                            ? 'bg-green-500/15 ring-green-500/30 ring-offset-transparent'
                            : jobStore.jobType === 'PARCEL_PICKUP'
                            ? 'bg-blue-500/15 ring-blue-500/30 ring-offset-transparent'
                            : 'bg-purple-500/15 ring-purple-500/30 ring-offset-transparent'
                    ]">
                    <span class="material-icons text-2xl leading-none"
                        :class="jobStore.jobType === 'PARCEL_DELIVERY' ? 'text-green-400' : jobStore.jobType === 'PARCEL_PICKUP' ? 'text-blue-400' : 'text-purple-400'">
                        {{ jobStore.jobType === 'HOUSE_SHIFT' ? 'moving' : jobStore.jobType === 'PARCEL_PICKUP' ? 'assignment_return' : 'local_shipping' }}
                    </span>
                </div>

                <!-- Text Block -->
                <div class="flex-1 min-w-0">
                    <!-- Job ID as Hero -->
                    <p class="text-xl font-black tracking-tight leading-tight truncate">
                        {{ jobStore.jobData.manifestId || jobStore.jobData.jobId }}
                    </p>
                    <!-- Subtitle: job type label -->
                    <p class="text-xs font-semibold mt-0.5 truncate"
                        :class="jobStore.jobType === 'PARCEL_DELIVERY' ? 'text-green-400' : jobStore.jobType === 'PARCEL_PICKUP' ? 'text-blue-400' : 'text-purple-400'">
                        {{ jobStore.jobTypeLabel }}
                    </p>
                </div>

                <!-- State Badge (top-right) -->
                <div class="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border shrink-0 self-start mt-0.5"
                    :class="isDark ? 'bg-primary/10 text-primary border-primary/20' : 'bg-primary/15 text-primary border-primary/30'">
                    {{ jobStore.stateLabel }}
                </div>
            </div>

            <!-- Divider -->
            <div class="h-px mb-4" :class="isDark ? 'bg-white/5' : 'bg-gray-100'"></div>

            <!-- Metadata Row -->
            <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center gap-1 text-xs font-medium"
                    :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                    <span class="material-icons leading-none" style="font-size:13px;">directions_car</span>
                    {{ jobStore.jobData.vehicleId }}
                </div>
                <span class="w-1 h-1 rounded-full" :class="isDark ? 'bg-gray-600' : 'bg-gray-300'"></span>
                <div class="flex items-center gap-1 text-xs font-medium"
                    :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                    <span class="material-icons leading-none" style="font-size:13px;">schedule</span>
                    Started {{ new Date(jobStore.jobData.assignedAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) }}
                </div>
            </div>

            <!-- Progress Bar (for Delivery/Pickup only) -->
            <div v-if="jobStore.jobType !== 'HOUSE_SHIFT' && jobStore.totalStops > 0"
                class="mt-5 p-4 rounded-2xl"
                :class="isDark ? 'bg-black/30 border border-white/5' : 'bg-gray-50 border border-gray-100'">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-black uppercase tracking-widest"
                        :class="isDark ? 'text-gray-400' : 'text-gray-500'">Route Progress</span>
                    <span class="text-lg font-black text-primary">{{ jobStore.completedStopsCount }} / {{
                        jobStore.totalStops }}</span>
                </div>
                <div class="w-full h-2.5 rounded-full overflow-hidden"
                    :class="isDark ? 'bg-gray-800' : 'bg-gray-200'">
                    <div class="h-full rounded-full bg-gradient-to-r from-primary to-primary-dark transition-all duration-500"
                        :style="`width: ${jobStore.progressPercent}%`"></div>
                </div>
                <div class="flex items-center justify-between mt-2">
                    <span class="text-[10px] font-semibold" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        {{ Math.round(jobStore.progressPercent) }}% Complete
                    </span>
                    <span class="text-[10px] font-semibold" :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                        {{ jobStore.totalStops - jobStore.completedStopsCount }} Remaining
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { commandCenterPageKey } from './commandCenterPageContext'

const { isDark, jobStore } = inject(commandCenterPageKey)
</script>
