<template>
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
</template>

<script setup>
import { inject } from 'vue'
import { smartDispatcherPageKey } from './smartDispatcherPageContext'

const {
    executeNLCommand,
    handleChipsScroll,
    nlCommand,
    nlProcessing,
    nlResponse,
    quickCommands,
} = inject(smartDispatcherPageKey)
</script>
