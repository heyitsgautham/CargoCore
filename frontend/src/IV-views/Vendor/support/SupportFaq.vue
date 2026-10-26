<template>
    <!-- FAQ -->
    <div class="glass-panel p-5 rounded-xl w-full shrink-0">
        <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-blue-500">help</span> Frequently Asked Questions
        </h3>
        <div class="flex flex-col gap-3">
            <div v-for="(faq, idx) in faqList" :key="idx"
                class="bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5 overflow-hidden">
                <button @click="toggleFaq(idx)"
                    class="w-full p-4 flex justify-between items-center text-left hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                    <span class="text-sm font-bold text-gray-800 dark:text-gray-200">{{ faq.q }}</span>
                    <span class="material-symbols-outlined text-gray-400 transition-transform duration-300"
                        :class="{ 'rotate-180': openFaq === idx }">expand_more</span>
                </button>
                <div v-show="openFaq === idx"
                    class="p-4 pt-0 text-xs text-gray-600 dark:text-gray-400 border-t border-gray-100 dark:border-white/5 mt-2 leading-relaxed">
                    {{ faq.a }}
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { vendorSupportPageKey } from './vendorSupportPageContext'

const { faqList, openFaq, toggleFaq } = inject(vendorSupportPageKey)
</script>
