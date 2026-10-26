<template>
    <!-- Personal Details Section -->
    <div
        class="bg-slate-900/70 p-4 rounded-xl border border-white/10 space-y-4 shadow-sm relative overflow-hidden group">
        <div
            class="absolute -left-10 -top-10 w-32 h-32 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors pointer-events-none">
        </div>
        <h4
            class="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2 relative z-10">
            <div
                class="w-6 h-6 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[14px]">person</span>
            </div>
            Personal Details
        </h4>
        <div class="grid grid-cols-2 gap-4 relative z-10 mt-3">
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Full
                    Name</label>
                <input v-model="formData.name" type="text" placeholder="e.g. John Doe"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Date
                    of Birth</label>
                <input v-model="formData.dob" type="date"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label class="flex justify-between items-center mb-1">
                    <span
                        class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Email
                        Address</span>
                    <button v-if="formData.email && !formData.emailVerified"
                        @click.prevent="openOtpModal('email')"
                        class="text-[9px] bg-primary/10 text-primary px-2 py-0.5 rounded shadow-sm hover:bg-primary hover:text-white transition-colors uppercase font-bold tracking-wider">Verify</button>
                    <span v-if="formData.emailVerified"
                        class="text-[9px] bg-green-500/10 text-green-600 dark:text-green-400 px-2 py-0.5 rounded uppercase font-bold tracking-wider flex items-center gap-1"><span
                            class="material-symbols-outlined text-[10px]">check_circle</span>
                        Verified</span>
                </label>
                <input v-model="formData.email" type="email"
                    placeholder="john@cargocore.com"
                    :disabled="modalMode === 'edit-profile'"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium disabled:opacity-60 disabled:cursor-not-allowed">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label class="flex justify-between items-center mb-1">
                    <span
                        class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Mobile
                        Number</span>
                    <button v-if="formData.mobile && !formData.mobileVerified"
                        @click.prevent="openOtpModal('mobile')"
                        class="text-[9px] bg-primary/10 text-primary px-2 py-0.5 rounded shadow-sm hover:bg-primary hover:text-white transition-colors uppercase font-bold tracking-wider">Verify</button>
                    <span v-if="formData.mobileVerified"
                        class="text-[9px] bg-green-500/10 text-green-600 dark:text-green-400 px-2 py-0.5 rounded uppercase font-bold tracking-wider flex items-center gap-1"><span
                            class="material-symbols-outlined text-[10px]">check_circle</span>
                        Verified</span>
                </label>
                <input v-model="formData.mobile" @input="formatField('mobile')" type="tel"
                    placeholder="+91 0000000000"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium tracking-wide">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Blood
                    Group</label>
                <div class="relative items-center">
                    <select v-model="formData.bloodGroup"
                        class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium appearance-none">
                        <option
                            v-for="bg in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']"
                            :key="bg" :value="bg"
                            class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                            {{ bg }}</option>
                    </select>
                    <span
                        class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none text-[18px]">expand_more</span>
                </div>
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Emergency
                    Contact</label>
                <input v-model="formData.emergencyContact"
                    @input="formatField('emergencyContact')" type="tel"
                    placeholder="+91 0000000000"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium tracking-wide">
            </div>
        </div>
    </div>

    <!-- Contact & Address Section -->
    <div
        class="bg-slate-900/70 p-4 rounded-xl border border-white/10 space-y-4 shadow-sm relative overflow-hidden group">
        <h4
            class="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2 relative z-10">
            <div
                class="w-6 h-6 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[14px]">home_pin</span>
            </div>
            Address Details
        </h4>
        <div class="grid grid-cols-2 gap-4 relative z-10 mt-3">
            <div class="col-span-2">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Street
                    Address</label>
                <input v-model="formData.address" type="text"
                    placeholder="123 Main St, Apt 4"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">City</label>
                <input v-model="formData.city" type="text" placeholder="City"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">State
                    / Province</label>
                <input v-model="formData.state" type="text" placeholder="State"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Pincode
                    / ZIP</label>
                <input v-model="formData.pincode" type="text" placeholder="000000"
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium tracking-wide font-mono">
            </div>
        </div>
    </div>

    <!-- Identification & Banking Section -->
    <div
        class="bg-slate-900/70 p-4 rounded-xl border border-white/10 space-y-4 shadow-sm relative overflow-hidden group">
        <h4
            class="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2 relative z-10">
            <div
                class="w-6 h-6 rounded bg-primary/10 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined text-[14px]">account_balance</span>
            </div>
            Identification
        </h4>
        <div class="grid grid-cols-2 gap-4 relative z-10 mt-3">
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Aadhar
                    / ID Number</label>
                <input v-model="formData.aadharCard" @input="formatField('aadharCard')"
                    type="text" placeholder="XXXX-XXXX-XXXX"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium uppercase font-mono tracking-wider">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">PAN
                    Number</label>
                <input v-model="formData.panCard" @input="formatField('panCard')"
                    type="text" placeholder="ABCDE1234F"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium uppercase font-mono tracking-wider">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">Bank
                    Account</label>
                <input v-model="formData.bankAccount" @input="formatField('bankAccount')"
                    type="text" placeholder="000011112222"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium font-mono tracking-wider">
            </div>
            <div class="col-span-2 md:col-span-1">
                <label
                    class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 uppercase tracking-wider">IFSC
                    Code</label>
                <input v-model="formData.ifscCode" @input="formatField('ifscCode')"
                    type="text" placeholder="BANK0001234"
                    class="w-full bg-slate-800 border border-white/10 rounded-lg px-4 py-2.5 text-[13px] text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium uppercase font-mono tracking-wider">
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const { formData, formatField, modalMode, openOtpModal } = inject(userManagementPageKey)
</script>
