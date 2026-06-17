<template>
  <Background image-url="https://images.unsplash.com/photo-1657828514928-de1e0be57fb1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg">
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
            <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-[#00C4FF]/20 to-[#1E3A8A]/20 flex items-center justify-center border border-[#00C4FF]/30">
              <Shield class="w-8 h-8 text-[#00C4FF]" />
            </div>
            <h2 class="text-2xl font-bold text-white mb-2">
              Enter Verification Code
            </h2>
            <p class="text-white/60 text-sm">
              We sent a 6-digit code to
              <br />
              <span class="text-[#00C4FF] font-medium">{{ maskedEmail }}</span>
            </p>
          </div>

          <div
            v-if="signupDebugOtp"
            class="mb-6 rounded-lg border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-center text-sm text-amber-200"
          >
            Development mode: email delivery is unavailable, so use this OTP instead:
            <span class="font-mono font-semibold tracking-[0.3em]">{{ signupDebugOtp }}</span>
          </div>

          <!-- OTP Input -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 10 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 400 } }"
            class="mb-6"
          >
            <div class="flex justify-center gap-3 mb-6">
              <input
                v-for="(_digit, index) in otp"
                :key="index"
                :ref="(el) => (inputRefs[index] = el)"
                v-model="otp[index]"
                type="text"
                inputmode="numeric"
                maxlength="1"
                class="w-12 h-14 text-center text-2xl font-bold bg-white/10 backdrop-blur-xl border-2 border-white/20 rounded-lg text-white focus:outline-none focus:border-[#00C4FF] focus:ring-2 focus:ring-[#00C4FF20] transition-all duration-300"
                :autofocus="index === 0"
                @input="handleChange(index, $event)"
                @keydown="handleKeyDown(index, $event)"
                @paste="handlePaste"
              />
            </div>

            <!-- Timer -->
            <div class="text-center mb-4">
              <p v-if="!canResend" class="text-white/60 text-sm">
                Resend code in
                <span class="text-[#00C4FF] font-semibold">
                  00:{{ timer.toString().padStart(2, '0') }}
                </span>
              </p>
              <button
                v-else
                @click="handleResend"
                class="text-[#00C4FF] text-sm font-semibold hover:text-[#00D4FF] transition-colors duration-300"
              >
                Resend code
              </button>
            </div>

            <!-- Verify Button -->
            <GlassButton
              variant="primary"
              :is-loading="isLoading"
              :disabled="otp.some((digit) => !digit)"
              class-name="w-full"
              @click="handleVerify"
            >
              Verify
            </GlassButton>

            <!-- Error Message -->
            <div
              v-if="authStore.otpError"
              class="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm text-center"
            >
              {{ authStore.otpError }}
            </div>
          </div>

          <!-- Back Button -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 500 } }"
            class="mt-6 text-center"
          >
            <button
              @click="router.back()"
              class="inline-flex items-center gap-2 text-white/60 hover:text-[#00C4FF] transition-colors duration-300 text-sm"
            >
              <ArrowLeft class="w-4 h-4" />
              Back to sign in
            </button>
          </div>

          <!-- Security Footer -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 700 } }"
            class="mt-8 pt-6 border-t border-white/10 text-center"
          >
            <div class="flex items-center justify-center gap-2 text-white/40 text-xs">
              <Shield class="w-4 h-4" />
              <span>Secured by Cargo Core • 256-bit encryption</span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Shield, ArrowLeft } from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassButton from '../components/GlassButton.vue';
import { useAuthStore } from '../stores/authStore';

const authStore = useAuthStore();

const router = useRouter();
const route = useRoute();

const otp = ref(['', '', '', '', '', '']);
const isLoading = ref(false);
const timer = ref(59);
const canResend = ref(false);
const inputRefs = ref([]);
const signupDebugOtp = ref('');

// Get email from auth store (set during login or signup)
const email = computed(() => authStore.pendingEmail || authStore.userEmail || 'user@example.com');
const maskedEmail = computed(() => email.value.replace(/(.{3})(.*)(@.*)/, '$1***$3'));

let countdown = null;

onMounted(() => {
  if (String(route.query.flow || '') === 'signup') {
    const debugOtp = typeof window !== 'undefined' ? sessionStorage.getItem('signup_debug_otp') || '' : '';
    if (/^\d{6}$/.test(debugOtp)) {
      signupDebugOtp.value = debugOtp;
      otp.value = debugOtp.split('');
    }
  }

  countdown = setInterval(() => {
    timer.value--;
    if (timer.value <= 0) {
      canResend.value = true;
      if (countdown) clearInterval(countdown);
    }
  }, 1000);
});

onUnmounted(() => {
  if (countdown) clearInterval(countdown);
});

const handleChange = (index, event) => {
  const target = event.target;
  const value = target.value;

  if (!/^\d*$/.test(value)) return;

  otp.value[index] = value.slice(-1);

  // Auto-focus next input
  if (value && index < 5) {
    inputRefs.value[index + 1]?.focus();
  }
};

const handleKeyDown = (index, event) => {
  if (event.key === 'Backspace' && !otp.value[index] && index > 0) {
    inputRefs.value[index - 1]?.focus();
  }
};

const handlePaste = (event) => {
  event.preventDefault();
  const pastedData = event.clipboardData?.getData('text').slice(0, 6) || '';
  const digits = pastedData.split('').filter((char) => /\d/.test(char));

  digits.forEach((digit, index) => {
    if (index < 6) otp.value[index] = digit;
  });

  // Focus the next empty input or the last one
  const nextEmptyIndex = otp.value.findIndex((val) => !val);
  if (nextEmptyIndex !== -1) {
    inputRefs.value[nextEmptyIndex]?.focus();
  } else {
    inputRefs.value[5]?.focus();
  }
};

const handleVerify = async () => {
  if (otp.value.some((digit) => !digit)) return;

  isLoading.value = true;
  authStore.clearErrors();

  const otpString = otp.value.join('');
  const result = await authStore.verifyOTP(otpString);

  isLoading.value = false;

  if (result.success) {
    const flow = String(route.query.flow || '') || authStore.pendingFlow || sessionStorage.getItem('authFlow') || '';
    sessionStorage.removeItem('authFlow');
    if (flow === 'signup') {
      router.push('/signup-success');
      return;
    }
    router.push('/dashboard');
  }
};

const handleResend = () => {
  if (!canResend.value) return;
  timer.value = 59;
  canResend.value = false;
  console.log('Resending code...');
};
</script>
