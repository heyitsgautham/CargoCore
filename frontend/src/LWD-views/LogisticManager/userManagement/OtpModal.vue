<template>
    <!-- OTP Verification Modal -->
    <Teleport to="body">
        <div v-if="isOtpModalOpen"
            class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            @click.self="isOtpModalOpen = false">
            <div
                class="bg-slate-950/98 w-full max-w-sm rounded-2xl shadow-2xl border border-white/10 overflow-hidden text-center p-6 relative backdrop-blur-xl">
                <button @click="isOtpModalOpen = false"
                    class="absolute top-4 right-4 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>

                <div
                    class="w-16 h-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto mb-4">
                    <span class="material-symbols-outlined text-[32px]">dialpad</span>
                </div>

                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">Verify {{ otpField === 'email'
                    ?
                    'Email Address' : 'Mobile Number' }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
                    Enter the 4-digit verification code sent to <br />
                    <span class="font-bold text-gray-900 dark:text-white">
                        {{ otpField === 'email' ? formData.email : formData.mobile }}</span>
                </p>

                <input v-model="otpValue" type="text" maxlength="4" placeholder="••••" @keyup.enter="verifyOtp"
                    class="w-32 bg-slate-800 text-center text-3xl tracking-widest border border-white/10 rounded-lg px-4 py-3 mx-auto text-white focus:outline-none focus:border-primary/50 transition-colors mb-2 font-mono">

                <p v-if="otpError" class="text-xs text-red-500 font-medium mb-4">{{ otpError }}</p>
                <p v-else class="text-xs text-gray-500 mb-4 tracking-wider">Hint: User 1234 to simulate success
                </p>
                <button @click="verifyOtp"
                    class="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors">
                    Verify Code
                </button>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const {
    formData,
    isOtpModalOpen,
    otpError,
    otpField,
    otpValue,
    verifyOtp,
} = inject(userManagementPageKey)
</script>
