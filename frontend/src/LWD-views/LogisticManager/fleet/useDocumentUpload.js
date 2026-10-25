// The upload document dialog on the vehicle and driver documents tabs.
import { computed, ref } from 'vue'

export const DOCUMENT_TYPES = {
    VEHICLE: ['Insurance Policy', 'Vehicle Registration', 'Pollution Certificate', 'Fitness Certificate'],
    DRIVER: ['Commercial License (CDL)', 'Medical Certificate', 'Background Verification', 'ID Proof'],
}

function emptyForm() {
    return { entityId: '', docType: '', expiryDate: '', fileBase64: null, fileName: '' }
}

/** The request body for POST /logistics/documents, or null while a required field is missing. */
export function buildDocumentPayload(mode, form, activeWarehouse) {
    if (!form.entityId || !form.docType || !form.fileBase64) return null
    return {
        entity_type: mode,
        entity_id: String(form.entityId),
        hub_id: activeWarehouse === 'all' ? null : activeWarehouse,
        doc_type: form.docType,
        document_url: form.fileBase64,
        expiry_date: form.expiryDate ? new Date(form.expiryDate).toISOString() : null,
    }
}

export function useDocumentUpload(store) {
    const isUploadModalOpen = ref(false)
    const uploadMode = ref('VEHICLE')
    const uploadFormData = ref(emptyForm())
    const uploading = ref(false)
    const uploadError = ref('')

    const uploadEntities = computed(() => (
        uploadMode.value === 'VEHICLE'
            ? store.filteredVehicles.map((v) => ({ id: v.id, label: `${v.code || v.id} · ${v.model || v.type || 'Vehicle'}` }))
            : store.filteredDrivers.map((d) => ({ id: d.id, label: d.name }))
    ))
    const uploadDocTypes = computed(() => DOCUMENT_TYPES[uploadMode.value])
    const canSubmitUpload = computed(() => (
        Boolean(buildDocumentPayload(uploadMode.value, uploadFormData.value, store.activeWarehouse)) && !uploading.value
    ))

    function openUploadModal(mode) {
        uploadMode.value = mode
        uploadFormData.value = emptyForm()
        uploadError.value = ''
        isUploadModalOpen.value = true
    }

    function closeUploadModal() {
        isUploadModalOpen.value = false
    }

    function handleUploadFile(event) {
        const file = event.target.files?.[0]
        if (!file) return
        uploadFormData.value.fileName = file.name
        const reader = new FileReader()
        reader.onload = (e) => {
            uploadFormData.value.fileBase64 = e.target.result
        }
        reader.readAsDataURL(file)
    }

    async function submitUpload() {
        const payload = buildDocumentPayload(uploadMode.value, uploadFormData.value, store.activeWarehouse)
        if (!payload) return
        uploading.value = true
        uploadError.value = ''
        try {
            await store.uploadDocument(payload)
            closeUploadModal()
        } catch (error) {
            uploadError.value = error.message || 'Upload failed. Please try again.'
        } finally {
            uploading.value = false
        }
    }

    return {
        isUploadModalOpen,
        uploadMode,
        uploadFormData,
        uploading,
        uploadError,
        uploadEntities,
        uploadDocTypes,
        canSubmitUpload,
        openUploadModal,
        closeUploadModal,
        handleUploadFile,
        submitUpload,
    }
}
