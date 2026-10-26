<template>
    <div
        class="bg-gradient-to-br from-purple-900 via-indigo-900 to-black rounded-2xl p-8 relative overflow-hidden shadow-lg border border-purple-500/20">
        <!-- Decorative Background elements -->
        <div
            class="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none">
        </div>
        <div
            class="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/2 w-64 h-64 bg-blue-500/20 rounded-full blur-3xl pointer-events-none">
        </div>

        <div class="relative z-10 max-w-2xl mx-auto text-center">
            <h3 class="text-2xl font-bold text-white mb-4">How can we help the AI today?</h3>
            <div class="relative">
                <input v-model="searchQuery" type="text"
                    placeholder="Search for standard operating procedures, policies, or scripts..."
                    class="w-full bg-white/10 dark:bg-black/40 backdrop-blur-md border border-white/20 rounded-xl pl-12 pr-4 py-4 text-white placeholder-white/60 focus:outline-none focus:border-purple-400 focus:bg-white/20 shadow-inner transition-all text-lg">
                <span class="material-symbols-outlined absolute left-4 top-4 text-white/60 text-2xl">search</span>
            </div>
            <div class="flex gap-2 justify-center mt-4 text-xs font-bold">
                <span class="text-white/60">Popular:</span>
                <button @click="searchQuery = 'Refund'"
                    class="text-purple-300 hover:text-white transition-colors">Refund Policy</button>
                <button @click="searchQuery = 'Damage'"
                    class="text-purple-300 hover:text-white transition-colors">Damage Claims</button>
                <button @click="searchQuery = 'Legal'"
                    class="text-purple-300 hover:text-white transition-colors">Legal Escalation</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { knowledgeBasePageKey } from './knowledgeBasePageContext'

const { searchQuery } = inject(knowledgeBasePageKey)
</script>
