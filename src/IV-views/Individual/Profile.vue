<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">My Profile</h2>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Profile Card -->
            <div class="glass-panel p-4 sm:p-6 rounded-xl text-center">
                <div @click="avatarModal = true" class="relative w-24 h-24 mx-auto mb-4 cursor-pointer group">
                    <div v-if="store.user.avatar"
                        class="w-full h-full rounded-full bg-gray-50 dark:bg-white/5 flex items-center justify-center text-5xl ring-4 ring-green-500/20 shadow-lg">
                        {{ store.user.avatar }}
                    </div>
                    <div v-else
                        class="w-full h-full rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-3xl font-bold text-white ring-4 ring-green-500/20 shadow-lg">
                        {{ store.userInitials }}
                    </div>
                    <div
                        class="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <span class="material-symbols-outlined text-white">edit</span>
                    </div>
                </div>
                <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ store.user.name }}</h3>
                <p class="text-gray-500 dark:text-gray-400 text-sm font-medium">{{ store.user.tier }}</p>
                <div
                    class="mt-2 text-xs bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400 px-3 py-1 rounded-full inline-block font-bold">
                    Joined {{ formatJoinDate(store.user.joiningDate) }}</div>

                <div class="mt-6 mb-6 space-y-3 text-sm text-left px-2">

                </div>

                <div class="grid grid-cols-2 gap-3 mb-6">
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xl font-bold text-green-600 dark:text-green-400">{{ apiStats?.total_orders || 0 }}
                        </div>
                        <div class="text-xs text-gray-500">Total Moves</div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                        <div class="text-xl font-bold text-blue-600 dark:text-blue-400">₹{{
                            Number(apiStats?.total_spent || 0).toLocaleString() }}</div>
                        <div class="text-xs text-gray-500">Total Spent</div>
                    </div>
                </div>

                <!-- Spending Chart -->
                <div class="mt-8 pt-6 border-t border-gray-100 dark:border-white/5 text-left">
                    <div class="flex justify-between items-baseline mb-4">
                        <h4 class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">6-Month
                            Spending History</h4>
                        <span class="text-[10px] text-gray-400 dark:text-gray-500">Powered by Cargo-Core.pvt.ltd</span>
                    </div>

                    <div class="h-64 w-full">
                        <Line :data="chartData" :options="chartOptions" />
                    </div>

                    <div class="mt-4 space-y-2">
                        <div
                            class="p-2.5 bg-gray-50/50 dark:bg-white/5 rounded-lg border border-gray-100 dark:border-white/5">
                            <p class="text-[10px] text-gray-500 dark:text-gray-400 leading-relaxed italic">
                                * This is an estimated spending history based on your completed moves.
                            </p>
                        </div>
                        <div class="text-center pt-1">
                            <span
                                class="text-[10px] font-black text-green-600/40 dark:text-green-400/30 uppercase tracking-[0.2em]">Moving
                                what Matters</span>
                        </div>
                    </div>
                </div>

            </div>

            <!-- Edit Profile Form -->
            <div class="lg:col-span-2 space-y-6">
                <div class="glass-panel p-4 sm:p-6 rounded-xl">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4">Personal Information</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Full
                                Name</label>
                            <input v-model="form.name" type="text"
                                class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
                        </div>
                        <div>
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Email
                                Address</label>
                            <input v-model="form.email" type="email"
                                class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
                        </div>
                        <div>
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Phone
                                Number</label>
                            <input v-model="form.phone" type="tel"
                                class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Primary
                                Address</label>
                            <input v-model="form.address" type="text" placeholder="Enter your primary address"
                                class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
                            <p v-if="!form.address" class="text-xs text-amber-600 dark:text-amber-400 mt-1">No address provided yet. Please add your primary address.</p>
                        </div>
                    </div>
                    <button @click="saveProfile"
                        class="mt-4 px-6 py-2.5 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-colors text-sm">
                        Save Changes
                    </button>
                </div>
            </div>
        </div>

        <!-- Avatar Selection Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="avatarModal" @close="avatarModal = false">
                <template #title>Choose Avatar</template>
                <div
                    class="grid grid-cols-4 sm:grid-cols-5 gap-3 py-4 max-h-[60vh] overflow-y-auto custom-scrollbar pr-2">
                    <button v-for="emoji in presetAvatars" :key="emoji" @click="selectAvatar(emoji)"
                        class="text-4xl p-3 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 transition-all transform hover:scale-110 border border-transparent hover:border-green-500/50 flex items-center justify-center bg-gray-50/50 dark:bg-white/5">
                        {{ emoji }}
                    </button>
                </div>
                <template #footer>
                    <button @click="avatarModal = false"
                        class="w-full py-2 bg-gray-100 hover:bg-gray-200 dark:bg-white/5 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-lg transition-colors">Close</button>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl text-white border max-w-sm"
                    :class="toast.type === 'error' ? 'bg-red-600 border-red-500' : 'bg-green-600 border-green-500'">
                    <span class="material-symbols-outlined">{{ toast.type === 'error' ? 'error' : 'check_circle' }}</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler } from 'chart.js'
