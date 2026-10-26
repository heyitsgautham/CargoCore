<template>
    <BaseModal :isOpen="ratingModal.show" @close="ratingModal.show = false">
        <template #title>Rate Your Driver</template>
        <div class="space-y-4 text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">How was your experience? (optional)</p>
            <div class="flex justify-center gap-2">
                <span v-for="n in 5" :key="n"
                    @click="ratingModal.selected = n"
                    @mouseenter="ratingModal.hover = n"
                    @mouseleave="ratingModal.hover = 0"
                    class="text-4xl cursor-pointer transition-colors select-none"
                    :class="(ratingModal.hover || ratingModal.selected) >= n ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'">★</span>
            </div>
            <textarea v-model="ratingModal.feedback" rows="2" placeholder="Leave a comment (optional)"
                class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-400/50 outline-none resize-none" />
        </div>
        <template #footer>
            <div class="flex gap-3 w-full">
                <button @click="submitRatingModal" :disabled="!ratingModal.selected"
                    class="flex-1 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 text-sm font-bold disabled:opacity-40">Submit Rating</button>
                <button @click="ratingModal.show = false"
                    class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm">Skip</button>
            </div>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { individualOrdersPageKey } from './individualOrdersPageContext'

const { ratingModal, submitRatingModal } = inject(individualOrdersPageKey)
</script>
