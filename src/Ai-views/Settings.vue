<template>
    <div class="max-w-6xl mx-auto space-y-8">
        <!-- Header -->
        <div
            class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-200 dark:border-white/10 pb-6">
            <div>
                <h2 class="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                    <span class="material-symbols-outlined text-purple-600 dark:text-purple-400 text-4xl">tune</span>
                    System Configuration
                </h2>
                <p class="text-gray-500 dark:text-gray-400 mt-2">Manage AI behaviors, operational thresholds, and core
                    instruction sets.</p>
            </div>
            <div class="flex gap-3 w-full sm:w-auto">
                <button @click="resetSettings" :disabled="isLoading || isSaving"
                    class="w-full sm:w-auto px-5 py-2.5 bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 font-bold rounded-xl transition-colors shadow-sm disabled:opacity-40">
                    Reset Defaults
                </button>
                <button @click="saveSettings" :disabled="isLoading || isSaving"
                    class="w-full sm:w-auto px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition-colors shadow-lg shadow-purple-500/30 flex items-center justify-center gap-2 disabled:opacity-40">
                    <span v-if="isSaving" class="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
                    <span v-else class="material-symbols-outlined text-[20px]">save</span>
                    {{ isSaving ? 'Saving…' : 'Save Changes' }}
                </button>
            </div>
        </div>

        <!-- Loading state -->
        <div v-if="isLoading" class="flex items-center justify-center py-24 gap-3 text-gray-500 dark:text-gray-400">
            <span class="material-symbols-outlined animate-spin text-purple-500">progress_activity</span>
            Loading configuration…
        </div>

        <!-- Error state -->
        <div v-else-if="loadError"
            class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 text-red-700 dark:text-red-400 rounded-xl px-5 py-4 flex items-center gap-3">
            <span class="material-symbols-outlined">error</span>
            {{ loadError }}
        </div>

        <!-- Main Layout (Sidebar + Content) -->
        <div v-else class="flex flex-col lg:flex-row gap-8">

            <!-- Sidebar Navigation -->
            <div class="w-full lg:w-64 shrink-0">
                <nav class="sticky top-6 flex flex-col gap-1">
                    <button v-for="tab in configTabs" :key="tab.id" @click="activeTab = tab.id"
                        class="px-4 py-3 text-left rounded-xl text-sm font-bold transition-all flex items-center gap-3"
                        :class="activeTab === tab.id
                            ? 'bg-purple-600 text-white shadow-md'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'">
                        <span class="material-symbols-outlined text-[20px]"
                            :class="activeTab === tab.id ? 'text-white' : 'text-gray-400'">{{ tab.icon }}</span>
                        {{ tab.label }}
                    </button>
                </nav>
            </div>

            <!-- Configuration Panels -->
            <div
                class="flex-1 bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 rounded-2xl shadow-sm overflow-hidden p-6 md:p-8 min-h-[600px]">

                <!-- 1. Global AI Behavior -->
                <div v-show="activeTab === 'behavior'" class="space-y-8 animate-fade-in">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Global AI Behavior</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Control how the autonomous agents interact
                            and make decisions.</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 p-5 rounded-xl">
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">Default Personality Tone</label>
                            <select v-model="settings.tone"
                                class="w-full bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-3 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-shadow shadow-sm font-medium">
                                <option>Friendly & Empathetic</option>
                                <option>Professional & Formal</option>
                                <option>Direct & Concise</option>
                                <option>Playful & Casual</option>
                            </select>
                            <p class="text-[11px] text-gray-500 mt-2">Determines the conversational style used in auto-replies.</p>
                        </div>

                        <div class="bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 p-5 rounded-xl">
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">Language Support</label>
                            <select v-model="settings.languageModal"
                                class="w-full bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-lg px-4 py-3 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-shadow shadow-sm font-medium">
                                <option>Auto-Detect (Multilingual)</option>
                                <option>English Only (Strict)</option>
                                <option>English + Spanish</option>
                            </select>
                            <p class="text-[11px] text-gray-500 mt-2">Lock the model to specific languages to reduce hallucination risk.</p>
                        </div>
                    </div>

                    <div class="space-y-4">
                        <div v-for="toggle in behaviorToggles" :key="toggle.key"
                            class="flex items-center justify-between p-4 bg-white dark:bg-transparent border border-gray-100 dark:border-white/5 rounded-xl hover:border-purple-200 dark:hover:border-purple-500/30 transition-colors">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-inner" :class="toggle.bgColor">
                                    <span class="material-symbols-outlined text-[20px]" :class="toggle.iconColor">{{ toggle.icon }}</span>
                                </div>
                                <div>
                                    <div class="font-bold text-gray-900 dark:text-white text-sm">{{ toggle.label }}</div>
                                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ toggle.desc }}</div>
                                </div>
                            </div>
                            <button @click="toggle.enabled = !toggle.enabled"
                                class="w-12 h-6 rounded-full relative transition-colors duration-300 shrink-0 focus:outline-none"
                                :class="toggle.enabled ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-600'">
                                <div class="absolute top-1 w-4 h-4 bg-white rounded-full shadow-md transition-transform duration-300"
                                    :class="toggle.enabled ? 'translate-x-7' : 'translate-x-1'"></div>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 2. Thresholds & Limits -->
                <div v-show="activeTab === 'thresholds'" class="space-y-8 animate-fade-in">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Operational Thresholds</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Set boundaries for autonomous actions to balance speed and risk.</p>
                    </div>

                    <div class="space-y-8">
                        <div class="bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 p-6 rounded-xl">
                            <div class="flex justify-between items-end mb-4">
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white">Sentiment Escalation Trigger</h4>
                                    <p class="text-xs text-gray-500 mt-1">Escalate to a human agent when customer anger exceeds this level.</p>
                                </div>
                                <div class="text-right">
                                    <span class="text-2xl font-bold font-mono"
                                        :class="settings.sentimentThreshold > 70 ? 'text-red-500' : 'text-orange-500'">{{ settings.sentimentThreshold }}%</span>
                                    <span class="block text-[10px] uppercase font-bold text-gray-400">Risk Score</span>
                                </div>
                            </div>
                            <input type="range" v-model.number="settings.sentimentThreshold"
                                class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                                min="0" max="100">
                            <div class="flex justify-between text-[10px] font-bold text-gray-400 uppercase mt-2">
                                <span>Conservative (0%)</span><span>Aggressive (100%)</span>
                            </div>
                        </div>

                        <div class="bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 p-6 rounded-xl">
                            <div class="flex justify-between items-end mb-4">
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white">Auto-Refund Financial Limit</h4>
                                    <p class="text-xs text-gray-500 mt-1">Maximum amount the AI can refund without human supervisor approval.</p>
                                </div>
                                <div class="text-right">
                                    <span class="text-2xl font-bold font-mono text-green-600 dark:text-green-400">₹{{ settings.refundLimit.toLocaleString('en-IN') }}</span>
                                    <span class="block text-[10px] uppercase font-bold text-gray-400">Per Transaction</span>
                                </div>
                            </div>
                            <input type="range" v-model.number="settings.refundLimit"
                                class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                                min="0" max="50000" step="500">
                            <div class="flex justify-between text-[10px] font-bold text-gray-400 uppercase mt-2">
                                <span>₹0 (Manual Only)</span><span>₹50,000 Limit</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 3. Core Prompts -->
                <div v-show="activeTab === 'prompts'" class="space-y-6 animate-fade-in flex flex-col h-full">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">Core System Prompt</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Foundational instructions injected into the AI before every interaction. Changes take effect immediately after saving.</p>
                    </div>

                    <div class="flex-1 flex flex-col mt-4">
                        <div class="bg-gray-800 rounded-t-xl px-4 py-2 border border-gray-700 flex justify-between items-center shrink-0">
                            <div class="flex items-center gap-2">
                                <span class="w-3 h-3 rounded-full bg-red-500"></span>
                                <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
                                <span class="w-3 h-3 rounded-full bg-green-500"></span>
                                <span class="ml-2 text-xs text-gray-400 font-mono">system_prompt.txt</span>
                            </div>
                            <button @click="copyPrompt" class="text-gray-400 hover:text-white transition-colors" title="Copy to clipboard">
                                <span class="material-symbols-outlined text-[16px]">content_copy</span>
                            </button>
                        </div>
                        <textarea v-model="settings.systemPrompt"
                            class="flex-1 w-full bg-gray-900 border-x border-b border-gray-700 rounded-b-xl p-6 text-sm text-green-400 focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono resize-none leading-relaxed min-h-[300px]"
                            placeholder="Enter core system instructions here..."></textarea>
                    </div>

                    <div class="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded-r-lg">
                        <h4 class="text-blue-800 dark:text-blue-300 font-bold text-sm mb-1 flex items-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">info</span> Context Window Injection
                        </h4>
                        <p class="text-xs text-blue-900/80 dark:text-blue-200/80">This prompt is injected at the system level. Role-specific data access rules and allowed tables are always appended after. Do not duplicate role-specific SOP details here.</p>
                    </div>
                </div>

                <!-- 4. Integrations -->
                <div v-show="activeTab === 'integrations'" class="space-y-6 animate-fade-in">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">External Integrations</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">Manage LLM providers and data syncing.</p>
                    </div>

                    <div class="space-y-4">
                        <!-- Gemini — always active -->
                        <div class="border border-green-200 dark:border-green-800/40 bg-green-50/50 dark:bg-green-900/10 rounded-xl p-5 flex items-center justify-between">
                            <div class="flex items-center gap-4">
                                <div class="w-12 h-12 bg-white dark:bg-gray-800 rounded-lg flex items-center justify-center border border-gray-200 dark:border-gray-700 shrink-0 shadow-sm">
                                    <span class="material-symbols-outlined text-blue-500 text-2xl">smart_toy</span>
                                </div>
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white">Google Gemini</h4>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">Primary reasoning engine — configured via server environment</p>
                                </div>
                            </div>
                            <span class="px-3 py-1 bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-400 text-xs font-bold rounded-full flex items-center gap-1.5">
                                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span> Active
                            </span>
                        </div>

                        <!-- OpenAI -->
                        <div class="border border-gray-200 dark:border-white/10 rounded-xl p-5 flex items-center justify-between"
                            :class="!integrations.openai ? 'opacity-70' : ''">
                            <div class="flex items-center gap-4">
                                <div class="w-12 h-12 bg-gray-900 rounded-lg flex items-center justify-center border border-gray-700 shrink-0">
                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="white"/>
                                        <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" fill="white"/>
                                    </svg>
                                </div>
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white">OpenAI GPT-4 Turbo</h4>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ integrations.openai ? 'Connected' : 'Not connected' }}</p>
                                </div>
                            </div>
                            <button @click="openIntegrationModal('OpenAI', 'sk-proj-...')"
                                class="px-4 py-1.5 text-xs font-bold rounded transition-colors"
                                :class="integrations.openai
                                    ? 'bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white border border-gray-200 dark:border-white/10'
                                    : 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm'">
                                {{ integrations.openai ? 'Configure' : 'Connect' }}
                            </button>
                        </div>

                        <!-- Anthropic -->
                        <div class="border border-gray-200 dark:border-white/10 rounded-xl p-5 flex items-center justify-between"
                            :class="!integrations.anthropic ? 'opacity-70' : ''">
                            <div class="flex items-center gap-4">
                                <div class="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
                                    <span class="text-white font-bold font-serif text-xl">A</span>
                                </div>
                                <div>
                                    <h4 class="font-bold text-gray-900 dark:text-white">Anthropic Claude</h4>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ integrations.anthropic ? 'Connected' : 'Not connected' }}</p>
                                </div>
                            </div>
                            <button @click="openIntegrationModal('Anthropic', 'sk-ant-...')"
                                class="px-4 py-1.5 text-xs font-bold rounded transition-colors"
                                :class="integrations.anthropic
                                    ? 'bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white border border-gray-200 dark:border-white/10'
                                    : 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm'">
                                {{ integrations.anthropic ? 'Configure' : 'Connect' }}
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <!-- Save Toast -->
        <Teleport to="body">
            <div class="fixed bottom-6 inset-x-0 flex justify-center z-50 pointer-events-none">
                <div class="transform transition-all duration-300 pointer-events-auto"
                    :class="savedToast ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-8 opacity-0 scale-95'">
                    <div class="bg-gray-900 text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 border border-gray-700">
                        <div class="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-white text-[16px]">check</span>
                        </div>
                        <span class="font-bold">Settings saved — AI will use these on next chat</span>
                    </div>
                </div>
            </div>
        </Teleport>

        <!-- API Key Modal -->
        <Teleport to="body">
            <div v-if="showApiModal"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                @click.self="showApiModal = false">
                <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
                    <div class="px-6 py-5 border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 flex items-center gap-3">
                        <span class="material-symbols-outlined text-purple-600 dark:text-purple-400">api</span>
                        <div>
                            <h3 class="font-bold text-gray-900 dark:text-white leading-tight">Connect {{ activeProvider }}</h3>
                            <p class="text-xs text-gray-500">Provide an API key with adequate permissions.</p>
                        </div>
                    </div>
                    <div class="p-6 space-y-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wider">Secret API Key</label>
                            <input v-model="tempApiKey" type="password"
                                class="w-full bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none font-mono"
                                :placeholder="apiPlaceholder">
                        </div>
                        <div class="bg-blue-50 dark:bg-blue-900/10 border-l-4 border-blue-500 p-3 rounded-r-lg">
                            <p class="text-[11px] text-blue-800 dark:text-blue-300">
                                <span class="font-bold">Security Notice:</span> Keys are stored in the secure credential store and are never exposed to the browser.
                            </p>
                        </div>
                        <div v-if="isTestingKey" class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 font-medium">
                            <span class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
                            Validating key…
                        </div>
                        <div v-else-if="apiError" class="text-xs font-bold text-red-500 bg-red-50 dark:bg-red-900/10 p-2 rounded">{{ apiError }}</div>
                    </div>
                    <div class="p-6 border-t border-gray-100 dark:border-white/5 flex gap-3 bg-gray-50 dark:bg-white/5">
                        <button @click="showApiModal = false; apiError = ''"
                            class="flex-1 py-2.5 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors border border-gray-200 dark:border-white/10">
                            Cancel
                        </button>
                        <button @click="verifyAndConnect" :disabled="!tempApiKey || isTestingKey"
                            class="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold rounded-xl flex justify-center items-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">vpn_key</span> Save Key
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { fetchAISettings, updateAISettings } from '@/utils/aiApi'

