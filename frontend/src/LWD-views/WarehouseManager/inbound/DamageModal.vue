<template>
    <!-- Damage Modal -->
    <Teleport to="body">
        <div v-if="showDamageModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="showDamageModal = false">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10">
                <div class="p-6 border-b border-gray-100 dark:border-white/5 flex justify-between items-center">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg">Report Shipment Damage</h3>
                    <button @click="showDamageModal = false"
                        class="text-gray-500 hover:text-gray-900 dark:text-white"><span
                            class="material-symbols-outlined">close</span></button>
                </div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">ASN ID</label>
                        <select v-model="damageForm.asnId"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option v-for="asn in asns" :key="asn.id" :value="asn.id" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">{{ asn.id }} — {{
                                asn.supplier }}
                            </option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damaged Items
                            Count</label>
                        <input type="number" v-model.number="damageForm.count" placeholder="0"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damage
                            Description</label>
                        <textarea v-model="damageForm.description" placeholder="Describe the damage..."
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-3 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm h-20 resize-none"></textarea>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Damage Camera Capture</label>
                        <div v-if="!damagePhoto" @click="openDamageCamera"
                            class="p-6 rounded-lg border-2 border-dashed text-center cursor-pointer transition-colors bg-gray-50 dark:bg-white/5 border-gray-300 dark:border-white/10 hover:border-primary/50 hover:bg-gray-100 dark:hover:bg-white/10">
                            <span class="material-symbols-outlined text-4xl text-gray-400 dark:text-gray-500">photo_camera</span>
                            <div class="text-sm mt-2 text-gray-600 dark:text-gray-400 font-medium">Open camera and capture damage photo</div>
                        </div>
                        <div v-else class="relative rounded-lg overflow-hidden border border-gray-200 dark:border-white/10">
                            <img :src="damagePhoto" class="w-full h-48 object-cover cursor-pointer" @click="viewImage(damagePhoto)" />
                            <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent pointer-events-none"></div>
                            <div class="absolute bottom-0 left-0 right-0 p-3 flex items-center justify-between">
                                <div class="flex items-center gap-2 text-white text-xs font-bold">
                                    <span class="material-symbols-outlined text-[16px]">check_circle</span>
                                    Photo captured
                                </div>
                                <div class="flex gap-2">
                                    <button @click.stop="viewImage(damagePhoto)" class="px-3 py-1 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded text-xs font-bold transition-colors">
                                        View
                                    </button>
                                    <button @click.stop="retakeDamagePhoto" class="px-3 py-1 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded text-xs font-bold transition-colors">
                                        Retake
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button @click="submitDamage" :disabled="!damageForm.asnId"
                        class="w-full bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-600 dark:text-yellow-400 font-bold py-3 rounded-lg transition-colors">
                        Submit Damage Report
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { inboundPageKey } from './inboundPageContext'

const {
    asns,
    damageForm,
    damagePhoto,
    openDamageCamera,
    retakeDamagePhoto,
    showDamageModal,
    submitDamage,
    viewImage,
} = inject(inboundPageKey)
</script>
