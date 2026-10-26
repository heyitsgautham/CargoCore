<template>
    <!-- Customer Photo Preview Modal (Damage Review) -->
    <Teleport to="body">
        <div v-if="reviewPhotoPreview"
            class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="reviewPhotoPreview = null">
            <div class="relative max-w-3xl w-full">
                <button @click="reviewPhotoPreview = null"
                    class="absolute -top-10 right-0 text-white/70 hover:text-white">
                    <span class="material-symbols-outlined text-3xl">close</span>
                </button>
                <img :src="reviewPhotoPreview" alt="Customer damage photo"
                    class="w-full max-h-[80vh] object-contain rounded-xl shadow-2xl" />
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { returnsWarehousePageKey } from './returnsWarehousePageContext'

const { reviewPhotoPreview } = inject(returnsWarehousePageKey)
</script>
