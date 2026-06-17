<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>

        <div v-if="settingsError" class="glass-panel p-4 rounded-xl border border-red-200/70 dark:border-red-500/20">
            <div class="flex items-start gap-3 text-red-600 dark:text-red-400">
                <span class="material-symbols-outlined">error</span>
                <div>
                    <div class="text-sm font-semibold">Unable to load settings</div>
                    <div class="text-xs opacity-90">{{ settingsError }}</div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Notification Preferences -->
            <div class="glass-panel p-4 sm:p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-500">notifications</span>
                    Notification Preferences
                </h3>
                <div v-if="isInitialLoading" class="space-y-3">
                    <div v-for="index in 5" :key="index" class="h-12 rounded-lg bg-gray-100 dark:bg-white/5 animate-pulse"></div>
                </div>
                <div v-else class="space-y-4">
                    <div v-for="pref in notificationOptions" :key="pref.key" class="flex items-center justify-between">
                        <div>
                            <div class="text-sm font-medium text-gray-900 dark:text-white">{{ pref.label }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">{{ pref.desc }}</div>
                        </div>
                        <button @click="togglePreference('notification_prefs', pref.key)"
                            :disabled="isSaving"
                            class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                            :class="settings.notification_prefs[pref.key] ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                            <span
                                class="inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                                :class="settings.notification_prefs[pref.key] ? 'translate-x-5' : 'translate-x-0'"></span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Privacy & Data -->
            <div class="glass-panel p-4 sm:p-6 rounded-xl">
                <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-500">shield</span>
                    Privacy & Data
                </h3>
                <div v-if="isInitialLoading" class="space-y-3">
                    <div v-for="index in 3" :key="index" class="h-12 rounded-lg bg-gray-100 dark:bg-white/5 animate-pulse"></div>
                </div>
                <div v-else class="space-y-4">
                    <div v-for="pref in privacyOptions" :key="pref.key" class="flex items-center justify-between">
                        <div>
                            <div class="text-sm font-medium text-gray-900 dark:text-white">{{ pref.label }}</div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">{{ pref.desc }}</div>
                        </div>
                        <button @click="togglePreference('privacy_prefs', pref.key)"
                            :disabled="isSaving"
                            class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out"
                            :class="settings.privacy_prefs[pref.key] ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'">
                            <span
                                class="inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                                :class="settings.privacy_prefs[pref.key] ? 'translate-x-5' : 'translate-x-0'"></span>
                        </button>
                    </div>
                    <button @click="deleteAccount" :disabled="isDeleting || isSaving"
                        class="w-full py-2 bg-red-500/10 text-red-600 dark:text-red-400 rounded-lg text-sm font-bold hover:bg-red-500/20 transition-colors disabled:opacity-60 disabled:cursor-not-allowed">
                        {{ isDeleting ? 'Deleting Account...' : 'Delete Account' }}
                    </button>
                </div>
            </div>
        </div>

        <div class="flex justify-end">
            <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ statusText }}
            </div>
        </div>

        <BaseModal :isOpen="showDeleteModal" @close="closeDeleteModal">
            <template #title>Delete Account</template>

            <div class="space-y-5">
                <div class="flex items-start gap-4">
                    <div class="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500 text-white flex items-center justify-center shadow-lg shadow-red-500/20 overflow-hidden">
                        <div class="absolute inset-[6px] rounded-xl border border-white/20 bg-white/10"></div>
                        <span class="material-symbols-outlined relative text-[30px] drop-shadow-[0_2px_6px_rgba(0,0,0,0.25)]">warning_amber</span>
                    </div>
                    <div class="space-y-2">
                        <p class="text-base font-semibold text-white">This action will deactivate your customer account.</p>
                        <p class="text-sm leading-6 text-slate-300">
                            You will be signed out immediately and will no longer be able to access this account unless it is reactivated later by support.
                        </p>
                    </div>
                </div>

                <div class="rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
                    <div class="flex items-start gap-3">
                        <div class="w-9 h-9 rounded-full border border-red-400/30 bg-red-500/10 flex items-center justify-center flex-shrink-0">
                            <span class="material-symbols-outlined text-[20px] text-red-400">priority_high</span>
                        </div>
                        <div class="space-y-1">
                            <p class="text-sm font-semibold text-red-300">Please confirm carefully</p>
                            <p class="text-sm text-red-100/80">
                                Your saved settings and access will be disabled as soon as you continue.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <button @click="closeDeleteModal"
                    class="px-4 py-2 rounded-xl text-sm font-semibold text-slate-300 hover:bg-white/5 transition-colors">
                    Keep Account
                </button>
                <button @click="confirmDeleteAccount" :disabled="isDeleting"
                    class="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-500 hover:to-orange-400 transition-all shadow-lg shadow-red-900/30 disabled:opacity-60 disabled:cursor-not-allowed">
                    {{ isDeleting ? 'Deleting...' : 'Yes, Delete Account' }}
                </button>
            </template>
        </BaseModal>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl bg-green-600 text-white border border-green-500 max-w-sm">
                    <span class="material-symbols-outlined">check_circle</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import BaseModal from '@/components/BaseModal.vue'
