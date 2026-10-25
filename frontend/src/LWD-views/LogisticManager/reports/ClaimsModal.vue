<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { reportsPageKey } from './reportsPageContext'

const { claimsModalOpen, resolveClaim, selectedClaim } = inject(reportsPageKey)
</script>
