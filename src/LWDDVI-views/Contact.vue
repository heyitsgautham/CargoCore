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

<style scoped>
.contact-page {
    min-height: 100vh;
    background: #000;
    color: #fff;
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
}

/* ── Navbar ─────────────────────────────────── */
.top-nav {
    position: sticky;
    top: 1.25rem;
    z-index: 50;
    width: calc(100% - 3rem);
    max-width: 1200px;
    margin: 1.25rem auto 0;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.nav-brand { display: flex; align-items: center; gap: 0.6rem; }
.brand-logo { height: 28px; width: auto; }
.brand-name { display: block; font-size: 1rem; font-weight: 700; color: #fff; line-height: 1.2; }
.brand-tagline { display: block; font-size: 0.5rem; color: rgba(255,255,255,0.5); letter-spacing: 0.1em; text-transform: uppercase; }
.nav-links { display: flex; align-items: center; gap: 0.25rem; }
.nav-link { padding: 0.35rem 0.85rem; font-size: 0.8rem; font-weight: 500; color: rgba(255,255,255,0.65); text-decoration: none; border-radius: 999px; border: 1px solid transparent; transition: all 0.2s; }
.nav-link:hover { color: #fff; border-color: rgba(255,255,255,0.18); background: rgba(255,255,255,0.06); }
.nav-link--cta { color: #fff; border-color: rgba(255,255,255,0.25); background: rgba(255,255,255,0.08); }
.nav-link--cta:hover { background: rgba(255,255,255,0.15); }

/* ── Blobs ───────────────────────────────────── */
.blobs { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.blob { position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.18; }
.blob-1 { width: 700px; height: 700px; background: #6366f1; top: -200px; left: -200px; }
.blob-2 { width: 600px; height: 600px; background: #1CE783; bottom: -150px; right: -150px; }

/* ── Hero ───────────────────────────────────── */
.hero {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 7rem 1.5rem 4rem;
    max-width: 700px;
    margin: 0 auto;
}

.hero-tag {
    display: inline-block;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #6366f1;
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 999px;
    padding: 0.25rem 0.9rem;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 1.25rem;
}

.gradient-text {
    background: linear-gradient(135deg, #1CE783 0%, #22d3ee 60%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-desc {
    font-size: 1rem;
    color: rgba(255,255,255,0.55);
    line-height: 1.75;
}

/* ── Section ────────────────────────────────── */
.section {
    position: relative;
    z-index: 1;
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem 6rem;
}

/* ── Contact Grid ────────────────────────────── */
.contact-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 2rem;
    align-items: start;
}

@media (max-width: 860px) {
    .contact-grid { grid-template-columns: 1fr; }
}

/* ── Glass Card ─────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 1.25rem;
    backdrop-filter: blur(12px);
    padding: 2rem;
}

/* ── Form ───────────────────────────────────── */
.form-title {
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
    color: #e2e8f0;
}

.form-sub {
    font-size: 0.85rem;
    color: rgba(148,163,184,0.7);
    margin-bottom: 1.75rem;
}

.contact-form { display: flex; flex-direction: column; gap: 1rem; }

.field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

@media (max-width: 540px) { .field-row { grid-template-columns: 1fr; } }

.field-group { display: flex; flex-direction: column; gap: 0.35rem; }

.field-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #94a3b8;
}

.field-input {
    background: rgba(15,23,42,0.55);
    border: 1px solid rgba(99,102,241,0.22);
    border-radius: 0.65rem;
    padding: 0.65rem 0.9rem;
    color: #e2e8f0;
    font-size: 0.875rem;
    font-family: inherit;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    width: 100%;
    box-sizing: border-box;
}

.field-input::placeholder { color: rgba(100,116,139,0.5); }

.field-input:focus {
    border-color: rgba(28,231,131,0.5);
    box-shadow: 0 0 0 3px rgba(28,231,131,0.08);
}

.field-select { cursor: pointer; appearance: none; }
.field-select option { background: #0f172a; }

.field-textarea { resize: vertical; min-height: 120px; line-height: 1.6; }

.btn-send {
    width: 100%;
    padding: 0.85rem;
    background: linear-gradient(135deg, #1CE783, #15b86a);
    color: #0a0e11;
    font-weight: 700;
    font-size: 0.9rem;
    border: none;
    border-radius: 0.75rem;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.25s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
}

.btn-send:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(28,231,131,0.25);
}

.btn-send:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-sending { display: flex; align-items: center; gap: 0.45rem; }

.spin-icon {
    width: 16px;
    height: 16px;
    animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.success-msg {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(28,231,131,0.08);
    border: 1px solid rgba(28,231,131,0.25);
    border-radius: 0.65rem;
    color: #1CE783;
    font-size: 0.85rem;
    font-weight: 500;
}

.success-msg svg { width: 18px; height: 18px; flex-shrink: 0; }

.error-msg {
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 0.65rem;
    color: #fca5a5;
    font-size: 0.85rem;
    font-weight: 500;
}

/* ── Info Column ────────────────────────────── */
.info-column { display: flex; flex-direction: column; gap: 1rem; }

.info-card {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1.25rem;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 1rem;
    backdrop-filter: blur(12px);
}

.info-icon {
    width: 44px;
    height: 44px;
    flex-shrink: 0;
    border-radius: 0.75rem;
    background: color-mix(in srgb, var(--c) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 30%, transparent);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--c);
}

.info-icon svg { width: 20px; height: 20px; }

.info-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.2rem; }
.info-value { font-size: 0.9rem; color: #e2e8f0; font-weight: 500; }

.hours-card { padding: 1.5rem; }

.hours-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 1rem;
}

.hours-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.8rem;
}

.hours-row:last-child { border-bottom: none; }
.hours-day { color: rgba(148,163,184,0.75); }
.hours-time { color: #e2e8f0; font-weight: 500; }

/* ── Footer strip ───────────────────────────── */
.footer-strip {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem 1.5rem 3rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-size: 0.8rem;
    color: rgba(255,255,255,0.3);
}

.footer-links { display: flex; align-items: center; gap: 0.5rem; }
.footer-link { color: rgba(255,255,255,0.35); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: #1CE783; }
.footer-sep { color: rgba(255,255,255,0.15); }
</style>
