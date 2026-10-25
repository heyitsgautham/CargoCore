<template>
    <Teleport to="body">
        <div v-if="isUploadModalOpen"
            class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            @click.self="closeUploadModal">
            <div role="dialog" aria-labelledby="upload-document-title"
                class="lm-vehicle-modal bg-slate-950/98 w-full max-w-md rounded-2xl shadow-2xl border border-white/10 overflow-hidden flex flex-col max-h-[90vh] backdrop-blur-xl">
                <div class="px-6 py-4 border-b border-white/10 flex justify-between items-center bg-slate-900/90">
                    <h3 id="upload-document-title" class="text-lg font-bold text-white">
                        Upload {{ uploadMode === 'VEHICLE' ? 'Vehicle' : 'Driver' }} Document
                    </h3>
                    <button @click="closeUploadModal" class="text-gray-400 hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="p-6 space-y-4 overflow-y-auto bg-slate-950/95 text-slate-200">
                    <div>
                        <label for="upload-entity" class="block text-sm font-medium mb-1">
                            {{ uploadMode === 'VEHICLE' ? 'Vehicle' : 'Driver' }}
                        </label>
                        <select id="upload-entity" v-model="uploadFormData.entityId"
                            class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-primary/50">
                            <option value="" disabled>Select {{ uploadMode === 'VEHICLE' ? 'a vehicle' : 'a driver' }}</option>
                            <option v-for="entity in uploadEntities" :key="entity.id" :value="entity.id">{{ entity.label }}</option>
                        </select>
                    </div>

                    <div>
                        <label for="upload-doc-type" class="block text-sm font-medium mb-1">Document type</label>
                        <select id="upload-doc-type" v-model="uploadFormData.docType"
                            class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-primary/50">
                            <option value="" disabled>Select a type</option>
                            <option v-for="type in uploadDocTypes" :key="type" :value="type">{{ type }}</option>
                        </select>
                    </div>

                    <div>
                        <label for="upload-expiry" class="block text-sm font-medium mb-1">Expiry date</label>
                        <input id="upload-expiry" v-model="uploadFormData.expiryDate" type="date"
                            class="w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-primary/50">
                    </div>

                    <div>
                        <span class="block text-sm font-medium mb-1">File</span>
                        <label class="w-full flex items-center justify-center gap-2 cursor-pointer bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-lg px-3 py-2 text-xs font-bold text-primary transition-colors h-[38px]">
                            <span class="material-symbols-outlined text-[16px]">cloud_upload</span>
                            <span class="truncate">{{ uploadFormData.fileName || 'Choose PDF or image' }}</span>
                            <input type="file" class="hidden" accept="image/*,.pdf" @change="handleUploadFile">
                        </label>
                    </div>

                    <p v-if="uploadError" class="text-sm text-red-400">{{ uploadError }}</p>
                </div>

                <div class="px-6 py-4 border-t border-white/10 flex justify-end gap-3 bg-slate-900/90">
                    <button @click="closeUploadModal"
                        class="px-4 py-2 rounded-lg font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors shadow-sm">Cancel</button>
                    <button @click="submitUpload" :disabled="!canSubmitUpload"
                        class="px-4 py-2 rounded-lg font-medium text-white flex items-center justify-center gap-2 min-w-[120px] bg-primary hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed">
                        <span v-if="uploading" class="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin"></span>
                        <span>{{ uploading ? 'Uploading...' : 'Upload' }}</span>
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    isUploadModalOpen,
    uploadMode,
    uploadFormData,
    uploading,
    uploadError,
    uploadEntities,
    uploadDocTypes,
    canSubmitUpload,
    closeUploadModal,
    handleUploadFile,
    submitUpload,
} = inject(fleetPageKey)
</script>

<style scoped src="./fleetModal.css"></style>
