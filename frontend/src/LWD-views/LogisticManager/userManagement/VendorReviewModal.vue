<template>
    <!-- Vendor Review Modal -->
    <Teleport to="body">
        <div v-if="reviewingVendor"
            class="fixed inset-0 z-[115] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            @click.self="closeVendorReview">
            <div
                class="bg-slate-950/98 w-full max-w-2xl rounded-2xl shadow-2xl border border-white/10 overflow-hidden flex flex-col backdrop-blur-xl">
                <div
                    class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <div>
                        <h3 class="text-lg font-bold text-white">Vendor Request Review</h3>
                        <p class="text-sm text-gray-400 mt-1">{{ reviewingVendor.companyName || reviewingVendor.name }}</p>
                    </div>
                    <button @click="closeVendorReview"
                        class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="p-6 space-y-5 max-h-[78vh] overflow-y-auto bg-slate-950/95">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 text-[10px] uppercase font-bold tracking-wider border border-blue-200 dark:border-blue-500/20">
                            {{ reviewingVendor.role }}
                        </span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border"
                            :class="approvalBadgeClass(reviewingVendor.approvalStatus)">
                            {{ formatApprovalStatus(reviewingVendor.approvalStatus) }}
                        </span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="rounded-xl border border-white/10 bg-slate-900/70 p-4 space-y-3">
                            <h4 class="text-sm font-bold text-white uppercase tracking-wider">Application Details</h4>
                            <div class="space-y-2 text-sm text-gray-300">
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Company</span>
                                    <span class="text-right font-medium">{{ reviewingVendor.companyName || 'Not provided' }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Contact Person</span>
                                    <span class="text-right font-medium">{{ reviewingVendor.contactPerson || reviewingVendor.name }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">GST / Tax ID</span>
                                    <span class="text-right font-medium">{{ reviewingVendor.taxId || 'Not provided' }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Submitted</span>
                                    <span class="text-right font-medium">{{ formatSubmittedAt(reviewingVendor.submittedAt) }}</span>
                                </div>
                            </div>
                        </div>

                        <div class="rounded-xl border border-white/10 bg-slate-900/70 p-4 space-y-3">
                            <h4 class="text-sm font-bold text-white uppercase tracking-wider">Contact Details</h4>
                            <div class="space-y-2 text-sm text-gray-300">
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Login Email</span>
                                    <span class="text-right font-medium break-all">{{ reviewingVendor.email }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Business Email</span>
                                    <span class="text-right font-medium break-all">{{ reviewingVendor.businessEmail || 'Not provided' }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Business Phone</span>
                                    <span class="text-right font-medium">{{ reviewingVendor.businessPhone || 'Not provided' }}</span>
                                </div>
                                <div class="flex justify-between gap-4">
                                    <span class="text-gray-400">Mobile</span>
                                    <span class="text-right font-medium">{{ reviewingVendor.mobile || 'Not provided' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-if="reviewingVendor.approvalNote"
                        class="rounded-xl border border-amber-200/20 bg-amber-50/30 dark:bg-amber-500/5 p-4">
                        <h4 class="text-sm font-bold text-amber-300 uppercase tracking-wider mb-2">Review Note</h4>
                        <p class="text-sm text-gray-300 leading-relaxed">{{ reviewingVendor.approvalNote }}</p>
                    </div>
                </div>

                <div class="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/90">
                    <button @click="closeVendorReview"
                        class="px-4 py-2 rounded-lg font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors shadow-sm">
                        Close
                    </button>
                    <button @click="handleVendorApproval(reviewingVendor, 'REJECTED')"
                        class="px-4 py-2 rounded-lg font-medium text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition-colors shadow-sm">
                        Reject
                    </button>
                    <button @click="handleVendorApproval(reviewingVendor, 'APPROVED')"
                        class="px-4 py-2 rounded-lg font-medium text-white bg-primary hover:bg-primary/90 transition-colors shadow-sm">
                        Approve
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const {
    approvalBadgeClass,
    closeVendorReview,
    formatApprovalStatus,
    formatSubmittedAt,
    handleVendorApproval,
    reviewingVendor,
} = inject(userManagementPageKey)
</script>
