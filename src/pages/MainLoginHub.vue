<template>
  <Background
    image-url="https://images.unsplash.com/photo-1611216625141-d52dc0441830?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuaWdodCUyMGhpZ2h3YXklMjB0cnVjayUyMGxpZ2h0cyUyMGJva2VofGVufDF8fHx8MTc3MTM4NTQxOHww&ixlib=rb-4.1.0&q=80&w=1080"
  >
    <Navbar />
    <AIHelpOrb />


<div class="min-h-screen flex items-center justify-center px-8 pt-32 pb-20">
      <div class="max-w-7xl w-full">
        <!-- Header -->
        <div
          v-motion
          :initial="{ opacity: 0, y: -30 }"
          :enter="{ opacity: 1, y: 0, transition: { duration: 600 } }"
          class="text-center mb-20"
        >
          <h1
            class="text-6xl md:text-7xl font-extrabold text-white mb-8 tracking-tight leading-tight"
            style="letter-spacing: -0.03em"
          >
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-[#00C4FF] via-[#00E4FF] to-[#FF9500] animate-gradient">
              Select Your Role
            </span>
          </h1>
          <p
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 200, duration: 600 } }"
            class="text-xl md:text-2xl text-white/80 max-w-3xl mx-auto font-light leading-relaxed"
          >
            Secure, role-specific access for your entire logistics ecosystem
          </p>
          <div
            v-motion
            :initial="{ opacity: 0, scale: 0 }"
            :enter="{ opacity: 1, scale: 1, transition: { delay: 400, duration: 500 } }"
            class="mt-6 inline-block"
          >
            <div class="h-1 w-24 bg-gradient-to-r from-[#00C4FF] to-[#FF9500] rounded-full mx-auto" />
          </div>
        </div>

        <!-- Featured Roles: Customer & Vendor -->
        <div
          v-motion
          :initial="{ opacity: 0 }"
          :enter="{ opacity: 1, transition: { delay: 300, duration: 600 } }"
          class="mb-16"
        >
          <h2 class="text-3xl font-bold text-white mb-8 text-center">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-[#00C4FF] to-[#FF9500]">
              Get Started
            </span>
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            <div
              v-for="(role, index) in featuredRoles"
              :key="role.id"
              v-motion
              :initial="{ opacity: 0, y: 20 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 400 + index * 100, duration: 500 } }"
              :hover="{ y: -8, scale: 1.02 }"
              class="group cursor-pointer"
              @click="handleRoleSelect(role.id)"
            >
              <GlassCard class-name="p-8 h-full hover:shadow-[0_12px_70px_rgba(0,196,255,0.4)] hover:border-[#00C4FF]/50 transition-all duration-500" :animate="false">
                <!-- Header with Logo -->
                <div class="flex items-start justify-between mb-6">
                  <div
                    class="w-20 h-20 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-500 shadow-lg"
                    :style="{
                      background: `linear-gradient(135deg, ${role.color}25, ${role.color}10)`,
                      border: `2px solid ${role.color}50`,
                      boxShadow: `0 0 20px ${role.color}20, 0 4px 12px rgba(0,0,0,0.3)`,
                    }"
                  >
                    <component :is="role.icon" class="w-10 h-10 drop-shadow-lg" :style="{ color: role.color, filter: 'drop-shadow(0 0 8px currentColor)' }" />
                  </div>
                  <img
                    src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
                    alt="Cargo Core"
                    class="h-10 w-auto opacity-40 group-hover:opacity-100 transition-all duration-300 drop-shadow-md"
                  />
                </div>

                <!-- Title -->
                <div class="mb-6">
                  <h3 class="text-3xl font-bold text-white mb-2 group-hover:text-[#00C4FF] transition-colors duration-300 tracking-tight">
                    {{ role.title }}
                  </h3>
                  <p class="text-base text-white/60 font-medium">{{ role.subtitle }}</p>
                </div>

                <!-- Description -->
                <p class="text-white/80 text-lg mb-6 leading-relaxed">
                  {{ role.description }}
                </p>

                <!-- Dashboard Preview Thumbnail -->
                <div class="relative rounded-xl overflow-hidden mb-6 h-32 border border-white/20 group-hover:border-[#00C4FF]/30 transition-colors duration-500 shadow-lg">
                  <img
                    :src="role.thumbnail"
                    :alt="`${role.title} dashboard`"
                    class="w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-110 transition-all duration-700"
                  />
                  <div class="absolute inset-0 bg-gradient-to-t from-[#0A1428]/90 via-[#0A1428]/40 to-transparent" />
                  <div class="absolute inset-0 bg-gradient-to-br from-transparent to-[#00C4FF]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                </div>

                <!-- Arrow -->
                <div class="flex items-center justify-between">
                  <span class="text-sm text-white/50 font-medium tracking-wide uppercase">Access Dashboard</span>
                  <div
                    v-motion
                    :animate="{ x: [0, 5, 0] }"
                    :transition="{ duration: 1500, repeat: Infinity, ease: 'easeInOut' }"
                    class="text-white/60 group-hover:text-[#00C4FF] transition-colors duration-300"
                  >
                    <ArrowRight class="w-7 h-7" />
                  </div>
                </div>
              </GlassCard>
            </div>
          </div>
        </div>

        <!-- Staff & Team Access -->
        <div
          v-motion
          :initial="{ opacity: 0 }"
          :enter="{ opacity: 1, transition: { delay: 500, duration: 600 } }"
          class="mb-12"
        >
          <h2 class="text-2xl font-bold text-white/90 mb-6 text-center">
            Staff & Team Access
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <div
              v-for="(role, index) in staffRoles"
              :key="role.id"
              v-motion
              :initial="{ opacity: 0, y: 20 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 600 + index * 100, duration: 500 } }"
              :hover="{ y: -8, scale: 1.02 }"
              class="group cursor-pointer"
              @click="handleRoleSelect(role.id)"
            >
              <GlassCard class-name="p-6 h-full hover:shadow-[0_10px_60px_rgba(0,196,255,0.35)] hover:border-[#00C4FF]/40 transition-all duration-500" :animate="false">
                <!-- Header with Logo -->
                <div class="flex items-start justify-between mb-4">
                  <div
                    class="w-14 h-14 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-500 shadow-lg"
                    :style="{
                      background: `linear-gradient(135deg, ${role.color}25, ${role.color}10)`,
                      border: `2px solid ${role.color}50`,
                      boxShadow: `0 0 20px ${role.color}20, 0 4px 12px rgba(0,0,0,0.3)`,
                    }"
                  >
                    <component :is="role.icon" class="w-7 h-7 drop-shadow-lg" :style="{ color: role.color, filter: 'drop-shadow(0 0 8px currentColor)' }" />
                  </div>
                  <img
                    src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
                    alt="Cargo Core"
                    class="h-8 w-auto opacity-40 group-hover:opacity-100 transition-all duration-300 drop-shadow-md"
                  />
                </div>

                <!-- Title -->
                <div class="mb-4">
                  <h3 class="text-xl font-bold text-white mb-1 group-hover:text-[#00C4FF] transition-colors duration-300 tracking-tight">
                    {{ role.title }}
                  </h3>
                  <p class="text-xs text-white/60 font-medium">{{ role.subtitle }}</p>
                </div>

                <!-- Description -->
                <p class="text-white/75 text-sm mb-4 leading-relaxed">
                  {{ role.description }}
                </p>

                <!-- Dashboard Preview Thumbnail -->
                <div class="relative rounded-xl overflow-hidden mb-4 h-24 border border-white/20 group-hover:border-[#00C4FF]/30 transition-colors duration-500 shadow-lg">
                  <img
                    :src="role.thumbnail"
                    :alt="`${role.title} dashboard`"
                    class="w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-110 transition-all duration-700"
                  />
                  <div class="absolute inset-0 bg-gradient-to-t from-[#0A1428]/90 via-[#0A1428]/40 to-transparent" />
                  <div class="absolute inset-0 bg-gradient-to-br from-transparent to-[#00C4FF]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                </div>

                <!-- Arrow -->
                <div class="flex items-center justify-between">
                  <span class="text-xs text-white/40 font-medium tracking-wide uppercase">Access</span>
                  <div
                    v-motion
                    :animate="{ x: [0, 5, 0] }"
                    :transition="{ duration: 1500, repeat: Infinity, ease: 'easeInOut' }"
                    class="text-white/60 group-hover:text-[#00C4FF] transition-colors duration-300"
                  >
                    <ArrowRight class="w-5 h-5" />
                  </div>
                </div>
              </GlassCard>
            </div>
          </div>
        </div>

        <!-- Signup CTA -->
        <div
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0, transition: { delay: 800, duration: 600 } }"
          class="text-center"
        >
          <button
            @click="router.push('/signup')"
            class="group relative inline-flex items-center gap-4 px-10 py-5 rounded-2xl bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl border-2 border-white/20 hover:border-[#00C4FF]/60 hover:from-white/15 hover:to-white/10 transition-all duration-500 shadow-lg hover:shadow-[0_0_40px_rgba(0,196,255,0.3)] hover:scale-105"
          >
            <span class="text-white text-xl font-light">
              New here? 
              <span class="bg-clip-text text-transparent bg-gradient-to-r from-[#00C4FF] to-[#00E4FF] font-bold ml-1">
                Sign up as Customer or Vendor
              </span>
            </span>
            <ArrowRight class="w-6 h-6 text-[#00C4FF] group-hover:translate-x-2 transition-transform duration-300 drop-shadow-[0_0_8px_rgba(0,196,255,0.8)]" />
            <div class="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#00C4FF]/0 via-[#00C4FF]/5 to-[#00C4FF]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          </button>
        </div>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import {
  Truck,
  Warehouse,
  Radio,
  Car,
  Users,
  UserCircle,
  ArrowRight,
} from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import { useToast } from '../composables/useToast';

