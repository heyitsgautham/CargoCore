<template>
    <div v-if="showArticleModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-6"
        @click.self="showArticleModal = false">
        <div
            class="bg-white dark:bg-gray-900 flex flex-col rounded-2xl w-full max-w-5xl h-[90vh] shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">

            <!-- App Bar -->
            <div
                class="px-6 py-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5 shrink-0">
                <div class="flex gap-2">
                    <span
                        class="px-2 py-1 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs font-bold rounded flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">{{ selectedArticleCat?.icon
                            }}</span>
                        {{ selectedArticleCat?.title }}
                    </span>
                    <span
                        class="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 text-xs font-bold rounded border border-purple-200 dark:border-purple-800/50">
                        Internal SOP
                    </span>
                </div>
                <div class="flex gap-2 text-gray-500 dark:text-gray-400">
                    <button @click="printArticle"
                        class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full transition tooltip-trigger relative text-gray-400 hover:text-gray-900 dark:hover:text-white">
                        <span class="material-symbols-outlined">print</span>
                        <span class="tooltip">Print</span>
                    </button>
                    <button @click="editArticle"
                        class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full transition tooltip-trigger relative text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                        <span class="material-symbols-outlined">edit</span>
                        <span class="tooltip">Edit</span>
                    </button>
                    <button @click="unpublishArticle"
                        class="p-2 hover:bg-gray-200 dark:hover:bg-white/10 rounded-full transition tooltip-trigger relative text-gray-400 hover:text-orange-600 dark:hover:text-orange-400">
                        <span class="material-symbols-outlined">unpublished</span>
                        <span class="tooltip">Unpublish</span>
                    </button>
                    <button @click="deleteArticle"
                        class="p-2 hover:bg-red-100 hover:text-red-500 dark:hover:bg-red-500/20 dark:hover:text-red-400 rounded-full transition tooltip-trigger relative text-gray-400">
                        <span class="material-symbols-outlined">delete</span>
                        <span class="tooltip">Delete</span>
                    </button>
                    <div class="w-px h-6 bg-gray-300 dark:bg-gray-700 my-auto mx-1"></div>
                    <button @click="showArticleModal = false"
                        class="p-2 hover:bg-red-100 hover:text-red-500 dark:hover:bg-red-500/20 dark:hover:text-red-400 rounded-full transition">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
            </div>

            <!-- Split Content Area -->
            <div class="flex-1 flex overflow-hidden">

                <!-- TOC Sidebar -->
                <div
                    class="hidden md:block w-64 border-r border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-black/20 p-6 overflow-y-auto">
                    <h4
                        class="text-xs uppercase font-bold text-gray-500 dark:text-gray-400 mb-4 tracking-wider">
                        On this page</h4>
                    <ul class="space-y-3 text-sm font-medium">
                        <li>
                            <a href="#" @click.prevent="scrollToSection('article-overview')"
                                class="text-purple-600 dark:text-purple-400 flex items-center gap-2">
                                <div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div> Overview
                            </a>
                        </li>
                        <li v-for="item in tocItems" :key="item.id">
                            <a href="#" @click.prevent="scrollToSection(item.id)"
                                class="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition flex items-center gap-2"
                                :class="item.level === 2 ? 'ml-3' : item.level === 3 ? 'ml-6' : ''">
                                <div class="w-1 h-1 rounded-full bg-gray-400 shrink-0"></div>
                                {{ item.text }}
                            </a>
                        </li>
                        <li v-if="tocItems.length === 0" class="text-gray-400 dark:text-gray-500 text-xs italic">
                            No headings found
                        </li>
                    </ul>
                </div>

                <!-- Main Document -->
                <div id="article-main-content"
                    class="flex-1 overflow-y-auto scroll-smooth p-6 md:p-10 custom-scrollbar bg-white dark:bg-transparent">
                    <div class="max-w-3xl mx-auto pb-10">
                        <h1 id="article-overview"
                            class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white leading-tight mb-4">
                            {{ selectedArticle?.title }}
                        </h1>

                        <div
                            class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-white/5 pb-6 mb-8">
                            <div class="flex items-center gap-2">
                                <div
                                    class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 font-bold flex justify-center items-center font-mono shadow-inner border border-indigo-200 dark:border-indigo-800">
                                    {{ selectedArticle?.authorInitials }}
                                </div>
                                <div>
                                    <span class="block text-gray-900 dark:text-gray-200 font-bold">Written by
                                        Policy
                                        Team</span>
                                    <span class="block text-xs">Last updated: {{ selectedArticle?.lastUpdated
                                        }}</span>
                                </div>
                            </div>
                            <div class="w-px h-8 bg-gray-200 dark:bg-gray-800"></div>
                            <div
                                class="flex items-center gap-1 text-green-600 dark:text-green-400 font-bold bg-green-50 dark:bg-green-500/10 px-2 py-1.5 rounded-lg border border-green-200 dark:border-green-800/50">
                                <span class="material-symbols-outlined text-[16px]">verified</span> Approved for
                                AI use
                            </div>
                        </div>

                        <div class="prose prose-sm md:prose-base dark:prose-invert prose-purple max-w-none prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-strong:text-gray-900 dark:prose-strong:text-white"
                            v-html="renderedContent">
                        </div>

                        <div class="mt-12 pt-8 border-t border-gray-100 dark:border-white/5 text-center">
                            <h4 class="text-sm font-bold text-gray-900 dark:text-white mb-4">Was this
                                article
                                helpful?</h4>
                            <div class="flex justify-center gap-3">
                                <button
                                    class="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-green-100 dark:hover:bg-green-900/30 hover:text-green-600 dark:hover:text-green-400 text-gray-600 dark:text-gray-300 font-bold text-sm rounded-lg transition-colors border border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[18px]">thumb_up</span> Yes,
                                    helpful
                                </button>
                                <button
                                    class="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-red-100 dark:hover:bg-red-900/30 hover:text-red-600 dark:hover:text-red-400 text-gray-600 dark:text-gray-300 font-bold text-sm rounded-lg transition-colors border border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[18px]">thumb_down</span>
                                    Needs
                                    improvement
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { knowledgeBasePageKey } from './knowledgeBasePageContext'

const {
    deleteArticle,
    editArticle,
    printArticle,
    renderedContent,
    scrollToSection,
    selectedArticle,
    selectedArticleCat,
    showArticleModal,
    tocItems,
    unpublishArticle,
} = inject(knowledgeBasePageKey)
</script>

<style scoped>
/* Tooltip styling */
.tooltip-trigger .tooltip {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-top: 0.5rem;
    padding: 0.25rem 0.5rem;
    background: rgb(17 24 39);
    color: white;
    font-size: 10px;
    border-radius: 0.25rem;
    opacity: 0;
    white-space: nowrap;
    pointer-events: none;
    transition: opacity 150ms ease;
    z-index: 1000;
}

.tooltip-trigger:hover .tooltip {
    opacity: 1;
}
</style>
