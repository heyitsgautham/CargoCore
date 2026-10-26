<template>
    <template v-for="cat in visibleCategories" :key="cat.title">

        <!-- Category Card Header -->
        <div class="col-span-1 md:col-span-2 lg:col-span-3 mt-4 mb-2 flex items-center gap-3"
            v-if="cat.articles.length > 0">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center shadow-sm" :class="cat.iconBg">
                <span class="material-symbols-outlined text-[20px]" :class="cat.iconColor">{{ cat.icon }}</span>
            </div>
            <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ cat.title }}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ cat.desc }}</p>
            </div>
        </div>

        <!-- Article Cards -->
        <div v-for="article in cat.articles" :key="article.title" @click="openArticleModal(article, cat)"
            class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-5 rounded-xl hover:border-purple-300 dark:hover:border-purple-500/50 hover:shadow-md dark:hover:bg-white/5 shadow-sm transition-all cursor-pointer flex flex-col group relative overflow-hidden">

            <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl opacity-0 group-hover:opacity-10 transition-opacity rounded-bl-full pointer-events-none"
                :class="cat.iconBg"></div>

            <div class="flex-1">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-2">
                        <span
                            class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400">
                            <span class="material-symbols-outlined text-[12px] align-sub">{{ article.typeIcon
                                }}</span> {{ article.type }}
                        </span>
                        <span v-if="article.featured"
                            class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-400">
                            Featured
                        </span>
                    </div>
                    <button
                        class="text-gray-400 hover:text-gray-900 dark:hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                        <span class="material-symbols-outlined text-[18px]">bookmark_border</span>
                    </button>
                </div>
                <h4
                    class="font-bold text-gray-900 dark:text-white text-lg mb-2 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                    {{ article.title }}</h4>
                <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">{{
                    article.excerpt }}</p>
            </div>

            <div
                class="mt-4 pt-4 border-t border-gray-100 dark:border-white/5 flex justify-between items-center">
                <div class="flex items-center gap-2">
                    <div
                        class="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 font-bold text-[10px] flex justify-center items-center text-gray-700 dark:text-gray-300 shadow-inner">
                        {{ article.authorInitials }}
                    </div>
                    <span class="text-xs text-gray-500 dark:text-gray-400">{{ article.lastUpdated }}</span>
                </div>
                <button @click.stop="handleLike(article._id)"
                    class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-bold bg-green-50 dark:bg-green-500/10 hover:bg-green-100 dark:hover:bg-green-500/20 px-2 py-1 rounded transition-colors">
                    <span class="material-symbols-outlined text-[14px]">thumb_up</span> {{ article.likes }}
                </button>
            </div>
        </div>
    </template>

    <div v-if="visibleCategories.length === 0"
        class="col-span-1 md:col-span-2 lg:col-span-3 text-center py-16 text-gray-500 dark:text-gray-400">
        <span class="material-symbols-outlined text-6xl mb-4 text-gray-300 dark:text-gray-600">search_off</span>
        <p class="text-lg font-bold text-gray-900 dark:text-white mb-2">No articles found</p>
        <p>We couldn't find anything matching "{{ searchQuery }}". Try adjusting your search or category filter.
        </p>
        <button @click="searchQuery = ''"
            class="mt-4 text-purple-600 dark:text-purple-400 font-bold hover:underline">Clear
            Search</button>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { knowledgeBasePageKey } from './knowledgeBasePageContext'

const { handleLike, openArticleModal, searchQuery, visibleCategories } = inject(knowledgeBasePageKey)
</script>
