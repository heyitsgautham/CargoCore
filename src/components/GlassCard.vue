<template>
  <div
    v-motion
    :initial="animate ? { opacity: 0, y: 20 } : undefined"
    :enter="animate ? { opacity: 1, y: 0, transition: { duration: 500 } } : undefined"
    :class="[
      'rounded-2xl bg-white/[0.07] backdrop-blur-[24px]',
      'border border-white/[0.15]',
      'shadow-[0_8px_32px_rgba(0,0,0,0.3)]',
      'transition-all duration-500',
      'hover:border-[#00C4FF]/40 hover:shadow-[0_0_40px_rgba(0,196,255,0.2)]',
      'hover:bg-white/[0.09]',
      className,
    ]"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({
  className: String,
  animate: { type: Boolean, default: true },
});

defineOptions({
  name: 'GlassCard',
});
</script>
