<template>
    <div v-for="rule in store.recurringRules" :key="rule.id"
        class="glass-panel p-5 rounded-xl border-l-4 transition-all duration-200"
        :class="rule.active ? 'border-blue-500' : 'border-gray-300 dark:border-gray-600 opacity-75'">
        <div class="flex justify-between items-start mb-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold"
                :class="rule.active ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' : 'bg-gray-500/20 text-gray-500'">{{ rule.frequency }}</span>
            <div class="flex gap-1">
                <button @click="openEditModal(rule)" class="p-1.5 rounded-lg hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="Edit">
                    <span class="material-symbols-outlined text-[16px]">edit</span>
                </button>
                <button @click="confirmDelete(rule)" class="p-1.5 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors" title="Delete">
                    <span class="material-symbols-outlined text-[16px]">delete</span>
                </button>
            </div>
        </div>

        <h3 class="font-bold text-gray-900 dark:text-white text-base mb-1">{{ rule.name }}</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ rule.description || '—' }}</p>

        <div class="space-y-2 mb-4">
            <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                <span class="material-symbols-outlined text-[14px] text-blue-500">warehouse</span>
                Hub: {{ getRuleMeta(rule).hub || rule.route }}
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                <span class="material-symbols-outlined text-[14px] text-amber-500">schedule</span>
                Vendor Drop Time: {{ getRuleMeta(rule).dropOffTime || 'Not set' }}
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                <span class="material-symbols-outlined text-[14px] text-emerald-500">pin_drop</span>
                Destination: {{ formatRuleDestination(getRuleMeta(rule)) }}
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                <span class="material-symbols-outlined text-[14px] text-purple-500">inventory_2</span>
                {{ getRuleMeta(rule).cargo }}
            </div>
            <div class="flex items-center gap-2 text-xs" :class="getRuleMeta(rule).autoDebitEnabled ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'">
                <span class="material-symbols-outlined text-[14px]" :class="getRuleMeta(rule).autoDebitEnabled ? 'text-emerald-500' : 'text-amber-500'">
                    {{ getRuleMeta(rule).autoDebitEnabled ? 'account_balance_wallet' : 'warning' }}
                </span>
                {{ getRuleMeta(rule).autoDebitEnabled ? 'Wallet auto-debit enabled' : 'Wallet auto-debit disabled' }}
            </div>
        </div>

        <div class="flex justify-between items-center border-t border-gray-100 dark:border-white/5 pt-3">
            <div class="text-[10px] text-gray-500">
                Next: <span class="font-bold text-gray-700 dark:text-gray-300">{{ formatNextRun(rule.nextRun) }}</span>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" :checked="rule.active" @change="toggleRule(rule)"
                    :disabled="togglingId === rule.id" class="sr-only peer">
                <div class="w-9 h-5 rounded-full transition-colors"
                    :class="[
                        togglingId === rule.id ? 'opacity-50' : '',
                        rule.active ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-700'
                    ]">
                    <div class="absolute top-[2px] left-[2px] bg-white rounded-full h-4 w-4 shadow transition-all"
                        :class="rule.active ? 'translate-x-4' : 'translate-x-0'"></div>
                </div>
            </label>
        </div>
    </div>

    <!-- Empty state -->
    <div v-if="store.recurringRules.length === 0" class="col-span-full glass-panel p-12 rounded-xl flex flex-col items-center justify-center">
        <span class="material-symbols-outlined text-5xl text-gray-300 dark:text-gray-600 mb-3">event_repeat</span>
        <p class="text-gray-500 dark:text-gray-400 mb-4">No recurring schedules yet</p>
        <button @click="openCreateModal" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors">Create Your First Schedule</button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { recurringPageKey } from './recurringPageContext'

const {
    confirmDelete,
    formatNextRun,
    formatRuleDestination,
    getRuleMeta,
    openCreateModal,
    openEditModal,
    store,
    toggleRule,
    togglingId,
} = inject(recurringPageKey)
</script>
