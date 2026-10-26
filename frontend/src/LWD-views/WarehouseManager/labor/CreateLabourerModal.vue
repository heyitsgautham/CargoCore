<template>
    <!-- Create Labourer Modal -->
    <Teleport to="body">
        <div v-if="showCreateModal"
            class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            @click.self="closeCreateModal">
            <div class="bg-white dark:bg-gray-900 shadow-2xl rounded-2xl w-full max-w-md border border-gray-200 dark:border-white/10 max-h-[90vh] flex flex-col">
                <div class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center flex-shrink-0">
                    <h3 class="font-bold text-gray-900 dark:text-white text-lg flex items-center gap-2">
                        <span class="material-symbols-outlined text-green-500">person_add</span>
                        Add New Labourer
                    </h3>
                    <button @click="closeCreateModal"
                        class="text-gray-500 hover:text-gray-900 dark:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="p-4 space-y-3 overflow-y-auto flex-1">
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Full Name *</label>
                        <input type="text" v-model="newLabourer.name" placeholder="Enter full name" autocomplete="off"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50" />
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Email</label>
                            <input type="email" v-model="newLabourer.email" placeholder="email@example.com" autocomplete="off"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm" />
                        </div>
                        <div>
                            <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Phone</label>
                            <input type="tel" v-model="newLabourer.phone" placeholder="+91 98765 43210" autocomplete="off"
                                class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm" />
                        </div>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1 block">Department / Role *</label>
                        <select v-model="newLabourer.role"
                            class="w-full bg-gray-50 dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-gray-900 dark:text-white focus:outline-none focus:border-primary/50">
                            <option value="" class="bg-white dark:bg-gray-800">Select role...</option>
                            <option value="Picking" class="bg-white dark:bg-gray-800">Picking</option>
                            <option value="Packing" class="bg-white dark:bg-gray-800">Packing</option>
                            <option value="Loading" class="bg-white dark:bg-gray-800">Loading</option>
                            <option value="Receiving" class="bg-white dark:bg-gray-800">Receiving</option>
                            <option value="General" class="bg-white dark:bg-gray-800">General Labour</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-gray-600 dark:text-gray-400 mb-1.5 block">Skills (select multiple)</label>
                        <div class="flex flex-wrap gap-1.5">
                            <button v-for="skill in availableSkills" :key="skill"
                                @click="toggleSkill(skill)"
                                class="px-2.5 py-1 rounded-lg text-xs font-medium transition-colors"
                                :class="newLabourer.skills.includes(skill)
                                    ? 'bg-primary text-white'
                                    : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-white/20'">
                                {{ skill }}
                            </button>
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t border-gray-100 dark:border-white/5 flex-shrink-0 space-y-3">
                    <div class="flex items-center gap-2 p-2.5 bg-green-500/10 rounded-lg border border-green-500/20 text-xs text-green-600 dark:text-green-400">
                        <span class="material-symbols-outlined text-[14px]">info</span>
                        Labourer will be created as "Available" and can be assigned immediately.
                    </div>
                    <button @click="createLabourer" :disabled="isCreating || !newLabourer.name || !newLabourer.role"
                        class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                        <span v-if="isCreating" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                        {{ isCreating ? 'Creating...' : 'Create Labourer' }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { laborPageKey } from './laborPageContext'

const {
    availableSkills,
    closeCreateModal,
    createLabourer,
    isCreating,
    newLabourer,
    showCreateModal,
    toggleSkill,
} = inject(laborPageKey)
</script>
