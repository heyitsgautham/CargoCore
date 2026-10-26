<template>
    <div v-if="showAddArticleModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="showAddArticleModal = false">
        <div
            class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-4xl shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden flex flex-col h-[85vh]">
            <div
                class="px-6 py-4 border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 flex justify-between items-center shrink-0">
                <div class="flex items-center gap-3">
                    <div
                        class="bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 p-2 rounded-lg inline-flex">
                        <span class="material-symbols-outlined">edit_document</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white leading-tight">Create
                            Knowledge
                            Article</h3>
                        <p class="text-xs text-gray-500">Draft new policy SOPs</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">Auto-saving... <span
                            class="material-symbols-outlined text-[14px] text-green-500 align-sub">cloud_done</span></span>
                </div>
            </div>

            <div class="p-6 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-5">
                <div class="grid grid-cols-2 gap-4 shrink-0">
                    <div class="col-span-2">
                        <label
                            class="block text-[10px] font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Article
                            Title</label>
                        <input v-model="newArticle.title" type="text"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-lg font-bold text-gray-900 dark:text-white outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-shadow shadow-sm"
                            placeholder="e.g. Expedited Shipping Refund Protocol" />
                    </div>

                    <div>
                        <label
                            class="block text-[10px] font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Category</label>
                        <select v-model="newArticle.category"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors shadow-sm font-medium">
                            <option v-for="cat in dynamicCategories" :key="cat" :value="cat">{{ cat }}</option>
                        </select>
                    </div>

                    <div>
                        <label
                            class="block text-[10px] font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Audience</label>
                        <select v-model="newArticle.audience"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors shadow-sm font-medium">
                            <option value="ALL">All Users</option>
                            <option value="VENDOR">Vendor Only</option>
                            <option value="INDIVIDUAL">Customer Only</option>
                        </select>
                    </div>

                    <div>
                        <label
                            class="block text-[10px] font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Document
                            Type</label>
                        <select v-model="newArticle.type"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors shadow-sm font-medium">
                            <option>SOP</option>
                            <option>Policy</option>
                            <option>Script</option>
                            <option>Guide</option>
                        </select>
                    </div>

                    <div class="col-span-2">
                        <label
                            class="block text-[10px] font-bold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Short
                            Excerpt / Summary</label>
                        <textarea rows="2" v-model="newArticle.excerpt"
                            class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white outline-none focus:border-purple-500 transition-colors shadow-sm resize-none"
                            placeholder="Provide a brief 1-2 sentence summary of this article..."></textarea>
                    </div>
                </div>

                <!-- WYSIWYG Editor Mockup -->
                <div
                    class="flex-1 border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden flex flex-col shadow-sm bg-white dark:bg-black/20">
                    <div
                        class="bg-gray-50 dark:bg-white/5 border-b border-gray-200 dark:border-white/10 p-2 flex gap-1 items-center shrink-0 flex-wrap">
                        <select
                            class="bg-transparent border-none text-sm font-bold text-gray-700 dark:text-gray-300 focus:ring-0 cursor-pointer p-1">
                            <option>Normal text</option>
                            <option>Heading 1</option>
                            <option>Heading 2</option>
                            <option>Heading 3</option>
                        </select>
                        <div class="w-px h-5 bg-gray-300 dark:bg-gray-700 mx-1"></div>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Bold"><span
                                class="material-symbols-outlined text-[18px]">format_bold</span></button>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Italic"><span
                                class="material-symbols-outlined text-[18px]">format_italic</span></button>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Underline"><span
                                class="material-symbols-outlined text-[18px]">format_underlined</span></button>
                        <div class="w-px h-5 bg-gray-300 dark:bg-gray-700 mx-1"></div>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Bullet List"><span
                                class="material-symbols-outlined text-[18px]">format_list_bulleted</span></button>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Numbered List"><span
                                class="material-symbols-outlined text-[18px]">format_list_numbered</span></button>
                        <div class="w-px h-5 bg-gray-300 dark:bg-gray-700 mx-1"></div>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Insert Link"><span
                                class="material-symbols-outlined text-[18px]">link</span></button>
                        <button
                            class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 transition"
                            title="Insert Image"><span
                                class="material-symbols-outlined text-[18px]">image</span></button>
                    </div>
                    <textarea v-model="newArticle.content"
                        class="flex-1 w-full bg-transparent border-none p-4 text-sm text-gray-900 dark:text-gray-100 outline-none resize-none font-mono"
                        placeholder="Write article content here using markdown format or the rich text tools above..."></textarea>
                </div>
            </div>

            <div
                class="px-6 py-4 border-t border-gray-100 dark:border-white/5 flex gap-3 shrink-0 bg-gray-50 dark:bg-white/5">
                <button @click="showAddArticleModal = false"
                    class="py-2.5 px-6 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors border border-gray-200 dark:border-white/10 shadow-sm ml-auto">
                    Discard Draft
                </button>
                <button @click="saveDraftTrigger" :disabled="!newArticle.title"
                    class="py-2.5 px-6 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors border border-gray-200 dark:border-white/10 shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">save</span> Save Draft
                </button>
                <button @click="addArticle" :disabled="!newArticle.title"
                    class="py-2.5 px-6 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold rounded-xl transition-colors shadow-sm flex items-center gap-2">
                    <span class="material-symbols-outlined text-[18px]">publish</span> Publish Article
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { knowledgeBasePageKey } from './knowledgeBasePageContext'

const {
    addArticle,
    dynamicCategories,
    newArticle,
    saveDraftTrigger,
    showAddArticleModal,
} = inject(knowledgeBasePageKey)
</script>
