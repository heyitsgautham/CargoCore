<template>
    <!-- Image Viewer Modal -->
    <Teleport to="body">
        <div v-if="viewerImage" class="fixed inset-0 bg-black/90 backdrop-blur-sm z-[999] flex items-center justify-center p-4" @click="viewerImage = null">
            <button @click="viewerImage = null" class="absolute top-4 right-4 text-white hover:text-primary transition-colors">
                <span class="material-symbols-outlined text-[32px]">close</span>
            </button>
            <div class="max-w-4xl max-h-[90vh] w-full" @click.stop>
                <img :src="viewerImage" class="w-full h-full object-contain rounded-lg" />
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const { viewerImage } = inject(inboundPageKey)
</script>
