<template>
    <div class="max-w-4xl mx-auto space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Company Settings</h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Sidebar Tabs -->
            <div class="glass-panel p-4 rounded-xl space-y-1">
                <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
                    class="w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    :class="activeTab === tab.key ? 'bg-blue-600 text-white' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'">
                    <span class="material-symbols-outlined text-[16px]">{{ tab.icon }}</span>{{ tab.label }}
                </button>
            </div>

            <!-- Content -->
            <div class="md:col-span-2 glass-panel p-6 rounded-xl space-y-5">
                <!-- General Profile -->
                <div v-if="activeTab === 'general'" class="space-y-5">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm border-b border-gray-200 dark:border-white/10 pb-2">Company Profile</h3>
                    <div class="flex items-center gap-4">
                        <div class="w-16 h-16 bg-gray-100 dark:bg-white/5 rounded-lg flex items-center justify-center text-gray-400">
                            <span class="material-symbols-outlined text-3xl">business</span>
                        </div>
                        <button class="px-3 py-1.5 border border-gray-200 dark:border-white/10 rounded-lg text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors">Upload Logo</button>
                    </div>
                    <div class="grid grid-cols-1 gap-4">
                        <div>
                            <label class="text-xs text-gray-500 dark:text-gray-400 block mb-1.5">Company Name</label>
                            <input v-model="settings.companyName" type="text" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                        </div>
                        <div>
                            <label class="text-xs text-gray-500 dark:text-gray-400 block mb-1.5">Tax ID / GSTIN</label>
                            <input v-model="settings.taxId" type="text" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="text-xs text-gray-500 dark:text-gray-400 block mb-1.5">Contact Person</label>
                                <input v-model="settings.contactPerson" type="text" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                            <div>
                                <label class="text-xs text-gray-500 dark:text-gray-400 block mb-1.5">Phone</label>
                                <input v-model="settings.phone" type="tel" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            </div>
                        </div>
                        <div>
                            <label class="text-xs text-gray-500 dark:text-gray-400 block mb-1.5">Email</label>
                            <input v-model="settings.email" type="email" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                        </div>
                    </div>
                    <div class="pt-2 flex justify-end">
                        <button @click="saveGeneral" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-sm transition-colors">Save Changes</button>
                    </div>
                </div>

                <!-- Team Members -->
                <div v-if="activeTab === 'team'" class="space-y-5">
                    <div class="flex justify-between items-center border-b border-gray-200 dark:border-white/10 pb-2">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">Team Members</h3>
                        <button @click="showAddMember = true" class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">person_add</span> Add Member
                        </button>
                    </div>
                    <div class="space-y-3">
                        <div v-for="m in store.companySettings.teamMembers" :key="m.id" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="flex items-center gap-3">
                                <div class="w-9 h-9 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 text-sm font-bold">{{ m.name.charAt(0) }}</div>
                                <div>
                                    <div class="text-sm font-bold text-gray-900 dark:text-white">{{ m.name }}</div>
                                    <div class="text-[10px] text-gray-500">{{ m.email }}</div>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-500">{{ m.role }}</span>
                                <button @click="removeMember(m)" class="p-1 rounded hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors">
                                    <span class="material-symbols-outlined text-[16px]">close</span>
                                </button>
                            </div>
                        </div>
                        <div v-if="store.companySettings.teamMembers.length === 0" class="text-center py-8 text-gray-400 text-sm">No team members</div>
                    </div>
                </div>

                <!-- Notifications -->
                <div v-if="activeTab === 'notifications'" class="space-y-5">
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm border-b border-gray-200 dark:border-white/10 pb-2">Notification Preferences</h3>
                    <div class="space-y-4">
                        <div v-for="(val, key) in store.companySettings.notifications" :key="key" class="flex items-center justify-between">
                            <div>
                                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ notificationLabels[key] }}</div>
                                <div class="text-[10px] text-gray-500">{{ notificationDescs[key] }}</div>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" :checked="val" @change="toggleNotification(key)" class="sr-only peer">
                                <div class="w-9 h-5 bg-gray-300 dark:bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                    </div>
                    <div class="pt-2 flex justify-end">
                        <button @click="saveNotifications" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-sm transition-colors">Save Preferences</button>
                    </div>
                </div>

                <!-- API Keys -->
                <div v-if="activeTab === 'api'" class="space-y-5">
                    <div class="flex justify-between items-center border-b border-gray-200 dark:border-white/10 pb-2">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">API Keys</h3>
                        <button @click="generateKey" class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-[14px]">vpn_key</span> Generate Key
                        </button>
                    </div>
                    <div class="space-y-3">
                        <div v-for="key in store.companySettings.apiKeys" :key="key.id" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white">{{ key.name }}</div>
                                <div class="text-[10px] text-gray-500 font-mono">{{ key.key }}</div>
                                <div class="text-[10px] text-gray-400 mt-0.5">Created {{ key.created }}</div>
                            </div>
                            <div class="flex items-center gap-2">
                                <button @click="copyKey(key.key)" class="p-1.5 rounded hover:bg-blue-500/10 text-gray-400 hover:text-blue-500 transition-colors" title="Copy">
                                    <span class="material-symbols-outlined text-[16px]">content_copy</span>
                                </button>
                                <button @click="revokeKey(key)" class="p-1.5 rounded hover:bg-red-500/10 text-gray-400 hover:text-red-500 transition-colors" title="Revoke">
                                    <span class="material-symbols-outlined text-[16px]">delete</span>
                                </button>
                            </div>
                        </div>
                        <div v-if="store.companySettings.apiKeys.length === 0" class="text-center py-8 text-gray-400 text-sm">No API keys generated</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Member Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showAddMember" @close="showAddMember = false">
                <template #title>Add Team Member</template>
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Name *</label>
                        <input v-model="memberForm.name" type="text" placeholder="Full name" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Email *</label>
                        <input v-model="memberForm.email" type="email" placeholder="email@company.com" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">Role</label>
                        <select v-model="memberForm.role" class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-blue-500">
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Admin</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Manager</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Viewer</option>
                            <option class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Dispatcher</option>
                        </select>
                    </div>
                </div>
                <template #footer>
                    <button @click="showAddMember = false" class="px-4 py-2 text-gray-500 text-sm">Cancel</button>
                    <button @click="addMember" :disabled="!memberForm.name || !memberForm.email" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50">Add Member</button>
                </template>
            </BaseModal>
        </Teleport>
    </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'
