<template>
    <div
        class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-white/10 transition-all cursor-pointer group"
        @click="$emit('open', wave)">
        <!-- Header -->
        <div class="flex justify-between items-start mb-3">
            <div>
                <div class="font-mono text-primary font-bold">{{ wave.id }}</div>
                <div class="flex items-center gap-2 mt-1">
                    <span :class="getPriorityBadgeClass(wave.priority)" class="px-2 py-0.5 rounded text-[10px] font-bold">
                        {{ getPriorityIcon(wave.priority) }} {{ wave.priority || 'Standard' }}
                    </span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border" :class="wave.statusClass">
                        {{ wave.status === 'ON_HOLD' ? 'ON HOLD' : wave.status }}
                    </span>
                </div>
            </div>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ wave.items }} items</span>
        </div>

        <!-- Labour Info (for ON_HOLD orders) -->
        <div v-if="wave.status === 'ON_HOLD'"
            class="mb-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
            <div class="flex items-center gap-2 text-red-600 dark:text-red-400">
                <span class="material-symbols-outlined text-[16px]">warning</span>
                <span class="text-xs font-medium">
                    Need {{ wave.laborRequired }} labourer(s) — {{ wave.laborAssigned?.length || 0 }} assigned
                </span>
            </div>
        </div>

        <!-- Labour Badge (for other orders) -->
        <div v-else-if="wave.laborRequired > 0" class="mb-3">
            <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500">Labour:</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                    :class="(wave.laborAssigned?.length || 0) >= wave.laborRequired
                        ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                        : 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'">
                    {{ wave.laborAssigned?.length || 0 }}/{{ wave.laborRequired }}
                </span>
                <div v-if="wave.laborAssigned?.length" class="flex -space-x-1">
                    <span v-for="l in wave.laborAssigned.slice(0, 3)" :key="l.id"
                        class="w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center text-[9px] font-bold border border-white dark:border-gray-800">
                        {{ (l.name || 'L')[0] }}
                    </span>
                    <span v-if="wave.laborAssigned.length > 3"
                        class="w-5 h-5 rounded-full bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-300 flex items-center justify-center text-[9px] font-bold border border-white dark:border-gray-800">
                        +{{ wave.laborAssigned.length - 3 }}
                    </span>
                </div>
            </div>
        </div>

        <!-- Direct Transport Notice -->
        <div v-if="isDirectTransport(wave)"
            class="mb-3 p-2.5 rounded-lg flex items-start gap-2"
            :class="wave.isDispatcherAssigned
                ? 'bg-blue-500/10 border border-blue-500/30'
                : 'bg-teal-500/10 border border-teal-500/30'">
            <span class="material-symbols-outlined text-[16px] shrink-0 mt-0.5"
                :class="wave.isDispatcherAssigned ? 'text-blue-400' : 'text-teal-400'">local_shipping</span>
            <div>
                <div class="text-[11px] font-bold"
                    :class="wave.isDispatcherAssigned ? 'text-blue-400' : 'text-teal-400'">
                    Direct Transport Order
                </div>
                <template v-if="wave.isDispatcherAssigned">
                    <div class="text-[10px] text-blue-300/70 mt-0.5 leading-snug">
                        Dispatcher assigned <span class="font-bold text-blue-300">{{ wave.assignedDriverName || 'a driver' }}</span> — driver will handle pickup directly. No warehouse action required.
                    </div>
                </template>
                <template v-else>
                    <div class="text-[10px] text-teal-300/70 mt-0.5 leading-snug">No packing service selected — driver handles pickup directly. No warehouse processing needed.</div>
                </template>
            </div>
        </div>

        <!-- Details -->
        <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
            <span>{{ formatCurrency(wave.value) }}</span>
            <span class="font-mono" :class="isOverdue(wave.deadline) ? 'text-red-500 font-bold' : ''">
                {{ wave.deadline }}
                <span v-if="isOverdue(wave.deadline)">⚠️</span>
            </span>
        </div>

        <!-- Action Button -->
        <div v-if="isDirectTransport(wave)" class="text-center text-xs py-2 border rounded-lg"
            :class="wave.isDispatcherAssigned
                ? 'text-blue-400/80 border-blue-500/20 bg-blue-500/5'
                : 'text-teal-400/70 border-teal-500/20 bg-teal-500/5'">
            {{ wave.isDispatcherAssigned
                ? 'Driver assigned by Dispatcher — no warehouse action required'
                : 'Awaiting Dispatcher — driver assignment pending' }}
        </div>
        <div v-else-if="wave.status === 'ON_HOLD'" class="flex gap-2">
            <button @click.stop="$emit('assign-labourers', wave)"
                class="flex-1 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1">
                <span class="material-symbols-outlined text-[14px]">group_add</span>
                Assign Labourers
            </button>
        </div>
        <div v-else-if="hasAction(wave)" class="flex gap-2">
            <button @click.stop="$emit('action', wave)"
                :disabled="startBlocked || actionPending"
                :title="actionPending ? 'Action in progress...' : (startBlocked ? 'Prerequisites not met — see warnings above' : '')"
                class="flex-1 py-2 rounded-lg text-xs font-bold transition-colors"
                :class="(startBlocked || actionPending)
                    ? 'bg-gray-200 dark:bg-white/10 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                    : 'bg-primary hover:bg-primary-dark text-background-dark'">
                {{ actionPending ? 'Working...' : getActionLabel(wave) }}
            </button>
            <button v-if="wave.canUndo" @click.stop="$emit('undo', wave)"
                class="px-3 py-2 bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-300 dark:hover:bg-white/20 transition-colors"
                title="Undo">
                <span class="material-symbols-outlined text-[14px]">undo</span>
            </button>
        </div>
        <div v-else class="text-center text-xs text-gray-400 py-2">
            Awaiting QC / Dispatch
        </div>
    </div>
</template>

<script setup>
import {
    isDirectTransport,
    getPriorityIcon,
    getPriorityBadgeClass,
    isOverdue,
    formatCurrency,
    getActionLabel,
    hasAction,
} from './pickingFormat'

defineProps({
    wave: { type: Object, required: true },
    startBlocked: { type: Boolean, default: false },
    actionPending: { type: Boolean, default: false },
})

defineEmits(['open', 'assign-labourers', 'action', 'undo'])
</script>
