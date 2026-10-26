import { describe, expect, it } from 'vitest'
import {
  mapToDisplay,
  renderMarkdown,
  tableOfContents,
} from '@/Ai-views/knowledgeBase/articleFormat'

describe('knowledge base article formatting', () => {
  it('escapes markup in article text before adding its own tags', () => {
    expect(renderMarkdown('Hello <img src=x onerror=alert(1)> **world**')).toBe(
      '<p>Hello &lt;img src=x onerror=alert(1)&gt; <strong>world</strong></p>',
    )
  })

  it('renders lists, numbered steps and paragraphs from blank-line separated blocks', () => {
    const html = renderMarkdown('* one\n* *two*\n\n1. first\n2. second\n\nline a\nline b')
    expect(html).toBe(
      '<ul><li>one</li><li><em>two</em></li></ul><ol><li>first</li><li>second</li></ol><p>line a<br>line b</p>',
    )
  })

  it('gives headings the same ids the table of contents links to', () => {
    const content = '# Refund Policy\n\n## Damaged goods & claims\n\n### Step 3: escalate'
    const toc = tableOfContents(content)
    expect(toc).toEqual([
      { level: 1, text: 'Refund Policy', id: 'refund-policy' },
      { level: 2, text: 'Damaged goods & claims', id: 'damaged-goods-claims' },
      { level: 3, text: 'Step 3: escalate', id: 'step-3-escalate' },
    ])
    const html = renderMarkdown(content)
    for (const { id } of toc.filter((item) => item.text.indexOf('&') === -1)) {
      expect(html).toContain(`id="${id}"`)
    }
    expect(tableOfContents('')).toEqual([])
  })

  it('maps an API article to a card with an excerpt and type icon', () => {
    const card = mapToDisplay({
      id: 'a1',
      title: 'Returns',
      article_type: 'SOP',
      content: 'x'.repeat(130),
      author_initials: 'AR',
      updated_at: null,
      likes: 21,
      audience: 'vendor',
      category: null,
      is_active: true,
    })
    expect(card).toMatchObject({
      _id: 'a1',
      typeIcon: 'rule',
      featured: true,
      category: 'General',
      lastUpdated: '',
    })
    expect(card.excerpt).toHaveLength(121)
    expect(card.excerpt.endsWith('…')).toBe(true)
  })
})