const router = useRouter();
const toast = useToast();
const authStore = useAuthStore();

const loggedInUser = computed(() => authStore.currentUser)
const loggedInDashboard = computed(() => {
  const role = loggedInUser.value?.role
  const map = {
    INDIVIDUAL: '/individual/dashboard', VENDOR: '/vendor/dashboard',
    LOGISTIC_MANAGER: '/logistic/dashboard', manager: '/logistic/dashboard',
    WAREHOUSE_MANAGER: '/warehouse/dashboard', warehouse: '/warehouse/dashboard',
    DISPATCHER: '/dispatcher/dashboard', dispatcher: '/dispatcher/dashboard',
    DRIVER: '/driver/dashboard', driver: '/driver/dashboard',
  }
  return map[role] || null
})

onMounted(() => {
  if (loggedInUser.value && loggedInDashboard.value) {
    router.replace(loggedInDashboard.value)
  }
})

const featuredRoles = [
  {
    id: 'customer',
    title: 'Customer',
    subtitle: 'External',
    description: 'Order tracking & service requests',
    icon: Users,
    color: '#FF6B00',
    thumbnail: 'https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=200&h=120&fit=crop',
  },
  {
    id: 'vendor',
    title: 'Vendor',
    subtitle: 'External',
    description: 'Service management & billing',
    icon: UserCircle,
    color: '#9333EA',
    thumbnail: 'https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=200&h=120&fit=crop',
  },
];

