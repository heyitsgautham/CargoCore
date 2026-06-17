<template>
    <div class="bg-black min-h-screen text-white overflow-x-hidden font-display" ref="mainContainer">
        <!-- Footer Navigation (Bottom Fixed) -->
        <!-- Logic: "No navbar (footer-only navigation)" - This likely means a footer at the bottom of the page, not fixed bottom. Detailed in Footer section. -->

        <!-- HERO SECTION -->
        <section class="relative h-screen flex items-center justify-center overflow-hidden panel hero-section">
            <div class="absolute inset-0 z-0 opacity-80 mix-blend-screen">
                <!-- Hero Spline -->
                <SplineScene scene="https://prod.spline.design/dly62PB8Wm4vg4E3/scene.splinecode" />
            </div>

            <div class="relative z-10 text-center px-6 max-w-6xl mx-auto mt-10">
                <div class="overflow-hidden mb-4">
                    <h1
                        class="text-6xl md:text-8xl font-black tracking-tighter leading-none hero-line translate-y-full opacity-0">
                        Effortless
                    </h1>
                </div>
                <div class="overflow-hidden mb-8">
                    <h1
                        class="text-6xl md:text-8xl font-black tracking-tighter leading-none hero-line translate-y-full opacity-0">
                        Logistics Intelligence
                    </h1>
                </div>

                <div class="overflow-hidden mb-12">
                    <h1
                        class="text-6xl md:text-8xl font-black tracking-tighter leading-none hero-line translate-y-full opacity-0 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 animate-gradient-x neon-text">
                        for modern movement
                    </h1>
                </div>

                <div class="overflow-hidden mb-12">
                    <p
                        class="text-xl md:text-2xl text-gray-400 font-light tracking-wide hero-subtitle translate-y-10 opacity-0">
                        One System. Six Roles. Infinite Precision.
                    </p>
                </div>

                <div class="flex flex-col sm:flex-row gap-6 justify-center hero-buttons opacity-0 translate-y-10">
                    <router-link to="/register"
                        class="px-8 py-4 bg-white text-black font-bold text-lg rounded-full hover:bg-cyan-50 hover:shadow-[0_0_20px_rgba(34,211,238,0.6)] transition-all duration-300">
                        Get Started
                    </router-link>
                    <router-link to="/login"
                        class="px-8 py-4 bg-transparent border border-white/20 backdrop-blur-md font-bold text-lg rounded-full hover:bg-white/10 hover:border-white/50 transition-all duration-300">
                        Login System
                    </router-link>
                </div>
            </div>

            <!-- Scroll Indicator -->
            <div
                class="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-0 hero-scroll">
                <span class="text-[10px] tracking-[0.3em] uppercase text-gray-500">Scroll</span>
                <div class="w-[1px] h-12 bg-gradient-to-b from-transparent via-cyan-500 to-transparent animate-pulse">
                </div>
            </div>
        </section>

        <!-- Role 1: Logistic Manager (Image Sequence) -->
        <!-- Role 1: Logistic Manager (Image Sequence) -->
        <section id="role-logistic"
            class="min-h-screen flex flex-col md:flex-row items-center justify-between px-6 py-20 relative role-section logistic-section">
            <div class="w-full md:w-1/2 p-8 relative z-10 h-[60vh] md:h-auto flex flex-col items-center">
                <!-- Laptop Frame -->
                <div
                    class="relative w-full max-w-[960px] aspect-[1920/1200] bg-[#1a1a1a] rounded-t-2xl p-2 md:p-3 shadow-2xl border-4 border-[#2a2a2a] border-b-0 perspective-1000 group">
                    <!-- Screen Bezel/Camera -->
                    <div class="absolute top-2 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-gray-600 rounded-full z-20">
                    </div>

                    <!-- Internal Screen Area -->
                    <div class="relative w-full h-full bg-black rounded-lg overflow-hidden border border-white/5">
                        <div class="relative w-full h-full">
                            <img v-for="(img, index) in logisticImages" :key="index" :src="img"
                                class="absolute inset-0 w-full h-full  logistic-frame bg-black"
                                :style="{ zIndex: index + 1 }" alt="Logistic Dashboard Screen" />
                        </div>
                    </div>

                    <!-- Laptop Base moved inside to align with Frame's exact width -->
                    <div
                        class="absolute top-full left-1/2 -translate-x-1/2 w-[115%] h-5 bg-[#252525] border-t border-[#444] rounded-b-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] transform perspective-1000 rotate-x-12 origin-top z-30">
                        <div class="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-1.5 bg-[#1a1a1a] rounded-b-md"></div>
                    </div>
                </div>
            </div>

            <div class="w-full md:w-1/2 p-8 md:pl-20 text-left">
                <div class="role-text-container">
                    <h2
                        class="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                        Logistic Manager</h2>
                    <div
                        class="typing-container h-24 text-xl md:text-2xl text-gray-300 font-light font-mono mb-8 relative">
                        <!-- Typing text will be injected here -->
                        <span class="typing-text"></span><span class="cursor animate-pulse text-cyan-400">|</span>
                    </div>
                    <p class="role-description opacity-0 translate-y-4 text-gray-400 leading-relaxed text-lg">
                        Controls warehouses, RBAC, geofences, fleet maps, KPIs, payroll, fraud detection, AI analytics.
                    </p>
                </div>
            </div>
        </section>

        <!-- Role 2: Warehouse Manager -->
        <section id="role-warehouse"
            class="min-h-screen flex flex-col md:flex-row-reverse items-center justify-between px-6 py-20 relative role-section bg-black/50">
            <div class="w-full md:w-1/2 h-[500px] relative z-10">
                <SplineScene scene="https://prod.spline.design/h-pIvYOqSBqshSxe/scene.splinecode" />
            </div>
            <div class="w-full md:w-1/2 p-8 md:pr-20 text-left">
                <div class="role-text-container">
                    <h2
                        class="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
                        Warehouse Manager</h2>
                    <div
                        class="typing-container h-24 text-xl md:text-2xl text-gray-300 font-light font-mono mb-8 relative">
                        <span class="typing-text"></span><span class="cursor animate-pulse text-purple-400">|</span>
                    </div>
                    <p class="role-description opacity-0 translate-y-4 text-gray-400 leading-relaxed text-lg">
                        Where Inventory Becomes Intelligence... Where Orders Take Shape... Where Labor Teams Deploy...
                    </p>
                </div>
            </div>
        </section>

        <!-- Role 3: Dispatcher -->
        <section id="role-dispatcher"
            class="min-h-screen flex flex-col md:flex-row items-center justify-between px-6 py-20 relative role-section">
            <div class="w-full md:w-1/2 h-[500px] relative z-10">
                <SplineScene scene="https://prod.spline.design/qjGo2c4YrEdZD6EY/scene.splinecode" />
            </div>
            <div class="w-full md:w-1/2 p-8 md:pl-20 text-left">
                <div class="role-text-container">
                    <h2
                        class="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-500">
                        Dispatcher</h2>
                    <div
                        class="typing-container h-24 text-xl md:text-2xl text-gray-300 font-light font-mono mb-8 relative">
                        <span class="typing-text"></span><span class="cursor animate-pulse text-green-400">|</span>
                    </div>
                    <p class="role-description opacity-0 translate-y-4 text-gray-400 leading-relaxed text-lg">
                        The Route Optimizer... The Crisis Controller... The Real-Time Coordinator...
                    </p>
                </div>
            </div>
        </section>

        <!-- Role 4: AI Customer Support -->
        <!-- Role 4: AI Customer Support (New Card Design) -->
        <section id="role-ai"
            class="min-h-screen px-6 py-20 flex items-center justify-center role-section relative bg-black">
            <div
                class="w-full max-w-7xl h-[600px] bg-black/[0.96] relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl">
                <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" />

                <div class="flex flex-col md:flex-row h-full relative z-10">
                    <!-- Left Content: Text -->
                    <div class="w-full md:w-1/2 p-8 md:p-16 flex flex-col justify-center text-left">
                        <div class="role-text-container">
                            <h2
                                class="text-4xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400">
                                AI Customer Support
                            </h2>
                            <div
                                class="typing-container h-24 text-xl md:text-2xl text-neutral-300 font-light font-mono mb-8 relative">
                                <span class="typing-text"></span><span
                                    class="cursor animate-pulse text-neutral-400">|</span>
                            </div>
                            <p
                                class="role-description opacity-0 translate-y-4 text-neutral-400 leading-relaxed text-lg max-w-lg">
                                Live GPS tracking, auto rescheduling, sentiment detection, return handling, multilingual
                                AI.
                            </p>
                        </div>
                    </div>

                    <!-- Right Content: Spline -->
                    <div class="w-full md:w-1/2 relative h-full">
                        <SplineScene scene="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode"
                            class="w-full h-full" />
                    </div>
                </div>
            </div>
        </section>

        <!-- Role 5: Driver -->
        <section id="role-driver"
            class="min-h-screen flex flex-col md:flex-row items-center justify-between px-6 py-20 relative role-section driver-section">
            <div class="w-full md:w-1/2 p-8 flex justify-center relative z-10">
                <!-- iPhone 13 Pro Mobile Frame (390x844 aspect ratio roughly translates to 300x650) -->
                <div
                    class="w-[300px] h-[650px] border-8 border-gray-800 rounded-[3rem] overflow-hidden bg-black relative shadow-[0_0_50px_rgba(255,255,255,0.1)]">
                    <div class="relative w-full h-full">
                        <img v-for="(img, index) in driverImages" :key="index" :src="img"
                            class="absolute inset-0 w-full h-full object-cover driver-frame bg-black"
                            :style="{ zIndex: index + 1 }" alt="Driver App Screen" />
                    </div>
                    <!-- iPhone 13 Pro Notch (Instead of Island) -->
                    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-36 h-7 bg-gray-800 rounded-b-3xl z-20 pointer-events-none"></div>
                </div>
            </div>
            <div class="w-full md:w-1/2 p-8 md:pl-20 text-left">
                <div class="role-text-container">
                    <h2
                        class="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500">
                        Driver</h2>
                    <div
                        class="typing-container h-24 text-xl md:text-2xl text-gray-300 font-light font-mono mb-8 relative">
                        <span class="typing-text"></span><span class="cursor animate-pulse text-orange-400">|</span>
                    </div>
                    <p class="role-description opacity-0 translate-y-4 text-gray-400 leading-relaxed text-lg">
                        Manifest, geofence auto-arrival, PoD photo, earnings wallet, AI voice assistant.
                    </p>
                </div>
            </div>
        </section>

        <!-- Role 6: Vendor -->
        <!-- Role 6: Vendor -->
        <section id="role-vendor"
            class="min-h-screen px-6 py-20 flex items-center justify-center role-section relative bg-black">
            <div class="absolute inset-0 z-0">
                <SplineScene scene="https://prod.spline.design/fDRu5GDs8Enzi-PA/scene.splinecode" />
            </div>

            <div
                class="relative z-10 w-full max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-start pointer-events-none">
                <div class="w-full md:w-1/2 p-8 md:p-16 text-left pointer-events-auto">
                    <div class="role-text-container">
                        <h2
                            class="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-500">
                            Vendor / Individual</h2>
                        <div
                            class="typing-container h-24 text-xl md:text-2xl text-gray-300 font-light font-mono mb-8 relative">
                            <span class="typing-text"></span><span class="cursor animate-pulse text-teal-400">|</span>
                        </div>
                        <p class="role-description opacity-0 translate-y-4 text-gray-400 leading-relaxed text-lg">
                            Booking form, labor selection, packing toggle, AI volume estimation, instant pricing.
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- FOOTER -->
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

    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import SplineScene from '../LWDDVI-components/SplineScene.vue'
