<template>
    <BaseModal :is-open="isOpen" @close="handleClose">
        <template #title>
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined" :class="getSeverityClass(alert?.severity)">
                    {{ alert?.icon || 'info' }}
                </span>
                {{ alert?.title || 'Alert Details' }}
            </div>
        </template>

        <div v-if="alert" class="space-y-4">
            <template v-if="activeView === 'details'">
                <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/5">
                    <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Description</div>
                    <div class="text-sm text-gray-700 dark:text-gray-200">{{ alert.description }}</div>
                </div>

                <div v-if="alert.location || alert.timestamp" class="grid grid-cols-2 gap-4">
                    <div v-if="alert.location"
                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/5">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Location</div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">{{ alert.location }}</div>
                    </div>
                    <div v-if="alert.timestamp"
                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-200 dark:border-white/5">
                        <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Time Reported</div>
                        <div class="text-sm text-gray-900 dark:text-white font-medium">{{ alert.timestamp }}</div>
                    </div>
                </div>

                <div v-if="alert.recommendation"
                    class="p-3 bg-blue-50 dark:bg-blue-500/10 rounded-lg border border-blue-100 dark:border-blue-500/20">
                    <div class="flex items-start gap-2">
                        <span
                            class="material-symbols-outlined text-blue-500 dark:text-blue-400 text-sm mt-0.5">lightbulb</span>
                        <div>
                            <div class="text-xs text-blue-600 dark:text-blue-300 font-bold mb-1">AI Recommendation</div>
                            <div class="text-sm text-blue-800 dark:text-blue-100">{{ alert.recommendation }}</div>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex flex-col gap-2 pt-2">
                    <!-- System Alerts -->
                    <template v-if="alert.type === 'system'">
                        <button @click="handleAction('acknowledge')"
                            class="w-full py-2 bg-primary hover:bg-primary-dark text-white rounded-lg font-medium text-sm transition-colors">
                            Acknowledge
                        </button>
                    </template>

                    <!-- Operations/Warning Alerts -->
                    <template v-else>
                        <button @click="handleAction('acknowledge')"
                            class="w-full py-2 bg-primary hover:bg-primary-dark text-white rounded-lg font-medium text-sm transition-colors">
                            Acknowledge & Assign Team
                        </button>
                        <button
                            v-if="alert.type === 'delayed' || alert.type === 'deviation' || alert.type === 'congestion'"
                            @click="activeView = 'drivers'"
                            class="w-full py-2 bg-blue-50 dark:bg-blue-500/10 hover:bg-blue-100 dark:hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-lg font-medium text-sm transition-colors border border-blue-200 dark:border-blue-500/20">
                            Contact Affected Driver(s)
                        </button>
                        <button @click="handleAction('ignore')"
                            class="w-full py-2 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg font-medium text-sm transition-colors border border-gray-200 dark:border-white/5">
                            Dismiss Alert
                        </button>
                    </template>
                </div>
            </template>

            <template v-else>
                <!-- Affected Drivers List -->
                <div class="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-white/10 -mt-2">
                    <button @click="activeView = 'details'"
                        class="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg text-gray-500 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">arrow_back</span>
                    </button>
                    <h3 class="font-bold text-sm text-gray-900 dark:text-white leading-tight">Affected Drivers</h3>
                </div>

                <div class="space-y-3 pt-2 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                    <div v-for="driver in store.drivers" :key="driver.id"
                        class="p-3 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/5 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-sm"
                                :class="driver.avatarColor || 'bg-gray-700'">
                                {{ driver.name.charAt(0) }}
                            </div>
                            <div>
                                <div class="font-semibold text-sm text-gray-900 dark:text-white">{{ driver.name }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">{{ driver.phone }}</div>
                            </div>
                        </div>
                        <button @click="handleAction('contactDriver', driver)"
                            class="w-8 h-8 flex items-center justify-center rounded-lg bg-primary/10 hover:bg-primary/20 text-primary transition-colors">
                            <span class="material-symbols-outlined text-[18px]">chat</span>
                        </button>
                    </div>
                </div>
            </template>
        </div>
    </BaseModal>
</template>

<script setup>
import { ref } from 'vue'
import BaseModal from '../components/BaseModal.vue'
import { useLogisticStore } from '@/stores/logisticStore'

const props = defineProps({
    isOpen: Boolean,
    alert: Object
})

const emit = defineEmits(['close', 'action'])
const store = useLogisticStore()

const activeView = ref('details')

const handleClose = () => {
    setTimeout(() => {
        activeView.value = 'details'
    }, 300)
    emit('close')
}

function getSeverityClass(severity) {
    switch (severity) {
        case 'high': return 'text-red-500'
        case 'medium': return 'text-yellow-500'
        default: return 'text-blue-500'
    }
}

function handleAction(type, data = null) {
    if (type === 'contactDriver') {
        emit('close')
        setTimeout(() => {
            store.openModal('driver-profile', data)
        }, 10)
        return
    }
    emit('action', { type, alertId: props.alert.id })
}
</script>
