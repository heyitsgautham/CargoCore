// Formatting for knowledge base articles: list cards, the markdown body and its table of contents.
// renderMarkdown escapes the text before adding tags, so article content never becomes live markup.

export function typeIcon(type) {
    return { SOP: 'rule', Policy: 'policy', Script: 'forum', Guide: 'auto_stories' }[type] || 'article'
}

export function relativeTime(iso) {
    if (!iso) return ''
    const diff = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    if (days < 30) return `${days}d ago`
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function mapToDisplay(a) {
    return {
        _id: a.id,
        title: a.title,
        type: a.article_type,
        typeIcon: typeIcon(a.article_type),
        excerpt: a.content.slice(0, 120) + (a.content.length > 120 ? '…' : ''),
        content: a.content,
        authorInitials: a.author_initials,
        lastUpdated: relativeTime(a.updated_at),
        likes: a.likes,
        featured: a.likes > 20,
        audience: a.audience,
        category: a.category || 'General',
        is_active: a.is_active,
    }
}

export function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
}

export function formatInlineMarkdown(line) {
    return line
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
}

export function renderMarkdown(content) {
    return escapeHtml(content)
        .split(/\n{2,}/)
        .map((block) => block.trim())
        .filter(Boolean)
        .map((block) => {
            const lines = block.split('\n').map((line) => line.trim()).filter(Boolean)
            if (!lines.length) return ''

            if (lines.every((line) => line.startsWith('* '))) {
                return `<ul>${lines.map((line) => `<li>${formatInlineMarkdown(line.slice(2))}</li>`).join('')}</ul>`
            }

            if (lines.every((line) => /^\d+\.\s/.test(line))) {
                return `<ol>${lines.map((line) => `<li>${formatInlineMarkdown(line.replace(/^\d+\.\s/, ''))}</li>`).join('')}</ol>`
            }

            if (lines.length === 1 && lines[0].startsWith('### ')) {
                const text = formatInlineMarkdown(lines[0].slice(4))
                const id = text.replace(/<[^>]+>/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
                return `<h3 id="${id}">${text}</h3>`
            }

            if (lines.length === 1 && lines[0].startsWith('## ')) {
                const text = formatInlineMarkdown(lines[0].slice(3))
                const id = text.replace(/<[^>]+>/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
                return `<h2 id="${id}">${text}</h2>`
            }

            if (lines.length === 1 && lines[0].startsWith('# ')) {
                const text = formatInlineMarkdown(lines[0].slice(2))
                const id = text.replace(/<[^>]+>/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
                return `<h1 id="${id}">${text}</h1>`
            }

            return `<p>${lines.map(formatInlineMarkdown).join('<br>')}</p>`
        })
        .join('')
}

/** Heading entries for the article sidebar. Ids match the ones renderMarkdown gives each heading. */
export function tableOfContents(content) {
    if (!content) return []
    const items = []
    content.split('\n').forEach((line) => {
        const match = line.match(/^(#{1,3})\s+(.+)$/)
        if (!match) return
        const text = match[2].trim()
        items.push({ level: match[1].length, text, id: text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') })
    })
    return items
}
