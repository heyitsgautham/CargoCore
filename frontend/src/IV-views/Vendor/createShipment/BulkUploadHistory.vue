<template>
    <!-- Upload History -->
    <div class="glass-panel p-6 rounded-xl">
        <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900 dark:text-white">Upload History</h3>
            <button @click="showUploadModal = true"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px]">upload_file</span>
                New Upload
            </button>
        </div>
        <div class="space-y-2">
            <div v-for="upload in bulkUploads" :key="upload.id"
                class="border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden">
                <!-- Upload Row -->
                <div @click="toggleUpload(upload.id)"
                    class="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer">
                    <span class="material-symbols-outlined text-gray-400"
                        :class="expandedUpload === upload.id ? 'rotate-90' : ''">chevron_right</span>
                    <div class="flex-1 grid grid-cols-5 items-center gap-4 text-sm">
                        <div>
                            <div class="font-medium text-gray-900 dark:text-white">{{ upload.fileName }}</div>
                            <div class="text-xs text-gray-500">{{ upload.date }}</div>
                        </div>
                        <div><span class="px-2 py-1 rounded text-xs font-bold"
                                :class="upload.type === 'CSV' ? 'bg-green-100 text-green-700' : upload.type === 'XLSX' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'">{{
                                    upload.type }}</span></div>
                        <div class="text-gray-600 dark:text-gray-400">{{ upload.size }}</div>
                        <div class="text-gray-900 dark:text-white">{{ upload.entries.length }} entries</div>
                        <div class="text-blue-500 font-medium">₹{{
                            upload.entries.reduce((s, e) => s + e.quotedPrice, 0).toLocaleString()}}</div>
                    </div>
                    <button @click.stop="deleteUpload(upload.id)"
                        class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">delete</span>
                    </button>
                </div>
                <!-- Expanded Entries -->
                <div v-if="expandedUpload === upload.id" class="bg-gray-50 dark:bg-white/5 p-4 space-y-2">
                    <div v-for="entry in upload.entries" :key="entry.orderId"
                        class="bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-lg overflow-hidden">
                        <!-- Entry Row -->
                        <div @click="toggleEntry(entry.orderId)"
                            class="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer">
                            <span class="material-symbols-outlined text-gray-400 text-[18px]"
                                :class="expandedEntry === entry.orderId ? 'rotate-90' : ''">chevron_right</span>
                            <div class="flex-1 grid grid-cols-6 items-center gap-3 text-xs">
                                <div class="font-bold text-blue-600 dark:text-blue-400">{{ entry.orderId }}
                                </div>
                                <div class="col-span-2 text-gray-900 dark:text-white">{{ entry.description }}
                                </div>
                                <div class="text-gray-600 dark:text-gray-400">{{ entry.palletCount }} pallets
                                </div>
                                <div class="text-gray-600 dark:text-gray-400">{{ entry.weight }} kg</div>
                                <div class="text-blue-500 font-bold">₹{{ entry.quotedPrice.toLocaleString() }}
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button @click.stop="openEditModal(entry)"
                                    class="p-1.5 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400"><span
                                        class="material-symbols-outlined text-[18px]">edit</span></button>
                                <button @click.stop="deleteEntry(upload.id, entry.orderId)"
                                    class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"><span
                                        class="material-symbols-outlined text-[18px]">delete</span></button>
                            </div>
                        </div>
                        <!-- Expanded Entry Details -->
                        <div v-if="expandedEntry === entry.orderId"
                            class="bg-gray-50 dark:bg-black/20 p-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs border-t border-gray-200 dark:border-white/10">
                            <div><span class="text-gray-500">Category:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.category
                                    }}</span></div>
                            <div><span class="text-gray-500">HSN Code:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.hsnCode || 'N/A'
                                    }}</span></div>
                            <div><span class="text-gray-500">Value:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">₹{{
                                        entry.declaredValue.toLocaleString() }}</span></div>
                            <div><span class="text-gray-500">Insurance:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.insuranceRequired
                                    }}</span></div>
                            <div><span class="text-gray-500">Pickup Hub:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.pickupHub
                                    }}</span></div>
                            <div><span class="text-gray-500">Destination:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.destinationCity
                                    }}</span></div>
                            <div><span class="text-gray-500">Pincode:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.pincode }}</span>
                            </div>
                            <div><span class="text-gray-500">Pickup Date:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.pickupDate
                                    }}</span></div>
                            <div><span class="text-gray-500">Priority:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.priority
                                    }}</span></div>
                            <div><span class="text-gray-500">Payment:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.paymentMode
                                    }}</span></div>
                            <div><span class="text-gray-500">Packing:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.packingRequired ?
                                        'Yes' : 'No' }}</span></div>
                            <div><span class="text-gray-500">Labor:</span> <span
                                    class="text-gray-900 dark:text-white font-medium">{{ entry.laborRequired ?
                                        entry.laborCount + ' helpers' : 'No' }}</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { createShipmentPageKey } from './createShipmentPageContext'

const {
    bulkUploads,
    deleteEntry,
    deleteUpload,
    expandedEntry,
    expandedUpload,
    openEditModal,
    showUploadModal,
    toggleEntry,
    toggleUpload,
} = inject(createShipmentPageKey)
</script>
