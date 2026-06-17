<template>
  <Background :image-url="currentRole.background">
    <Navbar :show-role-info="{ role: currentRole.title, onChangeRole: () => router.push('/login-hub') }" />
    <AIHelpOrb />

    <div class="min-h-screen flex items-center justify-center px-8 pt-32 pb-20">
      <div
        v-motion
        :initial="{ opacity: 0, scale: 0.95 }"
        :enter="{ opacity: 1, scale: 1, transition: { duration: 500 } }"
        class="w-full max-w-md"
      >
        <GlassCard class-name="p-10" :animate="false">
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

          <!-- Welcome Text -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 10 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 300 } }"
            class="text-center mb-10"
          >
            <h2 class="text-3xl font-extrabold text-white mb-3 tracking-tight">
              <span class="bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-[#00C4FF]">
                Welcome Back
              </span>
            </h2>
            <p class="text-white/70 text-base">
              Sign in to your <span class="text-[#00C4FF] font-semibold">{{ currentRole.title }}</span> account
            </p>
            <div class="mt-4 h-0.5 w-16 bg-gradient-to-r from-transparent via-[#00C4FF] to-transparent mx-auto" />
          </div>

          <!-- Login Form -->
          <form @submit.prevent="handleSubmit" class="space-y-5">
            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 400 } }"
            >
              <GlassInput
                v-model="emailOrPhone"
                type="text"
                placeholder="Email or Username"
                :icon="Mail"
                required
              />
            </div>

            <div
              v-motion
              :initial="{ opacity: 0, x: -20 }"
              :enter="{ opacity: 1, x: 0, transition: { delay: 500 } }"
            >
              <div class="relative">
                <GlassInput
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Password"
                  :icon="Lock"
                  required
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-[#00C4FF] transition-colors duration-300"
                >
                  <EyeOff v-if="showPassword" class="w-5 h-5" />
                  <Eye v-else class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- Remember Me & Forgot Password -->
            <div
              v-motion
              :initial="{ opacity: 0 }"
              :enter="{ opacity: 1, transition: { delay: 600 } }"
              class="flex items-center justify-between"
            >
              <label class="flex items-center gap-2 cursor-pointer group">
                <input
                  v-model="rememberMe"
                  type="checkbox"
                  class="w-4 h-4 rounded border-white/20 bg-white/5 text-[#00C4FF] focus:ring-[#00C4FF] focus:ring-offset-0"
                />
                <span class="text-sm text-white/70 group-hover:text-white transition-colors duration-300">
                  Remember me
                </span>
              </label>
              <button
                type="button"
                @click="router.push('/forgot-password')"
                class="text-sm text-[#00C4FF] hover:text-[#00D4FF] transition-colors duration-300"
              >
                Forgot password?
              </button>
            </div>

            <!-- Sign In Button -->
            <div
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 700 } }"
            >
              <GlassButton
                type="submit"
                variant="primary"
                :is-loading="isLoading"
                class-name="w-full"
              >
                Sign In
              </GlassButton>
            </div>

            <!-- Error Message -->
            <div
              v-if="authStore.loginError"
              class="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm text-center"
            >
              {{ authStore.loginError }}
            </div>

            <!-- Divider - Only show for roles with Google Auth -->
            <div
              v-if="currentRole.showGoogleAuth"
              v-motion
              :initial="{ opacity: 0 }"
              :enter="{ opacity: 1, transition: { delay: 800 } }"
              class="relative py-4"
            >
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-white/10" />
              </div>
              <div class="relative flex justify-center">
                <span class="px-4 text-sm text-white/50 bg-transparent">
                  Or sign in with
                </span>
              </div>
            </div>

            <!-- Google Sign In - Only for Customer, Vendor and Driver -->
            <div
              v-if="currentRole.showGoogleAuth"
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 900 } }"
              class="flex justify-center"
            >
              <GoogleLogin
                v-if="googleClientId"
                :callback="handleGoogleCredential"
                :error="handleGoogleError"
                :button-config="googleButtonConfig"
              />
              <button
                v-else
                type="button"
                @click="handleMissingGoogleConfig"
                class="w-full px-6 py-3.5 rounded-lg bg-white hover:bg-white/95 transition-all duration-300 flex items-center justify-center gap-3 group shadow-lg hover:shadow-xl"
              >
                <svg class="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                <span class="text-gray-700 font-semibold">
                  Sign in with Google
                </span>
              </button>
            </div>

            <!-- Driver Mobile QR Option -->
            <div
              v-if="role === 'driver'"
              v-motion
              :initial="{ opacity: 0 }"
              :enter="{ opacity: 1, transition: { delay: 1000 } }"
              class="pt-4"
            >
              <button
                type="button"
                @click="showMobileQR = !showMobileQR"
                class="w-full px-6 py-3.5 rounded-lg bg-white/5 backdrop-blur-xl border border-white/10 hover:border-[#00C4FF50] hover:bg-white/10 transition-all duration-300 flex items-center justify-center gap-3"
              >
                <Smartphone class="w-5 h-5 text-[#00C4FF]" />
                <span class="text-white/90">
                  Scan QR from Mobile App
                </span>
              </button>

              <Transition name="expand">
                <div
                  v-if="showMobileQR"
                  class="mt-4 p-6 bg-white/5 rounded-lg border border-white/10 text-center"
                >
                  <div class="w-48 h-48 mx-auto bg-white rounded-lg p-4 mb-4">
                    <div class="w-full h-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] rounded flex items-center justify-center">
                      <span class="text-white text-xs">QR Code</span>
                    </div>
                  </div>
                  <p class="text-white/70 text-sm mb-2">
                    Scan this QR code with your mobile app
                  </p>
                  <div class="flex items-center justify-center gap-2 text-[#00C4FF] text-sm">
                    <Smartphone class="w-4 h-4" />
                    <span>Use Face ID on your iPhone 16</span>
                  </div>
                </div>
              </Transition>
            </div>
          </form>

          <!-- Security Footer -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 1100 } }"
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
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  Smartphone,
  Shield,
} from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassInput from '../components/GlassInput.vue';
import GlassButton from '../components/GlassButton.vue';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../composables/useToast';
import { consumeAuthError } from '@/config/api';

