<template>
  <Teleport to="body">
    <!-- Floating Orb Button -->
    <button
      @click="toggleOpen"
      class="fixed bottom-8 right-8 z-50 group"
      aria-label="Open AI Chat"
    >
      <div class="relative w-16 h-16 rounded-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center cursor-pointer hover:scale-110 transition-transform duration-300 shadow-[0_0_28px_rgba(0,196,255,0.4)]">
        <!-- Pulse ring when open -->
        <span v-if="isOpen" class="absolute inset-0 rounded-full animate-ping bg-blue-400 opacity-20"></span>
        <span class="material-symbols-outlined text-white text-[26px]">{{ isOpen ? 'close' : 'smart_toy' }}</span>
      </div>
      <!-- Badge: unread count or label -->
      <span class="absolute -top-1 -left-1 bg-[#00C4FF] text-[10px] text-white font-bold px-1.5 py-0.5 rounded-full leading-none">
        {{ unreadCount > 0 ? unreadCount : 'AI' }}
      </span>
    </button>

    <!-- Chat Panel -->
    <Transition name="chat-panel">
      <div
        v-if="isOpen"
        class="fixed bottom-32 right-8 z-50 w-[380px] max-w-[calc(100vw-2rem)] bg-[#07111f]/96 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl flex flex-col overflow-hidden"
        style="height: 520px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-white/10 bg-white/5 flex-shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center">
              <span class="material-symbols-outlined text-white text-[18px]">smart_toy</span>
            </div>
            <div>
              <h3 class="text-white font-semibold text-sm">Cargo AI Assistant</h3>
              <div class="flex items-center gap-1.5 mt-0.5">
                <span class="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                <span class="text-[10px] text-gray-400">Online · {{ roleLabel }} mode · Powered by Gemini</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button @click="startNewChat" title="New chat" class="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
              <span class="material-symbols-outlined text-white/50 hover:text-white text-[18px]">add_comment</span>
            </button>
            <button @click="close" class="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
              <span class="material-symbols-outlined text-white/50 hover:text-white text-[18px]">close</span>
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div ref="chatContainer" class="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          <!-- Welcome state -->
          <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full gap-3 text-center opacity-70">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex items-center justify-center shadow-lg">
              <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
            </div>
            <p class="text-white/80 font-medium text-sm">Hi {{ auth.userName || '' }}! I'm your AI Assistant.</p>
            <p class="text-white/40 text-xs leading-relaxed max-w-[220px]">{{ welcomeHint }}</p>
          </div>

          <!-- Message bubbles -->
          <div
            v-for="(msg, i) in messages"
            :key="msg.id || i"
            class="flex gap-2.5"
            :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
          >
            <!-- Avatar -->
            <div class="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5"
              :class="msg.role === 'user'
                ? 'bg-white/10 text-white/70'
                : msg.role === 'support'
                  ? 'bg-gradient-to-br from-orange-500 to-orange-700 text-white'
                  : 'bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] text-white'">
              {{ msg.role === 'user' ? 'ME' : msg.role === 'support' ? 'SUP' : 'AI' }}
            </div>
            <div class="max-w-[78%] space-y-1">
              <!-- Support message label -->
              <div v-if="msg.role === 'support' && msg.ref" class="flex items-center gap-1 px-1 mb-0.5">
                <span class="material-symbols-outlined text-orange-400 text-[12px]">support_agent</span>
                <span class="text-[10px] text-orange-400 font-medium">Support · {{ msg.ref }}</span>
              </div>
              <div class="px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed"
                :class="msg.role === 'user'
                  ? 'bg-[#00C4FF]/20 border border-[#00C4FF]/30 rounded-tr-none text-white'
                  : msg.role === 'support'
                    ? 'bg-orange-500/10 border border-orange-500/30 rounded-tl-none text-white/90'
                    : 'bg-white/8 border border-white/10 rounded-tl-none text-white/90'">
                <span v-html="msg.text"></span>
              </div>
              <div class="text-[10px] text-white/30 px-1" :class="msg.role === 'user' ? 'text-right' : ''">{{ msg.time }}</div>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="isTyping" class="flex gap-2.5 animate-pulse">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-[#00C4FF] to-[#1E3A8A] flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white">AI</div>
            <div class="bg-white/8 border border-white/10 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
              <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
              <span class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
            </div>
          </div>
        </div>

        <!-- Suggestion chips -->
        <div v-if="messages.length === 0" class="px-4 pb-2 flex gap-2 overflow-x-auto no-scrollbar">
          <button
            v-for="chip in defaultChips"
            :key="chip"
            @click="sendChip(chip)"
            class="whitespace-nowrap text-[11px] px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-white/60 hover:text-white transition-colors flex-shrink-0"
          >{{ chip }}</button>
        </div>

        <!-- Input -->
        <div class="px-4 py-3 border-t border-white/10 bg-white/3 flex-shrink-0">
          <div class="flex items-center gap-2">
            <input
              v-model="userInput"
              @keydown.enter.exact.prevent="handleSend"
              type="text"
              placeholder="Type a message…"
              class="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-[#00C4FF]/50 transition-colors"
            />
            <button
              @click="handleSend"
              :disabled="!userInput.trim() || isTyping"
              class="w-9 h-9 flex items-center justify-center bg-[#00C4FF] hover:bg-[#00b3eb] rounded-xl transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            >
              <span class="material-symbols-outlined text-white text-[16px]">send</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, computed, onUnmounted } from 'vue'
import { sendChat, fetchSessions, fetchConversation } from '@/utils/aiApi'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()

