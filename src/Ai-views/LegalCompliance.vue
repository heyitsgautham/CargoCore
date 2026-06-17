<template>
    <div class="max-w-5xl mx-auto space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-green-500 text-3xl">gavel</span>
                    Legal & Compliance
                </h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Platform rules, terms of service, and data
                    policies</p>
            </div>
            <div class="flex gap-2">
                <button
                    class="px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/10 text-gray-700 dark:text-gray-300 text-sm font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                    <span class="material-symbols-outlined text-[18px]">history</span> Version History
                </button>
                <button
                    class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-bold rounded-lg transition-colors flex items-center gap-2 shadow-sm">
                    <span class="material-symbols-outlined text-[18px]">download</span> Export PDF
                </button>
            </div>
        </div>

        <!-- Compliance Status Banner -->
        <div
            class="bg-gradient-to-r from-green-50 to-white dark:from-green-900/20 dark:to-black/20 border border-green-200 dark:border-green-500/20 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
            <div class="flex items-center gap-4">
                <div
                    class="w-12 h-12 rounded-full bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 flex justify-center items-center shrink-0 shadow-inner">
                    <span class="material-symbols-outlined text-2xl">verified_user</span>
                </div>
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white">System Compliance: Optimal</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-0.5">All policies and platform rules are
                        up-to-date with current regional regulations.</p>
                </div>
            </div>
            <div class="flex items-center gap-8 self-end md:self-auto text-sm">
                <div>
                    <div class="text-xs text-gray-500 uppercase font-bold tracking-wider mb-0.5">Last Audit</div>
                    <div class="font-bold text-gray-900 dark:text-white">Oct 12, 2024</div>
                </div>
                <div>
                    <div class="text-xs text-gray-500 uppercase font-bold tracking-wider mb-0.5">Next Update</div>
                    <div class="font-bold text-gray-900 dark:text-white">Jan 1, 2025</div>
                </div>
            </div>
        </div>

        <!-- Content Area with Sidebar Nav -->
        <div class="flex flex-col md:flex-row gap-6">

            <!-- Sidebar Navigation -->
            <div class="w-full md:w-64 shrink-0">
                <div
                    class="bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 rounded-xl p-2 shadow-sm sticky top-6">
                    <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
                        class="w-full text-left px-4 py-3 rounded-lg text-sm font-bold transition-all flex items-center gap-3 mb-1 last:mb-0"
                        :class="activeTab === tab.id ? 'bg-green-50 text-green-700 dark:bg-green-500/20 dark:text-green-400 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/5'">
                        <span class="material-symbols-outlined text-[18px]"
                            :class="activeTab === tab.id ? 'text-green-600 dark:text-green-400' : 'text-gray-400'">{{
                            tab.icon }}</span>
                        {{ tab.label }}
                        <span v-if="tab.badge"
                            class="ml-auto px-2 py-0.5 bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400 text-[10px] rounded">{{
                            tab.badge }}</span>
                    </button>
                </div>
            </div>

            <!-- Main Content Area -->
            <div
                class="flex-1 bg-white dark:bg-black/20 border border-gray-100 dark:border-white/5 p-6 md:p-8 rounded-xl shadow-sm min-h-[600px]">

                <!-- Platform Rules -->
                <div v-if="activeTab === 'rules'" class="space-y-6 animate-fade-in">
                    <div class="mb-6 border-b border-gray-100 dark:border-white/5 pb-4">
                        <h3 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            Platform Rules & Guidelines
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">Mandatory behavioral and operational
                            standards for all network participants.</p>
                    </div>

                    <div class="space-y-4">
                        <div v-for="rule in platformRules" :key="rule.id"
                            class="bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-200 dark:border-white/10 overflow-hidden transition-all duration-300 shadow-sm"
                            :class="rule.expanded ? 'ring-2 ring-green-500/50 border-transparent dark:border-transparent' : 'hover:border-green-300 dark:hover:border-green-500/30'">
                            <button class="w-full flex items-center gap-4 p-5 text-left focus:outline-none"
                                @click="rule.expanded = !rule.expanded">
                                <div
                                    class="w-10 h-10 rounded-full bg-white dark:bg-black/40 flex items-center justify-center text-green-600 dark:text-green-400 shadow-sm shrink-0">
                                    <span class="material-symbols-outlined text-[20px]">{{ rule.icon }}</span>
                                </div>
                                <div class="flex-1">
                                    <h4 class="font-bold text-gray-900 dark:text-white text-base">{{ rule.title }}</h4>
                                </div>
                                <span class="material-symbols-outlined text-gray-400 transition-transform duration-300"
                                    :class="rule.expanded ? 'rotate-180' : ''">expand_more</span>
                            </button>
                            <!-- Expandable Content -->
                            <div class="grid transition-all duration-300 ease-in-out"
                                :class="rule.expanded ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'">
                                <div class="overflow-hidden">
                                    <div
                                        class="p-5 pt-0 text-sm text-gray-600 dark:text-gray-300 leading-relaxed border-t border-gray-200/50 dark:border-white/5 mt-2 mx-5">
                                        {{ rule.content }}
                                        <div
                                            class="mt-4 p-3 bg-red-50 dark:bg-red-500/10 border-l-2 border-red-500 rounded text-xs text-red-800 dark:text-red-200">
                                            <strong>Violation Penalty:</strong> {{ rule.penalty }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Terms of Service -->
                <div v-if="activeTab === 'tos'" class="space-y-6 animate-fade-in flex flex-col h-full">
                    <div
                        class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2 border-b border-gray-100 dark:border-white/5 pb-4 shrink-0">
                        <div>
                            <h3 class="text-2xl font-bold text-gray-900 dark:text-white">Terms of Service</h3>
                            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Binding legal agreement for
                                platform usage.</p>
                        </div>
                        <div class="text-right">
                            <span
                                class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold tracking-wider block mb-1">Last
                                Updated</span>
                            <span
                                class="px-2.5 py-1 bg-gray-100 dark:bg-white/10 text-gray-800 dark:text-white text-xs font-bold rounded">October
                                15, 2024</span>
                        </div>
                    </div>

                    <div
                        class="flex-1 bg-gray-50 dark:bg-black/40 rounded-xl border border-gray-200 dark:border-white/10 p-6 md:p-8 overflow-y-auto custom-scrollbar prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 shadow-inner">
                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">1. Acceptance of Terms</h4>
                        <p class="mb-6">By accessing or using the Cargo-Core Logistics platform, website, mobile
                            applications, or any associated services (collectively, the "Service"), you agree to be
                            bound by these Terms of Service. If you do not agree to all the terms and conditions, you
                            may not access the website or use any services.</p>

                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">2. User Accounts &
                            Responsibilities</h4>
                        <p class="mb-6">You are responsible for maintaining the confidentiality of your account password
                            and login credentials. You are solely responsible for all activities that occur under your
                            account. You must notify us immediately upon becoming aware of any breach of security or
                            unauthorized use of your account.</p>

                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">3. Service Modifications</h4>
                        <p class="mb-6">Cargo-Core reserves the right, at its sole discretion, to modify or replace any
                            part of this Agreement at any time. It is your responsibility to check this Agreement
                            periodically for changes. Your continued use of or access to the website following the
                            posting of any changes to this Agreement constitutes acceptance of those changes.</p>

                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">4. Logistics & Cargo Liability
                        </h4>
                        <p class="mb-6">Cargo-Core acts primarily as a technology platform connecting shippers with
                            carriers. We are not a motor carrier or freight forwarder. We are not liable for damages,
                            theft, or loss caused by third-party carriers beyond the explicitly declared insured value
                            selected at the time of booking. Claims must be filed within 30 days of the delivery
                            execution date.</p>

                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">5. Dispute Resolution &
                            Arbitration</h4>
                        <p class="mb-6">Any disputes arising out of or relating to these Terms or the Service shall be
                            resolved through binding arbitration in the State of Delaware, rather than in court. You and
                            Cargo-Core agree that any dispute resolution proceedings will be conducted only on an
                            individual basis and not in a class, consolidated, or representative action.</p>

                        <h4 class="font-bold text-lg text-gray-900 dark:text-white mb-4">6. Intellectual Property</h4>
                        <p class="mb-6">The Service and its original content, features, and functionality are owned by
                            Cargo-Core and are protected by international copyright, trademark, patent, trade secret,
                            and other intellectual property or proprietary rights laws.</p>
                    </div>
                </div>

                <!-- Privacy Policy -->
                <div v-if="activeTab === 'privacy'" class="space-y-6 animate-fade-in">
                    <div class="mb-6 border-b border-gray-100 dark:border-white/5 pb-4">
                        <h3 class="text-2xl font-bold text-gray-900 dark:text-white">Privacy & Data Policy</h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">How we collect, use, and protect your
                            information.</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div
                            class="bg-blue-50 dark:bg-blue-900/10 p-5 rounded-xl border border-blue-100 dark:border-blue-500/20 text-blue-900 dark:text-blue-100">
                            <h4 class="font-bold text-blue-700 dark:text-blue-300 flex items-center gap-2 mb-2"><span
                                    class="material-symbols-outlined text-[18px]">visibility</span> Data Collection</h4>
                            <p class="text-sm">We collect profile info, payment data, and real-time GPS location
                                strictly for facilitating logistics services and tracking features.</p>
                        </div>
                        <div
                            class="bg-purple-50 dark:bg-purple-900/10 p-5 rounded-xl border border-purple-100 dark:border-purple-500/20 text-purple-900 dark:text-purple-100">
                            <h4 class="font-bold text-purple-700 dark:text-purple-300 flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-[18px]">share</span> Third-Party Sharing
                            </h4>
                            <p class="text-sm">We share data with carrier partners, insurance providers, and payment
                                gateways strictly for executing your requested services. We never sell your data.</p>
                        </div>
                        <div
                            class="bg-green-50 dark:bg-green-900/10 p-5 rounded-xl border border-green-100 dark:border-green-500/20 text-green-900 dark:text-green-100">
                            <h4 class="font-bold text-green-700 dark:text-green-300 flex items-center gap-2 mb-2"><span
                                    class="material-symbols-outlined text-[18px]">verified</span> GDPR & CCPA</h4>
                            <p class="text-sm">We are fully compliant with GDPR and CCPA. You have the right to access,
                                export, or delete your personal data at any time.</p>
                        </div>
                        <div
                            class="bg-orange-50 dark:bg-orange-900/10 p-5 rounded-xl border border-orange-100 dark:border-orange-500/20 text-orange-900 dark:text-orange-100">
                            <h4 class="font-bold text-orange-700 dark:text-orange-300 flex items-center gap-2 mb-2">
                                <span class="material-symbols-outlined text-[18px]">cookie</span> Cookie Policy</h4>
                            <p class="text-sm">We use essential cookies required for the platform to function. Marketing
                                and tracking cookies are strictly opt-in.</p>
                        </div>
                    </div>

                    <!-- Data Deletion CTA -->
                    <div
                        class="bg-gray-900 dark:bg-black p-6 sm:p-8 rounded-xl relative overflow-hidden flex flex-col sm:flex-row items-center justify-between gap-6 shadow-lg">
                        <div
                            class="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 pointer-events-none">
                        </div>
                        <div class="relative z-10">
                            <h4 class="font-bold text-white text-lg flex items-center gap-2 mb-1">
                                <span class="material-symbols-outlined text-red-400">delete_forever</span> Data Deletion
                                Request
                            </h4>
                            <p class="text-sm text-gray-400">Exercise your Right to be Forgotten. Submit a formal
                                request to permanently purge your PII from our active databases.</p>
                        </div>
                        <button @click="showDataRequest = true"
                            class="relative z-10 whitespace-nowrap px-6 py-3 bg-white hover:bg-gray-100 text-gray-900 font-bold rounded-xl text-sm transition-colors shadow-sm">
                            Initiate Request
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Request Modal -->
        <Teleport to="body">
            <div v-if="showDataRequest"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                @click.self="showDataRequest = false">
                <div
                    class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 dark:border-white/10 overflow-hidden">
                    <div
                        class="p-6 border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/5 flex items-center gap-3">
                        <span class="material-symbols-outlined text-red-500 text-3xl">warning</span>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Data Deletion Request</h3>
                            <p class="text-xs text-gray-500 mt-1">This action cannot be undone.</p>
                        </div>
                    </div>
                    <div class="p-6 space-y-5">
                        <div
                            class="p-4 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl text-sm text-red-800 dark:text-red-300 mb-2">
                            Submitting this request will permanently delete your account, transaction history, and
                            associated Personal Identifiable Information (PII) within 30 days as per GDPR/CCPA
                            guidelines.
                        </div>

                        <!-- Formal Input Form -->
                        <div class="space-y-4">
                            <div>
                                <label
                                    class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Confirm
                                    Email Address</label>
                                <div class="relative">
                                    <input v-model="dataRequestEmail" type="email"
                                        class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-900 dark:text-white outline-none focus:border-red-500 transition-colors"
                                        placeholder="user@email.com" />
                                    <span
                                        class="material-symbols-outlined absolute left-3 top-3.5 text-gray-400 text-[18px]">mail</span>
                                </div>
                            </div>
                            <div>
                                <label
                                    class="block text-[10px] font-bold text-gray-700 dark:text-gray-300 mb-1.5 uppercase tracking-wider">Reason
                                    for Deletion (Optional)</label>
                                <textarea v-model="dataRequestReason" rows="3"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white outline-none focus:border-red-500 transition-colors resize-none"
                                    placeholder="Help us understand why you are leaving..."></textarea>
                            </div>

                            <!-- Checkbox confirmation -->
                            <label class="flex items-start gap-3 cursor-pointer group mt-2">
                                <div class="relative flex items-center justify-center shrink-0 mt-0.5">
                                    <input type="checkbox" v-model="confirmChecked"
                                        class="peer appearance-none w-5 h-5 border-2 border-gray-300 dark:border-gray-600 rounded-md checked:bg-red-500 checked:border-red-500 transition-colors cursor-pointer">
                                    <span
                                        class="material-symbols-outlined absolute text-white text-[16px] opacity-0 peer-checked:opacity-100 pointer-events-none transition-opacity">check</span>
                                </div>
                                <span
                                    class="text-xs text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-200 transition-colors leading-relaxed">I
                                    understand that deleting my data is permanent and my account cannot be recovered. I
                                    agree to forfeit any pending balances.</span>
                            </label>
                        </div>
                    </div>
                    <div class="p-6 border-t border-gray-100 dark:border-white/5 flex gap-3 bg-gray-50 dark:bg-white/5">
                        <button @click="showDataRequest = false"
                            class="flex-1 py-2.5 bg-white dark:bg-black/20 hover:bg-gray-100 dark:hover:bg-white/10 border border-gray-200 dark:border-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors shadow-sm">
                            Cancel
                        </button>
                        <button @click="submitDataRequest" :disabled="!isSubmitValid"
                            class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">delete</span> Submit Request
                        </button>
                    </div>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const tabs = [
    { id: 'rules', label: 'Platform Rules', icon: 'gavel' },
    { id: 'tos', label: 'Terms of Service', icon: 'description', badge: 'Updated' },
    { id: 'privacy', label: 'Privacy Policy', icon: 'shield_lock' }
]
const activeTab = ref('rules')

const showDataRequest = ref(false)
const dataRequestEmail = ref('')
const dataRequestReason = ref('')
const confirmChecked = ref(false)

const isSubmitValid = computed(() => {
    return dataRequestEmail.value.includes('@') && confirmChecked.value
})

const platformRules = ref([
    { id: 1, title: 'Driver Conduct & Professionalism', icon: 'support_agent', content: 'All drivers must maintain a professional demeanor at all times. Harassment, discrimination, or rude behavior towards customers, warehouse staff, or other drivers is strictly prohibited. Verbal or physical abuse will result in immediate permanent suspension from the platform. Drivers are expected to represent Cargo-Core positively.', penalty: 'Immediate Permanent Suspension', expanded: true },
    { id: 2, title: 'Vehicle Safety & Inspections', icon: 'car_repair', content: 'Vehicles must undergo documented weekly safety inspections. Tires, brakes, lights, and fluid levels must be maintained according to manufacturer specifications. Failure to report damages or driving an unsafe vehicle violates our core safety tenets and voids liability coverage.', penalty: 'Liability Void & 30-Day Suspension', expanded: false },
    { id: 3, title: 'Strict Cancellation Policy', icon: 'cancel', content: 'Drivers cannot cancel an accepted job within 1 hour of the scheduled pickup window without documented proof of a severe emergency (medical issue, major mechanical failure, accident). Excessive cancellations disrupt supply chain operations and negatively impact customer trust.', penalty: 'Account Lock (24 Hours)', expanded: false },
    { id: 4, title: 'Payment Processing Rules', icon: 'payments', content: 'All service payments must be processed digitally through the platform to ensure secure escrow and transparent accounting. Accepting physical cash tips is permitted, but soliciting or demanding off-platform extra fees for standard services is strictly prohibited.', penalty: 'Immediate Termination & Escrow Forfeit', expanded: false },
    { id: 5, title: 'Zero Tolerance Substance Policy', icon: 'no_drinks', content: 'Cargo-Core enforces a strict zero-tolerance policy for drug or alcohol use while on duty, on call, or operating a vehicle on the platform. Random screening may be requested. Any confirmed violation, or refusal to test following an incident, leads to immediate termination and reporting to local authorities.', penalty: 'Immediate Termination & Legal Reporting', expanded: false },
])

function submitDataRequest() {
    // In a real app this would call an API
    alert(`Data deletion request submitted for ${dataRequestEmail.value}`);
    dataRequestEmail.value = ''
    dataRequestReason.value = ''
    confirmChecked.value = false
    showDataRequest.value = false
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
