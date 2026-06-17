<template>
    <div class="about-page">

        <!-- Navbar (same as AuthLayout) -->
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
                <router-link to="/about" class="nav-link nav-link--active">About</router-link>
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
            <p class="hero-tag">About us</p>
            <h1 class="hero-title">
                Built for the<br />
                <span class="gradient-text">Future of Freight</span>
            </h1>
            <p class="hero-desc">
                Cargo-Core is an intelligent logistics platform engineered to connect drivers, dispatchers, warehouse teams,
                vendors, and customers — in one unified system.
            </p>
        </section>

        <!-- Mission / Vision / Values -->
        <section class="section">
            <div class="cards-grid">
                <div class="glass-card">
                    <div class="card-icon" style="--c: #6366f1;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                        </svg>
                    </div>
                    <h3>Our Mission</h3>
                    <p>To eliminate inefficiency in last-mile and mid-mile logistics by giving every stakeholder real-time
                        intelligence, automation, and complete visibility.</p>
                </div>
                <div class="glass-card">
                    <div class="card-icon" style="--c: #22d3ee;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10" />
                            <path stroke-linecap="round" d="M12 8v4l3 3" />
                        </svg>
                    </div>
                    <h3>Our Vision</h3>
                    <p>A world where every shipment is predictable, every delay is anticipated, and every route is optimal —
                        powered by AI and data.</p>
                </div>
                <div class="glass-card">
                    <div class="card-icon" style="--c: #1CE783;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round"
                                d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                    </div>
                    <h3>Our Values</h3>
                    <p>Transparency, reliability, and continuous improvement. We build for the people on the ground — drivers,
                        warehouse staff, and operations teams.</p>
                </div>
            </div>
        </section>

        <!-- Stats -->
        <section class="section stats-section">
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-num gradient-text">6</span>
                    <span class="stat-label">Role-based dashboards</span>
                </div>
                <div class="stat-item">
                    <span class="stat-num gradient-text">100+</span>
                    <span class="stat-label">Features built</span>
                </div>
                <div class="stat-item">
                    <span class="stat-num gradient-text">AI</span>
                    <span class="stat-label">Powered intelligence</span>
                </div>
                <div class="stat-item">
                    <span class="stat-num gradient-text">PWA</span>
                    <span class="stat-label">Offline-ready mobile</span>
                </div>
            </div>
        </section>

        <!-- Team / Tech Stack -->
        <section class="section">
            <div class="section-header">
                <h2>Tech Stack</h2>
                <p>Built with modern, battle-tested technologies.</p>
            </div>
            <div class="tech-grid">
                <div class="tech-pill" v-for="tech in techStack" :key="tech">{{ tech }}</div>
            </div>
        </section>

        <!-- CTA -->
        <section class="section cta-section">
            <h2>Ready to move what matters?</h2>
            <p>Join Cargo-Core and bring intelligence to your logistics operations.</p>
            <div class="cta-btns">
                <router-link to="/register" class="btn-primary">Get Started</router-link>
                <router-link to="/login" class="btn-secondary">Sign In</router-link>
            </div>
        </section>

        <!-- Footer -->
        <footer class="page-footer">
            <p>&copy; 2026 Cargo-Core Technologies Pvt. Ltd. · All rights reserved.</p>
        </footer>

    </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
let _prevBg = ''
onMounted(() => { _prevBg = document.body.style.backgroundColor; document.body.style.backgroundColor = '#000' })
onUnmounted(() => { document.body.style.backgroundColor = _prevBg })
const techStack = [
    'Vue 3', 'Vite', 'Tailwind CSS', 'Pinia', 'Vue Router',
    'FastAPI', 'PostgreSQL', 'SQLAlchemy', 'Alembic',
    'Docker', 'JWT Auth', 'PWA / Service Worker', 'Chart.js', 'Spline 3D'
]
</script>

<style scoped>
.about-page {
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

.nav-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.brand-logo {
    height: 28px;
    width: auto;
}

.brand-name {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
}

.brand-tagline {
    display: block;
    font-size: 0.5rem;
    color: rgba(255, 255, 255, 0.5);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.nav-link {
    padding: 0.35rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.65);
    text-decoration: none;
    border-radius: 999px;
    border: 1px solid transparent;
    transition: all 0.2s;
}

.nav-link:hover,
.nav-link--active {
    color: #fff;
    border-color: rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.06);
}

