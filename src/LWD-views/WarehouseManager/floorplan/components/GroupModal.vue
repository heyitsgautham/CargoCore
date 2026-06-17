<template>
    <Teleport to="body">
        <div v-if="visible"
            class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            @click.self="$emit('close')">
            <div
                class="bg-white dark:bg-card-dark w-full max-w-md rounded-2xl shadow-2xl border border-gray-200 dark:border-white/10 overflow-hidden">
                <div
                    class="px-6 py-3 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <h3 class="font-bold text-gray-900 dark:text-white">{{ editing ? 'Edit' : 'New' }} Category</h3>
                    <button @click="$emit('close')" class="text-gray-400 hover:text-gray-700 dark:hover:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-5 space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                        <input v-model="form.name" placeholder="e.g. Fragile"
                            class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Color</label>
                        <div class="flex gap-2 flex-wrap">
                            <button v-for="c in presetColors" :key="c" @click="form.color = c"
                                class="w-7 h-7 rounded-lg border-2 hover:scale-110 transition-transform"
                                :class="form.color === c ? 'border-white ring-2 ring-primary scale-110' : 'border-transparent'"
                                :style="{ background: c }"></button>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Internal
                                Gap</label>
                            <input type="number" v-model.number="form.internalGap" min="0" max="20"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none" />
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">External
                                Gap</label>
                            <input type="number" v-model.number="form.externalGap" min="0" max="40"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-none" />
                        </div>
                    </div>
                </div>
                <div
                    class="px-6 py-3 border-t border-gray-200 dark:border-white/5 flex justify-between bg-gray-50 dark:bg-white/5">
                    <button v-if="editing" @click="$emit('delete')"
                        class="text-red-500 text-sm font-bold">Delete</button>
                    <div v-else></div>
                    <div class="flex gap-2">
                        <button @click="$emit('close')"
                            class="px-3 py-1.5 text-gray-600 dark:text-gray-400 text-sm">Cancel</button>
                        <button @click="$emit('save', { ...form })"
                            class="px-4 py-1.5 bg-primary text-white rounded-lg font-bold text-sm">
                            {{ editing ? 'Save' : 'Create' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
    visible: { type: Boolean, default: false },
    editing: { type: Object, default: null },
    presetColors: { type: Array, default: () => [] }
})

defineEmits(['close', 'save', 'delete'])

const form = reactive({
    name: '',
    color: '#3b82f6',
    internalGap: 2,
    externalGap: 10
})

watch(() => props.editing, g => {
    if (g) {
        form.name = g.name
        form.color = g.color
        form.internalGap = g.internalGap
        form.externalGap = g.externalGap
    } else {
        form.name = ''
        form.color = '#3b82f6'
        form.internalGap = 2
        form.externalGap = 10
    }
}, { immediate: true })

watch(() => props.visible, v => {
    if (v && !props.editing) {
        form.name = ''
        form.color = '#3b82f6'
        form.internalGap = 2
        form.externalGap = 10
    }
})
</script>
