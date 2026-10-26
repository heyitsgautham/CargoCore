<template>
    <!-- Analytics -->
    <div v-if="globalTab === 'graphs'" class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-5">
        <div class="glass-panel p-6 rounded-2xl flex flex-col">
            <div class="flex items-center justify-between mb-5">
                <h4 class="text-sm font-bold text-gray-900 dark:text-white">Spend Overview</h4>
                <span class="text-[10px] font-bold text-blue-500 bg-blue-500/10 px-2 py-1 rounded-lg">Last 6 Months</span>
            </div>
            <div class="flex-1 relative min-h-[200px]"><Bar :data="spendChartData" :options="spendChartOptions" /></div>
            <div class="mt-5 pt-4 border-t border-gray-100 dark:border-white/5 grid grid-cols-2 gap-4">
                <div>
                    <div class="text-[10px] text-gray-400 uppercase font-bold mb-1">Transit Efficiency</div>
                    <div class="flex items-end gap-1">
                        <div class="text-2xl font-black text-gray-900 dark:text-white">{{ store.analyticsData.onTime }}%</div>
                        <span class="text-[10px] text-green-500 font-bold mb-0.5 flex items-center"><span class="material-symbols-outlined text-[12px]">trending_up</span>+1.2%</span>
                    </div>
                    <div class="text-[9px] text-gray-400">vs last month</div>
                </div>
                <div>
                    <div class="text-[10px] text-gray-400 uppercase font-bold mb-1">Success Rate</div>
                    <div class="text-2xl font-black text-gray-900 dark:text-white">{{ store.analyticsData.successRate }}%</div>
                    <div class="flex items-end gap-0.5 mt-1.5">
                        <div v-for="i in 5" :key="'spark-'+i" class="w-2.5 rounded-sm bg-blue-500/40" :style="{ height: (8 + i * 3) + 'px' }"></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="glass-panel p-6 rounded-2xl flex flex-col">
            <div class="flex items-center justify-between mb-5">
                <h4 class="text-sm font-bold text-gray-900 dark:text-white">Volume Overview</h4>
                <div class="flex items-center gap-1.5 text-[10px] text-gray-500">
                    <div class="w-2 h-2 rounded-full bg-blue-500"></div> Daily Orders
                </div>
            </div>
            <div class="flex-1 relative min-h-[160px] mb-4"><Line :data="volumeChartData" :options="volumeChartOptions" /></div>
            <div class="space-y-2">
                <div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">High Volume Routes</div>
                <div v-if="topRoutes.length === 0" class="text-[10px] text-gray-400 text-center py-3">No route data yet</div>
                <div v-for="r in topRoutes" :key="r.route"
                    class="flex items-center justify-between p-2.5 rounded-xl bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                    <div class="flex items-center gap-2.5">
                        <div class="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 font-black text-[11px]">{{ r.rank }}</div>
                        <div>
                            <div class="text-[11px] font-bold text-gray-900 dark:text-white">{{ r.route }}</div>
                            <div class="text-[9px] text-gray-400">{{ r.count }} trips</div>
                        </div>
                    </div>
                    <div class="text-[11px] font-bold text-green-500">{{ r.onTime }}% on-time</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import { vendorTrackingPageKey } from './vendorTrackingPageContext'

const {
    globalTab,
    spendChartData,
    spendChartOptions,
    store,
    topRoutes,
    volumeChartData,
    volumeChartOptions,
} = inject(vendorTrackingPageKey)
</script>