import BaseModal from '@/components/BaseModal.vue'

const store = useVendorStore()
const activeTab = ref('general')
const showAddMember = ref(false)

const tabs = [
    { key: 'general', label: 'General Profile', icon: 'business' },
    { key: 'team', label: 'Team Members', icon: 'group' },
    { key: 'notifications', label: 'Notifications', icon: 'notifications' },
    { key: 'api', label: 'API Keys', icon: 'vpn_key' },
]

const settings = reactive({
    companyName: store.companySettings.companyName,
    taxId: store.companySettings.taxId,
    contactPerson: store.companySettings.contactPerson,
    phone: store.companySettings.phone,
    email: store.companySettings.email,
})

const memberForm = ref({ name: '', email: '', role: 'Viewer' })

const newKeyName = ref('')

const notificationLabels = {
    email: 'Email Alerts',
    sms: 'SMS Alerts',
    push: 'Push Notifications',
    orderUpdates: 'Order Updates',
    invoiceAlerts: 'Invoice Reminders',
    promotions: 'Marketing & Promotions',
}

const notificationDescs = {
    email: 'Receive critical alerts via email',
    sms: 'Get SMS for high-priority events',
    push: 'Browser and mobile push notifications',
    orderUpdates: 'Real-time shipment & order status changes',
    invoiceAlerts: 'Reminders for unpaid invoices',
    promotions: 'Product updates and offers',
}

async function saveGeneral() {
    await store.updateCompanySettings(settings)
    showToast('Profile updated')
}

async function addMember() {
    if (!memberForm.value.name || !memberForm.value.email) return
    await store.addTeamMember({ ...memberForm.value })
    showAddMember.value = false
    memberForm.value = { name: '', email: '', role: 'Viewer' }
    showToast('Member added')
}

async function removeMember(m) {
    if (!confirm(`Remove ${m.name}?`)) return
    await store.removeTeamMember(m.id)
    showToast('Member removed')
}

function toggleNotification(key) {
    store.companySettings.notifications[key] = !store.companySettings.notifications[key]
}

async function saveNotifications() {
    await store.updateCompanySettings(settings)
    showToast('Notification preferences saved')
}

async function generateKey() {
    const name = newKeyName.value.trim() || `Key ${store.companySettings.apiKeys.length + 1}`
    await store.generateApiKey(name)
    newKeyName.value = ''
    showToast('API key generated')
}

async function revokeKey(key) {
    if (!confirm(`Revoke key "${key.name}"?`)) return
    await store.revokeApiKey(key.id)
    showToast('API key revoked')
}

function copyKey(key) {
    navigator.clipboard.writeText(key)
    showToast('Copied to clipboard')
}

function showToast(msg) {
    const t = document.createElement('div')
    t.className = 'fixed right-4 bottom-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

onMounted(async () => {
    await store.initializeVendorData().catch(() => {})
    Object.assign(settings, {
        companyName: store.companySettings.companyName,
        taxId: store.companySettings.taxId,
        contactPerson: store.companySettings.contactPerson,
        phone: store.companySettings.phone,
        email: store.companySettings.email,
    })
})

</script>