.nav-link--cta {
    color: #fff;
    border-color: rgba(255, 255, 255, 0.25);
    background: rgba(255, 255, 255, 0.08);
}

.nav-link--cta:hover {
    background: rgba(255, 255, 255, 0.15);
}

/* ── Blobs ──────────────────────────────────── */
.blobs {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}

.blob {
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.18;
}

.blob-1 {
    width: 700px;
    height: 700px;
    background: #6366f1;
    top: -200px;
    left: -200px;
}

.blob-2 {
    width: 500px;
    height: 500px;
    background: #22d3ee;
    bottom: -150px;
    right: -150px;
}

/* ── Hero ───────────────────────────────────── */
.hero {
    position: relative;
    z-index: 1;
    max-width: 860px;
    margin: 6rem auto 4rem;
    padding: 0 2rem;
    text-align: center;
}

.hero-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 0.35rem 1rem;
    border-radius: 999px;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 1.25rem;
}

.hero-desc {
    font-size: 1.05rem;
    color: rgba(255, 255, 255, 0.55);
    line-height: 1.7;
    max-width: 600px;
    margin: 0 auto;
}

.gradient-text {
    background: linear-gradient(90deg, #6366f1, #22d3ee, #1CE783);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Sections ───────────────────────────────── */
.section {
    position: relative;
    z-index: 1;
    max-width: 1100px;
    margin: 0 auto 5rem;
    padding: 0 2rem;
}

.section-header {
    text-align: center;
    margin-bottom: 2.5rem;
}

.section-header h2 {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}

.section-header p {
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.95rem;
}

/* ── Cards ──────────────────────────────────── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
}

.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 1.25rem;
    padding: 2rem;
    transition: border-color 0.25s, background 0.25s;
}

.glass-card:hover {
    background: rgba(255, 255, 255, 0.055);
    border-color: rgba(255, 255, 255, 0.15);
}

.card-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--c) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 25%, transparent);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.25rem;
}

.card-icon svg {
    width: 22px;
    height: 22px;
    color: var(--c);
}

.glass-card h3 {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}

.glass-card p {
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.5);
    line-height: 1.7;
}

/* ── Stats ──────────────────────────────────── */
.stats-section {
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 3rem 2rem;
    margin-bottom: 5rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 2rem;
    text-align: center;
}

.stat-num {
    display: block;
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.stat-label {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Tech Stack ─────────────────────────────── */
.tech-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
}

.tech-pill {
    padding: 0.4rem 1rem;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    color: rgba(255, 255, 255, 0.65);
    background: rgba(255, 255, 255, 0.03);
    transition: all 0.2s;
}

.tech-pill:hover {
    border-color: rgba(255, 255, 255, 0.25);
    color: #fff;
    background: rgba(255, 255, 255, 0.07);
}

/* ── CTA ────────────────────────────────────── */
.cta-section {
    text-align: center;
}

.cta-section h2 {
    font-size: 2.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.75rem;
}

.cta-section p {
    color: rgba(255, 255, 255, 0.45);
    font-size: 1rem;
    margin-bottom: 2rem;
}

.cta-btns {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

.btn-primary {
    padding: 0.75rem 2rem;
    border-radius: 999px;
    background: #fff;
    color: #000;
    font-weight: 700;
    font-size: 0.9rem;
    text-decoration: none;
    transition: all 0.2s;
}

.btn-primary:hover {
    background: #e5e7eb;
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
}

.btn-secondary {
    padding: 0.75rem 2rem;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
    font-weight: 600;
    font-size: 0.9rem;
    text-decoration: none;
    transition: all 0.2s;
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.4);
}

/* ── Footer ─────────────────────────────────── */
.page-footer {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.25);
}

@media (max-width: 640px) {
    .brand-tagline,
    .nav-link:not(.nav-link--cta):not(.nav-link--active) { display: none; }
    .hero { margin-top: 4rem; }
}
</style>
