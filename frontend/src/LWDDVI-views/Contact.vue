<template>
    <div class="contact-page" style="background:#000">

        <!-- Navbar -->
        <header class="top-nav">
            <div class="nav-brand">
                <img src="@/assets/cargo-core-logo.png" alt="Cargo-Core" class="brand-logo" />
                <div>
                    <span class="brand-name">Cargo-Core</span>
                    <span class="brand-tagline">Moving What Matters</span>
                </div>
            </div>
            <nav class="nav-links">
                <router-link to="/" class="nav-link">Home</router-link>
                <router-link to="/about" class="nav-link">About</router-link>
                <router-link to="/article" class="nav-link">Article</router-link>
                <router-link to="/login" class="nav-link nav-link--cta">Login</router-link>
            </nav>
        </header>

        <!-- Blobs -->
        <div class="blobs" aria-hidden="true">
            <div class="blob blob-1"></div>
            <div class="blob blob-2"></div>
        </div>

        <!-- Hero -->
        <section class="hero">
            <p class="hero-tag">Get in touch</p>
            <h1 class="hero-title">
                We'd love to<br />
                <span class="gradient-text">hear from you</span>
            </h1>
            <p class="hero-desc">
                Have a question, a partnership inquiry, or just want to learn more about Cargo-Core?
                Our team is ready to help — usually within one business day.
            </p>
        </section>

        <!-- Contact Content -->
        <section class="section">
            <div class="contact-grid">

                <!-- Form -->
                <div class="glass-card form-card">
                    <h2 class="form-title">Send us a message</h2>
                    <p class="form-sub">Fill out the form and we'll get back to you as soon as possible.</p>

                    <form class="contact-form" @submit.prevent="sendMessage">
                        <div class="field-row">
                            <div class="field-group">
                                <label class="field-label">Full Name</label>
                                <input v-model="form.name" class="field-input" type="text"
                                    placeholder="John Doe" required />
                            </div>
                            <div class="field-group">
                                <label class="field-label">Email Address</label>
                                <input v-model="form.email" class="field-input" type="email"
                                    placeholder="john@company.com" required />
                            </div>
                        </div>
                        <div class="field-group">
                            <label class="field-label">Subject</label>
                            <select v-model="form.subject" class="field-input field-select">
                                <option value="">Select a subject</option>
                                <option value="general">General Inquiry</option>
                                <option value="sales">Sales &amp; Pricing</option>
                                <option value="support">Technical Support</option>
                                <option value="partnership">Partnership</option>
                                <option value="press">Press / Media</option>
                            </select>
                        </div>
                        <div class="field-group">
                            <label class="field-label">Message</label>
                            <textarea v-model="form.message" class="field-input field-textarea"
                                placeholder="Tell us how we can help..." rows="5" required></textarea>
                        </div>

                        <button type="submit" class="btn-send" :disabled="sending">
                            <span v-if="!sending">Send Message</span>
                            <span v-else class="btn-sending">
                                <svg class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" d="M12 3a9 9 0 100 18A9 9 0 0012 3z" />
                                </svg>
                                Sending…
                            </span>
                        </button>

                        <div v-if="sent" class="success-msg">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Message sent! Your ticket is <strong>{{ submittedId }}</strong>. We'll be in touch soon.
                        </div>

                        <div v-if="submitError" class="error-msg">
                            {{ submitError }}
                        </div>
                    </form>
                </div>

                <!-- Info -->
                <div class="info-column">
                    <div class="info-card" v-for="item in contactInfo" :key="item.label">
                        <div class="info-icon" :style="{ '--c': item.color }">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                                v-html="item.icon"></svg>
                        </div>
                        <div>
                            <p class="info-label">{{ item.label }}</p>
                            <p class="info-value">{{ item.value }}</p>
                        </div>
                    </div>

                    <div class="hours-card glass-card">
                        <h3 class="hours-title">Business Hours</h3>
                        <div class="hours-row" v-for="h in hours" :key="h.day">
                            <span class="hours-day">{{ h.day }}</span>
                            <span class="hours-time">{{ h.time }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer strip -->
        <footer class="footer-strip">
            <p>© {{ new Date().getFullYear() }} Cargo-Core. All rights reserved.</p>
            <div class="footer-links">
                <router-link to="/terms" class="footer-link">Terms</router-link>
                <span class="footer-sep">·</span>
                <router-link to="/privacy" class="footer-link">Privacy</router-link>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useContactStore } from '@/stores/contactStore'

onMounted(() => { document.body.style.backgroundColor = '#000' })
onUnmounted(() => { document.body.style.backgroundColor = '' })

const contactStore = useContactStore()
const sending = ref(false)
const sent = ref(false)
const submittedId = ref('')
const submitError = ref('')
const form = reactive({ name: '', email: '', subject: '', message: '' })

// Map Contact.vue subject values → store categories
const categoryMap = {
    general: 'general',
    sales: 'billing',
    support: 'technical',
    partnership: 'general',
    press: 'general',
}

async function sendMessage() {
    sending.value = true
    submitError.value = ''
    try {
        const id = await contactStore.submit({
            name: form.name,
            email: form.email,
            phone: '',
            category: categoryMap[form.subject] || 'general',
            subject: form.subject
                ? form.subject.charAt(0).toUpperCase() + form.subject.slice(1)
                : 'General Inquiry',
            priority: 'medium',
            message: form.message,
        })
        submittedId.value = id
        sent.value = true
        Object.assign(form, { name: '', email: '', subject: '', message: '' })
        setTimeout(() => sent.value = false, 5000)
    } catch (error) {
        submitError.value = error.message || 'Unable to send message right now.'
    } finally {
        sending.value = false
    }
}

const contactInfo = [
    {
        label: 'Email',
        value: 'hello@cargo-core.io',
        color: '#6366f1',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>'
    },
    {
        label: 'Phone',
        value: '+91 98765 43210',
        color: '#22d3ee',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>'
    },
    {
        label: 'Headquarters',
        value: 'Mumbai, Maharashtra — India',
        color: '#1CE783',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>'
    }
]

const hours = [
    { day: 'Monday – Friday', time: '9:00 AM – 6:00 PM IST' },
    { day: 'Saturday', time: '10:00 AM – 2:00 PM IST' },
    { day: 'Sunday', time: 'Closed' }
]
</script>

<style scoped src="./styles/Contact.css"></style>
