<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Proof of Delivery</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">View delivery confirmations, signatures, and photos</p>
            </div>
            <div class="flex gap-3">
                <select v-model="viewMode" class="text-sm bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none">
                    <option value="grid" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Grid View</option>
                    <option value="list" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">List View</option>
                </select>
                <button @click="exportAll" class="px-4 py-2 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white rounded-lg font-bold text-sm transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined text-[16px]">download</span> Export All
                </button>
            </div>
        </div>

        <!-- Summary -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="glass-panel p-5 rounded-xl flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center text-green-500">
                    <span class="material-symbols-outlined text-2xl">verified</span>
                </div>
                <div>
                    <div class="text-xs text-gray-500">Confirmed Deliveries</div>
                    <div class="text-xl font-bold text-green-500">{{ deliveries.length }}</div>
                </div>
            </div>
            <div class="glass-panel p-5 rounded-xl flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                    <span class="material-symbols-outlined text-2xl">photo_camera</span>
                </div>
                <div>
                    <div class="text-xs text-gray-500">With Photo Proof</div>
                    <div class="text-xl font-bold text-blue-500">{{ withPhoto }}</div>
                </div>
            </div>
            <div class="glass-panel p-5 rounded-xl flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500">
                    <span class="material-symbols-outlined text-2xl">draw</span>
                </div>
                <div>
                    <div class="text-xs text-gray-500">E-Signed</div>
                    <div class="text-xl font-bold text-purple-500">{{ eSigned }}</div>
                </div>
            </div>
        </div>

        <!-- Search -->
        <div class="glass-panel p-4 rounded-xl">
            <div class="relative">
                <span class="material-symbols-outlined absolute left-3 top-2.5 text-gray-400 text-sm">search</span>
                <input v-model="searchQuery" type="text" placeholder="Search delivery ID, recipient..."
                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
            </div>
        </div>

        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="d in filtered" :key="d.id" class="glass-panel rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer" @click="openDetail(d)">
                <!-- Photo Area -->
                <div class="h-40 bg-gradient-to-br from-green-500/10 to-blue-500/10 flex items-center justify-center relative">
                    <span class="material-symbols-outlined text-5xl text-green-500/30">local_shipping</span>
                    <div class="absolute top-3 right-3 px-2 py-0.5 bg-green-500 text-white text-[10px] font-bold rounded">Delivered</div>
                    <div v-if="d.pod?.photo" class="absolute bottom-3 left-3 flex items-center gap-1 bg-black/50 text-white text-[10px] px-2 py-0.5 rounded">
                        <span class="material-symbols-outlined text-[12px]">photo_camera</span> Photo Proof
                    </div>
                </div>
                <div class="p-4 space-y-2">
                    <div class="flex justify-between items-start">
                        <div class="font-mono text-blue-500 text-xs font-bold">{{ d.id }}</div>
                        <div class="text-[10px] text-gray-500">{{ d.pod?.time || 'N/A' }}</div>
                    </div>
                    <div class="text-xs text-gray-900 dark:text-white font-medium">{{ d.origin }} → {{ d.destination }}</div>
                    <div class="flex items-center gap-2 text-xs text-gray-500">
                        <span class="material-symbols-outlined text-[14px]">person</span>
                        Signed by: <span class="font-bold text-gray-700 dark:text-gray-300">{{ d.pod?.signedBy || 'N/A' }}</span>
                    </div>
                    <div v-if="d.pod?.location" class="flex items-center gap-2 text-xs text-gray-500">
                        <span class="material-symbols-outlined text-[14px]">location_on</span>
                        {{ d.pod.location }}
                    </div>
                </div>
            </div>

            <div v-if="filtered.length === 0" class="col-span-full glass-panel p-12 rounded-xl flex flex-col items-center justify-center">
                <span class="material-symbols-outlined text-5xl text-gray-300 dark:text-gray-600 mb-3">verified</span>
                <p class="text-gray-500 dark:text-gray-400">No delivery proofs found</p>
            </div>
        </div>

        <!-- List View -->
        <div v-if="viewMode === 'list'" class="glass-panel rounded-xl overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm min-w-[700px]">
                    <thead class="bg-gray-100 dark:bg-white/5 text-gray-500 dark:text-gray-400 uppercase text-[10px]">
                        <tr>
                            <th class="px-4 py-3">Shipment</th>
                            <th class="px-4 py-3">Route</th>
                            <th class="px-4 py-3">Signed By</th>
                            <th class="px-4 py-3">Time</th>
                            <th class="px-4 py-3">Location</th>
                            <th class="px-4 py-3">Proof</th>
                            <th class="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                        <tr v-if="filtered.length === 0">
                            <td colspan="7" class="px-4 py-8 text-center text-gray-400 text-sm">No delivery proofs found</td>
                        </tr>
                        <tr v-for="d in filtered" :key="d.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <td class="px-4 py-3 font-mono text-blue-500 text-xs font-bold">{{ d.id }}</td>
                            <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">{{ d.origin }} → {{ d.destination }}</td>
                            <td class="px-4 py-3 text-xs font-bold text-gray-900 dark:text-white">{{ d.pod?.signedBy || '—' }}</td>
                            <td class="px-4 py-3 text-xs text-gray-500">{{ d.pod?.time || '—' }}</td>
                            <td class="px-4 py-3 text-xs text-gray-500">{{ d.pod?.location || '—' }}</td>
                            <td class="px-4 py-3">
                                <div class="flex items-center gap-1">
                                    <span v-if="d.pod?.photo" class="material-symbols-outlined text-[14px] text-blue-500" title="Photo">photo_camera</span>
                                    <span v-if="d.pod?.signedBy" class="material-symbols-outlined text-[14px] text-purple-500" title="Signature">draw</span>
                                </div>
                            </td>
                            <td class="px-4 py-3 text-right">
                                <button @click="openDetail(d)" class="p-1.5 rounded-lg hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="View">
                                    <span class="material-symbols-outlined text-[16px]">visibility</span>
                                </button>
                                <button @click="downloadPod(d)" class="p-1.5 rounded-lg hover:bg-gray-500/10 text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors" title="Download">
                                    <span class="material-symbols-outlined text-[16px]">download</span>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Detail Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="!!detailShipment" @close="detailShipment = null">
                <template #title>Delivery Proof — {{ detailShipment?.id }}</template>
                <div v-if="detailShipment" class="space-y-4">
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Origin</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailShipment.origin }}</div></div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg"><div class="text-[10px] text-gray-500 mb-1">Destination</div><div class="text-xs font-bold text-gray-900 dark:text-white">{{ detailShipment.destination }}</div></div>
                    </div>

                    <!-- Photo Proof -->
                    <div class="p-4 bg-gradient-to-br from-green-500/10 to-blue-500/10 rounded-lg text-center">
                        <span class="material-symbols-outlined text-4xl text-green-500/50 mb-2">photo_camera</span>
                        <div class="text-xs text-gray-500">{{ detailShipment.pod?.photo ? 'Photo proof available' : 'No photo uploaded' }}</div>
                    </div>

                    <!-- Delivery Info -->
                    <div class="space-y-3">
                        <div class="flex items-center gap-3 p-3 bg-green-500/10 rounded-lg">
                            <span class="material-symbols-outlined text-green-500">verified</span>
                            <div>
                                <div class="text-xs font-bold text-green-600 dark:text-green-400">Delivery Confirmed</div>
                                <div class="text-[10px] text-gray-500">Signed by {{ detailShipment.pod?.signedBy || 'N/A' }}</div>
                            </div>
                        </div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Delivery Time</span><span class="font-bold text-gray-900 dark:text-white">{{ detailShipment.pod?.time || 'N/A' }}</span></div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">GPS Location</span><span class="font-bold text-gray-900 dark:text-white">{{ detailShipment.pod?.location || 'N/A' }}</span></div>
                        <div class="flex justify-between text-xs"><span class="text-gray-500">Weight</span><span class="font-bold text-gray-900 dark:text-white">{{ detailShipment.weight }}</span></div>
                    </div>
                </div>
                <template #footer>
                    <button @click="detailShipment = null" class="px-4 py-2 text-gray-500 text-sm">Close</button>
                    <button @click="downloadPod(detailShipment); detailShipment = null" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors">Download PoD</button>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import BaseModal from '@/components/BaseModal.vue'

