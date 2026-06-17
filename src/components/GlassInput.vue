<template>
  <div class="w-full">
    <div class="relative group">
      <div
        v-if="icon"
        class="absolute left-4 top-1/2 -translate-y-1/2 text-white/50 group-focus-within:text-[#00C4FF] transition-colors duration-300"
      >
        <component :is="icon" />
      </div>
      <input
        v-bind="$attrs"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :class="[
          'w-full px-4 py-3.5',
          icon ? 'pl-12' : '',
          'bg-white/5 backdrop-blur-xl',
          'border border-white/10 rounded-lg',
          'text-white placeholder:text-white/40',
          'focus:outline-none focus:border-[#00C4FF] focus:ring-2 focus:ring-[#00C4FF20]',
          'transition-all duration-300',
          error ? 'border-red-500/50' : '',
          className,
        ]"
      />
    </div>
    <Transition
      name="slide-fade"
      @enter="onEnter"
      @leave="onLeave"
    >
      <p v-if="error" class="mt-1.5 text-sm text-red-400">
        {{ error }}
      </p>
    </Transition>
  </div>
</template>

<script setup>
defineProps({
  modelValue: [String, Number],
  icon: Object,
  error: String,
  className: String,
});

defineEmits(['update:modelValue']);

defineOptions({
  name: 'GlassInput',
  inheritAttrs: false,
});

const onEnter = (el) => {
  const element = el;
  element.style.opacity = '0';
  element.style.transform = 'translateY(-5px)';
  setTimeout(() => {
    element.style.transition = 'opacity 0.3s, transform 0.3s';
    element.style.opacity = '1';
    element.style.transform = 'translateY(0)';
  }, 0);
};

const onLeave = (el) => {
  const element = el;
  element.style.opacity = '0';
  element.style.transform = 'translateY(-5px)';
};
</script>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-5px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