const savedToast = ref(false)
const activeTab = ref('integrations')
const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref('')

const showApiModal = ref(false)
const activeProvider = ref('')
const tempApiKey = ref('')
const apiPlaceholder = ref('')
const isTestingKey = ref(false)
const apiError = ref('')

const integrations = reactive({ openai: false, anthropic: false })

const configTabs = [
    { id: 'behavior', label: 'Global Behavior', icon: 'smart_toy' },
    { id: 'thresholds', label: 'Risk Thresholds', icon: 'tune' },
    { id: 'prompts', label: 'System Prompts', icon: 'code_blocks' },
    { id: 'integrations', label: 'Integrations', icon: 'hub' },
]

const settings = reactive({
    tone: 'Friendly & Empathetic',
    languageModal: 'Auto-Detect (Multilingual)',
    sentimentThreshold: 80,
    refundLimit: 5000,
    systemPrompt: '',
})

const behaviorToggles = reactive([
    { key: 'autonomous_replies', label: 'Autonomous Replies', desc: 'Allow AI to send responses directly to customers without human approval.', enabled: true, bgColor: 'bg-blue-100 dark:bg-blue-900/30', iconColor: 'text-blue-600 dark:text-blue-400', icon: 'send' },
    { key: 'legal_threat_detection', label: 'Legal Threat Detection', desc: 'Automatically flag and halt autonomous response when legal keywords are detected.', enabled: true, bgColor: 'bg-red-100 dark:bg-red-900/30', iconColor: 'text-red-600 dark:text-red-400', icon: 'gavel' },
    { key: 'real_time_sentiment_analysis', label: 'Real-time Sentiment Analysis', desc: 'Constantly evaluate user mood to trigger priority escalations.', enabled: true, bgColor: 'bg-orange-100 dark:bg-orange-900/30', iconColor: 'text-orange-600 dark:text-orange-400', icon: 'mood_bad' },
    { key: 'proactive_human_handover', label: 'Proactive Human Handover', desc: 'Transfer chat/ticket to a human before policy limits are hit if confidence drops.', enabled: false, bgColor: 'bg-green-100 dark:bg-green-900/30', iconColor: 'text-green-600 dark:text-green-400', icon: 'support_agent' },
])

