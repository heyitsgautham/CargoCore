<template>
    <div class="space-y-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">My Quotes</h2>
            <router-link to="/individual/book-move"
                class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center gap-2 text-sm">
                <span class="material-symbols-outlined text-sm">add</span> New Quote
            </router-link>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="q in store.quotes" :key="q.id" class="glass-panel p-5 rounded-xl">
                <div class="flex items-center justify-between mb-3">
                    <span class="font-mono font-bold text-green-600 dark:text-green-400">{{ q.id }}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase" :class="{
                        'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400': q.status === 'active',
                        'bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-400': q.status === 'expired',
                        'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400': q.status === 'converted',
                    }">{{ q.status }}</span>
                </div>

                <div class="space-y-2 text-sm mb-4">
                    <div class="flex justify-between">
                        <span class="text-gray-500 dark:text-gray-400">Cargo Type</span>
                        <span class="text-gray-900 dark:text-white font-medium">{{ q.cargoType }}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-500 dark:text-gray-400">Route</span>
                        <span class="text-gray-900 dark:text-white font-medium">{{ q.from }} → {{ q.to }}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-500 dark:text-gray-400">Helpers</span>
                        <span class="text-gray-900 dark:text-white font-medium">{{ q.laborCount }}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-500 dark:text-gray-400">Packing</span>
                        <span class="text-gray-900 dark:text-white font-medium">{{ q.packing ? 'Yes' : 'No' }}</span>
                    </div>
                </div>

                <div class="border-t border-gray-200 dark:border-white/5 pt-3 flex justify-between items-center">
                    <div>
                        <div class="text-xs text-gray-500">Estimated Total</div>
                        <div class="text-xl font-bold text-green-600 dark:text-green-400">₹{{ q.total.toLocaleString()
                            }}</div>
                    </div>
                    <button v-if="q.status === 'active'" @click="convertToOrder(q.id)"
                        class="px-4 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-colors">
                        Book Now
                    </button>
                </div>
            </div>
        </div>

        <div v-if="store.quotes.length === 0"
            class="text-center py-16 text-gray-500 dark:text-gray-400 glass-panel rounded-xl">
            <span class="material-symbols-outlined text-5xl mb-2 block">request_quote</span>
            <p class="font-medium">No quotes yet.</p>
            <router-link to="/individual/book-move"
                class="text-green-600 dark:text-green-400 text-sm font-bold hover:underline mt-2 inline-block">Get a
                Quote →</router-link>
        </div>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl bg-green-600 text-white border border-green-500 max-w-sm">
                    <span class="material-symbols-outlined">check_circle</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>
    </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useIndividualStore } from '@/stores/individualStore'

const store = useIndividualStore()

const toast = reactive({ show: false, message: '' })
function showToast(msg) { toast.show = true; toast.message = msg; setTimeout(() => { toast.show = false }, 3000) }

async function convertToOrder(quoteId) {
    const result = await store.convertQuoteToOrderRemote(quoteId)
    if (result.success) showToast(`Order ${result.data.tracking_code} created from quote!`)
    else showToast(result.message || 'Failed to create order from quote.')
}

onMounted(() => {
    store.fetchQuotes()
})
</script>
