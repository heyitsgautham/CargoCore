<template>
    <!-- Document Viewer Modal -->
    <Teleport to="body">
        <div v-if="activeDoc"
            class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            @click.self="closeDocModal">
            <div class="bg-white dark:bg-card-dark w-full max-w-3xl rounded-2xl shadow-2xl border border-gray-200 dark:border-white/10 overflow-hidden flex flex-col h-[80vh]">
                <div class="px-6 py-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-primary">description</span>
                        <div>
                            <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ activeDoc.type }}</h3>
                            <p class="text-xs text-gray-500">
                                {{ activeDoc.vehicleId ? `Vehicle: ${activeDoc.vehicleId}` : `Driver: ${activeDoc.driver}` }}
                            </p>
                        </div>
                    </div>
                    <button @click="closeDocModal"
                        class="text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="flex-1 bg-gray-100 dark:bg-black/50 overflow-hidden relative flex items-center justify-center p-4">
                    <!-- Mock Doc Viewer -->
                    <div class="bg-white shadow-lg p-2 max-h-full overflow-y-auto">
                        <img :src="activeDoc.url" class="max-w-full object-contain" alt="Document Preview"/>
                    </div>
                    <div class="absolute bottom-6 bg-black/60 backdrop-blur-md px-4 py-2 rounded-full text-white text-sm flex gap-4">
                        <button @click="downloadDoc(activeDoc)" class="hover:text-primary transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">download</span> Download</button>
                        <span class="w-px h-4 bg-white/20 my-auto"></span>
                        <button @click="printDoc(activeDoc)" class="hover:text-primary transition-colors flex items-center gap-1"><span class="material-symbols-outlined text-[16px]">print</span> Print</button>
                        <span class="w-px h-4 bg-white/20 my-auto"></span>
                        <button @click="openShareModal" class="hover:text-primary transition-colors flex items-center gap-1" ref="shareButton"><span class="material-symbols-outlined text-[16px]">share</span> Share</button>

                        <!-- Share Popover -->
                        <div v-if="isShareModalOpen" class="absolute bottom-12 right-0 bg-white dark:bg-card-dark border border-gray-200 dark:border-white/10 rounded-xl shadow-xl w-72 overflow-hidden animate-fade-in-up z-[130]">
                            <div class="p-3 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-white/5">
                                <h4 class="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider">Share Document</h4>
                                <button @click.stop="isShareModalOpen = false" class="text-gray-400 hover:text-gray-900 dark:hover:text-white"><span class="material-symbols-outlined text-sm">close</span></button>
                            </div>
                            <div v-if="shareStep === 'select'" class="p-2 grid grid-cols-1 gap-1">
                                <button @click="shareVia('whatsapp')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                    <div class="w-8 h-8 rounded-full bg-[#25D366]/10 flex items-center justify-center text-[#25D366]"><span class="material-symbols-outlined text-lg">chat</span></div>
                                    <div>
                                        <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-[#25D366]">WhatsApp</p>
                                        <p class="text-[10px] text-gray-500">Share via link</p>
                                    </div>
                                </button>
                                <button @click="shareVia('telegram')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                    <div class="w-8 h-8 rounded-full bg-[#0088cc]/10 flex items-center justify-center text-[#0088cc]"><span class="material-symbols-outlined text-lg">send</span></div>
                                    <div>
                                        <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-[#0088cc]">Telegram</p>
                                        <p class="text-[10px] text-gray-500">Share via message</p>
                                    </div>
                                </button>
                                <button @click="shareVia('cargocore')" class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg transition-colors text-left group">
                                    <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary"><span class="material-symbols-outlined text-lg">local_shipping</span></div>
                                    <div>
                                        <p class="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary">CargoCore Messenger</p>
                                        <p class="text-[10px] text-gray-500">Internal secure share</p>
                                    </div>
                                </button>
                            </div>

                            <!-- CargoCore Share Form -->
                            <div v-if="shareStep === 'form'" class="p-4 space-y-3">
                                <div class="bg-primary/5 rounded-lg p-2 flex items-center gap-2 border border-primary/10">
                                    <span class="material-symbols-outlined text-primary text-sm">picture_as_pdf</span>
                                    <span class="text-xs font-medium text-gray-700 dark:text-gray-300 truncate max-w-[150px]">{{ activeDoc.type }}.pdf</span>
                                </div>

                                <div>
                                    <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Assigned Warehouse</label>
                                    <div class="w-full text-xs bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded px-2 py-2 text-gray-500 dark:text-gray-400 font-mono">
                                        {{ store.hubs.find(h => h.id === shareFormData.hubId)?.name || 'Unknown Hub' }}
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Recipient Role</label>
                                    <div class="flex gap-2">
                                        <button @click="shareFormData.role = 'dispatcher'" 
                                            class="flex-1 py-1.5 text-xs rounded border transition-colors font-medium"
                                            :class="shareFormData.role === 'dispatcher' ? 'bg-primary text-white border-primary' : 'bg-slate-100 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-slate-200 dark:hover:bg-white/10'">
                                            Dispatcher
                                        </button>
                                        <button @click="shareFormData.role = 'manager'" 
                                            class="flex-1 py-1.5 text-xs rounded border transition-colors font-medium"
                                            :class="shareFormData.role === 'manager' ? 'bg-primary text-white border-primary' : 'bg-slate-100 dark:bg-white/5 border-slate-300 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-slate-200 dark:hover:bg-white/10'">
                                            Manager
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Message (Optional)</label>
                                    <textarea v-model="shareFormData.message" rows="2" placeholder="Add a note..." class="w-full text-xs bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1.5 focus:border-primary focus:outline-none text-gray-900 dark:text-white resize-none"></textarea>
                                </div>

                                <button @click="submitShare" class="w-full bg-primary hover:bg-primary/90 text-white text-xs font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                                    <span class="material-symbols-outlined text-sm">send</span> Send Document
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="px-6 py-4 border-t border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-white/5 grid grid-cols-3 gap-4">
                    <div>
                        <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Expiry Date</p>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">{{ activeDoc.expiry }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Status</p>
                        <p class="text-sm font-bold" :class="activeDoc.status === 'Active' ? 'text-green-600' : 'text-red-500'">{{ activeDoc.status }}</p>
                    </div>
                     <div>
                        <p class="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Verified By</p>
                        <p class="text-sm font-medium text-gray-900 dark:text-white">Admin System (Auto)</p>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { inject } from 'vue'
import { fleetPageKey } from './fleetPageContext'

const {
    activeDoc,
    closeDocModal,
    downloadDoc,
    isShareModalOpen,
    openShareModal,
    printDoc,
    shareFormData,
    shareStep,
    shareVia,
    store,
    submitShare,
} = inject(fleetPageKey)
</script>
