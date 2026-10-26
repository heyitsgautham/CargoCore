// The logistics and dispatcher AI assistant chats, each with its own session.
import { apiRequest, authHeaders } from './api'

export function useLogisticAssistant({ aiMessages, aiSessionId, dispatcherAiSessionId }) {
    async function askAiDispatcher(query) {
        try {
            const payload = { message: query, context: 'dispatcher' }
            if (dispatcherAiSessionId.value) payload.session_id = dispatcherAiSessionId.value
            const response = await apiRequest('/ai/chat', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(payload),
            })
            if (response.session_id) dispatcherAiSessionId.value = response.session_id
            let text = response.message || response.reply || response.text || 'No response.'
            text = text.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            return { text }
        } catch (err) {
            return { text: 'AI engine unavailable. Please try again.' }
        }
    }

    async function askAi(query) {
        const userMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            text: query,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
        aiMessages.value.push(userMessage)

        try {
            const payload = { message: query, context: 'logistic_manager' }
            if (aiSessionId.value) {
                payload.session_id = aiSessionId.value
            }
            const response = await apiRequest('/ai/chat', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(payload),
            })
            if (response.session_id) {
                aiSessionId.value = response.session_id
            }
            
            let renderedText = response.message || response.reply || response.text || 'Process completed.'
            // Convert basic markdown to HTML for Vue v-html
            renderedText = renderedText.replace(/\n*```sql(.*?)```\n*/gs, '<br><pre class="bg-gray-800 text-green-400 p-3 text-xs rounded-xl my-2 overflow-x-auto shadow-inner">$1</pre><br>')
                .replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
                .replace(/\*(.*?)\*/g, '<i>$1</i>')

            const aiMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                text: renderedText,
                data: null,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            aiMessages.value.push(aiMessage)
            return aiMessage
        } catch (err) {
            console.error('AI Query Error:', err)
            const errorMessage = {
                id: `ai-${Date.now()}`,
                role: 'ai',
                text: `<span class="text-red-500 font-bold">Error:</span> ${err.message || 'Could not connect to the AI engine. Please try again.'}`,
                data: null,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            aiMessages.value.push(errorMessage)
            return errorMessage
        }
    }

    return { askAiDispatcher, askAi }
}