const staffRoles = [
  {
    id: 'manager',
    title: 'Logistics Manager',
    subtitle: 'Owner',
    description: 'Full platform control & analytics',
    icon: Truck,
    color: '#00C4FF',
    thumbnail: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=200&h=120&fit=crop',
  },
  {
    id: 'warehouse',
    title: 'Warehouse Manager',
    subtitle: 'Operations',
    description: 'Inventory & shipment management',
    icon: Warehouse,
    color: '#FF9500',
    thumbnail: 'https://images.unsplash.com/photo-1553413077-190dd305871c?w=200&h=120&fit=crop',
  },
  {
    id: 'dispatcher',
    title: 'Dispatcher',
    subtitle: 'Coordination',
    description: 'Route planning & driver assignment',
    icon: Radio,
    color: '#00C4FF',
    thumbnail: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&h=120&fit=crop',
  },
  {
    id: 'driver',
    title: 'Driver',
    subtitle: 'Field Team',
    description: 'Delivery tracking & mobile access',
    icon: Car,
    color: '#1E3A8A',
    thumbnail: 'https://images.unsplash.com/photo-1519003722824-194d4455a60c?w=200&h=120&fit=crop',
  },
];

const handleRoleSelect = (roleId) => {
  // AI Support is open/public - no login required
  if (roleId === 'support') {
    toast.info('AI Support is publicly accessible — Coming soon!');
    return;
  }
  router.push(`/login/${roleId}`);
};
</script>

<style scoped>
@keyframes gradient {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient 6s ease infinite;
}
</style>
