// Viewing, expanding and sharing vehicle and driver documents.
import { ref } from 'vue'

export function useFleetDocuments(store) {
    const activeDoc = ref(null)
    const expandedDocs = ref([]) // IDs of expanded rows

    const isShareModalOpen = ref(false)
    const shareStep = ref('select') // 'select' or 'form'
    const shareFormData = ref({
        activeDocId: null,
        hubId: store.activeWarehouse === 'all' ? 1 : store.activeWarehouse,
        role: 'dispatcher', // dispatcher or manager
        message: ''
    })

    const downloadDoc = (doc) => {
        window.alert(`Starting download for ${doc.type}.pdf...`)
    }

    const printDoc = (_doc) => {
        window.print()
    }

    const openShareModal = () => {
        isShareModalOpen.value = !isShareModalOpen.value
        // Reset form if opening fresh
        if (isShareModalOpen.value) {
            shareStep.value = 'select'
            shareFormData.value = {
                activeDocId: activeDoc.value.id,
                hubId: activeDoc.value.hubId || (store.activeWarehouse === 'all' ? 1 : store.activeWarehouse),
                role: 'dispatcher',
                message: `Please review attached ${activeDoc.value.type} for ${activeDoc.value.vehicleId || activeDoc.value.driver}.`
            }
        }
    }

    const shareVia = (platform) => {
        if (platform === 'whatsapp') {
            window.open(`https://wa.me/?text=Check this document: ${activeDoc.value.url}`, '_blank')
            isShareModalOpen.value = false
        } else if (platform === 'telegram') {
            window.open(`https://t.me/share/url?url=${activeDoc.value.url}&text=Check this document`, '_blank')
            isShareModalOpen.value = false
        } else if (platform === 'cargocore') {
            shareStep.value = 'form'
        }
    }

    const submitShare = () => {
        // Mock API call to internal messaging system
        console.log('Sending CargoCore Message:', {
            docId: shareFormData.value.activeDocId,
            hubId: shareFormData.value.hubId,
            role: shareFormData.value.role,
            message: shareFormData.value.message
        })

        // Simulate success
        window.alert(`Document sent to ${shareFormData.value.role === 'dispatcher' ? 'Dispatch Team' : 'Warehouse Manager'} successfully!`)
        isShareModalOpen.value = false
    }

    const toggleDocExpand = (id) => {
        if (expandedDocs.value.includes(id)) {
            expandedDocs.value = expandedDocs.value.filter(e => e !== id)
        } else {
            expandedDocs.value.push(id)
        }
    }

    const openDocModal = (doc) => {
        activeDoc.value = doc
    }

    const closeDocModal = () => {
        activeDoc.value = null
    }

    return {
        activeDoc,
        expandedDocs,
        isShareModalOpen,
        shareStep,
        shareFormData,
        downloadDoc,
        printDoc,
        openShareModal,
        shareVia,
        submitShare,
        toggleDocExpand,
        openDocModal,
        closeDocModal,
    }
}
