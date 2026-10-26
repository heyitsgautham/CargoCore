<template>
    <footer class="py-20 px-6 border-t border-white/5 bg-black/80 backdrop-blur-xl relative z-10">
        <div class="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-12 mb-16">
            <div>
                <h4 class="font-bold text-white mb-6">Learn</h4>
                <ul class="space-y-4 text-gray-400 text-sm">
                    <li><a href="#role-logistic" class="hover:text-cyan-400 transition-colors">Logistics Manager</a>
                    </li>
                    <li><a href="#role-warehouse" class="hover:text-cyan-400 transition-colors">Warehouse
                            Manager</a></li>
                    <li><a href="#role-dispatcher" class="hover:text-cyan-400 transition-colors">Dispatcher</a></li>
                    <li><a href="#role-ai" class="hover:text-cyan-400 transition-colors">AI Bot</a></li>
                    <li><a href="#role-driver" class="hover:text-cyan-400 transition-colors">Driver</a></li>
                    <li><a href="#role-vendor" class="hover:text-cyan-400 transition-colors">Vendor</a></li>
                </ul>
            </div>
            <div>
                <h4 class="font-bold text-white mb-6">Account</h4>
                <ul class="space-y-4 text-gray-400 text-sm">
                    <li><router-link to="/register"
                            class="hover:text-cyan-400 transition-colors">Register</router-link></li>
                    <li><router-link to="/login" class="hover:text-cyan-400 transition-colors">Login</router-link>
                    </li>
                </ul>
            </div>
            <div>
                <h4 class="font-bold text-white mb-6">Company</h4>
                <ul class="space-y-4 text-gray-400 text-sm">
                    <li><router-link to="/contact" class="hover:text-cyan-400 transition-colors">Contact
                            Us</router-link></li>
                    <li><router-link to="/terms" class="hover:text-cyan-400 transition-colors">Terms</router-link>
                    </li>
                    <li><router-link to="/privacy"
                            class="hover:text-cyan-400 transition-colors">Privacy</router-link></li>
                </ul>
            </div>
            <div>
                <h4 class="font-bold text-white mb-6">Social</h4>
                <div class="flex gap-4">
                    <!-- LinkedIn -->
                    <a href="https://linkedin.com" target="_blank"
                        class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-blue-600/20 hover:text-blue-400 border border-white/5 hover:border-blue-500/30 transition-all duration-300 group">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                            stroke-linejoin="round" class="group-hover:scale-110 transition-transform">
                            <path
                                d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z">
                            </path>
                            <rect x="2" y="9" width="4" height="12"></rect>
                            <circle cx="4" cy="4" r="2"></circle>
                        </svg>
                    </a>
                    <!-- Twitter/X -->
                    <a href="https://twitter.com" target="_blank"
                        class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/20 hover:text-white border border-white/5 hover:border-white/30 transition-all duration-300 group">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                            fill="currentColor" class="group-hover:scale-110 transition-transform">
                            <path
                                d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z" />
                        </svg>
                    </a>
                    <!-- Instagram -->
                    <a href="https://instagram.com" target="_blank"
                        class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-pink-600/20 hover:text-pink-400 border border-white/5 hover:border-pink-500/30 transition-all duration-300 group">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                            stroke-linejoin="round" class="group-hover:scale-110 transition-transform">
                            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                        </svg>
                    </a>
                </div>
            </div>
        </div>

        <div class="text-center pt-8 border-t border-white/5">
            <p class="text-gray-500 text-sm tracking-widest uppercase">Cargo-Core &mdash; Moving What Matters</p>
        </div>
    </footer>
</template>
