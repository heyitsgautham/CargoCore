<template>
    <Transition name="slide-up">
        <div v-if="undoAction"
            class="fixed bottom-20 left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-6 py-3 rounded-xl shadow-2xl flex items-center gap-4 z-50">
            <span class="text-sm">{{ undoAction.message }}</span>
            <button @click="$emit('undo')"
                class="bg-primary text-background-dark px-3 py-1 rounded-lg text-xs font-bold hover:bg-primary-dark transition-colors">
                Undo
            </button>
            <button @click="$emit('dismiss')" class="text-gray-400 hover:text-white">
                <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
        </div>
    </Transition>
</template>

<script setup>
defineProps({
    undoAction: { type: Object, default: null },
})

defineEmits(['undo', 'dismiss'])
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
