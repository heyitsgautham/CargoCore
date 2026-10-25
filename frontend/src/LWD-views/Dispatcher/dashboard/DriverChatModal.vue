<template>
    <Teleport to="body">
    <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="$emit('close')">
        <div class="bg-white dark:bg-card-dark rounded-2xl w-full max-w-sm m-4 border border-gray-200 dark:border-white/10 shadow-2xl flex flex-col h-[400px]">
            <div class="p-4 border-b border-gray-200 dark:border-white/5 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <img :src="driver?.avatar" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700">
                    <div><div class="text-sm font-bold text-gray-900 dark:text-white">{{ driver?.name }}</div><div class="text-[10px] text-gray-400">{{ driver?.id }}</div></div>
                </div>
                <button @click="$emit('close')" class="text-gray-400 hover:text-gray-900 dark:text-white"><span class="material-symbols-outlined">close</span></button>
            </div>
            <div class="flex-1 overflow-y-auto no-scrollbar p-4 space-y-2">
                <div v-for="msg in messages" :key="msg.id" :class="msg.from === 'dispatch' ? 'flex justify-end' : 'flex justify-start'">
                    <div class="max-w-[80%] p-2 rounded-xl text-xs" :class="msg.from === 'dispatch' ? 'bg-primary/20 text-gray-900 dark:text-white' : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300'">{{ msg.text }}</div>
                </div>
            </div>
            <div class="p-3 border-t border-gray-200 dark:border-white/5 flex gap-2">
                <input v-model="draft" @keyup.enter="$emit('send')" type="text" placeholder="Type message..."
                    class="flex-1 bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full px-3 py-1.5 text-sm text-gray-900 dark:text-white focus:outline-none">
                <button @click="$emit('send')" class="p-1.5 bg-primary rounded-full text-black"><span class="material-symbols-outlined text-[16px]">send</span></button>
            </div>
        </div>
    </div>
    </Teleport>
</template>

<script setup>
const draft = defineModel('draft', { type: String, required: true })

defineProps({
    show: { type: Boolean, default: false },
    driver: { type: Object, default: null },
    messages: { type: Array, required: true },
})

defineEmits(['close', 'send'])
</script>