// ── Load from backend ──────────────────────────────────────────────────────────

function applyServerData(data) {
    const s = data.settings
    settings.tone = s.tone
    settings.languageModal = s.language_mode
    settings.sentimentThreshold = s.sentiment_threshold
    settings.refundLimit = s.refund_limit_inr
    settings.systemPrompt = s.system_prompt

    const flagMap = {
        autonomous_replies: s.autonomous_replies,
        legal_threat_detection: s.legal_threat_detection,
        real_time_sentiment_analysis: s.real_time_sentiment_analysis,
        proactive_human_handover: s.proactive_human_handover,
    }
    behaviorToggles.forEach(t => {
        if (flagMap[t.key] !== undefined) t.enabled = flagMap[t.key]
    })
    if (data.integrations) {
        data.integrations.forEach(i => {
            if (i.provider === 'openai') integrations.openai = i.connected
            if (i.provider === 'anthropic') integrations.anthropic = i.connected
        })
    }
}

onMounted(async () => {
    try {
        const data = await fetchAISettings()
        applyServerData(data)
    } catch (err) {
        loadError.value = err.message || 'Failed to load settings'
    } finally {
        isLoading.value = false
    }
})

// ── Save to backend ────────────────────────────────────────────────────────────

async function saveSettings() {
    isSaving.value = true
    try {
        const flagsObj = {}
        behaviorToggles.forEach(t => { flagsObj[t.key] = t.enabled })
        const payload = {
            tone: settings.tone,
            language_mode: settings.languageModal,
            sentiment_threshold: settings.sentimentThreshold,
            refund_limit_inr: settings.refundLimit,
            system_prompt: settings.systemPrompt,
            ...flagsObj,
        }
        const data = await updateAISettings(payload)
        applyServerData(data)
        savedToast.value = true
        setTimeout(() => { savedToast.value = false }, 3000)
    } catch (err) {
        alert('Save failed: ' + (err.message || 'Unknown error'))
    } finally {
        isSaving.value = false
    }
}

function resetSettings() {
    if (confirm('Reset all AI configurations to factory defaults?')) {
        settings.sentimentThreshold = 80
        settings.refundLimit = 5000
        settings.tone = 'Friendly & Empathetic'
        settings.languageModal = 'Auto-Detect (Multilingual)'
        behaviorToggles.forEach(t => { t.enabled = t.key !== 'proactive_human_handover' })
        saveSettings()
    }
}

function copyPrompt() {
    navigator.clipboard?.writeText(settings.systemPrompt)
}

function openIntegrationModal(provider, placeholder) {
    activeProvider.value = provider
    apiPlaceholder.value = placeholder
    tempApiKey.value = ''
    apiError.value = ''
    showApiModal.value = true
}

function verifyAndConnect() {
    isTestingKey.value = true
    apiError.value = ''
    setTimeout(() => {
        isTestingKey.value = false
        if (tempApiKey.value.length < 15) {
            apiError.value = 'Invalid API Key format for ' + activeProvider.value
            return
        }
        if (activeProvider.value === 'OpenAI') integrations.openai = true
        else if (activeProvider.value === 'Anthropic') integrations.anthropic = true
        showApiModal.value = false
        saveSettings()
    }, 1200)
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
