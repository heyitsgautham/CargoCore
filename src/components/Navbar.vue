<template>
  <nav class="relative top-0 left-0 right-0 z-50 px-8 py-4">
    <div class="max-w-[1440px] mx-auto flex items-center justify-between">
      <!-- Logo -->
      <div
        v-motion
        :initial="{ opacity: 0, x: -20 }"
        :enter="{ opacity: 1, x: 0, transition: { duration: 500 } }"
      >
        <img
          src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
          alt="Cargo Core Logo"
          class="h-[80px] w-auto cursor-pointer hover:opacity-90 transition-opacity duration-300"
          @click="router.push('/')"
        />
      </div>

      <!-- Role Info (if present) -->
      <div
        v-if="showRoleInfo"
        v-motion
        :initial="{ opacity: 0, y: -10 }"
        :enter="{ opacity: 1, y: 0 }"
        class="flex items-center gap-3 px-5 py-2.5 rounded-full bg-white/5 backdrop-blur-xl border border-[#00C4FF30]"
      >
        <span class="text-white/90 text-sm">
          Logging in as <span class="text-[#00C4FF] font-semibold">{{ showRoleInfo.role }}</span>
        </span>
        <button
          v-if="showRoleInfo.onChangeRole"
          @click="showRoleInfo.onChangeRole"
          class="text-xs text-white/60 hover:text-[#00C4FF] transition-colors duration-300 underline underline-offset-2"
        >
          Change role
        </button>
      </div>

    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router';

defineProps({
  showRoleInfo: { type: Object, default: null },
});

const router = useRouter();
</script>