import Spotlight from '../LWDDVI-components/Spotlight.vue'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'
import TextPlugin from 'gsap/TextPlugin'

gsap.registerPlugin(ScrollTrigger, TextPlugin)

const mainContainer = ref(null)

const logisticImages = [
    '/images/logistic-screens/01-dashboard.png',
    '/images/logistic-screens/02-warehouse-management.png',
    '/images/logistic-screens/03-user-roles.png',
    '/images/logistic-screens/04-fleet-drivers.png',
    '/images/logistic-screens/05-geofencing.png',
    '/images/logistic-screens/06-finance-payroll.png',
    '/images/logistic-screens/07-rate-governance.png',
    '/images/logistic-screens/08-reverse-logistics.png',
    '/images/logistic-screens/09-reports.png',
    '/images/logistic-screens/10-ai-intelligence.png',
    '/images/logistic-screens/11-communication.png',
    '/images/logistic-screens/12-comparative-viewers.png'
]

const driverImages = [
    '/images/mobile-screens/splash.png',
    '/images/mobile-screens/login.png',
    '/images/mobile-screens/login-help.png',
    '/images/mobile-screens/pre-shift.png',
    '/images/mobile-screens/binding%20scanner.png',
    '/images/mobile-screens/binding.png'
]

// Preload Spline Scenes for "Instant" feel
const splineScenes = [
    'https://prod.spline.design/dly62PB8Wm4vg4E3/scene.splinecode', // Hero
    'https://prod.spline.design/h-pIvYOqSBqshSxe/scene.splinecode', // Warehouse
    'https://prod.spline.design/qjGo2c4YrEdZD6EY/scene.splinecode', // Dispatcher
    'https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode', // AI Support
    'https://prod.spline.design/fDRu5GDs8Enzi-PA/scene.splinecode'  // Vendor
]

