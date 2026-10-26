<template>
    <!-- Call Modal -->
    <Teleport to="body">
        <div v-if="showCallModal && activeMove?.driver" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-slide-up border border-gray-100 dark:border-white/10">
                <div class="p-6 text-center">
                    <div class="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-2xl font-bold mb-4 shadow-lg shadow-green-500/20">
                        {{ activeMove.driver.name.split(' ').map(n => n[0]).join('') }}
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">{{ activeMove.driver.name }}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">Driver · {{ activeMove.vehicleType?.toUpperCase() }}</p>

                    <div class="bg-gray-50 dark:bg-white/5 p-4 rounded-xl mb-6">
                        <div class="text-xs text-gray-500 mb-1 uppercase font-bold">Phone Number</div>
                        <div class="text-lg font-mono font-bold text-gray-900 dark:text-white tracking-widest">{{ activeMove.driver.phone || '+91 98765 43210' }}</div>
                    </div>

                    <div class="flex gap-3">
                        <button @click="showCallModal = false" class="flex-1 py-3 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors">Cancel</button>
                        <a :href="'tel:' + (activeMove.driver.phone || '+910000000000')" @click="showCallModal = false" class="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-colors flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined">call</span> Call
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { customerTrackingPageKey } from './customerTrackingPageContext'

const { activeMove, showCallModal } = inject(customerTrackingPageKey)
</script>
