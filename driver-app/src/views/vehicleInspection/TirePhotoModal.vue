<template>
    <Transition name="fade-scale">
        <div v-if="tireModal" class="absolute inset-0 z-50 flex items-center justify-center px-6"
            :class="isDark ? 'bg-background-dark/90' : 'bg-background-light/90'"
            style="backdrop-filter: blur(8px);">
            <div class="w-full max-w-sm rounded-3xl p-6 border"
                :class="isDark ? 'bg-surface-dark border-white/10' : 'bg-white border-gray-200 shadow-xl'">
                <div class="text-center mb-5">
                    <div class="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center mb-3"
                        :class="isDark ? 'bg-primary/15' : 'bg-primary/10'">
                        <span class="material-icons text-primary text-2xl">donut_large</span>
                    </div>
                    <h3 class="text-lg font-black">Tire Inspection</h3>
                    <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                        Capture a photo of each tire · {{ tireCaptured }} of 4 done
                    </p>
                </div>

                <!-- 4 tire grid -->
                <div class="grid grid-cols-2 gap-3 mb-5">
                    <div v-for="(tire, idx) in tirePhotos" :key="idx"
                        class="aspect-square rounded-2xl border-2 flex flex-col relative overflow-hidden transition-all"
                        :class="tire.url
                            ? 'border-primary'
                            : isDark ? 'border-dashed border-gray-600 hover:border-gray-500 cursor-pointer' : 'border-dashed border-gray-300 hover:border-gray-400 cursor-pointer'"
                        @click="!tire.url && captureTirePhoto(idx)">

                        <!-- Captured state (Image) -->
                        <template v-if="tire.url">
                            <div class="absolute inset-0 m-1 rounded-xl overflow-hidden">
                                <img :src="tire.url" class="w-full h-full object-cover" />
                                <div
                                    class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none">
                                </div>
                                <div
                                    class="absolute bottom-2 left-2 right-2 flex items-center justify-between z-10">
                                    <div class="flex items-center gap-1">
                                        <span class="material-icons text-primary text-[10px]">check_circle</span>
                                        <span class="text-[10px] font-bold text-white">{{ tire.label }}</span>
                                    </div>
                                </div>
                                <button @click.stop="removeTirePhoto(idx)"
                                    class="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/60 text-white flex items-center justify-center backdrop-blur-sm active:scale-90 transition-transform hover:bg-black/80 z-20">
                                    <span class="material-icons text-xs">close</span>
                                </button>
                            </div>
                        </template>

                        <!-- Uncaptured state -->
                        <template v-else>
                            <div class="w-full h-full flex flex-col items-center justify-center gap-1">
                                <span class="material-icons text-2xl"
                                    :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                                    photo_camera
                                </span>
                                <span class="text-xs font-bold text-center px-2"
                                    :class="isDark ? 'text-gray-500' : 'text-gray-400'">
                                    {{ tire.label }}
                                </span>
                            </div>
                        </template>
                    </div>
                </div>

                <div class="flex gap-3">
                    <button @click="tireModal = false"
                        class="flex-1 py-3.5 rounded-2xl font-semibold text-sm border active:scale-[0.97] transition-all"
                        :class="isDark ? 'border-white/10 text-white/60' : 'border-gray-200 text-gray-500'">
                        Cancel
                    </button>
                    <button @click="confirmTires"
                        class="flex-[2] py-3.5 rounded-2xl font-bold text-sm active:scale-[0.97] transition-all"
                        :class="tireCaptured === 4
                            ? 'bg-primary text-background-dark shadow-glow'
                            : isDark ? 'bg-gray-700 text-gray-500 opacity-40 cursor-not-allowed' : 'bg-gray-100 text-gray-400 opacity-40 cursor-not-allowed'">
                        Confirm · {{ tireCaptured }}/4 tires
                    </button>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup>
import { inject } from 'vue'
import { vehicleInspectionPageKey } from './vehicleInspectionPageContext'

const {
    captureTirePhoto,
    confirmTires,
    isDark,
    removeTirePhoto,
    tireCaptured,
    tireModal,
    tirePhotos,
} = inject(vehicleInspectionPageKey)
</script>
