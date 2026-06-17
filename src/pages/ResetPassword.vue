<template>
  <Background :image-url="'https://images.unsplash.com/photo-1611216625141-d52dc0441830?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuaWdodCUyMGhpZ2h3YXklMjB0cnVjayUyMGxpZ2h0cyUyMGJva2VofGVufDF8fHx8MTc3MTM4NTQxOHww&ixlib=rb-4.1.0&q=80&w=1080'">
    <Navbar />
    <AIHelpOrb />

    <div class="min-h-screen flex items-center justify-center px-8 pt-32 pb-20">
      <div
        v-motion
        :initial="{ opacity: 0, scale: 0.95 }"
        :enter="{ opacity: 1, scale: 1, transition: { duration: 500 } }"
        class="w-full max-w-md"
      >
        <GlassCard class-name="p-8" :animate="false">
          <!-- Logo -->
          <div class="flex justify-center mb-8">
            <img
              v-motion
              :initial="{ scale: 0.8, opacity: 0 }"
              :enter="{ scale: 1, opacity: 1, transition: { delay: 200, type: 'spring', stiffness: 200 } }"
              src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
              alt="Cargo Core Logo"
              class="h-20 w-auto"
            />
          </div>

          <!-- Header -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 10 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 300 } }"
            class="text-center mb-8"
          >
            <h2 class="text-2xl font-bold text-white mb-2">Reset Password</h2>
            <p class="text-white/60 text-sm">
              We sent a verification code to
              <span class="text-[#00C4FF]">{{ email }}</span>
            </p>
          </div>

          <!-- Reset Form -->
          <form @submit.prevent="handleResetPassword" class="space-y-5">
            <!-- OTP Input -->
            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 400 } }"
            >
              <label class="text-white/70 text-sm mb-2 block">Verification Code</label>
              <GlassInput
                v-model="otp"
                type="text"
                placeholder="Enter 6-digit code"
                :icon="Shield"
                maxlength="6"
                required
              />
            </div>

            <!-- New Password -->
            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 450 } }"
            >
              <label class="text-white/70 text-sm mb-2 block">New Password</label>
              <GlassInput
                v-model="newPassword"
                type="password"
                placeholder="Enter new password"
                :icon="Lock"
                required
              />
            </div>

            <!-- Confirm Password -->
            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 500 } }"
            >
              <label class="text-white/70 text-sm mb-2 block">Confirm Password</label>
              <GlassInput
                v-model="confirmPassword"
                type="password"
                placeholder="Confirm new password"
                :icon="Lock"
                required
              />
            </div>

            <!-- Error Message -->
            <div v-if="errorMessage" class="text-red-400 text-sm text-center p-3 rounded-lg bg-red-500/15 border border-red-500/30">
              {{ errorMessage }}
            </div>


            <!-- Resend Code -->
            <div class="flex items-center justify-between text-sm">
              <span class="text-white/60">Didn't receive code?</span>
              <button
                type="button"
                @click="handleResendCode"
                :disabled="resendTimer > 0"
                class="text-[#00C4FF] hover:text-[#00A8E8] disabled:text-white/40 disabled:cursor-not-allowed transition-colors duration-300"
              >
                {{ resendTimer > 0 ? `Resend in ${resendTimer}s` : 'Resend Code' }}
              </button>
            </div>

            <!-- Reset Password Button -->
            <div
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 600 } }"
            >
              <GlassButton
                type="submit"
                variant="primary"
                :loading="loading"
                class="w-full"
              >
                Reset Password
              </GlassButton>
            </div>
          </form>

          <!-- Back to Sign In -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 700 } }"
            class="mt-6 text-center"
          >
            <button
              @click="router.back()"
              class="text-white/60 hover:text-[#00C4FF] text-sm transition-colors duration-300 flex items-center justify-center gap-2 mx-auto"
            >
              <ArrowLeft class="w-4 h-4" />
              <span>Back to forgot password</span>
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Shield, Lock, ArrowLeft } from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassInput from '../components/GlassInput.vue';
import GlassButton from '../components/GlassButton.vue';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../composables/useToast';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const toast = useToast();

// Email comes from the store (set by sendPasswordResetOTP) or query param fallback
const email = ref(authStore.pendingEmail || route.query.email || '');
const otp = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const errorMessage = ref('');
const resendTimer = ref(60);

let timerInterval = null;

onMounted(() => {
  if (!email.value) {
    router.push('/forgot-password');
    return;
  }
  startResendTimer();
});

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval);
  }
});

const startResendTimer = () => {
  resendTimer.value = 60;
  timerInterval = window.setInterval(() => {
    if (resendTimer.value > 0) {
      resendTimer.value--;
    } else if (timerInterval) {
      clearInterval(timerInterval);
    }
  }, 1000);
};

const handleResendCode = async () => {
  const result = await authStore.sendPasswordResetOTP(email.value);
  startResendTimer();
  if (result.success) {
    toast.success('Verification code resent to ' + email.value);
  } else {
    toast.error(result.message);
  }
};

const handleResetPassword = async () => {
  errorMessage.value = '';
  authStore.clearErrors();

  if (otp.value.length !== 6) {
    errorMessage.value = 'Please enter a valid 6-digit code';
    toast.warning('Please enter a valid 6-digit code');
    return;
  }

  if (newPassword.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters';
    toast.warning('Password must be at least 8 characters');
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match';
    toast.error('Passwords do not match');
    return;
  }

  loading.value = true;

  const result = await authStore.resetPassword(email.value, otp.value, newPassword.value);

  loading.value = false;

  if (result.success) {
    toast.success('Password reset successfully! Please log in with your new password.');
    setTimeout(() => router.replace('/login'), 1800);
  } else {
    errorMessage.value = result.message;
    toast.error(result.message);
  }
};
</script>
