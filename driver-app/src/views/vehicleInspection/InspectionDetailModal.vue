<template>
    <Transition name="fade-scale">
        <div v-if="detailModal" class="absolute inset-0 z-50 flex flex-col items-center justify-center px-6"
            :class="isDark ? 'bg-background-dark/90' : 'bg-background-light/90'" style="backdrop-filter: blur(8px);"
            @click.self="cancelDetail">
            <div class="w-full max-w-sm rounded-3xl p-6 border flex flex-col gap-4"
                :class="isDark ? 'bg-surface-dark border-white/10' : 'bg-white border-gray-200 shadow-xl'">

                <!-- ── Image Preview ─────────────────── -->
                <div v-if="photoUrl" class="w-full h-40 rounded-2xl overflow-hidden relative border"
                    :class="isDark ? 'border-white/10' : 'border-gray-200'">
                    <img :src="photoUrl" class="w-full h-full object-cover" />
                    <button @click.stop="removePhoto"
                        class="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center backdrop-blur-sm active:scale-95 transition-transform hover:bg-black/70">
                        <span class="material-icons text-lg">close</span>
                    </button>
                    <div
                        class="absolute bottom-2 left-2 px-2 py-1 rounded bg-black/50 text-white text-[10px] font-bold backdrop-blur-sm uppercase tracking-wider">
                        Captured Info
                    </div>
                </div>

                <!-- ── Fuel Modal ──────────────────── -->
                <template v-if="detailType === 'fuel'">
                    <div class="text-center mb-1 mt-2">
                        <div class="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center mb-3"
                            :class="isDark ? 'bg-primary/15' : 'bg-primary/10'">
                            <span class="material-icons text-primary text-2xl">local_gas_station</span>
                        </div>
                        <h3 class="text-lg font-black">Fuel Level</h3>
                        <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                            Photo captured ✓ · Enter fuel in liters (Tank: {{ TANK_CAPACITY }}L)
                        </p>
                    </div>

                    <div @click="() => fuelInputRef?.focus()" class="glass-input rounded-2xl flex items-center px-4 py-4 gap-3 mb-3 cursor-text">
                        <span class="material-icons text-lg"
                            :class="fuelLiters ? 'text-primary' : isDark ? 'text-white/30' : 'text-gray-400'">opacity</span>
                        <input id="inspFuelLiters" v-model.number="fuelLiters" type="number" inputmode="decimal" min="0"
                            :max="TANK_CAPACITY" :placeholder="`0 – ${TANK_CAPACITY}`"
                            class="flex-1 min-w-0 bg-transparent border-none outline-none font-black text-2xl"
                            style="pointer-events: auto; touch-action: manipulation;"
                            :class="isDark ? 'text-white placeholder-white/20' : 'text-gray-900 placeholder-gray-300'"
                            @input="clampFuel" ref="fuelInputRef" enterkeyhint="done" />
                        <span class="text-sm font-bold" :class="isDark ? 'text-gray-400' : 'text-gray-500'">L</span>
                    </div>

                    <!-- Auto-calculated % -->
                    <div class="rounded-2xl p-4 border text-center mb-5"
                        :class="fuelPercent > 0 ? 'border-primary/30 bg-primary/8' : isDark ? 'border-white/5 bg-white/3' : 'border-gray-100 bg-gray-50'">
                        <p class="text-4xl font-black"
                            :class="fuelPercent > 0 ? 'text-primary' : isDark ? 'text-gray-600' : 'text-gray-300'">
                            {{ fuelPercent }}%</p>
                        <div class="w-full h-2 rounded-full mt-2" :class="isDark ? 'bg-gray-800' : 'bg-gray-200'">
                            <div class="h-2 rounded-full transition-all duration-300"
                                :class="fuelPercent > 50 ? 'bg-primary' : fuelPercent > 20 ? 'bg-yellow-400' : 'bg-red-400'"
                                :style="`width: ${fuelPercent}%`"></div>
                        </div>
                    </div>
                </template>

                <!-- ── Odometer Modal ──────────────── -->
                <template v-if="detailType === 'odometer'">
                    <div class="text-center mb-1 mt-2">
                        <div v-if="!photoUrl"
                            class="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center mb-3"
                            :class="isDark ? 'bg-primary/15' : 'bg-primary/10'">
                            <span class="material-icons text-primary text-2xl">speed</span>
                        </div>
                        <h3 class="text-lg font-black">Odometer Reading</h3>
                        <p class="text-xs mt-1" :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                            {{ odometerAutoDetected ? 'OCR detected value below — edit if incorrect' : 'Photo captured — enter the reading manually if needed' }}
                        </p>
                    </div>

                    <div @click="() => odometerInputRef?.focus()" class="glass-input rounded-2xl flex items-center px-4 py-4 gap-3 mb-5 cursor-text">
                        <span class="material-icons text-lg"
                            :class="odometerKm ? 'text-primary' : isDark ? 'text-white/30' : 'text-gray-400'">straighten</span>
                        <input id="inspOdometerKm" v-model.number="odometerKm" type="number" inputmode="numeric"
                            placeholder="e.g. 48230"
                            class="flex-1 min-w-0 bg-transparent border-none outline-none font-black text-2xl"
                            style="pointer-events: auto; touch-action: manipulation;"
                            :class="isDark ? 'text-white placeholder-white/20' : 'text-gray-900 placeholder-gray-300'"
                            enterkeyhint="done" ref="odometerInputRef" />
                        <span class="text-sm font-bold"
                            :class="isDark ? 'text-gray-400' : 'text-gray-500'">km</span>
                    </div>
                </template>

                <!-- Buttons -->
                <div class="flex gap-3">
                    <button @click="cancelDetail"
                        class="flex-1 py-3.5 rounded-2xl font-semibold text-sm border active:scale-[0.97] transition-all"
                        :class="isDark ? 'border-white/10 text-white/60 hover:bg-white/5' : 'border-gray-200 text-gray-500 hover:bg-gray-50'">
                        Cancel
                    </button>
                    <button @click="confirmDetail"
                        class="flex-[2] py-3.5 rounded-2xl font-bold text-sm active:scale-[0.97] transition-all"
                        :class="canConfirmDetail
                            ? 'bg-primary text-background-dark shadow-glow'
                            : isDark ? 'bg-gray-700 text-gray-500 opacity-40 cursor-not-allowed' : 'bg-gray-100 text-gray-400 opacity-40 cursor-not-allowed'">
                        <template v-if="detailType === 'fuel'">Confirm · {{ fuelPercent }}%</template>
                        <template v-else>Confirm · {{ odometerKm ? `${Number(odometerKm).toLocaleString('en-IN')}
                            km` : '—' }}</template>
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
    TANK_CAPACITY,
    canConfirmDetail,
    cancelDetail,
    clampFuel,
    confirmDetail,
    detailModal,
    detailType,
    fuelInputRef,
    fuelLiters,
    fuelPercent,
    isDark,
    odometerAutoDetected,
    odometerInputRef,
    odometerKm,
    photoUrl,
    removePhoto,
} = inject(vehicleInspectionPageKey)
</script>
