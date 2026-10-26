<template>
    <div v-if="showSuspendConfirm" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center" @click.self="showSuspendConfirm = false">
        <div class="bg-gray-900 border border-white/10 shadow-2xl rounded-2xl p-6 w-full max-w-sm m-4">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                    :class="suspendConfirmDriver?.suspended ? 'bg-green-500/15' : 'bg-red-500/15'">
                    <span class="material-symbols-outlined" :class="suspendConfirmDriver?.suspended ? 'text-green-400' : 'text-red-400'">
                        {{ suspendConfirmDriver?.suspended ? 'lock_open' : 'block' }}
                    </span>
                </div>
                <div>
                    <h3 class="font-bold text-white text-sm">{{ suspendConfirmDriver?.suspended ? 'Unsuspend Driver' : 'Suspend Driver' }}</h3>
                    <p class="text-[11px] text-gray-400">{{ suspendConfirmDriver?.name }}</p>
                </div>
            </div>
            <p class="text-[12px] text-gray-400 mb-5 leading-relaxed">
                <template v-if="suspendConfirmDriver?.suspended">
                    This will <strong class="text-green-400">restore access</strong> for {{ suspendConfirmDriver?.name }}. They will appear in the driver assignment list and can receive new orders.
                </template>
                <template v-else>
                    This will <strong class="text-red-400">block {{ suspendConfirmDriver?.name }}</strong> from receiving new order assignments. They will be excluded from dispatch until unsuspended.
                </template>
            </p>
            <div class="flex gap-2">
                <button @click="confirmSuspend"
                    class="flex-1 font-bold py-2 rounded-lg text-sm transition-colors"
                    :class="suspendConfirmDriver?.suspended ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-red-600 hover:bg-red-700 text-white'">
                    {{ suspendConfirmDriver?.suspended ? 'Yes, Unsuspend' : 'Yes, Suspend' }}
                </button>
                <button @click="showSuspendConfirm = false"
                    class="flex-1 bg-white/5 hover:bg-white/10 text-gray-300 py-2 rounded-lg text-sm font-bold transition-colors">Cancel</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { driverManagementPageKey } from './driverManagementPageContext'

const { confirmSuspend, showSuspendConfirm, suspendConfirmDriver } = inject(driverManagementPageKey)
</script>