onMounted(() => {
    // Preload assets in background
    splineScenes.forEach(url => {
        const link = document.createElement('link')
        link.rel = 'prefetch'
        link.href = url
        link.as = 'fetch'
        link.crossOrigin = 'anonymous'
        document.head.appendChild(link)
    })

    // Cinematic Hero Animation
    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })

    tl.to('.hero-line', {
        y: 0,
        opacity: 1,
        duration: 1.8,
        stagger: 0.15,
        skewY: 0
    })
        .to('.hero-subtitle', {
            y: 0,
            opacity: 1,
            duration: 1.5,
            filter: 'blur(0px)'
        }, '-=1.2')
        .to('.hero-buttons', {
            y: 0,
            opacity: 1,
            duration: 1.2,
            ease: 'elastic.out(1, 0.5)'
        }, '-=1')
        .to('.hero-scroll', {
            opacity: 1,
            duration: 2
        }, '-=0.5')

    // Logistic Manager Image Sequence
    const frames = gsap.utils.toArray('.logistic-frame')
    if (frames.length > 0) {
        gsap.set(frames, { yPercent: 100 })
        gsap.set(frames[0], { yPercent: 0 })
    }

    const tlLogistic = gsap.timeline({
        scrollTrigger: {
            trigger: '.logistic-section',
            start: 'top top',
            end: '+=400%',
            pin: true,
            scrub: 1
        }
    })

    frames.slice(1).forEach((frame, i) => {
        tlLogistic.to(frame, {
            yPercent: 0,
            duration: 1,
            ease: 'power2.out'
        })
    })

    // Driver Mobile Image Sequence
    const driverFrames = gsap.utils.toArray('.driver-frame')
    if (driverFrames.length > 0) {
        gsap.set(driverFrames, { yPercent: 100 })
        gsap.set(driverFrames[0], { yPercent: 0 })
    }

    const tlDriver = gsap.timeline({
        scrollTrigger: {
            trigger: '.driver-section',
            start: 'top top',
            end: '+=400%',
            pin: true,
            scrub: 1
        }
    })

    driverFrames.slice(1).forEach((frame) => {
        tlDriver.to(frame, {
            yPercent: 0,
            duration: 1,
            ease: 'power2.out'
        })
    })

    // Role Section Animations (Premium Scramble)
    const roleTexts = [
        ["The Architect of Movement...", "The Owner of the System...", "The Strategic Intelligence Layer..."],
        ["Where Inventory Becomes Intelligence...", "Where Orders Take Shape...", "Where Labor Teams Deploy..."],
        ["The Route Optimizer...", "The Crisis Controller...", "The Real-Time Coordinator..."],
        ["24/7 Transparency...", "Instant Answers...", "Autonomous Resolution..."],
        ["The Final Mile Hero...", "Proof. Precision. Performance."],
        ["Request the Move...", "Customize the Service...", "Track Every Detail..."]
    ]

    const sections = gsap.utils.toArray('.role-section')

    sections.forEach((section, index) => {
        const textContainer = section.querySelector('.typing-text')
        const description = section.querySelector('.role-description')
        const texts = roleTexts[index] || ["Loading..."]

        // Initial set for cleaner enter
        gsap.set(description, { y: 20, opacity: 0, filter: 'blur(10px)' })

        ScrollTrigger.create({
            trigger: section,
            start: "top 60%",
            once: true, // Only play once for cleaner feel
            onEnter: () => {
                let mainTl = gsap.timeline()

                // Cycle through texts with Scramble effect if plugin available, else standard
                // Since user didn't request scramble plugin explicitly, we'll simulate a fast "decrypt" effect
                // by just swapping text quickly or using TextPlugin which we have.

                texts.forEach((text, i) => {
                    mainTl.to(textContainer, {
                        text: { value: text, delimiter: "" },
                        duration: 0.8,
                        ease: "none",
                    })
                        .to({}, { duration: 1.5 }) // Longer pause to read

                    if (i < texts.length - 1) {
                        mainTl.to(textContainer, { text: "", duration: 0.3, ease: "power2.in" })
                    }
                })

                // Final State
                mainTl.to(description, {
                    y: 0,
                    opacity: 1,
                    filter: 'blur(0px)',
                    duration: 1.5,
                    ease: "power3.out"
                }, "-=0.5")
            }
        })
    })
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800&display=swap');

.font-display {
    font-family: 'Space Grotesk', sans-serif;
}

.perspective-1000 {
    perspective: 1000px;
}

/* Gradient Animation */
.animate-gradient-x {
    background-size: 200% auto;
    animation: gradient-x 3s linear infinite;
}

@keyframes gradient-x {
    0% {
        background-position: 0% 50%;
    }

    50% {
        background-position: 100% 50%;
    }

    100% {
        background-position: 0% 50%;
    }
}

/* Splash Effect */
.splash-effect {
    position: absolute;
    top: 50%;
    left: 0;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.8) 0%, rgba(34, 211, 238, 0) 70%);
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    pointer-events: none;
    mix-blend-mode: screen;
}
</style>
