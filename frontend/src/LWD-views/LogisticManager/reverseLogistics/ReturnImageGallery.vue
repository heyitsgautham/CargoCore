<template>
    <!-- Image Gallery Modal -->
    <Teleport to="body">
        <div v-if="showImageModal" class="fixed inset-0 bg-black/90 backdrop-blur-md z-[60] flex items-center justify-center p-4 animate-fade-in" @click.self="showImageModal = false">
            <div class="w-full max-w-4xl h-[80vh] flex flex-col relative">
                <div class="absolute top-0 left-0 w-full p-4 flex justify-between items-start z-10 pointer-events-none">
                    <div class="pointer-events-auto">
                        <span class="bg-white/10 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-mono border border-white/20">
                            {{ selectedRMA?.referenceCode || selectedRMA?.id }}
                        </span>
                    </div>
                    <button @click="showImageModal = false" class="pointer-events-auto text-white/50 hover:text-white bg-black/50 hover:bg-black/80 rounded-full p-2 transition-all">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="flex-1 flex items-center justify-center relative overflow-hidden rounded-xl bg-black border border-white/10">
                    <img v-if="selectedImages.length > 0"
                         :src="selectedImages[activeImageIndex]"
                         class="max-h-full max-w-full object-contain transition-opacity duration-300"
                         :key="activeImageIndex"
                         alt="Claim proof">
                    <div v-else class="text-white/40 flex flex-col items-center gap-3 px-6 text-center">
                        <span class="material-symbols-outlined text-6xl">broken_image</span>
                        <template v-if="legacyFileNames.length > 0">
                            <p class="text-sm font-medium text-white/60">Image preview unavailable</p>
                            <p class="text-xs text-white/30 max-w-xs">This report was submitted before image upload was supported. The customer attached {{ legacyFileNames.length }} file(s) but only the filename(s) were saved.</p>
                            <div class="mt-1 space-y-1">
                                <div v-for="name in legacyFileNames" :key="name" class="text-[11px] font-mono bg-white/10 px-3 py-1 rounded-full text-white/50">{{ name }}</div>
                            </div>
                            <p class="text-[11px] text-amber-400/70 mt-2">Ask the customer to resubmit with the new report form to view images.</p>
                        </template>
                        <template v-else>
                            <p class="text-sm">No images attached to this report.</p>
                        </template>
                    </div>
                    <button v-if="selectedImages.length > 1"
                            @click="activeImageIndex = (activeImageIndex - 1 + selectedImages.length) % selectedImages.length"
                            class="absolute left-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white text-white hover:text-black rounded-full p-4 hover:shadow-lg transition-all backdrop-blur-md">
                        <span class="material-symbols-outlined text-2xl">chevron_left</span>
                    </button>
                    <button v-if="selectedImages.length > 1"
                            @click="activeImageIndex = (activeImageIndex + 1) % selectedImages.length"
                            class="absolute right-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white text-white hover:text-black rounded-full p-4 hover:shadow-lg transition-all backdrop-blur-md">
                        <span class="material-symbols-outlined text-2xl">chevron_right</span>
                    </button>
                </div>
                <div v-if="selectedImages.length > 0" class="h-24 mt-4 flex gap-2 justify-center overflow-x-auto py-2">
                    <button v-for="(img, idx) in selectedImages" :key="idx"
                        @click="activeImageIndex = idx"
                        class="relative h-full aspect-video rounded-lg overflow-hidden border-2 transition-all"
                        :class="activeImageIndex === idx ? 'border-primary shadow-lg ring-2 ring-primary/30 scale-105' : 'border-transparent opacity-60 hover:opacity-100'">
                        <img :src="img" class="w-full h-full object-cover">
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { reverseLogisticsPageKey } from './reverseLogisticsPageContext'

const {
    activeImageIndex,
    legacyFileNames,
    selectedImages,
    selectedRMA,
    showImageModal,
} = inject(reverseLogisticsPageKey)
</script>
