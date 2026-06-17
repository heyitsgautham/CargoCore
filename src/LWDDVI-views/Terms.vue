<template>
    <div class="legal-page" style="background:#000">

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
            <p class="hero-tag">Legal</p>
            <h1 class="hero-title">Terms of <span class="gradient-text">Service</span></h1>
            <p class="hero-meta">Last updated: <strong>March 3, 2026</strong></p>
        </section>

        <!-- Content -->
        <section class="section">
            <div class="legal-layout">

                <!-- TOC sidebar -->
                <aside class="toc">
                    <p class="toc-heading">On this page</p>
                    <a v-for="s in sections" :key="s.id" :href="`#${s.id}`" class="toc-link">{{ s.title }}</a>
                </aside>

                <!-- Body -->
                <article class="legal-body">
                    <div class="intro-card glass-card">
                        <p>
                            Welcome to Cargo-Core. By accessing or using our platform, you agree to be bound by these Terms
                            of Service. Please read them carefully before using our services. If you do not agree to these
                            terms, do not use Cargo-Core.
                        </p>
                    </div>

                    <div v-for="s in sections" :key="s.id" :id="s.id" class="legal-section">
                        <h2 class="section-heading">
                            <span class="section-num">{{ String(sections.indexOf(s) + 1).padStart(2,'0') }}</span>
                            {{ s.title }}
                        </h2>
                        <div class="section-body" v-for="(para, i) in s.content" :key="i">
                            <p v-if="typeof para === 'string'" v-html="para"></p>
                            <ul v-else-if="para.list" class="legal-list">
                                <li v-for="item in para.items" :key="item">{{ item }}</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Contact block -->
                    <div class="contact-block glass-card">
                        <div class="contact-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path stroke-linecap="round" stroke-linejoin="round"
                                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div>
                            <p class="contact-label">Questions about these Terms?</p>
                            <p class="contact-value">
                                Contact us at <a href="mailto:legal@cargo-core.io" class="legal-link">legal@cargo-core.io</a>
                                or visit our <router-link to="/contact" class="legal-link">Contact page</router-link>.
                            </p>
                        </div>
                    </div>
                </article>
            </div>
        </section>

        <!-- Footer strip -->
        <footer class="footer-strip">
            <p>© {{ new Date().getFullYear() }} Cargo-Core. All rights reserved.</p>
            <div class="footer-links">
                <router-link to="/privacy" class="footer-link">Privacy Policy</router-link>
                <span class="footer-sep">·</span>
                <router-link to="/contact" class="footer-link">Contact</router-link>
            </div>
        </footer>
    </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

onMounted(() => { document.body.style.backgroundColor = '#000' })
onUnmounted(() => { document.body.style.backgroundColor = '' })

