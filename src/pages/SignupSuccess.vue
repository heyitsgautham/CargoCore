<template>
  <Background image-url="https://images.unsplash.com/photo-1657828514928-de1e0be57fb1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg">
    <Navbar />
    <AIHelpOrb />

    <div class="min-h-screen flex items-center justify-center px-8 pt-32 pb-20">
      <div
        v-motion
        :initial="{ opacity: 0, scale: 0.9 }"
        :enter="{ opacity: 1, scale: 1, transition: { duration: 600, type: 'spring', stiffness: 100 } }"
        class="w-full max-w-lg"
      >
        <GlassCard class-name="p-12 text-center relative overflow-hidden" :animate="false">
          <!-- Logo -->
          <div
            v-motion
            :initial="{ scale: 0, rotate: -180 }"
            :enter="{ scale: 1, rotate: 0, transition: { delay: 200, type: 'spring', stiffness: 200 } }"
            class="flex justify-center mb-8"
          >
            <img
              src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
              alt="Cargo Core Logo"
              class="h-24 w-auto"
            />
          </div>

          <!-- Success Animation -->
          <div
            v-motion
            :initial="{ scale: 0 }"
            :enter="{ scale: 1, transition: { delay: 400, type: 'spring', stiffness: 200 } }"
            class="relative mb-8"
          >
            <!-- Animated Rings -->
            <div
              v-motion
              :animate="{
                scale: [1, 1.5, 1],
                opacity: [0.5, 0, 0.5],
              }"
              :transition="{ duration: 2000, repeat: Infinity, ease: 'easeInOut' }"
              class="absolute inset-0 flex items-center justify-center"
            >
              <div class="w-32 h-32 rounded-full border-4 border-[#00C4FF]" />
            </div>

            <div
              v-motion
              :animate="{
                scale: [1, 1.5, 1],
                opacity: [0.3, 0, 0.3],
              }"
              :transition="{ duration: 2000, repeat: Infinity, ease: 'easeInOut', delay: 500 }"
              class="absolute inset-0 flex items-center justify-center"
            >
              <div class="w-32 h-32 rounded-full border-4 border-[#FF9500]" />
            </div>

            <!-- Success Icon -->
            <div class="relative w-32 h-32 mx-auto rounded-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center shadow-[0_0_50px_rgba(0,196,255,0.5)]">
              <div
                v-motion
                :initial="{ scale: 0 }"
                :enter="{ scale: 1, transition: { delay: 600, type: 'spring', stiffness: 300 } }"
              >
                <CheckCircle2 class="w-16 h-16 text-white" />
              </div>
            </div>

            <!-- Sparkles -->
            <div
              v-motion
              :animate="{ rotate: 360 }"
              :transition="{ duration: 4000, repeat: Infinity, ease: 'linear' }"
              class="absolute inset-0 flex items-center justify-center"
            >
              <Sparkles class="w-6 h-6 text-[#FF9500] absolute -top-2 left-1/2" />
              <Sparkles class="w-6 h-6 text-[#00C4FF] absolute top-1/2 -right-2" />
              <Sparkles class="w-6 h-6 text-[#FF6B00] absolute -bottom-2 left-1/2" />
              <Sparkles class="w-6 h-6 text-[#00C4FF] absolute top-1/2 -left-2" />
            </div>
          </div>

          <!-- Success Message -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 800 } }"
            class="mb-8"
          >
            <h1 class="text-3xl font-bold text-white mb-4">
              Welcome to Cargo Core<span v-if="authStore.userName">, {{ authStore.userName.split(' ')[0] }}</span>!
            </h1>
            <p class="text-white/70 text-lg mb-2">
              Your account has been successfully created
            </p>
            <p class="text-white/60 text-sm">
              You're all set to start managing your logistics operations with AI-powered efficiency.
            </p>
          </div>

          <!-- Features Preview -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 1000 } }"
            class="mb-8 space-y-3"
          >
            <div class="p-4 bg-white/5 rounded-lg border border-white/10 text-left">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-[#00C4FF]/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 class="w-5 h-5 text-[#00C4FF]" />
                </div>
                <div>
                  <h4 class="text-white font-semibold text-sm mb-1">
                    Real-Time Tracking
                  </h4>
                  <p class="text-white/60 text-xs">
                    Monitor all your shipments with live GPS tracking
                  </p>
                </div>
              </div>
            </div>

            <div class="p-4 bg-white/5 rounded-lg border border-white/10 text-left">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-[#FF9500]/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 class="w-5 h-5 text-[#FF9500]" />
                </div>
                <div>
                  <h4 class="text-white font-semibold text-sm mb-1">
                    AI-Powered Analytics
                  </h4>
                  <p class="text-white/60 text-xs">
                    Get intelligent insights to optimize your operations
                  </p>
                </div>
              </div>
            </div>

            <div class="p-4 bg-white/5 rounded-lg border border-white/10 text-left">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-[#1E3A8A]/40 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 class="w-5 h-5 text-[#00C4FF]" />
                </div>
                <div>
                  <h4 class="text-white font-semibold text-sm mb-1">
                    24/7 Support
                  </h4>
                  <p class="text-white/60 text-xs">
                    Our AI assistant is always ready to help you
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- CTA Button -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 1200 } }"
          >
            <GlassButton
              variant="primary"
              :icon="ArrowRight"
              class-name="w-full text-lg py-4"
              @click="handleGoToLogin"
            >
              Go to Login
            </GlassButton>

            <p class="mt-4 text-white/50 text-xs">
              Redirecting to login shortly...
            </p>
          </div>

          <!-- Confetti Effect -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 500 } }"
            class="absolute inset-0 pointer-events-none overflow-hidden rounded-xl"
          >
            <div
              v-for="i in 20"
              :key="i"
              v-motion
              :initial="{ y: -100, x: `${Math.random() * 100}%`, opacity: 1 }"
              :enter="{
                y: '100vh',
                rotate: Math.random() * 360,
                opacity: 0,
                transition: {
                  duration: Math.random() * 2000 + 2000,
                  delay: Math.random() * 500,
                  ease: 'easeIn',
                },
              }"
              class="absolute w-2 h-2 rounded-full"
              :style="{
                backgroundColor: ['#00C4FF', '#FF9500', '#FF6B00', '#1E3A8A'][Math.floor(Math.random() * 4)],
              }"
            />
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { CheckCircle2, ArrowRight, Sparkles } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassButton from '../components/GlassButton.vue';
import { useAuthStore } from '../stores/authStore';

const router = useRouter();
const authStore = useAuthStore();
let redirectTimer = null;

const handleGoToLogin = () => {
  const rawRole = authStore.pendingRole || authStore.currentUser?.role || '';
  const role = rawRole === 'INDIVIDUAL' ? 'customer' : String(rawRole).toLowerCase();
  authStore.logout();
  if (role === 'customer' || role === 'vendor') {
    router.replace(`/login/${role}`);
    return;
  }

  router.replace('/login-hub');
};

onMounted(() => {
  redirectTimer = setTimeout(() => {
    handleGoToLogin();
  }, 3500);
});

onUnmounted(() => {
  if (redirectTimer) clearTimeout(redirectTimer);
});
</script>
