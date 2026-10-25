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

<style scoped src="./styles/About.css"></style>
