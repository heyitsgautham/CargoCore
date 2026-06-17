<template>
  <Background image-url="https://images.unsplash.com/photo-1611216625141-d52dc0441830?crop=entropy&cs=tinysrgb&fit=max&fm=jpg">
    <Navbar />
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
              Sign in to your <span class="text-[#00C4FF] font-semibold">Cargo Core</span> account
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
                placeholder="Email or Phone"
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

            <!-- Divider -->
            <div
              v-if="showGoogleSignIn"
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
                  Or continue with
                </span>
              </div>
            </div>

            <!-- Google Sign In -->
            <div
              v-if="showGoogleSignIn"
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
          </form>

          <!-- Sign Up Link -->
          <div
            v-if="showSignupLink"
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 1000 } }"
            class="mt-8 text-center"
          >
            <p class="text-white/60 text-sm">
              Don't have an account?
              <button
                @click="router.push('/signup')"
                class="text-[#00C4FF] hover:text-[#00D4FF] font-semibold transition-colors duration-300 ml-1"
              >
                Sign up
              </button>
            </p>
          </div>

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
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
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

const selectedRole = computed(() => String(route.query.role || '').toLowerCase());
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const showGoogleSignIn = computed(() => selectedRole.value === 'customer');
const showSignupLink = computed(() => !['vendor', 'manager', 'warehouse', 'dispatcher'].includes(selectedRole.value));
const googleButtonConfig = {
  theme: 'filled_white',
  size: 'large',
  text: 'signin_with',
  shape: 'rectangular',
  width: 360,
};

const showPassword = ref(false);
const emailOrPhone = ref('');
const password = ref('');
const rememberMe = ref(false);
const isLoading = ref(false);

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

  const result = await authStore.login(emailOrPhone.value, password.value);

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
  isLoading.value = true;
  const result = await authStore.googleLogin(response.credential, 'INDIVIDUAL');
  isLoading.value = false;

  if (result.success) {
    toast.success(result.message);
    router.push(result.redirect || '/dashboard');
    return;
  }

  if (result.status === 409) {
    toast.warning(result.message);
    return;
  }

  toast.error(result.message);
};

const handleGoogleError = (error) => {
  console.error(error);
  toast.error('Google Sign-In failed. Check the Google client configuration and allowed origins.');
};
</script>
