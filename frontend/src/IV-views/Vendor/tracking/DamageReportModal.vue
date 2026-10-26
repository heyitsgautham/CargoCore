<template>
    <!-- Damage Report Modal -->
    <Teleport to="body">
        <BaseModal :isOpen="showDamageModal" @close="showDamageModal = false">
            <template #title>Report Damage / Issue</template>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Severity *</label>
                    <div class="flex gap-3">
                        <label v-for="sev in ['Low', 'Medium', 'High']" :key="sev"
                            class="flex-1 text-center px-3 py-2 rounded-lg border cursor-pointer text-sm font-medium transition-colors"
                            :class="damageForm.severity === sev ? severityClass(sev) : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400'">
                            <input type="radio" :value="sev" v-model="damageForm.severity" class="sr-only">{{ sev }}
                        </label>
                    </div>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Description *</label>
                    <textarea v-model="damageForm.description" rows="3"
                        placeholder="Describe the damage or issue..."
                        class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
                </div>
                <div>
                    <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Upload Evidence</label>
                    <div
                        class="border-2 border-dashed border-gray-300 dark:border-white/20 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 transition-colors">
                        <span class="material-symbols-outlined text-3xl text-gray-400 mb-2">cloud_upload</span>
                        <div class="text-xs text-gray-500">Click to upload photos</div>
                    </div>
                </div>
            </div>
            <template #footer>
                <button @click="showDamageModal = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                <button @click="submitDamage" :disabled="!damageForm.description.trim()"
                    class="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-bold hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Submit
                    Report</button>
            </template>
        </BaseModal>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const { damageForm, severityClass, showDamageModal, submitDamage } = inject(vendorTrackingPageKey)
</script>
