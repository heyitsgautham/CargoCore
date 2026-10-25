<template>
    <Teleport to="body">
        <div v-if="show"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="emit('close')">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-4xl border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">list_alt</span>
                            Pick List — {{ wave?.id }}
                        </h3>
                        <p class="text-xs text-gray-500 mt-1">Item-by-item picking locations</p>
                    </div>
                    <button @click="emit('close')" class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-6 overflow-y-auto flex-1">
                    <div v-if="loading" class="flex items-center justify-center py-8">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                    <div v-else-if="items.length === 0" class="text-center py-8 text-gray-500">
                        <span class="material-symbols-outlined text-4xl mb-2 opacity-50">inventory_2</span>
                        <p>No items found for this order</p>
                    </div>
                    <div v-else class="space-y-3">
                        <div v-for="(item, idx) in items" :key="getPickItemKey(item)"
                            class="p-4 rounded-xl border transition-all"
                            :class="item.is_complete
                                ? 'bg-green-500/10 border-green-500/30'
                                : getItemPickedQuantity(item) > 0
                                    ? 'bg-blue-500/10 border-blue-500/30'
                                    : 'bg-gray-50 dark:bg-white/5 border-gray-100 dark:border-white/5'">
                            <div class="flex justify-between items-start">
                                <div class="flex items-start gap-4">
                                    <div class="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
                                        {{ idx + 1 }}
                                    </div>
                                    <div>
                                        <div class="font-bold text-gray-900 dark:text-white">{{ item.item_name || item.name }}</div>
                                        <div class="text-xs text-gray-500 font-mono">SKU: {{ item.sku }}</div>
                                        <div class="mt-2 flex gap-4 text-xs">
                                            <span class="text-gray-600 dark:text-gray-400">
                                                <strong class="text-primary">{{ item.required_quantity || item.quantity }}</strong> {{ item.unit || 'pcs' }} required
                                            </span>
                                            <span v-if="getItemPickedQuantity(item) > 0"
                                                class="font-bold"
                                                :class="item.is_complete ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                                                Picked: {{ getItemPickedQuantity(item) }} / {{ getItemRequiredQuantity(item) }}
                                            </span>
                                            <span v-if="item.shortage_quantity > 0" class="text-red-500 font-bold">
                                                ⚠ Shortage: {{ item.shortage_quantity }}
                                            </span>
                                        </div>
                                        <div v-if="item.picker_name" class="mt-2 text-[11px] text-gray-500">
                                            Last confirmed by {{ item.picker_name }}
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-bold mb-2">
                                        {{ item.location_path || formatLocation(item) }}
                                    </div>
                                    <div class="text-[10px] text-gray-500 font-mono">
                                        Scan: {{ item.scan_code || item.sku }}
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3 flex items-center justify-between">
                                <div class="flex gap-2 text-[10px] text-gray-500">
                                    <span v-if="item.zone" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Zone: {{ item.zone }}</span>
                                    <span v-if="item.aisle" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Aisle: {{ item.aisle }}</span>
                                    <span v-if="item.rack" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Rack: {{ item.rack }}</span>
                                    <span v-if="item.shelf" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Shelf: {{ item.shelf }}</span>
                                    <span v-if="item.bin" class="px-2 py-0.5 bg-gray-100 dark:bg-white/10 rounded">Bin: {{ item.bin }}</span>
                                </div>
                                <div class="flex gap-2">
                                    <button @click="emit('scan-item', item)"
                                        :disabled="!canConfirmPickItem(item)"
                                        class="px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1"
                                        :class="canConfirmPickItem(item)
                                            ? 'bg-primary/15 text-primary hover:bg-primary/25'
                                            : 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed'">
                                        <span class="material-symbols-outlined text-[14px]">qr_code_scanner</span>
                                        Scan to Confirm
                                    </button>
                                    <button @click="emit('pick-item', item)"
                                        :disabled="!canConfirmPickItem(item)"
                                        class="px-3 py-1 rounded text-xs font-bold transition-all flex items-center gap-1"
                                        :class="item.is_complete
                                            ? 'bg-green-500/30 text-green-600 dark:text-green-400 cursor-not-allowed'
                                            : getItemPickedQuantity(item) > 0
                                                ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 hover:bg-blue-500/30'
                                                : 'bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-primary/20 hover:text-primary'">
                                        <span class="material-symbols-outlined text-[14px]">
                                            {{ item.syncing ? 'sync' : item.is_complete ? 'check_circle' : getItemPickedQuantity(item) > 0 ? 'inventory_2' : 'radio_button_unchecked' }}
                                        </span>
                                        {{ getPickActionLabel(item) }}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t border-gray-100 dark:border-white/5 flex justify-between items-center shrink-0 bg-gray-50 dark:bg-black/20">
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                        {{ pickedCount }} / {{ items.length }} items picked
                    </div>
                    <div class="flex gap-2">
                        <button @click="emit('print')" class="px-4 py-2 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white rounded-lg text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/20 transition-colors flex items-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">print</span>
                            Print List
                        </button>
                        <button @click="emit('complete')" :disabled="actionDisabled"
                            class="px-4 py-2 bg-primary text-background-dark rounded-lg text-sm font-bold transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                            <span class="material-symbols-outlined text-[18px]">check</span>
                            {{ wave ? (getActionLabel(wave) || 'Proceed with Order') : 'Proceed with Order' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { canConfirmPick } from './pickingBoard'
import {
    formatLocation,
    getActionLabel,
    getPickItemKey,
    getItemRequiredQuantity,
    getItemPickedQuantity,
    getPickActionLabel,
} from './pickingFormat'

const props = defineProps({
    show: { type: Boolean, default: false },
    wave: { type: Object, default: null },
    items: { type: Array, required: true },
    loading: { type: Boolean, default: false },
    actionDisabled: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'scan-item', 'pick-item', 'print', 'complete'])

const pickedCount = computed(() => props.items.filter(item => item.is_complete).length)

function canConfirmPickItem(item) {
    return canConfirmPick(props.wave, item)
}
</script>