const sections = [
    {
        id: 'acceptance',
        title: 'Acceptance of Terms',
        content: [
            'By creating an account or accessing Cargo-Core, you confirm that you are at least 18 years old, have the legal capacity to enter into binding agreements, and agree to these Terms of Service and our Privacy Policy.',
            'If you are using Cargo-Core on behalf of a company or organization, you represent that you have the authority to bind that entity to these terms.'
        ]
    },
    {
        id: 'platform',
        title: 'Use of the Platform',
        content: [
            'Cargo-Core is a logistics intelligence platform that provides tools for logistics managers, warehouse managers, dispatchers, drivers, vendors, and customers. Access to specific features is determined by your assigned role.',
            'You agree to use the platform only for lawful purposes and in accordance with these Terms. You must not use the platform in any way that may cause harm to Cargo-Core, its users, or third parties.'
        ]
    },
    {
        id: 'accounts',
        title: 'User Accounts',
        content: [
            'You are responsible for maintaining the confidentiality of your account credentials. You agree to notify Cargo-Core immediately of any unauthorized use of your account.',
            'Each account is for a single user. You may not share your login credentials with any other person. Cargo-Core reserves the right to terminate accounts that are shared or compromised.',
            { list: true, items: [
                'Provide accurate and complete registration information',
                'Update your information as necessary to keep it current',
                'Accept responsibility for all activity under your account',
                'Not transfer your account to any other person without prior written consent'
            ]}
        ]
    },
    {
        id: 'prohibited',
        title: 'Prohibited Activities',
        content: [
            'You may not engage in any of the following prohibited activities:',
            { list: true, items: [
                'Attempting to hack, disrupt, or gain unauthorized access to any part of the platform',
                'Uploading or transmitting malicious code, viruses, or any software that may damage the platform',
                'Scraping, crawling, or otherwise extracting data from the platform without written permission',
                'Impersonating another user, Cargo-Core employee, or any other person or entity',
                'Using the platform to facilitate any fraudulent, illegal, or harmful activity',
                'Circumventing geofence, role-based access controls, or any security measure',
                'Reverse engineering, decompiling, or disassembling any part of the platform'
            ]}
        ]
    },
    {
        id: 'ip',
        title: 'Intellectual Property',
        content: [
            'All content on the Cargo-Core platform — including but not limited to software, design, logos, trademarks, text, graphics, and data — is owned by or licensed to Cargo-Core and is protected by applicable intellectual property laws.',
            'Subject to these Terms, Cargo-Core grants you a limited, non-exclusive, non-transferable, revocable license to access and use the platform for your intended operational purposes. This license does not grant you the right to reproduce, distribute, or create derivative works from our content.'
        ]
    },
    {
        id: 'data',
        title: 'Data and Privacy',
        content: [
            'Your use of Cargo-Core is also governed by our <router-link to="/privacy" class="legal-link">Privacy Policy</router-link>, which is incorporated into these Terms by reference. By using our platform, you consent to the collection, use, and sharing of data as described in that policy.',
            'You retain ownership of any data you input into the platform. By uploading data, you grant Cargo-Core a license to use, process, and store that data solely for the purpose of providing the service.'
        ]
    },
    {
        id: 'termination',
        title: 'Termination',
        content: [
            'Cargo-Core may suspend or terminate your access to the platform at any time, with or without notice, for any violation of these Terms or for any other reason at our sole discretion.',
            'Upon termination, your right to use the platform immediately ceases. Sections of these Terms that by their nature should survive termination — including intellectual property rights, disclaimers, and limitations of liability — will continue to apply.'
        ]
    },
    {
        id: 'liability',
        title: 'Limitation of Liability',
        content: [
            'To the maximum extent permitted by applicable law, Cargo-Core and its officers, directors, employees, and agents shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of or inability to use the platform.',
            'The platform is provided "as is" and "as available" without any warranties of any kind, either express or implied. Cargo-Core does not warrant that the platform will be uninterrupted, error-free, or free of viruses or other harmful components.'
        ]
    },
    {
        id: 'governing',
        title: 'Governing Law',
        content: [
            'These Terms shall be governed by and construed in accordance with the laws of the Republic of India. Any dispute arising from these Terms shall be subject to the exclusive jurisdiction of the courts located in Mumbai, Maharashtra.',
            'If any provision of these Terms is found to be unenforceable, the remaining provisions will continue in full force and effect.'
        ]
    },
    {
        id: 'changes',
        title: 'Changes to These Terms',
        content: [
            'Cargo-Core reserves the right to modify these Terms at any time. We will provide notice of significant changes by posting a notice on our platform or by sending an email to registered users.',
            'Your continued use of the platform after changes become effective constitutes your acceptance of the revised Terms. If you do not agree with the updated Terms, you must stop using the platform.'
        ]
    }
]
</script>

<style scoped>
.legal-page {
    min-height: 100vh;
    background: #000;
    color: #fff;
    font-family: 'Inter', sans-serif;
    overflow-x: clip;
}

