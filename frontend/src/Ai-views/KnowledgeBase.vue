<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-500 text-3xl">menu_book</span>
                    Knowledge Base & SOPs
                </h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Official policies, standard operating
                    procedures, and AI training data</p>
            </div>
            <div class="flex gap-2 w-full sm:w-auto">
                <button @click="showAddArticleModal = true"
                    class="w-full sm:w-auto px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg flex justify-center items-center gap-2 transition-colors shadow-sm">
                    <span class="material-symbols-outlined text-sm">edit_document</span> New Article
                </button>
            </div>
        </div>

        <!-- Hero Search Section -->
        <KnowledgeHero />

        <!-- Filter Tabs -->
        <div
            class="p-1 bg-gray-100 dark:bg-white/5 rounded-xl inline-flex overflow-x-auto no-scrollbar max-w-full shadow-sm">
            <button v-for="cat in categories" :key="cat" @click="activeCategory = cat"
                class="px-5 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all flex items-center gap-2"
                :class="activeCategory === cat
                    ? 'bg-white text-purple-700 shadow-sm dark:bg-gray-800 dark:text-purple-400'
                    : 'text-gray-600 hover:text-gray-900 border-transparent dark:text-gray-400 dark:hover:text-gray-200'">
                {{ cat }}
            </button>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="flex items-center justify-center py-20 gap-3 text-gray-500 dark:text-gray-400">
            <span class="material-symbols-outlined animate-spin text-purple-500">progress_activity</span>
            Loading knowledge base…
        </div>

        <!-- Dynamic Content Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <ArticleGrid />
        </div>

        <!-- Rich Article Viewer Modal -->
        <Teleport to="body">
            <ArticleViewerModal />
        </Teleport>

        <!-- Add Article Modal (WYSIWYG Mockup) -->
        <Teleport to="body">
            <AddArticleModal />
        </Teleport>
    </div>
</template>

<script setup>
import KnowledgeHero from './knowledgeBase/KnowledgeHero.vue'
import ArticleGrid from './knowledgeBase/ArticleGrid.vue'
import ArticleViewerModal from './knowledgeBase/ArticleViewerModal.vue'
import AddArticleModal from './knowledgeBase/AddArticleModal.vue'
import { knowledgeBasePageKey } from './knowledgeBase/knowledgeBasePageContext'
import { mapToDisplay, renderMarkdown, tableOfContents } from './knowledgeBase/articleFormat'
import { ref, computed, onMounted, provide } from 'vue'
import {
    fetchKnowledgeArticles,
    createKnowledgeArticle,
    updateKnowledgeArticle,
    deleteKnowledgeArticle,
    likeKnowledgeArticle,
} from '@/utils/aiApi'

const searchQuery = ref('')
const activeCategory = ref('All')
const isLoading = ref(true)

const showArticleModal = ref(false)
const showAddArticleModal = ref(false)
const isSavingArticle = ref(false)

const selectedArticle = ref(null)
const selectedArticleCat = ref(null)
const editingArticleId = ref(null)  // null = create mode, string = edit mode

const newArticle = ref({
    title: '',
    category: 'General',
    audience: 'ALL',
    type: 'SOP',
    excerpt: '',
    content: '',
})

// ── Category display metadata ──────────────────────────────────────────────
const CAT_META = {
    'Vendor': { icon: 'local_shipping', iconBg: 'bg-purple-100 dark:bg-purple-500/20', iconColor: 'text-purple-600 dark:text-purple-400', desc: 'Vendor-specific policies, shipment SOPs, and platform guides.' },
    'Customer': { icon: 'support_agent', iconBg: 'bg-blue-100 dark:bg-blue-500/20', iconColor: 'text-blue-600 dark:text-blue-400', desc: 'Customer-facing support scripts, refund policies, and how-to guides.' },
    'General': { icon: 'menu_book', iconBg: 'bg-green-100 dark:bg-green-500/20', iconColor: 'text-green-600 dark:text-green-400', desc: 'Platform-wide policies available to all user roles.' },
}
const DEFAULT_META = { icon: 'folder', iconBg: 'bg-gray-100 dark:bg-white/10', iconColor: 'text-gray-500', desc: 'Knowledge articles.' }

// ── Raw articles from backend ──────────────────────────────────────────────
const rawArticles = ref([])

// ── Grouped categories for the grid ───────────────────────────────────────
const allCategories = computed(() => {
    const groups = {}
    rawArticles.value.forEach(a => {
        const cat = a.category || 'General'
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(mapToDisplay(a))
    })
    return Object.entries(groups).map(([title, articles]) => ({
        title,
        articles,
        ...(CAT_META[title] || DEFAULT_META),
    }))
})

const categories = computed(() => ['All', ...Object.keys(
    rawArticles.value.reduce((acc, a) => { acc[a.category || 'General'] = 1; return acc }, {})
)])

