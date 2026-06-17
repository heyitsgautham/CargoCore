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
            <h2 class="text-2xl font-bold text-white mb-2">Forgot Password?</h2>
            <p class="text-white/60 text-sm">
              Enter your email address and we'll send you a verification code
            </p>
          </div>

          <!-- Email Form -->
          <form @submit.prevent="handleSendOTP" class="space-y-5">
            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 400 } }"
            >
              <GlassInput
                v-model="email"
                type="email"
                placeholder="Email address"
                :icon="Mail"
                required
              />
            </div>

            <!-- Send Code Button -->
            <div
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 500 } }"
            >
              <GlassButton
                type="submit"
                variant="primary"
                :loading="loading"
                class="w-full"
              >
                Send Verification Code
              </GlassButton>
            </div>

            <!-- Error Message -->
            <div
              v-if="authStore.resetError"
              class="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm text-center"
            >
              {{ authStore.resetError }}
            </div>
          </form>

          <!-- Back to Sign In -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 600 } }"
            class="mt-6 text-center"
          >
            <button
              @click="router.back()"
              class="text-white/60 hover:text-[#00C4FF] text-sm transition-colors duration-300 flex items-center justify-center gap-2 mx-auto"
            >
              <ArrowLeft class="w-4 h-4" />
              <span>Back to sign in</span>
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Mail, ArrowLeft } from 'lucide-vue-next';
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
const toast = useToast();
const email = ref('');
const loading = ref(false);

const handleSendOTP = async () => {
  if (!email.value || email.value.trim() === '') {
    toast.warning('Please enter your email address');
    return;
  }

  authStore.clearErrors();
  loading.value = true;

  const result = await authStore.sendPasswordResetOTP(email.value.trim());

  loading.value = false;

  if (result.success) {
    toast.success('Verification code sent to ' + email.value);
    router.push({ path: '/reset-password', query: { email: email.value } });
  } else {
    toast.error(result.message);
  }
};
</script>
