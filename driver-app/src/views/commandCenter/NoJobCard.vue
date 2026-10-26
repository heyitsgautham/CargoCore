<template>
    <div
        class="rounded-3xl p-8 border text-center relative flex flex-col items-center justify-center"
        :class="isDark ? 'bg-surface-dark/40 border-white/8' : 'bg-white border-gray-100 shadow-lg'">
        <!-- Decorative background (contained in own overflow-hidden layer) -->
        <div class="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
            <div class="absolute inset-0 opacity-5">
                <div class="absolute top-0 left-0 w-full h-full"
                    style="background-image: radial-gradient(circle, currentColor 1px, transparent 1px); background-size: 20px 20px;">
                </div>
            </div>
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 rounded-full blur-3xl opacity-20 bg-primary animate-pulse"></div>
        </div>

        <div class="relative">
            <!-- Icon -->
            <div class="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-4 relative"
                :class="isDark ? 'bg-gradient-to-br from-gray-800 to-gray-900 border border-white/5' : 'bg-gradient-to-br from-gray-100 to-gray-200 border border-gray-200'">
                <span class="material-icons text-3xl leading-none"
                    :class="isDark ? 'text-gray-500' : 'text-gray-400'">assignment</span>
                <div class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-amber-500 rounded-full flex items-center justify-center border-2"
                    :class="isDark ? 'border-background-dark' : 'border-background-light'">
                    <span class="material-icons text-white leading-none" style="font-size:10px;">schedule</span>
                </div>
            </div>

            <!-- Text -->
            <h3 class="font-black text-xl mb-1.5">No Active Job</h3>
            <p class="text-xs mb-4 max-w-[220px] mx-auto leading-relaxed"
                :class="isDark ? 'text-gray-400' : 'text-gray-500'">
                Waiting for job assignment from dispatch
            </p>

            <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold"
                :class="isDark ? 'bg-primary/10 border-primary/20 text-primary' : 'bg-primary/10 border-primary/30 text-primary'">
                <span class="material-icons leading-none" style="font-size:14px;">notifications_active</span>
                Waiting for dispatch assignment
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { commandCenterPageKey } from './commandCenterPageContext'

const { isDark } = inject(commandCenterPageKey)
</script>
