<template>
    <BaseModal :isOpen="rescheduleModal.show" @close="rescheduleModal.show = false">
        <template #title>Reschedule Move</template>
        <div class="space-y-4">
            <div><label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">New
                    Date</label>
                <input v-model="rescheduleModal.date" type="date"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 outline-none" />
            </div>
            <div><label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">New
                    Time</label>
                <select v-model="rescheduleModal.time"
                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 outline-none">
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">06:00 AM - 09:00 AM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">09:00 AM - 12:00 PM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">12:00 PM - 03:00 PM</option>
                    <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">03:00 PM - 06:00 PM</option>
                </select>
            </div>
        </div>
        <template #footer>
            <div class="flex gap-3 w-full">
                <button @click="doReschedule"
                    class="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-bold">Reschedule</button>
                <button @click="rescheduleModal.show = false"
                    class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm">Cancel</button>
            </div>
        </template>
    </BaseModal>
</template>

<script setup>
import { inject } from 'vue'
import BaseModal from '@/components/BaseModal.vue'
import { individualOrdersPageKey } from './individualOrdersPageContext'

const { doReschedule, rescheduleModal } = inject(individualOrdersPageKey)
</script>
