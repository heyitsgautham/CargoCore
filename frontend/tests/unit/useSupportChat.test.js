import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

vi.mock('@/utils/aiApi', () => ({
  sendChat: vi.fn(),
  fetchConversation: vi.fn(async () => ({ messages: [] })),
}))

const { sendChat } = await import('@/utils/aiApi')
const { useSupportChat } = await import('@/IV-views/Vendor/support/useSupportChat')
const { escapeHtml, formatChatText } = await import('@/utils/html')

function chat() {
  const c = useSupportChat({
    SESSION_KEY: 'test-support-session',
    activeTab: ref('chat'),
    store: { shipments: [] },
  })
  return c
}

describe('vendor support chat rendering', () => {
  afterEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    localStorage.clear()
  })

  it('shows markup in the vendor message and in agent replies as text, never as tags', async () => {
    sendChat.mockResolvedValue({
      session_id: 's-1',
      intent: 'agent_reply',
      message: '**Done** <img src=x onerror="alert(1)">',
    })
    const c = chat()
    c.userInput.value = 'Help <img src=x onerror="alert(2)">'

    await c.handleSend()
    c.stopPolling()

    const [mine, reply] = c.chatMessages.value
    expect(mine.text).toBe('Help &lt;img src=x onerror=&quot;alert(2)&quot;&gt;')
    expect(reply.role).toBe('support')
    expect(reply.text).toBe('<b>Done</b> &lt;img src=x onerror=&quot;alert(1)&quot;&gt;')
  })

  it('escapes a failed request message too', async () => {
    sendChat.mockRejectedValue(new Error('<b>bad</b>'))
    const c = chat()
    c.userInput.value = 'hi'

    await c.handleSend()

    expect(c.chatMessages.value.at(-1).text).toContain('&lt;b&gt;bad&lt;/b&gt;')
  })
})

describe('html helpers', () => {
  it('escapes every character that can open markup or an attribute', () => {
    expect(escapeHtml(`<a href="x" title='y'>&</a>`)).toBe(
      '&lt;a href=&quot;x&quot; title=&#39;y&#39;&gt;&amp;&lt;/a&gt;',
    )
    expect(escapeHtml(null)).toBe('')
  })

  it('allows only bold, italic and line breaks', () => {
    expect(formatChatText('**a** *b*\nc')).toBe('<b>a</b> <i>b</i><br>c')
  })
})
