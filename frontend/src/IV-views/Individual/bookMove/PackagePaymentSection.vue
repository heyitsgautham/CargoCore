<template>
    <!-- Package Payment -->
    <div class="glass-panel p-4 sm:p-6 rounded-xl">
        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-blue-500">payments</span> Payment
        </h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
            <label v-for="mode in paymentModes" :key="mode.value"
                class="p-3 rounded-xl border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 transition-all flex items-center gap-3"
                :class="form.paymentMode === mode.value ? 'border-blue-500 bg-blue-500/5' : 'border-gray-200 dark:border-white/10'">
                <input type="radio" :value="mode.value" v-model="form.paymentMode"
                    class="accent-blue-500" />
                <div><span class="text-sm text-gray-900 dark:text-white font-medium">{{ mode.label
                        }}</span>
                    <p class="text-xs text-gray-500">{{ mode.desc }}</p>
                </div>
            </label>
        </div>
        <!-- Dummy Payment removed -->
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { bookMovePageKey } from './bookMovePageContext'

const { form, paymentModes } = inject(bookMovePageKey)
</script>
