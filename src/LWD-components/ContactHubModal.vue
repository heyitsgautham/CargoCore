<template>
    <BaseModal :is-open="isOpen" @close="$emit('close')">
        <template #title>
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-gray-500">support_agent</span>
                Contact Hub: {{ hub?.name || 'Unknown' }}
            </div>
        </template>

        <div v-if="hub" class="space-y-4">
            <div class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5 space-y-3">

                <div class="flex items-center gap-3">
                    <div
                        class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-400">
                        <span class="material-symbols-outlined text-[16px]">alternate_email</span>
                    </div>
                    <div>
                        <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Manager Email</div>
                        <a href="#"
                            class="text-sm font-medium text-gray-900 dark:text-white hover:text-primary dark:hover:text-primary transition-colors">hub.manager@logistic.com</a>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    <div
                        class="w-8 h-8 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center text-green-600 dark:text-green-400">
                        <span class="material-symbols-outlined text-[16px]">call</span>
                    </div>
                    <div>
                        <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Dispatcher Phone</div>
                        <a href="tel:5551234567"
                            class="text-sm font-medium text-gray-900 dark:text-white hover:text-primary dark:hover:text-primary transition-colors">+1
                            (555) 123-4567</a>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    <div
                        class="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-500/20 flex items-center justify-center text-purple-600 dark:text-purple-400">
                        <span class="material-symbols-outlined text-[16px]">deskphone</span>
                    </div>
                    <div>
                        <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Main Office Number
                        </div>
                        <a href="tel:5559876543"
                            class="text-sm font-medium text-gray-900 dark:text-white hover:text-primary dark:hover:text-primary transition-colors">+1
                            (555) 987-6543</a>
                    </div>
                </div>

            </div>

            <div class="pt-2">
                <button @click="$emit('close')"
                    class="w-full py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 rounded-xl font-bold transition-all duration-300">
                    Close
                </button>
            </div>
        </div>
    </BaseModal>
</template>

<script setup>
import BaseModal from '@/components/BaseModal.vue'

defineProps({
    isOpen: {
        type: Boolean,
        default: false
    },
    hub: {
        type: Object,
        default: () => null
    }
})

defineEmits(['close'])
</script>