const visibleCategories = computed(() => {
    let cats = allCategories.value
    if (activeCategory.value !== 'All') cats = cats.filter(c => c.title === activeCategory.value)
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        cats = cats.map(cat => ({
            ...cat,
            articles: cat.articles.filter(a =>
                a.title.toLowerCase().includes(q) || a.excerpt.toLowerCase().includes(q)
            )
        })).filter(cat => cat.articles.length > 0)
    }
    return cats
})

const renderedContent = computed(() => {
    if (!selectedArticle.value?.content) return ''
    return renderMarkdown(selectedArticle.value.content)
})

const tocItems = computed(() => tableOfContents(selectedArticle.value?.content))

const BUILT_IN_CATEGORIES = ['General', 'Vendor', 'Customer', 'Legal & Compliance', 'Operations']
const dynamicCategories = computed(() => {
    const fromArticles = rawArticles.value.map(a => a.category || 'General')
    return [...new Set([...BUILT_IN_CATEGORIES, ...fromArticles])]
})

// ── Load articles on mount ─────────────────────────────────────────────────
async function loadArticles() {
    isLoading.value = true
    try {
        const data = await fetchKnowledgeArticles({ activeOnly: false })
        rawArticles.value = data.articles || []
    } catch (err) {
        console.error('[KnowledgeBase] Failed to load articles:', err)
    } finally {
        isLoading.value = false
    }
}

onMounted(loadArticles)

// ── CRUD ──────────────────────────────────────────────────────────────────
function openArticleModal(article, cat) {
    selectedArticle.value = article
    selectedArticleCat.value = cat
    showArticleModal.value = true
}

async function addArticle() {
    if (!newArticle.value.title) return
    isSavingArticle.value = true
    try {
        const payload = {
            title: newArticle.value.title,
            audience: newArticle.value.audience,
            category: newArticle.value.category,
            article_type: newArticle.value.type,
            content: newArticle.value.content || newArticle.value.excerpt || newArticle.value.title,
            keywords: [],
        }
        if (editingArticleId.value) {
            await updateKnowledgeArticle(editingArticleId.value, payload)
        } else {
            await createKnowledgeArticle(payload)
        }
        await loadArticles()
        newArticle.value = { title: '', category: 'General', audience: 'ALL', type: 'SOP', excerpt: '', content: '' }
        editingArticleId.value = null
        showAddArticleModal.value = false
    } catch (err) {
        alert('Failed to save: ' + (err.message || 'Unknown error'))
    } finally {
        isSavingArticle.value = false
    }
}

function saveDraftTrigger() {
    addArticle()
}

function printArticle() { window.print() }

function editArticle() {
    if (!selectedArticle.value) return
    editingArticleId.value = selectedArticle.value._id
    newArticle.value = {
        title: selectedArticle.value.title,
        category: selectedArticle.value.category || 'General',
        audience: selectedArticle.value.audience || 'ALL',
        type: selectedArticle.value.type || 'SOP',
        excerpt: selectedArticle.value.excerpt,
        content: selectedArticle.value.content,
    }
    showArticleModal.value = false
    showAddArticleModal.value = true
}

async function unpublishArticle() {
    if (!selectedArticle.value) return
    try {
        await updateKnowledgeArticle(selectedArticle.value._id, { is_active: false })
        await loadArticles()
        showArticleModal.value = false
    } catch (err) {
        alert('Failed to unpublish: ' + (err.message || 'Unknown error'))
    }
}

async function deleteArticle() {
    if (!selectedArticle.value) return
    if (!confirm(`Permanently delete "${selectedArticle.value.title}"?`)) return
    try {
        await deleteKnowledgeArticle(selectedArticle.value._id)
        await loadArticles()
        showArticleModal.value = false
    } catch (err) {
        alert('Failed to delete: ' + (err.message || 'Unknown error'))
    }
}

async function handleLike(articleId) {
    try {
        await likeKnowledgeArticle(articleId)
        const idx = rawArticles.value.findIndex(a => a.id === articleId)
        if (idx !== -1) rawArticles.value[idx].likes++
    } catch { /* ignore */ }
}

function scrollToSection(id) {
    const el = document.getElementById(id);
    const container = document.getElementById('article-main-content');
    if (el && container) {
        // Subtract a little offset for breathing room at the top
        container.scrollTo({
            top: el.offsetTop - 40,
            behavior: 'smooth'
        });
    }
}

provide(knowledgeBasePageKey, {
    addArticle,
    deleteArticle,
    dynamicCategories,
    editArticle,
    handleLike,
    newArticle,
    openArticleModal,
    printArticle,
    renderedContent,
    saveDraftTrigger,
    scrollToSection,
    searchQuery,
    selectedArticle,
    selectedArticleCat,
    showAddArticleModal,
    showArticleModal,
    tocItems,
    unpublishArticle,
    visibleCategories,
})
</script>

