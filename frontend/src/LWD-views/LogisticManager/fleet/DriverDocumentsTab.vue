<template>
    <!-- Tab Content: Driver Documents -->
    <div v-if="activeTab === 'Driver Documents'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <div class="glass-panel rounded-xl p-6 h-[500px] flex flex-col relative overflow-hidden col-span-2">
        <div class="flex justify-between items-center mb-4 flex-shrink-0">
            <h3 class="font-bold text-gray-900 dark:text-white">Driver Personnel Files</h3>
            <button @click="openUploadModal('DRIVER')" class="bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-md shadow-primary/20 flex items-center gap-1">
                <span class="material-symbols-outlined text-[16px]">upload_file</span> Upload Doc
            </button>
        </div>
             <div class="overflow-x-auto overflow-y-auto flex-grow custom-scrollbar">
                <table class="w-full text-left text-sm">
                     <thead class="bg-gray-50 dark:bg-transparent sticky top-0 z-10 backdrop-blur-md">
                        <tr class="text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-white/10 uppercase tracking-wider text-[10px]">
                            <th class="py-2 px-2 font-medium">Driver Name</th>
                            <th class="py-2 font-medium">Warehouse</th>
                            <th class="py-2 font-medium">Files on Record</th>
                            <th class="py-2 font-medium">Next Expiry</th>
                            <th class="py-2 font-medium">Compliance Status</th>
                            <th class="py-2 px-2 text-right">View</th>
                        </tr>
                    </thead>
                   <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <template v-for="driverGroup in groupedDriverDocs" :key="driverGroup.id">
                            <!-- Parent Row -->
                            <tr class="group hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer" @click="toggleDocExpand(driverGroup.id)">
                                <td class="py-3 px-2 flex items-center gap-3">
                                    <span class="material-symbols-outlined text-gray-400 text-sm transition-transform duration-200" :class="expandedDocs.includes(driverGroup.id) ? 'rotate-90' : ''">chevron_right</span>
                                    <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-600 dark:text-gray-300">
                                        {{ driverGroup.name.charAt(0) }}
                                    </div>
                                    <span class="text-gray-900 dark:text-white font-medium">{{ driverGroup.name }}</span>
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 font-medium whitespace-nowrap">
                                    {{ store.hubs.find(h => h.id === driverGroup.docs[0]?.hubId)?.name || 'Main Hub' }}
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300">
                                    <div class="flex flex-wrap gap-1">
                                        <span v-for="doc in driverGroup.docs.slice(0, 2)" :key="doc.id" class="text-[10px] bg-gray-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-300 truncate max-w-[100px]">
                                            {{ doc.type }}
                                        </span>
                                        <span v-if="driverGroup.docs.length > 2" class="text-[10px] text-gray-400">+{{ driverGroup.docs.length - 2 }}</span>
                                    </div>
                                </td>
                                <td class="py-3 text-gray-600 dark:text-gray-300 text-xs">
                                    {{ driverGroup.docs.map(d => d.expiry).sort((a,b) => new Date(a) - new Date(b))[0] }}
                                </td>
                                <td class="py-3">
                                      <div class="flex gap-2 items-center">
                                        <span v-if="driverGroup.docs.some(d => new Date(d.expiry) < new Date())" class="w-2 h-2 rounded-full bg-red-500" title="Expired Doc"></span>
                                        <span v-else-if="driverGroup.docs.some(d => d.status === 'Expiring Soon')" class="w-2 h-2 rounded-full bg-yellow-500" title="Expiring Soon"></span>
                                        <span v-else class="w-2 h-2 rounded-full bg-green-500" title="All Good"></span>
                                        <span class="text-xs text-gray-500 dark:text-gray-400">
                                            {{ driverGroup.docs.some(d => new Date(d.expiry) < new Date()) ? 'Action Required' : (driverGroup.docs.some(d => d.status === 'Expiring Soon') ? 'Renew Soon' : 'Compliant') }}
                                        </span>
                                    </div>
                                </td>
                                <td class="py-3 px-2 text-right">
                                     <button @click.stop="toggleDocExpand(driverGroup.id)" class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white p-1 rounded-full transition-colors hover:bg-gray-100 dark:hover:bg-white/10">
                                        <span class="material-symbols-outlined">expand_circle_down</span>
                                    </button>
                                </td>
                            </tr>
                            <!-- Child Rows -->
                            <tr v-if="expandedDocs.includes(driverGroup.id)" class="bg-gray-50/50 dark:bg-white/5">
                                <td colspan="5" class="p-0">
                                    <div class="px-4 py-2 border-l-2 border-primary ml-10 my-2 space-y-2">
                                        <div v-for="doc in driverGroup.docs" :key="doc.id" class="flex justify-between items-center p-2 rounded-lg hover:bg-white dark:hover:bg-white/5 border border-transparent hover:border-gray-200 dark:hover:border-white/10 transition-colors">
                                            <div class="flex items-center gap-3">
                                                <span class="material-symbols-outlined text-gray-400">badge</span>
                                                <div>
                                                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ doc.type }}</p>
                                                    <p class="text-[10px] text-gray-500">ID: {{ doc.licenseNo }}</p>
                                                </div>
                                            </div>
                                            <div class="flex items-center gap-4">
                                                <div class="text-right">
                                                    <p class="text-[10px] text-gray-400">Expiry</p>
                                                    <p class="text-xs font-medium" :class="new Date(doc.expiry) < new Date() ? 'text-red-500' : 'text-gray-900 dark:text-white'">{{ doc.expiry }}</p>
                                                </div>
                                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border"
                                                    :class="doc.status === 'Active' ? 'bg-green-50 text-green-600 border-green-200 dark:bg-green-500/10 dark:text-green-400' : (doc.status === 'Expiring Soon' ? 'bg-yellow-50 text-yellow-600 border-yellow-200 dark:bg-yellow-500/10 dark:text-yellow-400' : (doc.status === 'Pending Verification' ? 'bg-orange-50 text-orange-600 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400' : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400'))">
                                                    {{ doc.status }}
                                                </span>
                                                <button @click.stop="openDocModal(doc)" class="text-primary hover:text-primary/80 font-medium text-xs flex items-center gap-1 bg-primary/10 px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors">
                                                    <span class="material-symbols-outlined text-[14px]">visibility</span> View
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    activeTab,
    expandedDocs,
    groupedDriverDocs,
    openDocModal,
    openUploadModal,
    store,
    toggleDocExpand,
} = inject(fleetPageKey)
</script>
