<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">User & Role Management</h2>
            <button @click="openModal('create')"
                class="bg-slate-900 hover:bg-slate-800 dark:bg-primary dark:hover:bg-primary/90 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors shadow-lg border border-slate-700 dark:border-primary/30">
                <span class="material-symbols-outlined">person_add</span>
                Create Manager / Dispatcher
            </button>
        </div>

        <!-- Role Filter Tabs -->
        <div class="flex gap-4 border-b border-gray-200 dark:border-white/10 pb-1">
            <button v-for="tab in tabs" :key="tab" class="px-4 py-2 text-sm font-medium transition-colors relative"
                :class="activeTab === tab ? 'text-primary' : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'"
                @click="activeTab = tab">
                {{ tab }}
                <div v-if="activeTab === tab"
                    class="absolute bottom-[-5px] left-0 w-full h-1 bg-primary rounded-t-full"></div>
            </button>
        </div>

        <!-- User List -->
        <div class="glass-panel rounded-xl overflow-hidden p-6">
            <UserCardsGrid />

            <!-- User Form Modal -->
            <Teleport to="body">
                <div v-if="isModalOpen"
                    class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
                    @click.self="closeModal">
                    <div
                        class="lm-user-form-modal bg-slate-950/98 w-full max-w-4xl rounded-2xl shadow-2xl border border-white/10 overflow-visible flex flex-col backdrop-blur-xl">
                        <!-- Header -->
                        <div
                            class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                            <h3 class="text-lg font-bold text-white">
                                {{ modalMode === 'create' ? 'Create Manager / Dispatcher' :
                                    (modalMode === 'create-support' ? 'Create Customer Support' :
                                        (modalMode === 'create-driver' ? 'Create Driver Profile' :
                                            (modalMode === 'edit-profile' ? `Edit Profile: ${formData.role || 'User'}` :
                                                `Edit Access: ${formData.role || 'User'}`))) }}
                            </h3>
                            <button @click="closeModal"
                                class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <!-- Body / Form -->
                        <div class="p-6 overflow-y-auto overflow-x-visible space-y-4 max-h-[78vh] bg-slate-950/95">

                            <!-- === CREATE MODE: Strict Form === -->
                            <template v-if="modalMode === 'create'">
                                <CreateStaffFields />
                            </template>

                            <!-- === CREATE SUPPORT MODE === -->
                            <template v-else-if="modalMode === 'create-support'">
                                <CreateSupportFields />
                            </template>

                            <!-- Common Fields for Creation (shared by Manager/Dispatcher and Support) -->
                            <!-- === UNIFIED FORM TABS OR SECTIONS === -->
                            <template
                                v-if="['create', 'create-support', 'create-driver', 'edit-profile'].includes(modalMode)">

                                <ProfileFormSections />
                            </template>

                            <!-- === EDIT ACCESS MODE === -->
                            <template v-else>
                                <EditAccessFields />
                            </template>

                            <DriverCredentialsFields />
                        </div>

                        <!-- Footer -->
                        <div
                            class="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/90">
                            <button @click="closeModal"
                                class="px-4 py-2 rounded-lg font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 dark:bg-white/10 dark:border-white/10 dark:text-gray-200 dark:hover:bg-white/15 transition-colors shadow-sm">
                                Cancel
                            </button>
                            <button @click="submitForm"
                                class="px-4 py-2 rounded-lg font-medium text-white bg-primary hover:bg-primary/90 transition-colors shadow-sm">
                                {{ modalMode === 'create' || modalMode === 'create-support' || modalMode ===
                                    'create-driver' ? 'Add User' :
                                    'Save Changes' }}
                            </button>
                        </div>
                    </div>
                </div>
            </Teleport>

            <CredentialsModal />

            <VendorReviewModal />


            <OtpModal />
        </div>
    </div>
</template>

<script setup>
import UserCardsGrid from './userManagement/UserCardsGrid.vue'
import CreateStaffFields from './userManagement/CreateStaffFields.vue'
import CreateSupportFields from './userManagement/CreateSupportFields.vue'
import ProfileFormSections from './userManagement/ProfileFormSections.vue'
import EditAccessFields from './userManagement/EditAccessFields.vue'
import DriverCredentialsFields from './userManagement/DriverCredentialsFields.vue'
import CredentialsModal from './userManagement/CredentialsModal.vue'
import VendorReviewModal from './userManagement/VendorReviewModal.vue'
import OtpModal from './userManagement/OtpModal.vue'
import {
    approvalBadgeClass,
    avatarGradient,
    emptyStaffForm,
    filterUsersByTab,
    formatApprovalStatus,
    formatLastLogin,
    formatSubmittedAt,
    getInitials,
    isVendorRequest,
    normalizeFieldValue,
} from './userManagement/userFields'
import { userManagementPageKey } from './userManagement/userManagementPageContext'
import { ref, computed, provide } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'

const store = useLogisticStore()
const { filteredUsers } = storeToRefs(store)
const toast = useToast()

