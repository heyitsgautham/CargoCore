<template>
    <TransitionGroup name="slide-up" tag="div" class="space-y-2">
        <div v-for="order in orders" :key="order.rawId"
            class="flex items-start gap-3 px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/30">
            <span class="material-symbols-outlined text-blue-400 text-[20px] shrink-0 mt-0.5">local_shipping</span>
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-sm font-bold text-blue-300">Dispatcher assigned a driver to {{ order.id }}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-bold border border-blue-500/20">No WM Action</span>
                </div>
                <div class="text-xs text-blue-300/70 mt-0.5">
                    <span class="font-semibold text-blue-300">{{ order.driverName }}</span> will pick up directly from {{ order.pickupAddr || 'the pickup location' }}. No warehouse picking or packing required.
                </div>
            </div>
            <button @click="$emit('dismiss', order.rawId)"
                class="shrink-0 text-blue-400/60 hover:text-blue-300 transition-colors mt-0.5"
                title="Dismiss">
                <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
        </div>
    </TransitionGroup>
</template>

<script setup>
defineProps({
    orders: { type: Array, required: true },
})

defineEmits(['dismiss'])
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
    transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
    transform: translate(-50%, 100%);
    opacity: 0;
}
</style>
