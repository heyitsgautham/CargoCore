<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Warehouse Management</h2>
            <button @click="openAddModal"
                class="bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-lg border border-slate-700 dark:border-primary/30">
                <span class="material-symbols-outlined">add</span>
                Add New Hub
            </button>
        </div>

        <!-- Stats Overview -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass-panel p-6 rounded-xl relative overflow-hidden">
                <div class="text-gray-500 dark:text-gray-400 text-sm font-medium">Total Warehouses</div>
                <div class="text-4xl font-bold text-gray-900 dark:text-white mt-2">{{ totalWarehouses }}</div>
                <div class="text-green-500 dark:text-green-400 text-xs mt-1 flex items-center gap-1"><span
                        class="material-symbols-outlined text-[14px]">trending_up</span> Active tracking</div>
            </div>
            <div class="glass-panel p-6 rounded-xl relative overflow-hidden">
                <div class="text-gray-500 dark:text-gray-400 text-sm font-medium">Avg Capacity Utilized</div>
                <div class="text-4xl font-bold text-gray-900 dark:text-white mt-2">{{ avgCapacity }}%</div>
                <div class="w-full bg-gray-200 dark:bg-gray-700 h-1.5 mt-2 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500"
                        :class="avgCapacity > 90 ? 'bg-red-500' : (avgCapacity > 70 ? 'bg-yellow-500' : 'bg-blue-500')"
                        :style="`width: ${avgCapacity}%`"></div>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-xl relative overflow-hidden">
                <div class="text-gray-500 dark:text-gray-400 text-sm font-medium">Congested Hubs</div>
                <div class="text-4xl font-bold text-gray-900 dark:text-white mt-2">{{ congestedCount }}</div>
                <div class="text-red-500 dark:text-red-400 text-xs mt-1" v-if="congestedCount > 0">Requires immediate
                    attention</div>
                <div class="text-green-500 dark:text-green-400 text-xs mt-1" v-else>All systems optimal</div>
            </div>
        </div>

        <!-- Warehouse List -->
        <div class="glass-panel rounded-xl flex flex-col">
            <div class="p-6 border-b border-gray-200 dark:border-white/5 flex flex-col sm:flex-row gap-4">
                <div class="relative flex-1">
                    <span
                        class="material-symbols-outlined absolute left-3 top-2.5 text-gray-500 dark:text-gray-400">search</span>
                    <input type="text" v-model="searchQuery" placeholder="Search warehouses..."
                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg py-2 pl-10 pr-4 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 dark:focus:border-primary/50 transition-colors">
                </div>

                <div class="relative">
                    <button @click="isFilterOpen = !isFilterOpen"
                        class="px-4 py-2 border border-gray-200 dark:border-white/10 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors font-medium">
                        <span class="material-symbols-outlined">filter_list</span>
                        <span class="hidden sm:inline">Filter:</span> {{ statusFilter }}
                    </button>

                    <!-- Filter Dropdown -->
                    <div v-show="isFilterOpen"
                        class="absolute right-0 mt-2 w-48 bg-white dark:bg-card-dark rounded-xl shadow-lg border border-gray-200 dark:border-white/10 py-1 z-10">
                        <button v-for="status in ['All', 'Optimal', 'Congested', 'Active']" :key="status"
                            @click="setStatusFilter(status)"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
                            :class="{ 'bg-primary/10 text-primary dark:text-primary font-medium': statusFilter === status }">
                            {{ status }}
                        </button>
                    </div>
                </div>
            </div>

            <div class="overflow-x-auto min-h-[300px]">
                <table class="w-full text-left">
                    <thead
                        class="bg-gray-50 dark:bg-white/5 text-gray-500 dark:text-gray-400 text-xs uppercase tracking-wider">
                        <tr>
                            <th class="p-4 font-medium">Hub Name</th>
                            <th class="p-4 font-medium">Location</th>
                            <th class="p-4 font-medium">Operating Hours</th>
                            <th class="p-4 font-medium">Manager</th>
                            <th class="p-4 font-medium">Capacity</th>
                            <th class="p-4 font-medium">Status</th>
                            <th class="p-4 font-medium">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-white/5 text-sm">
                        <tr v-for="hub in filteredHubs" :key="hub.id"
                            class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group">
                            <td class="p-4">
                                <div class="font-bold text-gray-900 dark:text-white">{{ hub.name }}</div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">{{ hub.hubCode }}</div>
                            </td>
                            <td class="p-4 text-gray-600 dark:text-gray-300">{{ hub.location }}</td>
                            <td class="p-4 text-gray-600 dark:text-gray-300 font-mono text-xs">{{ hub.operatingHours ||
                                '09:00 AM - 09:00 PM' }}</td>
                            <td class="p-4">
                                <div class="flex items-center gap-2">
                                    <div
                                        class="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-[10px] text-gray-700 dark:text-white font-bold tracking-wider">
                                        {{ hub.managerInitials }}</div>
                                    <span class="text-gray-700 dark:text-gray-300 font-medium">{{ hub.manager }}</span>
                                </div>
                            </td>
                            <td class="p-4 text-gray-600 dark:text-gray-300">
                                <div class="flex items-center gap-3">
                                    <div class="w-24 bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
                                        <div class="h-full rounded-full" :style="`width: ${hub.capacity}%`"
                                            :class="hub.capacity > 90 ? 'bg-red-500' : (hub.capacity > 70 ? 'bg-yellow-500' : 'bg-primary')">
                                        </div>
                                    </div>
                                    <span class="font-medium text-xs">{{ hub.capacity }}%</span>
                                </div>
                            </td>
                            <td class="p-4">
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border" :class="[
                                    hub.status.toLowerCase() === 'optimal' ? 'bg-green-50 border-green-200 text-green-600 dark:bg-green-500/10 dark:border-green-500/20 dark:text-green-500' :
                                        (hub.status.toLowerCase() === 'congested' ? 'bg-red-50 border-red-200 text-red-600 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-500' :
                                            'bg-blue-50 border-blue-200 text-blue-600 dark:bg-blue-500/10 dark:border-blue-500/20 dark:text-blue-500')
                                ]">
                                    {{ hub.status }}
                                </span>
                            </td>
                            <td class="p-4">
                                <!-- Action Menu (Dots) -->
                                <div class="relative group/menu">
                                    <button
                                        class="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors p-1 rounded-md hover:bg-gray-100 dark:hover:bg-white/10">
                                        <span class="material-symbols-outlined text-[20px]">more_horiz</span>
                                    </button>

                                    <!-- Dropdown -->
                                    <div
                                        class="absolute right-0 mt-2 w-36 bg-white dark:bg-card-dark rounded-xl shadow-lg border border-gray-200 dark:border-white/10 py-1 z-20 
                                                opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all duration-200 origin-top-right scale-95 group-hover/menu:scale-100">
                                        <button @click="openEditModal(hub)"
                                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[16px]">edit</span>
                                            Edit Hub
                                        </button>
                                        <button @click="store.deleteHub(hub.id)"
                                            class="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors flex items-center gap-2">
                                            <span class="material-symbols-outlined text-[16px]">delete</span>
                                            Delete Hub
                                        </button>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Add / Edit Hub Modal -->
        <Teleport to="body">
            <div v-if="isModalOpen"
                class="fixed inset-0 w-screen h-screen z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <div class="bg-slate-950/98 rounded-2xl shadow-xl w-full max-w-lg overflow-hidden border border-white/10 backdrop-blur-xl"
                    @click.stop>
                    <div
                        class="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                        <h3 class="text-lg font-bold text-white flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">{{ isEditing ? 'edit' : 'add_business'
                                }}</span>
                            {{ isEditing ? 'Edit Hub' : 'Add New Hub' }}
                        </h3>
                        <button @click="closeModal"
                            class="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="p-6 space-y-4 bg-slate-950/95">
                        <div class="space-y-1">
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Hub
                                Code</label>
                            <input type="text" v-model="draftHub.hubCode" placeholder="e.g. HUB-NY-01"
                                class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                        </div>

                        <div class="space-y-1">
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Hub
                                Name</label>
                            <input type="text" v-model="draftHub.name" placeholder="North-East Distribution Center"
                                class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                        </div>

                        <div class="space-y-1">
                            <label
                                class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Location</label>
                            <input type="text" v-model="draftHub.location" placeholder="New York, NY"
                                class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                        </div>

                        <div class="space-y-1">
                            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Operating
                                Hours</label>
                            <input type="text" v-model="draftHub.operatingHours" placeholder="09:00 AM - 09:00 PM"
                                class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm font-mono text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label
                                    class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Manager
                                    Name</label>
                                <input type="text" v-model="draftHub.manager" placeholder="Alex Chen"
                                    class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                            </div>
                            <div class="space-y-1">
                                <label
                                    class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Capacity
                                    (%)</label>
                                <input type="number" v-model="draftHub.capacity" min="0" max="100" placeholder="92"
                                    class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:border-primary/50 transition-colors">
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label
                                class="text-xs font-semibold text-gray-500 uppercase tracking-wider block">Status</label>
                            <select v-model="draftHub.status"
                                class="w-full bg-slate-800 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:outline-none focus:border-primary/50 transition-colors">
                                <option value="Optimal" class="bg-slate-900 text-white">Optimal</option>
                                <option value="Active" class="bg-slate-900 text-white">Active</option>
                                <option value="Congested" class="bg-slate-900 text-white">Congested</option>
                            </select>
                        </div>
                    </div>

                    <div
                        class="p-6 border-t border-white/10 bg-slate-900/90 flex justify-end gap-3">
                        <button @click="closeModal" :disabled="isSavingHub"
                            class="px-5 py-2 rounded-lg text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 border border-white/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                            Cancel
                        </button>
                        <button @click="saveHub" :disabled="isSavingHub"
                            class="px-5 py-2 rounded-lg text-sm font-medium bg-primary hover:bg-primary/90 text-white transition-colors shadow-sm border border-primary/30 disabled:opacity-60 disabled:cursor-not-allowed">
                            {{ isSavingHub ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create Hub') }}
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'

const store = useLogisticStore()
const { hubs } = storeToRefs(store)
const toast = useToast()

// --- Search & Filtering ---
const searchQuery = ref('')
const statusFilter = ref('All')
const isFilterOpen = ref(false)

const setStatusFilter = (status) => {
    statusFilter.value = status
    isFilterOpen.value = false
}

const filteredHubs = computed(() => {
    return hubs.value.filter(hub => {
        // Status Filter
        if (statusFilter.value !== 'All' && hub.status !== statusFilter.value) {
            return false
        }

        // Search Filter
        if (searchQuery.value) {
            const query = searchQuery.value.toLowerCase()
            return (
                (hub.name && hub.name.toLowerCase().includes(query)) ||
                (hub.hubCode && hub.hubCode.toLowerCase().includes(query)) ||
                (hub.location && hub.location.toLowerCase().includes(query)) ||
                (hub.manager && hub.manager.toLowerCase().includes(query))
            )
        }

        return true
    })
})

// --- Computed Stats ---
const totalWarehouses = computed(() => hubs.value.length)
const congestedCount = computed(() => hubs.value.filter(h => h.status === 'Congested').length)
const avgCapacity = computed(() => {
    if (hubs.value.length === 0) return 0
    const total = hubs.value.reduce((sum, h) => sum + h.capacity, 0)
    return Math.round(total / hubs.value.length)
})

// --- Add / Edit Modal Logic ---
const isModalOpen = ref(false)
const isEditing = ref(false)
const isSavingHub = ref(false)

const draftHub = ref({
    id: null,
    hubCode: '',
    name: '',
    location: '',
    manager: '',
    capacity: 0,
    status: 'Optimal'
})

const openAddModal = () => {
    isEditing.value = false
    draftHub.value = {
        id: null,
        hubCode: '',
        name: '',
        location: '',
        manager: '',
        operatingHours: '09:00 AM - 09:00 PM',
        capacity: 0,
        status: 'Optimal'
    }
    isModalOpen.value = true
}

const openEditModal = (hub) => {
    isEditing.value = true
    draftHub.value = { ...hub }
    isModalOpen.value = true
}

const closeModal = () => {
    if (isSavingHub.value) return
    isModalOpen.value = false
}

const saveHub = async () => {
    if (!draftHub.value.name?.trim()) {
        toast.error('Hub name is required.')
        return
    }
    if (!draftHub.value.location?.trim() || draftHub.value.location.trim().length < 5) {
        toast.error('Location must be at least 5 characters.')
        return
    }

    // Generate initials from manager name
    const initials = (draftHub.value.manager || '')
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2)

    const payload = {
        ...draftHub.value,
        managerInitials: initials || 'UN'
    }

    isSavingHub.value = true

    try {
        if (isEditing.value) {
            await store.updateHub(payload)
            toast.success('Hub updated successfully.')
        } else {
            await store.addHub(payload)
            toast.success('Hub created successfully.')
        }

        closeModal()
    } catch (error) {
        toast.error(error.message || 'Unable to save hub right now.')
    } finally {
        isSavingHub.value = false
    }
}
</script>