const activeTab = ref('All Users')
const tabs = ['All Users', 'Vendor Requests', 'Managers', 'Dispatchers', 'Drivers', 'Support']

const displayedUsers = computed(() => filterUsersByTab(filteredUsers.value, activeTab.value))
// --- Dropdown Management ---
import { onMounted, onUnmounted } from 'vue'

const activeDropdown = ref(null)
const isHubMenuOpen = ref(false)

const toggleDropdown = (email) => {
    activeDropdown.value = activeDropdown.value === email ? null : email
}

const closeDropdowns = () => {
    activeDropdown.value = null
    isHubMenuOpen.value = false
}

onMounted(() => {
    document.addEventListener('click', closeDropdowns)
})
onUnmounted(() => {
    document.removeEventListener('click', closeDropdowns)
})

// --- Modal Management ---
const isModalOpen = ref(false)
const modalMode = ref('create')
const isCredentialsVisible = ref(false)

const strictFields = {
    name: { label: 'Full Name', type: 'text', placeholder: 'e.g. John Doe' },
    dob: { label: 'Date of Birth', type: 'date', placeholder: '' },
    mobile: { label: 'Mobile Number', type: 'tel', placeholder: '+1 (555) 000-0000' },
    email: { label: 'Email Address', type: 'email', placeholder: 'john@cargocore.com' },
    aadharCard: { label: 'Aadhar / ID Number', type: 'text', placeholder: 'XXXX-XXXX-XXXX' },
    panCard: { label: 'PAN Number', type: 'text', placeholder: 'ABCDE1234F' },
    bankAccount: { label: 'Bank Account Number', type: 'text', placeholder: '000011112222' },
    ifscCode: { label: 'IFSC / Routing Code', type: 'text', placeholder: 'BANK0001234' },
    address: { label: 'Address', type: 'text', placeholder: '123 Main St' },
    city: { label: 'City', type: 'text', placeholder: 'e.g. Austin' },
    state: { label: 'State', type: 'text', placeholder: 'e.g. TX' },
    pincode: { label: 'Pincode / ZIP', type: 'text', placeholder: '00000' },
    emergencyContact: { label: 'Emergency Contact', type: 'tel', placeholder: '+1 000-0000' },
    bloodGroup: { label: 'Blood Group', type: 'text', placeholder: 'O+' },
    dateOfJoining: { label: 'Date of Joining', type: 'date', placeholder: '' }
}

// OTP State
const isOtpModalOpen = ref(false)
const otpField = ref('') // 'mobile' or 'email'
const otpValue = ref('')
const otpError = ref('')

const openOtpModal = (field) => {
    otpField.value = field
    otpValue.value = ''
    otpError.value = ''
    isOtpModalOpen.value = true
}

const verifyOtp = () => {
    if (otpValue.value === '1234') {
        if (otpField.value === 'mobile') formData.value.mobileVerified = true
        if (otpField.value === 'email') formData.value.emailVerified = true
        isOtpModalOpen.value = false
    } else {
        otpError.value = 'Invalid OTP. Use 1234.'
    }
}

const formData = ref({})
const unlockedFields = ref({})
const assignableHubs = computed(() => store.activeHubs || store.hubs.filter((hub) => hub.status !== 'Archived'))
const hubOptionsForEdit = computed(() => {
    const selectedHub = store.hubs.find((hub) => hub.id === formData.value.hubId)
    if (!selectedHub || assignableHubs.value.some((hub) => hub.id === selectedHub.id)) {
        return assignableHubs.value
    }
    return [...assignableHubs.value, selectedHub]
})
const defaultHubId = () => {
    if (store.activeWarehouse !== 'all' && assignableHubs.value.some((hub) => hub.id === store.activeWarehouse)) {
        return store.activeWarehouse
    }
    return assignableHubs.value[0]?.id || null
}

const initEmptyForm = (mode) => {
    const blank = emptyStaffForm(mode, defaultHubId())
    if (blank) formData.value = blank
    unlockedFields.value = {}
    Object.keys(strictFields).forEach(key => {
        formData.value[key] = ''
        unlockedFields.value[key] = false // All locked by default
    })
}

const formatField = (key) => {
    const val = formData.value[key]
    if (!val) return
    formData.value[key] = normalizeFieldValue(key, val)
}
const roles = ['Warehouse Manager', 'Dispatcher', 'Driver', 'Customer Support']
const statuses = ['Active', 'Inactive']
const selectedHubLabel = computed(() => {
    const selectedHub = store.hubs.find((hub) => hub.id === formData.value.hubId)
    return selectedHub?.name || 'Select a hub'
})

const toggleHubMenu = () => {
    isHubMenuOpen.value = !isHubMenuOpen.value
}

const selectHub = (hubId) => {
    formData.value.hubId = hubId
    isHubMenuOpen.value = false
}

// Credential View Modal
const viewingUserCreds = ref(null)
const reviewingVendor = ref(null)

const openCreds = (user, reveal = false) => {
    viewingUserCreds.value = user
    isCredentialsVisible.value = reveal
}

const closeCreds = () => { viewingUserCreds.value = null; store.clearCreatedCredentials() }