const authStore = useAuthStore();
const toast = useToast();

const router = useRouter();
const route = useRoute();
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const googleButtonConfig = {
  theme: 'filled_white',
  size: 'large',
  text: 'signin_with',
  shape: 'rectangular',
  width: 360,
};

const role = computed(() => route.params.role);

const roleDataMap = {
  manager: {
    title: 'Logistics Manager',
    background: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
  },
  warehouse: {
    title: 'Warehouse Manager',
    background: 'https://images.unsplash.com/photo-1575565147602-f9f8d0721dbe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
  },
  dispatcher: {
    title: 'Dispatcher',
    background: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
  },
  driver: {
    title: 'Driver',
    background: 'https://images.unsplash.com/photo-1763623252413-579b4695557b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
    showGoogleAuth: true,
  },
  customer: {
    title: 'Customer',
    background: 'https://images.unsplash.com/photo-1644134913822-1cd030b3d148?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
    showGoogleAuth: true,
  },
  vendor: {
    title: 'Vendor',
    background: 'https://images.unsplash.com/photo-1553484771-371a605b060b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
    showGoogleAuth: true,
  },
  support: {
    title: 'AI Customer Support',
    background: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?crop=entropy&cs=tinysrgb&fit=max&fm=jpg',
  },
};

const currentRole = computed(() => roleDataMap[role.value] || roleDataMap.manager);

const showPassword = ref(false);
const emailOrPhone = ref('');
const password = ref('');
const rememberMe = ref(false);
const isLoading = ref(false);
const showMobileQR = ref(false);

onMounted(() => {
  const authError = consumeAuthError();
  if (authError) {
    authStore.loginError = authError;
    toast.error(authError);
  }
});

const handleSubmit = async () => {
  authStore.clearErrors();
  isLoading.value = true;

  const result = await authStore.login(emailOrPhone.value, password.value, role.value);

  isLoading.value = false;

  if (result.success) {
    toast.success(result.message);
    router.push(result.redirect || '/dashboard');
  } else {
    toast.error(result.message);
  }
};

const handleMissingGoogleConfig = () => {
  toast.error('Google Sign-In is not configured yet. Add VITE_GOOGLE_CLIENT_ID to the frontend env.');
};

const handleGoogleCredential = async (response) => {
  if (!['customer', 'vendor', 'driver'].includes(String(role.value || ''))) {
    return toast.error('Google Sign-In is only allowed for Customers, Vendors, and Drivers.');
  }

  isLoading.value = true;
  const mappedRole = String(role.value).toLowerCase() === 'vendor' ? 'VENDOR' : 'INDIVIDUAL';
  const result = await authStore.googleLogin(response.credential, mappedRole);
  isLoading.value = false;

  if (result.success) {
    toast.success(result.message);
    router.push(result.redirect || '/dashboard');
    return;
  }

  toast.error(result.message);
};

const handleGoogleError = (error) => {
  console.error(error);
  toast.error('Google Sign-In failed. Check the Google client configuration and allowed origins.');
};
</script>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
