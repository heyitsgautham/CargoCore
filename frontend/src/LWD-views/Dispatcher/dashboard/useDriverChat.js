// The quick chat with a driver from the roster. Messages go to the driver
// through the dispatcher store, and the reply bubble is a local acknowledgement.
import { ref } from 'vue'

export function useDriverChat(store) {
    const showChatModal = ref(false)
    const chatDriver = ref(null)
    const chatMsg = ref('')
    const driverChatMessages = ref([])
    let chatMsgId = 1
    function chatWithDriver(driver) {
        chatDriver.value = driver
        driverChatMessages.value = [
            { id: chatMsgId++, from: 'driver', text: `Hi dispatch, I'm at ${driver.location}. Ready for next instructions.` },
            { id: chatMsgId++, from: 'dispatch', text: `Copy ${driver.name.split(' ')[0]}. Stand by for assignment update.` }
        ]
        showChatModal.value = true
    }

    function sendDriverMsg() {
        if (!chatMsg.value.trim()) return
        const text = chatMsg.value
        driverChatMessages.value.push({ id: chatMsgId++, from: 'dispatch', text })
        chatMsg.value = ''
        store.sendMessageToDriver(chatDriver.value?.id, text)
        setTimeout(() => {
            driverChatMessages.value.push({ id: chatMsgId++, from: 'driver', text: text.includes('?') ? 'Yes, copy that. I\'ll check and confirm.' : 'Roger, acknowledged.' })
        }, 1000)
    }

    return { showChatModal, chatDriver, chatMsg, driverChatMessages, chatWithDriver, sendDriverMsg }
}