/* ── Navbar ─────────────────────────────────── */
.top-nav {
    position: sticky; top: 1.25rem; z-index: 50;
    width: calc(100% - 3rem); max-width: 1200px; margin: 1.25rem auto 0;
    height: 60px; display: flex; align-items: center; justify-content: space-between;
    padding: 0 1.5rem;
    background: rgba(255,255,255,0.03); backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 999px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
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
.blob { position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.15; }
.blob-1 { width: 700px; height: 700px; background: #6366f1; top: -200px; right: -200px; }
.blob-2 { width: 500px; height: 500px; background: #1CE783; bottom: -100px; left: -100px; }

/* ── Hero ───────────────────────────────────── */
.hero {
    position: relative; z-index: 1; text-align: center;
    padding: 7rem 1.5rem 3.5rem; max-width: 700px; margin: 0 auto;
}
.hero-tag {
    display: inline-block; font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #6366f1; border: 1px solid rgba(99,102,241,0.3); border-radius: 999px;
    padding: 0.25rem 0.9rem; margin-bottom: 1.25rem;
}
.hero-title { font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; margin-bottom: 1rem; }
.gradient-text { background: linear-gradient(135deg, #1CE783 0%, #22d3ee 60%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-meta { font-size: 0.85rem; color: rgba(255,255,255,0.35); }
.hero-meta strong { color: rgba(255,255,255,0.55); }

/* ── Section ────────────────────────────────── */
.section { position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; padding: 1rem 1.5rem 6rem; }

/* ── Legal Layout ────────────────────────────── */
.legal-layout { display: grid; grid-template-columns: 220px 1fr; gap: 3rem; align-items: start; }
@media (max-width: 780px) { .legal-layout { grid-template-columns: 1fr; } .toc { display: none; } }

/* ── TOC ─────────────────────────────────────── */
.toc { position: sticky; top: 90px; align-self: start; display: flex; flex-direction: column; gap: 0.15rem; }
.toc-heading { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #64748b; margin-bottom: 0.5rem; }
.toc-link { font-size: 0.8rem; color: rgba(148,163,184,0.6); text-decoration: none; padding: 0.3rem 0.5rem; border-radius: 0.4rem; transition: all 0.2s; border-left: 2px solid transparent; }
.toc-link:hover { color: #1CE783; background: rgba(28,231,131,0.05); border-left-color: rgba(28,231,131,0.4); }

/* ── Legal Body ─────────────────────────────── */
.legal-body { display: flex; flex-direction: column; gap: 2.5rem; }

.glass-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 1.25rem; backdrop-filter: blur(12px); padding: 1.5rem; }

.intro-card p { font-size: 0.95rem; color: rgba(148,163,184,0.75); line-height: 1.75; }

.legal-section {}
.section-heading { display: flex; align-items: center; gap: 0.75rem; font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 1rem; }
.section-num { font-size: 0.65rem; font-weight: 600; color: #6366f1; background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25); padding: 0.2rem 0.5rem; border-radius: 0.35rem; letter-spacing: 0.05em; flex-shrink: 0; }

.section-body { margin-bottom: 0.75rem; }
.section-body p { font-size: 0.9rem; color: rgba(148,163,184,0.7); line-height: 1.8; }

.legal-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.legal-list li { display: flex; align-items: flex-start; gap: 0.6rem; font-size: 0.875rem; color: rgba(148,163,184,0.7); line-height: 1.65; }
.legal-list li::before { content: '–'; color: #1CE783; flex-shrink: 0; margin-top: 0.05rem; }

.legal-link { color: #1CE783; text-decoration: none; }
.legal-link:hover { text-decoration: underline; }

.contact-block { display: flex; align-items: flex-start; gap: 1rem; }
.contact-icon { width: 44px; height: 44px; flex-shrink: 0; border-radius: 0.75rem; background: rgba(28,231,131,0.1); border: 1px solid rgba(28,231,131,0.25); display: flex; align-items: center; justify-content: center; color: #1CE783; }
.contact-icon svg { width: 20px; height: 20px; }
.contact-label { font-size: 0.8rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.3rem; }
.contact-value { font-size: 0.85rem; color: rgba(148,163,184,0.7); line-height: 1.6; }

/* ── Footer strip ───────────────────────────── */
.footer-strip { position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: center; max-width: 1100px; margin: 0 auto; padding: 1.5rem 1.5rem 3rem; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.8rem; color: rgba(255,255,255,0.3); }
.footer-links { display: flex; align-items: center; gap: 0.5rem; }
.footer-link { color: rgba(255,255,255,0.35); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: #1CE783; }
.footer-sep { color: rgba(255,255,255,0.15); }
</style>