import { useIndividualStore } from '@/stores/individualStore'

const router = useRouter()
const authStore = useAuthStore()
const store = useIndividualStore()
const isSaving = ref(false)
const isDeleting = ref(false)
const showDeleteModal = ref(false)
const hasLoadedSettings = ref(false)
const lastSyncedAt = ref('')

const settings = reactive({
    language: 'en',
    currency: 'INR',
    default_payment: 'Full Payment',
    notification_prefs: {
        push: true,
        sms: true,
        email: true,
        geofence: true,
        promo: false,
    },
    privacy_prefs: {
        location: true,
        analytics: true,
        marketing: false,
    },
})

const notificationOptions = [
    { key: 'push', label: 'Push Notifications', desc: 'Get alerts on your device' },
    { key: 'sms', label: 'SMS Alerts', desc: 'Receive text message updates' },
    { key: 'email', label: 'Email Updates', desc: 'Order confirmations and receipts' },
    { key: 'geofence', label: 'Geofence Alerts', desc: 'When driver is near your location' },
    { key: 'promo', label: 'Promotional Offers', desc: 'Discounts and special deals' },
]

const privacyOptions = [
    { key: 'location', label: 'Location Sharing', desc: 'Share location for accurate pickup' },
    { key: 'analytics', label: 'Usage Analytics', desc: 'Help us improve with anonymized data' },
    { key: 'marketing', label: 'Marketing Emails', desc: 'Receive marketing communications' },
]

const toast = reactive({ show: false, message: '' })
function showToast(msg) { toast.show = true; toast.message = msg; setTimeout(() => { toast.show = false }, 3000) }

const settingsLoading = computed(() => store.settingsLoading)
const settingsError = computed(() => store.settingsError)
const isInitialLoading = computed(() => settingsLoading.value && !hasLoadedSettings.value)
const statusText = computed(() => {
    if (isDeleting.value) return 'Deleting account...'
    if (isSaving.value) return 'Saving changes to backend...'
    if (lastSyncedAt.value) return `Synced with backend at ${lastSyncedAt.value}`
    if (hasLoadedSettings.value) return 'Live customer settings loaded from backend.'
    return 'Loading live customer settings...'
})

function applySettings(data = {}) {
    settings.language = data.language || 'en'
    settings.currency = data.currency || 'INR'
    settings.default_payment = data.default_payment || 'Full Payment'
    settings.notification_prefs = {
        ...settings.notification_prefs,
        ...(data.notification_prefs || {}),
    }
    settings.privacy_prefs = {
        ...settings.privacy_prefs,
        ...(data.privacy_prefs || {}),
    }
}

async function saveSettings() {
    isSaving.value = true
    const result = await store.saveSettingsRemote({
        language: settings.language,
        currency: settings.currency,
        default_payment: settings.default_payment,
        notification_prefs: { ...settings.notification_prefs },
        privacy_prefs: { ...settings.privacy_prefs },
    })
    isSaving.value = false
    if (result.success && result.data) {
        applySettings(result.data)
        lastSyncedAt.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    showToast(result.success ? 'Settings saved successfully!' : (result.message || 'Failed to save settings.'))
    return result
}

async function togglePreference(groupName, key) {
    const currentValue = settings[groupName][key]
    settings[groupName][key] = !currentValue

    const result = await saveSettings()
    if (!result.success) {
        settings[groupName][key] = currentValue
    }
}

function deleteAccount() {
    showDeleteModal.value = true
}

function closeDeleteModal() {
    if (isDeleting.value) return
    showDeleteModal.value = false
}

async function confirmDeleteAccount() {
    isDeleting.value = true
    const result = await store.deleteAccountRemote()
    isDeleting.value = false

    if (!result.success) {
        showDeleteModal.value = false
        showToast(result.message || 'Failed to delete account.')
        return
    }

    showDeleteModal.value = false
    showToast(result.message || 'Account deleted successfully.')
    authStore.logout()
    await router.replace('/login')
}

onMounted(async () => {
    const result = await store.fetchSettings()
    if (result.success && result.data) {
        applySettings(result.data)
        lastSyncedAt.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    hasLoadedSettings.value = true
})
</script>
