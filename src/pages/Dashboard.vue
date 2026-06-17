<template>
  <div class="min-h-screen bg-[#0A1428] flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-white mb-4">✅ You're In!</h1>
      <p class="text-white/60 text-lg mb-2">Welcome, <span class="text-[#00C4FF] font-semibold">{{ authStore.userName || 'User' }}</span></p>
      <p class="text-white/40 text-sm mb-8">Role: <span class="text-[#FF9500] font-semibold">{{ authStore.userRoleLabel }}</span></p>
      <button
        @click="router.replace(authStore.logout())"
        class="px-6 py-2 rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20 transition"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';

const router = useRouter();
const authStore = useAuthStore();
</script>
