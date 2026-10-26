<template>
    <Teleport to="body">
    <div v-if="showBroadcast" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showBroadcast = false">
        <div class="bg-gray-900 shadow-2xl border border-red-500/30 rounded-2xl p-6 w-full max-w-md m-4">
            <h3 class="font-bold text-red-400 mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined">campaign</span> Broadcast Crisis Alert
            </h3>
            <select v-model="broadcastSeverity" class="w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none mb-3">
                <option class="bg-gray-800" value="critical">CRITICAL — Immediate action required</option>
                <option class="bg-gray-800" value="high">HIGH — Urgent attention</option>
                <option class="bg-gray-800" value="warning">WARNING — Advisory</option>
            </select>
            <textarea v-model="broadcastMsg" rows="3" placeholder="Alert message for all drivers..."
                class="w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-red-500/50 mb-3 resize-none"></textarea>
            <div class="flex gap-2">
                <button @click="sendBroadcast" :disabled="!broadcastMsg || broadcastSending" class="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold py-2 rounded-lg text-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-1 transition-colors">
                    <span v-if="broadcastSending" class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                    {{ broadcastSending ? 'Sending...' : 'Broadcast Now' }}
                </button>
                <button @click="showBroadcast = false" class="flex-1 bg-white/10 text-white py-2 rounded-lg text-sm hover:bg-white/20 transition-colors">Cancel</button>
            </div>
            <div v-if="broadcastSent" class="mt-2 text-center text-xs text-green-400 font-bold">✓ Alert broadcast to all active drivers</div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { crisisPageKey } from './crisisPageContext'

const {
    broadcastMsg,
    broadcastSending,
    broadcastSent,
    broadcastSeverity,
    sendBroadcast,
    showBroadcast,
} = inject(crisisPageKey)
</script>