import BaseModal from '@/components/BaseModal.vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler)

const store = useIndividualStore()

const apiStats = computed(() => store.dashboardSummary?.stats || null)

const form = reactive({
    name: store.user.name,
    email: store.user.email,
    phone: store.user.phone,
    address: store.user.address || '',
})

async function saveProfile() {
    const result = await store.saveProfileRemote({
        name: form.name,
        email: form.email,
        phone: form.phone,
        address: form.address
    })
    if (result.success) {
        showToast('Profile updated successfully!', 'success')
    } else {
        let errMsg = result.message || 'Failed to update profile.'
        if (Array.isArray(errMsg)) errMsg = errMsg.map(e => e.msg).join(', ')
        else if (typeof errMsg === 'object') errMsg = JSON.stringify(errMsg)
        showToast(errMsg, 'error')
    }
}

// Chart Data
const chartData = computed(() => {
    const monthlyActivity = store.dashboardSummary?.monthly_activity || []

    // If we have API data, use it
    if (monthlyActivity.length > 0) {
        return {
            labels: monthlyActivity.map(d => d.month),
            datasets: [{
                label: 'Orders',
                data: monthlyActivity.map(d => d.count),
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#22c55e',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#16a34a',
                fill: true,
                tension: 0.4
            }]
        }
    }

    // Fallback to static data if no API data available
    return {
        labels: store.monthlySpending.map(d => d.month),
        datasets: [{
            label: 'Spent (₹)',
            data: store.monthlySpending.map(d => d.amount),
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            borderWidth: 2,
            pointBackgroundColor: '#22c55e',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#16a34a',
            fill: true,
            tension: 0.4
        }]
    }
})

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 10,
            displayColors: false,
            callbacks: {
                label: (ctx) => `₹${ctx.raw.toLocaleString()}`
            }
        }
    },
    scales: {
        x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } },
        y: { display: false, min: 0 }
    },
    interaction: { intersect: false, mode: 'index' }
}

// Avatar Logistics
const avatarModal = ref(false)
const presetAvatars = [
    '👨', '👩', '🧑', '👨‍🦱', '👩‍🦱', '🧔', '👱‍♂️', '👱‍♀️',
    '👨‍🦰', '👩‍🦰', '👨‍🦳', '👩‍🦳', '👨‍🦲', '👩‍🦲', '😎', '🤓',
    '🤠', '👽', '🤖', '👻', '🐻', '🐼', '🦊', '🦁'
]

function selectAvatar(emoji) {
    store.updateProfile({ avatar: emoji })
    avatarModal.value = false
    showToast('Avatar updated!')
}

const toast = reactive({ show: false, message: '', type: 'success' })
function showToast(msg, type = 'success') { 
    toast.show = true; 
    toast.message = msg; 
    toast.type = type;
    setTimeout(() => { toast.show = false }, 3000) 
}

function formatJoinDate(dateString) {
    if (!dateString) return 'Recently'

    try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    } catch {
        return 'Recently'
    }
}

onMounted(async () => {
    await Promise.all([
        store.fetchProfile(),
        store.fetchDashboardSummary()
    ])
    form.name = store.user.name
    form.email = store.user.email
    form.phone = store.user.phone
    form.address = store.user.address || ''
})
</script>
