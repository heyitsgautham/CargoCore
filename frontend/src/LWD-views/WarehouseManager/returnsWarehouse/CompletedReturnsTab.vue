<template>
    <!-- ===== COMPLETED TAB ===== -->
    <div v-if="activeTab === 'completed'">
        <div class="glass-panel rounded-xl overflow-hidden">
            <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-100 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white">Completed Returns Log</h3>
                <div class="flex gap-2">
                    <button v-for="f in ['All', 'restock', 'claims', 'discard', 'recycle']" :key="f"
                        @click="completedFilter = f === 'All' ? '' : f"
                        class="px-3 py-1 rounded text-xs font-bold transition-colors"
                        :class="(f === 'All' && !completedFilter) || completedFilter === f ? 'bg-primary/20 text-primary' : 'bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                        {{ f === 'All' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1) }}
                    </button>
                </div>
            </div>
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 dark:bg-white/5 text-gray-600 dark:text-gray-400 uppercase">
                    <tr>
                        <th class="p-4">Item</th>
                        <th class="p-4">RMA</th>
                        <th class="p-4">Condition</th>
                        <th class="p-4">Disposition</th>
                        <th class="p-4">Photo</th>
                        <th class="p-4">Time</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                    <tr v-for="item in filteredCompleted" :key="item.id" class="hover:bg-gray-50 dark:bg-white/5 transition-colors">
                        <td class="p-4 text-gray-900 dark:text-white font-bold">{{ item.name }}</td>
                        <td class="p-4 font-mono text-gray-600 dark:text-gray-400 text-xs">{{ item.rma || '--' }}</td>
                        <td class="p-4">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold" :class="getConditionClass(item.condition)">{{ item.condition }}</span>
                        </td>
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <div class="w-6 h-6 rounded flex items-center justify-center" :class="getDispositionBg(item.disposition)">
                                    <span class="material-symbols-outlined text-[14px]" :class="getDispositionColor(item.disposition)">{{ getDispositionIcon(item.disposition) }}</span>
                                </div>
                                <span class="text-xs" :class="getDispositionColor(item.disposition)">{{ item.dispositionLabel }}</span>
                            </div>
                        </td>
                        <td class="p-4">
                            <button v-if="item.hasPhoto" @click="photoItem = item; showPhotoModal = true"
                                class="text-blue-600 dark:text-blue-400 text-xs hover:underline cursor-pointer flex items-center gap-1">
                                <span class="material-symbols-outlined text-[14px]">photo_camera</span> Attached
                            </button>
                            <span v-else class="text-gray-600 text-xs">—</span>
                        </td>
                        <td class="p-4 text-gray-500 font-mono text-xs">{{ item.time }}</td>
                    </tr>
                    <tr v-if="filteredCompleted.length === 0">
                        <td colspan="6" class="p-8 text-center text-gray-500">No completed returns found.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { returnsWarehousePageKey } from './returnsWarehousePageContext'

const {
    activeTab,
    completedFilter,
    filteredCompleted,
    getConditionClass,
    getDispositionBg,
    getDispositionColor,
    getDispositionIcon,
    photoItem,
    showPhotoModal,
} = inject(returnsWarehousePageKey)
</script>
