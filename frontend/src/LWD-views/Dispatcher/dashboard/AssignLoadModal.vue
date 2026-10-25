<template>
    <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="$emit('close')">
        <div class="bg-white dark:bg-card-dark rounded-2xl p-6 w-full max-w-md m-4 border border-gray-200 dark:border-white/10 shadow-2xl">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">assignment_turned_in</span> Quick Assign Load
            </h3>
            <div class="mb-3">
                <label class="text-xs text-gray-400 mb-1 block">Select Order</label>
                <select v-model="orderId" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Choose order...</option>
                    <option v-for="load in pendingLoads" :key="load.id" :value="load.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ load.id }} — {{ load.type }} ({{ load.weight }}kg)</option>
                </select>
            </div>
            <div class="mb-4">
                <label class="text-xs text-gray-400 mb-1 block">Select Driver</label>
                <select v-model="driverId" class="w-full bg-gray-100 dark:bg-black/30 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none">
                    <option value="" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Choose driver...</option>
                    <option v-for="d in assignableDrivers" :key="d.id" :value="d.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ d.name }} ({{ d.vehicle }}, {{ d.load }}% load)</option>
                </select>
            </div>
            <div class="flex gap-2">
                <button @click="$emit('confirm')" :disabled="!orderId || !driverId || assigning"
                    class="flex-1 bg-primary text-black font-bold py-2 rounded-lg text-sm disabled:opacity-50 hover:bg-primary-dark transition-colors flex items-center justify-center gap-1">
                    <span v-if="assigning" class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                    {{ assigning ? 'Assigning...' : 'Assign' }}
                </button>
                <button @click="$emit('close')" :disabled="assigning" class="flex-1 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white py-2 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-white/20 transition-colors disabled:opacity-50">Cancel</button>
            </div>
            <div v-if="success" class="mt-3 text-center text-xs text-green-400 font-bold">✓ Order assigned successfully!</div>
            <div v-if="error" class="mt-3 text-center text-xs text-red-400 font-bold">{{ error }}</div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
const orderId = defineModel('orderId', { type: [String, Number], required: true })
const driverId = defineModel('driverId', { type: [String, Number], required: true })

defineProps({
    show: { type: Boolean, default: false },
    pendingLoads: { type: Array, required: true },
    assignableDrivers: { type: Array, required: true },
    assigning: { type: Boolean, default: false },
    success: { type: Boolean, default: false },
    error: { type: String, default: '' },
})

defineEmits(['close', 'confirm'])
</script>