const openVendorReview = (user) => {
    reviewingVendor.value = user
    activeDropdown.value = null
}

const closeVendorReview = () => {
    reviewingVendor.value = null
}

const openModal = (mode, user = null) => {
    modalMode.value = mode
    isCredentialsVisible.value = false
    isHubMenuOpen.value = false

    if (mode === 'edit-profile' || mode === 'edit-access') {
        formData.value = {
            ...user,
            mobileVerified: user.mobileVerified ?? true, // mock existing users as verified
            emailVerified: user.emailVerified ?? true
        } // copy data

    } else {
        initEmptyForm(mode) // Pass mode to initEmptyForm
    }
    isModalOpen.value = true
}

const closeModal = () => {
    isModalOpen.value = false
    isHubMenuOpen.value = false
}

const handleVendorApproval = async (user, nextStatus) => {
    activeDropdown.value = null
    try {
        if (nextStatus === 'APPROVED') {
            await store.approveVendor(user.id)
            toast.success(`${user.companyName || user.name} approved successfully.`)
        } else {
            await store.rejectVendor(user.id)
            toast.success(`${user.companyName || user.name} rejected.`)
        }
        if (reviewingVendor.value?.id === user.id) {
            closeVendorReview()
        }
    } catch (error) {
        toast.error(error.message || 'Unable to update this vendor request right now.')
    }
}

const submitForm = async () => {
    try {
        if (['create', 'create-support'].includes(modalMode.value)) {
            if (!formData.value.username?.trim()) {
                toast.error('Username is required for this account.')
                return
            }
            if (!formData.value.password || formData.value.password.length < 8) {
                toast.error('Password must be at least 8 characters long.')
                return
            }
        }

        if (modalMode.value === 'create-driver') {
            if (!formData.value.username?.trim()) {
                toast.error('Driver ID is required.')
                return
            }
            if (!formData.value.password || !/^\d{4}$/.test(formData.value.password)) {
                toast.error('PIN must be exactly 4 digits.')
                return
            }
        }

        if (modalMode.value === 'create' || modalMode.value === 'create-support' || modalMode.value === 'create-driver') {
            if (!formData.value.hubId || formData.value.hubId === 'all') {
                toast.error('Please assign the user to a warehouse hub.')
                return
            }
            const selectedHub = store.hubs.find((hub) => hub.id === formData.value.hubId)
            if (!selectedHub || selectedHub.status === 'Archived') {
                toast.error('Archived hubs cannot receive new user assignments.')
                return
            }
            await store.addUser({
                ...formData.value,
                lastLogin: 'Never',
            })
            toast.success(`${formData.value.role} account created successfully.`)
        } else {
            await store.updateUser(formData.value.email, { ...formData.value })
            toast.success('User details updated successfully.')
        }
        closeModal()
        const fresh = store.lastCreatedCredentials // in memory only: shown once, cleared when the dialog closes
        if (fresh) openCreds({ ...store.users.find((user) => user.email === fresh.email), ...fresh }, true)
    } catch (error) {
        toast.error(error.message || 'Unable to save the user right now.')
    }
}

provide(userManagementPageKey, {
    activeDropdown,
    activeTab,
    approvalBadgeClass,
    assignableHubs,
    avatarGradient,
    closeCreds,
    closeVendorReview,
    displayedUsers,
    formData,
    formatApprovalStatus,
    formatField,
    formatLastLogin,
    formatSubmittedAt,
    getInitials,
    handleVendorApproval,
    hubOptionsForEdit,
    isCredentialsVisible,
    isHubMenuOpen,
    isOtpModalOpen,
    isVendorRequest,
    modalMode,
    openCreds,
    openModal,
    openOtpModal,
    openVendorReview,
    otpError,
    otpField,
    otpValue,
    reviewingVendor,
    roles,
    selectHub,
    selectedHubLabel,
    statuses,
    store,
    toggleDropdown,
    toggleHubMenu,
    verifyOtp,
    viewingUserCreds,
})
</script>

<style scoped>
.lm-user-form-modal {
    color: #e2e8f0;
}

.lm-user-form-modal :deep(h3),
.lm-user-form-modal :deep(h4) {
    color: #ffffff !important;
}

.lm-user-form-modal :deep(label) {
    color: #cbd5e1 !important;
}

.lm-user-form-modal :deep(input),
.lm-user-form-modal :deep(select),
.lm-user-form-modal :deep(textarea) {
    background-color: rgba(15, 23, 42, 0.92) !important;
    color: #f8fafc !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color-scheme: dark;
}

.lm-user-form-modal :deep(input::placeholder),
.lm-user-form-modal :deep(textarea::placeholder) {
    color: #94a3b8 !important;
}

.lm-user-form-modal :deep(.text-gray-400),
.lm-user-form-modal :deep(.text-gray-500) {
    color: #94a3b8 !important;
}

.lm-user-form-modal :deep(input[type='date']::-webkit-calendar-picker-indicator) {
    filter: invert(1);
    opacity: 0.85;
}
</style>
