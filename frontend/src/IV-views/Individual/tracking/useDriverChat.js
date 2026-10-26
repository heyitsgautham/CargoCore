// The quick chat with the assigned driver on the tracking page.
import { ref, nextTick } from 'vue'

export function useDriverChat() {
    // ─── Modals State ───
    const showCallModal = ref(false)
    const showChatModal = ref(false)

    const chatMessages = ref([
        { text: 'Okay perfect. Please park near Gate B.', time: '10:48 AM' }
    ])
    const pendingMessage = ref('')
    const chatScrollContainer = ref(null)

    const sendChatMessage = () => {
        if (!pendingMessage.value.trim()) return

        chatMessages.value.push({
            text: pendingMessage.value,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        })
        pendingMessage.value = ''

        nextTick(() => {
            if (chatScrollContainer.value) {
                chatScrollContainer.value.scrollTop = chatScrollContainer.value.scrollHeight
            }
        })
    }

    return {
        showCallModal,
        showChatModal,
        chatMessages,
        pendingMessage,
        chatScrollContainer,
        sendChatMessage,
    }
}
