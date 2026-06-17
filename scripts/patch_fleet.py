import sys

path = 'c:/Users/pruth/Downloads/Login Signup Flow Design/src/LWD-views/LogisticManager/FleetManagement.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

script_vars = '''
// Document Upload State
const isUploadModalOpen = ref(false)
const uploadMode = ref('VEHICLE') // 'VEHICLE' or 'DRIVER'
const uploadFormData = ref({
    entityId: '',
    docType: '',
    expiryDate: '',
    fileBase64: null,
    fileName: ''
})

const openUploadModal = (mode) => {
    uploadMode.value = mode
    uploadFormData.value = {
        entityId: '',
        docType: '',
        expiryDate: '',
        fileBase64: null,
        fileName: ''
    }
    isUploadModalOpen.value = true
}

const closeUploadModal = () => {
    isUploadModalOpen.value = false
}

const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
        uploadFormData.value.fileName = file.name
        const reader = new FileReader()
        reader.onload = (e) => {
            uploadFormData.value.fileBase64 = e.target.result
        }
        reader.readAsDataURL(file)
    }
}

const submitDocument = async () => {
    if (!uploadFormData.value.entityId || !uploadFormData.value.docType) return
    
    await store.uploadDocument({
        entity_type: uploadMode.value,
        entity_id: uploadFormData.value.entityId,
        hub_id: store.activeWarehouse === 'all' ? null : store.activeWarehouse,
        doc_type: uploadFormData.value.docType,
        document_url: uploadFormData.value.fileBase64 || f\"https://placehold.co/400x500?text={uploadFormData.value.docType.replace(' ', '+')}+Upload\",
        expiry_date: uploadFormData.value.expiryDate ? new Date(uploadFormData.value.expiryDate).toISOString() : null
    })
    closeUploadModal()
}

const verifyDocumentStatus = async (docId, status) => {
    await store.updateDocumentStatus(docId, status)
    activeDoc.value = null // Close the viewer
}

// Share Modal State
'''

content = content.replace('// Share Modal State', script_vars)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patch complete!')
