// Helpers for text that ends up in v-html. Escape first, then add the few tags we allow,
// so nothing a user, an agent or a model typed can become live markup.

export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/** Chat text with **bold**, *italic* and line breaks, safe for v-html. */
export function formatChatText(raw) {
  return escapeHtml(raw)
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/\n/g, '<br>')
}
