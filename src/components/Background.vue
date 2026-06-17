<template>
  <div class="relative min-h-screen w-full overflow-hidden bg-[#0A1428]">
    <!-- Background Image with Grain Texture -->
    <div class="absolute inset-0">
      <div
        class="absolute inset-0 bg-cover bg-center bg-no-repeat"
        :style="{
          backgroundImage: `url(${imageUrl})`,
          filter: blur ? 'blur(8px)' : 'none',
          opacity: 0.35,
          transform: 'scale(1.1)',
        }"
      />
      <!-- Grain Texture Overlay -->
      <div
        class="absolute inset-0 opacity-[0.03]"
        :style="{
          backgroundImage: `url('data:image/svg+xml,%3Csvg viewBox=\'0 0 400 400\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'3.5\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E')`
        }"
      />
      <!-- Dark Overlay -->
      <div
        class="absolute inset-0 bg-gradient-to-b from-[#0A1428]/80 via-[#0A1428]/90 to-[#0A1428]"
        :style="{ opacity: overlay }"
      />
    </div>

    <!-- Content -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  imageUrl: String,
  overlay: Number,
  blur: Boolean,
});

defineOptions({
  name: 'Background',
});
</script>
