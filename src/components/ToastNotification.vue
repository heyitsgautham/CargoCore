<template>
  <Teleport to="body">
    <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none" style="min-width: 300px; max-width: 380px;">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl backdrop-blur-xl border shadow-2xl"
          :class="toastClasses[toast.type]"
        >
          <!-- Icon -->
          <div class="flex-shrink-0 mt-0.5">
            <CheckCircle2 v-if="toast.type === 'success'" class="w-5 h-5" />
            <XCircle      v-else-if="toast.type === 'error'"   class="w-5 h-5" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5" />
            <Info          v-else                               class="w-5 h-5" />
          </div>
          <!-- Message -->
          <p class="text-sm font-medium leading-snug flex-1">{{ toast.message }}</p>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-vue-next';
import { useToast } from '../composables/useToast';

const { toasts } = useToast();

const toastClasses = {
  success: 'bg-[#00C4FF]/15 border-[#00C4FF]/40 text-[#00E4FF]',
  error:   'bg-red-500/15   border-red-500/40   text-red-400',
  warning: 'bg-[#FF9500]/15 border-[#FF9500]/40 text-[#FF9500]',
  info:    'bg-white/10     border-white/20      text-white/90',
};
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
}
.toast-leave-active {
  transition: all 0.25s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px) scale(0.9);
}
</style>
