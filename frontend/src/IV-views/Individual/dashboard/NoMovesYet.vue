<template>
    <span class="material-symbols-outlined text-6xl text-gray-400 dark:text-gray-600 mb-4">local_shipping</span>
    <h3 class="font-bold text-xl text-gray-900 dark:text-white mb-2">No Moves Yet</h3>
    <p class="text-gray-500 dark:text-gray-400 mb-6">Start your first move by booking a service or getting a quote.</p>
    <div class="flex gap-4 justify-center flex-wrap">
        <router-link to="/individual/book-move"
            class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold transition-colors">
            Book a Move
        </router-link>
        <router-link to="/individual/quotes"
            class="px-6 py-2 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 rounded-lg font-bold transition-colors">
            Get Quote
        </router-link>
    </div>
</template>