const store = useVendorStore()
const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()
const searchQuery = ref('')
const viewMode = ref('grid')
const detailShipment = ref(null)

const deliveries = computed(() => store.shipmentsWithPod)

const withPhoto = computed(() => deliveries.value.filter(d => d.pod?.photo).length)
const eSigned = computed(() => deliveries.value.filter(d => d.pod?.signedBy).length)

const filtered = computed(() => {
    if (!searchQuery.value.trim()) return deliveries.value
    const q = searchQuery.value.toLowerCase()
    return deliveries.value.filter(d =>
        d.id.toLowerCase().includes(q) ||
        d.destination.toLowerCase().includes(q) ||
        (d.pod?.signedBy || '').toLowerCase().includes(q)
    )
})

function openDetail(d) { detailShipment.value = d }

function downloadPod(d) {
    openSlipWithData('proofOfDelivery', d, authStore.currentUser)
}

function exportAll() {
    const rows = [
        ['Shipment ID', 'Origin', 'Destination', 'Signed By', 'Time', 'Location', 'Photo Proof', 'E-Signed'],
        ...deliveries.value.map(d => [
            d.id,
            d.origin || '',
            d.destination || '',
            d.pod?.signedBy || '',
            d.pod?.time || '',
            d.pod?.location || '',
            d.pod?.photo ? 'Yes' : 'No',
            d.pod?.signedBy ? 'Yes' : 'No',
        ])
    ]
    downloadCsv(`proof_of_delivery_${new Date().toISOString().slice(0, 10)}.csv`, rows)
}

function downloadCsv(filename, rows) {
    const csv = rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

function showToast(msg) {
    const t = document.createElement('div')
    t.className = 'fixed right-4 bottom-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

</script>
