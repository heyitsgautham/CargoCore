<template>
  <button
    v-motion="{
      hover: disabled ? {} : { scale: 1.02 },
      tap: disabled ? {} : { scale: 0.98 },
    }"
    :disabled="disabled || isLoading"
    :class="[
      'relative px-6 py-3.5 rounded-lg',
      'flex items-center justify-center gap-2',
      'transition-all duration-300',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variants[variant],
      className,
    ]"
    v-bind="$attrs"
  >
    <div v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
    <template v-else>
      <component v-if="icon" :is="icon" />
      <slot />
    </template>

    <div
      v-if="variant === 'primary' && !disabled && !isLoading"
      v-motion
      :animate="{
        background: [
          'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
          'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
        ],
        backgroundPosition: ['-200%', '200%'],
      }"
      :transition="{ duration: 2000, repeat: Infinity, ease: 'linear' }"
      class="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none"
    />
  </button>
</template>

<script setup>
const props = defineProps({
  variant: { type: String, default: 'primary' },
  isLoading: { type: Boolean, default: false },
  icon: Object,
  className: String,
  disabled: { type: Boolean, default: false },
});

defineOptions({
  name: 'GlassButton',
  inheritAttrs: false,
});

const variants = {
  primary: `
    bg-gradient-to-r from-[#00C4FF] via-[#FF9500] to-[#FF6B00]
    text-white font-semibold
    hover:shadow-[0_0_30px_rgba(0,196,255,0.4)]
    hover:scale-[1.02]
    active:scale-[0.98]
  `,
  secondary: `
    bg-white/10 backdrop-blur-xl
    border border-white/20
    text-white font-semibold
    hover:bg-white/15 hover:border-[#00C4FF50]
    hover:shadow-[0_0_20px_rgba(0,196,255,0.2)]
  `,
  ghost: `
    bg-transparent
    text-white/70
    hover:text-white hover:bg-white/5
  `,
};
</script>
