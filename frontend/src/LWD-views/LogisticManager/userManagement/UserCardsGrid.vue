<template>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
        <!-- User Card -->
        <div v-for="user in displayedUsers" :key="user.email"
            class="bg-gray-50 dark:bg-white/5 rounded-xl p-4 border border-gray-200 dark:border-white/5 hover:border-primary/50 dark:hover:border-primary/30 transition-all group relative shadow-sm flex flex-col gap-3 self-start">

            <!-- Top row: avatar + name/contact + actions -->
            <div class="flex items-start gap-3">
                <!-- Initials avatar -->
                <div class="w-11 h-11 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0 select-none"
                    :style="{ background: avatarGradient(user.name) }">
                    {{ getInitials(user.name) }}
                </div>

                <!-- Name + contact details -->
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="font-bold text-gray-900 dark:text-white text-sm leading-tight">{{ user.name }}</span>
                        <span v-if="user.mobileVerified && user.emailVerified"
                            class="text-green-500 material-symbols-outlined text-[15px]"
                            title="Fully Verified">verified</span>
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5">
                        <span class="material-symbols-outlined text-[13px] flex-shrink-0">mail</span>
                        <span class="break-all leading-tight">{{ user.email }}</span>
                        <span v-if="user.emailVerified"
                            class="material-symbols-outlined text-[13px] text-green-500 flex-shrink-0">check_circle</span>
                    </div>
                    <div v-if="user.mobile"
                        class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5">
                        <span class="material-symbols-outlined text-[13px] flex-shrink-0">call</span>
                        <span>{{ user.mobile }}</span>
                        <span v-if="user.mobileVerified"
                            class="material-symbols-outlined text-[13px] text-green-500 flex-shrink-0">check_circle</span>
                    </div>
                </div>

                <!-- Actions -->
                <div class="relative flex items-center gap-0.5 flex-shrink-0" @click.stop>
                    <button v-if="user.username" @click="openCreds(user)"
                        class="text-gray-400 hover:text-primary transition-colors p-1 rounded-full hover:bg-gray-100 dark:hover:bg-white/10"
                        title="View Credentials">
                        <span class="material-symbols-outlined text-[18px]">visibility</span>
                    </button>
                    <button @click="toggleDropdown(user.email)"
                        class="text-gray-400 hover:text-gray-900 dark:text-gray-500 dark:hover:text-white transition-colors p-1 rounded-full hover:bg-gray-100 dark:hover:bg-white/10">
                        <span class="material-symbols-outlined text-[20px]">more_vert</span>
                    </button>
                    <div v-if="activeDropdown === user.email"
                        class="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-xl shadow-lg z-10 py-1 overflow-hidden">
                        <template v-if="isVendorRequest(user)">
                            <button @click="openVendorReview(user)"
                                class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                                <span class="material-symbols-outlined text-[18px]">description</span>
                                Review Request
                            </button>
                            <div class="h-px bg-gray-200 dark:bg-white/5 my-1"></div>
                            <button @click="handleVendorApproval(user, 'APPROVED')"
                                class="w-full text-left px-4 py-2 text-sm text-green-700 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-500/10 flex items-center gap-2 transition-colors">
                                <span class="material-symbols-outlined text-[18px]">verified</span>
                                Approve Request
                            </button>
                            <button @click="handleVendorApproval(user, 'REJECTED')"
                                class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-2 transition-colors">
                                <span class="material-symbols-outlined text-[18px]">cancel</span>
                                Reject Request
                            </button>
                            <div class="h-px bg-gray-200 dark:bg-white/5 my-1"></div>
                        </template>
                        <button @click="openModal('edit-profile', user); activeDropdown = null"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                            <span class="material-symbols-outlined text-[18px]">edit</span>
                            Edit Profile
                        </button>
                        <button @click="store.toggleUserStatus(user.email); activeDropdown = null"
                            class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2 transition-colors">
                            <span class="material-symbols-outlined text-[18px]">{{ user.status === 'Active' ? 'block' : 'check_circle' }}</span>
                            {{ user.status === 'Active' ? 'Suspend User' : 'Activate User' }}
                        </button>
                        <div class="h-px bg-gray-200 dark:bg-white/5 my-1"></div>
                        <button @click="store.deleteUser(user.email); activeDropdown = null"
                            class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-2 transition-colors">
                            <span class="material-symbols-outlined text-[18px]">delete</span>
                            Delete
                        </button>
                    </div>
                </div>
            </div>

            <!-- Role + status badges -->
            <div class="flex gap-2 flex-wrap">
                <span class="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 text-[10px] uppercase font-bold tracking-wider border border-blue-200 dark:border-blue-500/20">{{ user.role }}</span>
                <span v-if="user.status === 'Active'"
                    class="px-2 py-0.5 rounded-full bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400 text-[10px] uppercase font-bold tracking-wider border border-green-200 dark:border-green-500/20">Active</span>
                <span v-else
                    class="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-500/10 dark:text-gray-400 text-[10px] uppercase font-bold tracking-wider border border-gray-200 dark:border-gray-500/20">Inactive</span>
                <span v-if="user.role === 'Vendor'"
                    class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border"
                    :class="approvalBadgeClass(user.approvalStatus)">
                    {{ formatApprovalStatus(user.approvalStatus) }}
                </span>
            </div>

            <!-- Footer -->
            <div v-if="isVendorRequest(user)"
                class="pt-2 border-t border-gray-200 dark:border-white/5 flex justify-between items-center gap-2">
                <div class="text-xs text-gray-500 dark:text-gray-400 leading-tight">
                    <span class="block text-[10px] uppercase font-semibold tracking-wider mb-0.5">Submitted</span>
                    <span>{{ formatSubmittedAt(user.submittedAt) }}</span>
                </div>
                <button @click="openVendorReview(user)"
                    class="text-xs font-semibold text-primary hover:text-primary/80 transition-colors whitespace-nowrap flex items-center gap-1 px-2 py-1 rounded hover:bg-primary/10">
                    <span class="material-symbols-outlined text-[14px]">description</span>
                    Review Request
                </button>
            </div>
            <div v-else class="pt-2 border-t border-gray-200 dark:border-white/5 flex justify-between items-center gap-2">
                <div class="text-xs text-gray-500 dark:text-gray-400 leading-tight">
                    <span class="block text-[10px] uppercase font-semibold tracking-wider mb-0.5">Last Login</span>
                    <span>{{ formatLastLogin(user.lastLogin) }}</span>
                </div>
                <button @click="openModal('edit-access', user)"
                    class="text-xs font-semibold text-primary hover:text-primary/80 transition-colors whitespace-nowrap flex items-center gap-1 px-2 py-1 rounded hover:bg-primary/10">
                    <span class="material-symbols-outlined text-[14px]">manage_accounts</span>
                    Edit Access
                </button>
            </div>
        </div>

        <!-- Add Support Card (Moved to the end) -->
        <div v-if="activeTab === 'Support'" @click="openModal('create-support')"
            class="bg-gray-50/50 dark:bg-white/5 border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-5 hover:border-primary/50 dark:hover:border-primary/50 hover:bg-primary/5 dark:hover:bg-primary/10 transition-all cursor-pointer flex flex-col items-center justify-center min-h-[160px] text-gray-500 dark:text-gray-400 hover:text-primary group">
            <div
                class="w-12 h-12 rounded-full bg-gray-100 dark:bg-white/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
                <span class="material-symbols-outlined text-[24px]">person_add</span>
            </div>
            <span class="font-medium">Add Customer Support</span>
        </div>

        <!-- Add Driver Card -->
        <div v-if="activeTab === 'Drivers'" @click="openModal('create-driver')"
            class="bg-gray-50/50 dark:bg-white/5 border-2 border-dashed border-gray-300 dark:border-white/20 rounded-xl p-5 hover:border-primary/50 dark:hover:border-primary/50 hover:bg-primary/5 dark:hover:bg-primary/10 transition-all cursor-pointer flex flex-col items-center justify-center min-h-[160px] text-gray-500 dark:text-gray-400 hover:text-primary group">
            <div
                class="w-12 h-12 rounded-full bg-gray-100 dark:bg-white/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
                <span class="material-symbols-outlined text-[24px]">local_shipping</span>
            </div>
            <span class="font-medium">Add Driver</span>
        </div>

        <div v-if="displayedUsers.length === 0 && activeTab === 'Vendor Requests'"
            class="col-span-full rounded-2xl border border-dashed border-amber-200/30 bg-amber-50/30 dark:bg-amber-500/5 px-6 py-10 text-center">
            <div
                class="w-14 h-14 mx-auto rounded-2xl bg-amber-100/70 dark:bg-amber-500/10 text-amber-600 dark:text-amber-300 flex items-center justify-center mb-4">
                <span class="material-symbols-outlined text-[28px]">verified_user</span>
            </div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">No vendor requests pending</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
                New vendor applications will appear here for Logistics Manager review.
            </p>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const {
    activeDropdown,
    activeTab,
    approvalBadgeClass,
    avatarGradient,
    displayedUsers,
    formatApprovalStatus,
    formatLastLogin,
    formatSubmittedAt,
    getInitials,
    handleVendorApproval,
    isVendorRequest,
    openCreds,
    openModal,
    openVendorReview,
    store,
    toggleDropdown,
} = inject(userManagementPageKey)
</script>