const isOpen = ref(false)
const userInput = ref('')
const isTyping = ref(false)
const chatContainer = ref(null)
const messages = ref([])
const sessionId = ref(null)
const historyLoaded = ref(false)
// ISO string of the last server message we know about — used to detect new support messages
let lastLoadedAt = null
let pollTimer = null

const roleName = computed(() => String(auth.userRole || '').toUpperCase())
const roleLabel = computed(() => {
  if (roleName.value === 'VENDOR') return 'Vendor'
  if (roleName.value === 'INDIVIDUAL') return 'Customer'
  return 'General'
})

const welcomeHint = computed(() => {
  if (roleName.value === 'VENDOR') {
    return 'Ask me about your vendor shipments, inbound schedules, invoices, and wallet balance.'
  }
  if (roleName.value === 'INDIVIDUAL') {
    return 'Ask me about your move bookings, tracking, estimates, payments, and support.'
  }
  return 'Ask me about your orders, bookings, tracking, estimates, or anything about Cargo Core.'
})

const defaultChips = computed(() => {
  if (roleName.value === 'VENDOR') {
    return [
      'Show my pending vendor shipments',
      'Do I have any overdue invoices?',
      'What is my current wallet balance?',
      'Talk to a human agent',
    ]
  }
  if (roleName.value === 'INDIVIDUAL') {
    return [
      'Where is my order?',
      'Estimate cost for my move',
      'Show my recent bookings',
      'Talk to a human agent',
    ]
  }
  return [
    'Where is my order?',
    'How do I book a move?',
    'Estimate cost for my move',
    'Talk to a human agent',
  ]
})

const unreadCount = ref(0)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function formatText(raw) {
  return String(raw)
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/\n/g, '<br>')
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// ── History loading ──────────────────────────────────────────────────────────

const SUPPORT_PREFIX_RE = /^\[Support — ([^\]]+)\]\s*/

function mapServerMsg(m, idx) {
  if (['support_message', 'agent_reply', 'handover'].includes(m.intent)) {
    const match = m.message.match(SUPPORT_PREFIX_RE)
    return {
      id: `h-${m.created_at}-${idx}`,
      role: 'support',
      ref: match ? match[1] : null,
      text: formatText(m.message.replace(SUPPORT_PREFIX_RE, '')),
      time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      createdAt: m.created_at,
    }
  }
  return {
    id: `h-${m.created_at}-${idx}`,
    role: m.role === 'user' ? 'user' : 'ai',
    text: formatText(m.message),
    time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    createdAt: m.created_at,
  }
}

async function loadHistory() {
  try {
    const { sessions } = await fetchSessions()
    if (!sessions?.length) return
    const sid = sessions[0].session_id
    sessionId.value = sid
    const { messages: hist } = await fetchConversation(sid)
    if (!hist?.length) return
    messages.value = hist.map(mapServerMsg)
    lastLoadedAt = hist[hist.length - 1].created_at
    historyLoaded.value = true
  } catch (err) {
    console.warn('[AIHelpOrb] loadHistory failed:', err)
  }
}

// Polls for new messages (support or otherwise) injected by the backend
async function pollHistory() {
  if (!sessionId.value || isTyping.value) return
  try {
    const { messages: hist } = await fetchConversation(sessionId.value)
    if (!hist?.length) return
    const newHist = lastLoadedAt
      ? hist.filter(m => m.created_at > lastLoadedAt)
      : []
    if (!newHist.length) return
    const offset = hist.length - newHist.length
    const newMsgs = newHist.map((m, i) => mapServerMsg(m, offset + i))
    messages.value.push(...newMsgs)
    lastLoadedAt = hist[hist.length - 1].created_at
    const supportCount = newMsgs.filter(m => m.role === 'support').length
    if (!isOpen.value && supportCount > 0) unreadCount.value += supportCount
    if (isOpen.value) await scrollToBottom()
  } catch { /* ignore transient poll errors */ }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollHistory, 15_000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onUnmounted(stopPolling)

// ── Sending ──────────────────────────────────────────────────────────────────

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return

  userInput.value = ''
  messages.value.push({ id: `u-${Date.now()}`, role: 'user', text, time: now() })
  isTyping.value = true
  await scrollToBottom()

  try {
    const res = await sendChat(text, sessionId.value)
    if (res.session_id) sessionId.value = res.session_id

    const reply = formatText(res.message || `I'm here to help!`)
    messages.value.push({
      id: `ai-${Date.now()}`,
      role: ['handover', 'agent_reply', 'support_message'].includes(res.intent) ? 'support' : 'ai',
      text: reply,
      time: now(),
    })

    // Advance lastLoadedAt so the next poll skips these locally-added messages
    lastLoadedAt = new Date().toISOString()

    if (!isOpen.value) unreadCount.value++
  } catch (err) {
    messages.value.push({
      id: `ai-err-${Date.now()}`,
      role: 'ai',
      text: `<span class="text-red-400">⚠ ${err.message || 'Something went wrong. Please try again.'}</span>`,
      time: now(),
    })
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

function sendChip(chip) {
  userInput.value = chip
  handleSend()
}

function startNewChat() {
  messages.value = []
  sessionId.value = null
  historyLoaded.value = false
  lastLoadedAt = null
  unreadCount.value = 0
  stopPolling()
}

async function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    unreadCount.value = 0
    if (!historyLoaded.value) await loadHistory()
    startPolling()
    nextTick(scrollToBottom)
  } else {
    stopPolling()
  }
}

function close() {
  isOpen.value = false
  stopPolling()
}
</script>

<style scoped>
.chat-panel-enter-active, .chat-panel-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.chat-panel-enter-from, .chat-panel-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.96);
}
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
