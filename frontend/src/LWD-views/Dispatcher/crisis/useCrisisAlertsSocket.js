import { onMounted, onUnmounted } from 'vue'
import { getStoredAccessToken } from '@/config/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE = API_BASE.replace(/^http/, 'ws')
const RECONNECT_MS = 5000

/**
 * Listens on ws/fleet for drivers' SOS messages and refreshes alerts the moment one arrives,
 * so the crisis card and map marker appear without waiting for a poll.
 * Reconnects after an unexpected close while the page is open.
 */
export function useCrisisAlertsSocket(onCrisisAlert) {
  let socket = null

  function connect() {
    const token = getStoredAccessToken()
    if (!token) return
    socket = new WebSocket(`${WS_BASE}/ws/fleet?token=${encodeURIComponent(token)}`)

    socket.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'crisis_alert') await onCrisisAlert()
      } catch {
        /* ignore malformed frames */
      }
    }

    socket.onclose = () => {
      setTimeout(() => {
        if (socket?.readyState === WebSocket.CLOSED) connect()
      }, RECONNECT_MS)
    }
  }

  onMounted(connect)
  onUnmounted(() => {
    socket?.close()
    socket = null
  })
}
