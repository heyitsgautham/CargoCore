// What a vendor can do with the selected shipment: change the address, reschedule,
// cancel, report damage, rate the driver, message the driver and raise a support ticket.
import { reactive, ref } from 'vue'

export function showToast(msg, type = 'success') {
    const t = document.createElement('div')
    const bg = type === 'error' ? 'bg-red-500' : 'bg-green-500'
    t.className = `fixed right-4 bottom-4 z-[9999] ${bg} text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl`
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

export function useShipmentActions(store, selected) {
    const showAddressModal = ref(false)
    const showRescheduleModal = ref(false)
    const showDamageModal = ref(false)
    const showSupportModal = ref(false)
    const showCallModal = ref(false)
    const showChatModal = ref(false)
    const newAddress = ref('')
    const newDate = ref('')
    const rescheduleReason = ref('')
    const supportMessage = ref('')
    const newChatMessage = ref('')
    const chatMessages = ref([])
    const damageForm = reactive({ severity: 'Medium', description: '' })
    const vendorRatingModal = reactive({ show: false, order: null, selected: 0, hover: 0, feedback: '' })

    function sendChatMessage() {
        if (!newChatMessage.value.trim()) return
        chatMessages.value.push({
            text: newChatMessage.value,
            time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
        })
        newChatMessage.value = ''

        // Auto reply mock
        setTimeout(() => {
            showToast('Driver received your message')
        }, 1500)
    }

    function handleFileUpload(event) {
        const file = event.target.files[0]
        if (!file) return

        // Create a mock chat message with the file
        chatMessages.value.push({
            text: `📎 Attached: ${file.name}`,
            time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
        })

        // Reset file input
        event.target.value = ''
        showToast('File attached successfully')
    }

    function submitSupport() {
        if (!selected.value || !supportMessage.value.trim()) return
        store.addTicket({
            subject: `Support needed for ${selected.value.id}`,
            description: supportMessage.value,
            orderId: selected.value.id,
            priority: 'Medium'
        })
        showSupportModal.value = false
        supportMessage.value = ''
        showToast('Support ticket created successfully')
    }

    async function updateAddress() {
        if (!selected.value || !newAddress.value.trim()) return
        await store.updateShipmentAddress(selected.value.id, newAddress.value.trim())
        showAddressModal.value = false
        newAddress.value = ''
        showToast('Address updated successfully')
    }

    async function reschedule() {
        if (!selected.value || !newDate.value) return
        const formatted = new Date(newDate.value).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
        await store.rescheduleShipment(selected.value.id, formatted)
        showRescheduleModal.value = false
        newDate.value = ''
        rescheduleReason.value = ''
        showToast('Delivery rescheduled')
    }

    async function handleCancel() {
        if (!selected.value) return
        if (confirm(`Cancel shipment ${selected.value.id}? This action cannot be undone.`)) {
            await store.cancelShipment(selected.value.id)
            showToast('Shipment cancelled')
        }
    }

    async function submitDamage() {
        if (!selected.value || !damageForm.description.trim()) return
        await store.reportDamage(selected.value.id, { ...damageForm, photos: [] })
        showDamageModal.value = false
        damageForm.severity = 'Medium'
        damageForm.description = ''
        showToast('Damage report submitted — reverse logistics ticket created')
    }

    function openVendorRatingModal(shipment = selected.value) {
        if (!shipment) return
        Object.assign(vendorRatingModal, {
            show: true,
            order: shipment,
            selected: Number(shipment.customerRating || 0),
            hover: 0,
            feedback: shipment.customerFeedback || '',
        })
    }

    async function submitVendorRating() {
        if (!vendorRatingModal.selected || !vendorRatingModal.order?.backendId) return
        const result = await store.submitCustomerRating(
            vendorRatingModal.order.backendId,
            vendorRatingModal.selected,
            vendorRatingModal.feedback || null
        )
        vendorRatingModal.show = false
        showToast(
            result.success ? 'Thanks for rating your driver!' : (result.message || 'Failed to submit rating.'),
            result.success ? 'success' : 'error'
        )
    }

    return {
        showAddressModal,
        showRescheduleModal,
        showDamageModal,
        showSupportModal,
        showCallModal,
        showChatModal,
        newAddress,
        newDate,
        rescheduleReason,
        supportMessage,
        newChatMessage,
        chatMessages,
        damageForm,
        vendorRatingModal,
        sendChatMessage,
        handleFileUpload,
        submitSupport,
        updateAddress,
        reschedule,
        handleCancel,
        submitDamage,
        openVendorRatingModal,
        submitVendorRating,
    }
}
