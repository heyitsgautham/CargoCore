<template>
    <!-- Credentials Mini Modal -->
    <Teleport to="body">
        <div v-if="viewingUserCreds"
            class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            @click.self="closeCreds">
            <div
                class="bg-slate-950/98 w-full max-w-sm rounded-2xl shadow-2xl border border-white/10 overflow-hidden flex flex-col relative items-center p-6 backdrop-blur-xl">
                <button @click="closeCreds"
                    class="absolute top-4 right-4 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>

                <img :src="viewingUserCreds.avatar"
                    class="w-16 h-16 rounded-full border-2 border-gray-200 dark:border-white/10 shadow-sm mb-3">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ viewingUserCreds.name }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{{ viewingUserCreds.role }}</p>

                <div
                    class="w-full bg-primary/5 dark:bg-primary/10 border border-primary/20 rounded-xl p-4 relative text-left">
                    <h4 class="text-xs font-bold text-primary uppercase tracking-wider mb-3">System Credentials
                    </h4>
                    <button @click.prevent="isCredentialsVisible = !isCredentialsVisible"
                        class="absolute top-3 right-3 text-primary hover:text-primary/80 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">
                            {{ isCredentialsVisible ? 'visibility_off' : 'visibility' }}
                        </span>
                    </button>

                    <div class="space-y-3">
                        <div>
                            <label
                                class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Username</label>
                            <div
                                class="text-sm font-mono text-white bg-slate-800 px-3 py-1.5 rounded border border-white/10">
                                {{ isCredentialsVisible ? viewingUserCreds.username : '********' }}
                            </div>
                        </div>
                        <div>
                            <label
                                class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Password</label>
                            <div
                                class="text-sm font-mono text-white bg-slate-800 px-3 py-1.5 rounded border border-white/10">
                                {{ isCredentialsVisible ? (viewingUserCreds.password || 'Shown only once, when the account was created') : '********' }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { userManagementPageKey } from './userManagementPageContext'

const { closeCreds, isCredentialsVisible, viewingUserCreds } = inject(userManagementPageKey)
</script>
