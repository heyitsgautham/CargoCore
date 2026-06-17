<template>
    <Teleport to="body">
        <div v-if="isOpen"
            class="fixed inset-0 w-screen h-screen z-[9999] flex items-center justify-center p-4 bg-transparent">
            <!-- Backdrop -->
            <div class="absolute inset-0 w-full h-full bg-black/60 backdrop-blur-sm transition-opacity"
                @click="$emit('close')"></div>

            <!-- Modal Content -->
            <div
                class="relative bg-slate-950/98 border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden transform transition-all scale-100 opacity-100 backdrop-blur-xl">
                <!-- Header -->
                <div
                    class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 class="text-lg font-bold text-white">
                        <slot name="title">Modal Title</slot>
                    </h3>
                    <button @click="$emit('close')"
                        class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <!-- Body -->
                <div class="p-6 max-h-[70vh] overflow-y-auto custom-scrollbar bg-slate-950/95">
                    <slot></slot>
                </div>

                <!-- Footer (Optional) -->
                <div v-if="$slots.footer"
                    class="px-6 py-4 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                    <slot name="footer"></slot>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
defineProps({
    isOpen: {
        type: Boolean,
        default: false
    }
})

defineEmits(['close'])
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
}
</style>
