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
            <h1 class="hero-title">Privacy <span class="gradient-text">Policy</span></h1>
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
                            Cargo-Core is committed to protecting your privacy. This Privacy Policy explains how we collect,
                            use, disclose, and safeguard your information when you use our logistics platform. By using
                            Cargo-Core, you agree to the practices described in this policy.
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
                                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        </div>
                        <div>
                            <p class="contact-label">Privacy questions or data requests?</p>
                            <p class="contact-value">
                                Email our Data Protection Officer at
                                <a href="mailto:privacy@cargo-core.io" class="legal-link">privacy@cargo-core.io</a>
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
                <router-link to="/terms" class="footer-link">Terms of Service</router-link>
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
        id: 'collect',
        title: 'Information We Collect',
        content: [
            'We collect several types of information in connection with your use of Cargo-Core:',
            { list: true, items: [
                'Account information: name, email address, phone number, and password hash',
                'Role-specific profile data: company name, GST/Tax ID, business address (for vendors)',
                'Location data: GPS coordinates during active deliveries (drivers only, with your consent)',
                'Usage data: pages visited, features used, session duration, and device information',
                'Transaction data: shipment records, payment references, and delivery confirmations',
                'Communications: messages you send through our support or contact channels'
            ]}
        ]
    },
    {
        id: 'use',
        title: 'How We Use Your Information',
        content: [
            'Cargo-Core uses the information we collect for the following purposes:',
            { list: true, items: [
                'Providing, maintaining, and improving the platform and its features',
                'Processing shipments, tracking deliveries, and coordinating logistics operations',
                'Authenticating your identity and enforcing role-based access controls',
                'Sending operational notifications, alerts, and OTP codes',
                'Generating analytics and performance reports for authorized users',
                'Detecting, investigating, and preventing fraud, abuse, or security incidents',
                'Complying with applicable legal obligations and regulatory requirements'
            ]}
        ]
    },
    {
        id: 'sharing',
        title: 'Sharing of Information',
        content: [
            'We do not sell your personal information. We may share your information in the following limited circumstances:',
            { list: true, items: [
                'With other users on your platform account who need it to perform their role (e.g., dispatcher sees driver location)',
                'With trusted third-party service providers who assist in operating our platform (cloud hosting, SMS providers)',
                'With law enforcement or government authorities when required by law or to protect rights and safety',
                'During a merger, acquisition, or sale of assets — you will be notified before any transfer occurs',
                'With your explicit consent for any other purpose not described here'
            ]}
        ]
    },
    {
        id: 'cookies',
        title: 'Cookies and Tracking',
        content: [
            'Cargo-Core uses cookies and similar technologies to maintain your session, remember preferences, and analyze platform usage. We use the following types:',
            { list: true, items: [
                'Essential cookies: required for authentication, session management, and basic functionality',
                'Analytics cookies: aggregate usage data to help us improve the platform (anonymized)',
                'Preference cookies: store your settings such as language and display preferences'
            ]},
            'You can control cookie settings through your browser. Note that disabling essential cookies may affect platform functionality.'
        ]
    },
    {
        id: 'security',
        title: 'Data Security',
        content: [
            'We implement industry-standard security measures to protect your information, including:',
            { list: true, items: [
                'AES-256 encryption for data at rest and TLS 1.3 for data in transit',
                'Hashed and salted password storage — we never store plain-text passwords',
                'Role-based access controls (RBAC) limiting data access to authorized users',
                'Regular security audits, penetration testing, and vulnerability scanning',
                'Two-factor authentication (2FA) available for all accounts'
            ]},
            'Despite our safeguards, no system is completely secure. In the event of a data breach, we will notify affected users within 72 hours as required by applicable law.'
        ]
    },
    {
        id: 'rights',
        title: 'Your Rights',
        content: [
            'Depending on your jurisdiction, you may have the following rights regarding your personal data:',
            { list: true, items: [
                'Access: request a copy of the personal data we hold about you',
                'Correction: request correction of inaccurate or incomplete data',
                'Deletion: request deletion of your personal data ("right to be forgotten")',
                'Portability: receive your data in a structured, machine-readable format',
                'Objection: object to certain types of processing, including direct marketing',
                'Restriction: request that we limit how we use your data in certain circumstances'
            ]},
            'To exercise any of these rights, contact our Data Protection Officer at <a href="mailto:privacy@cargo-core.io" class="legal-link">privacy@cargo-core.io</a>. We will respond within 30 days.'
        ]
    },
    {
        id: 'retention',
        title: 'Data Retention',
        content: [
            'We retain your personal data for as long as your account is active or as needed to provide services. Specific retention periods:',
            { list: true, items: [
                'Account data: retained for the duration of account activity plus 90 days after deletion',
                'Transaction and shipment records: retained for 7 years for financial and compliance purposes',
                'GPS location logs: retained for 30 days after delivery completion',
                'Support communications: retained for 2 years from last interaction',
                'Security logs: retained for 12 months'
            ]},
            'After the retention period expires, data is securely deleted or anonymized.'
        ]
    },
    {
        id: 'third-party',
        title: 'Third-Party Services',
        content: [
            'Cargo-Core integrates with certain third-party services to provide its functionality. These services have their own privacy policies:',
            { list: true, items: [
                'Google Maps API — for route planning and mapping',
                'Firebase / Cloud Messaging — for push notifications',
                'Razorpay / Payment Gateway — for payment processing (we do not store card data)',
                'AWS S3 — for file storage (damage photos, delivery proofs)',
                'Spline — for 3D interactive visualizations on public pages'
            ]},
            'We encourage you to review the privacy policies of these third parties. Cargo-Core is not responsible for their practices.'
        ]
    },
    {
        id: 'children',
        title: 'Children\'s Privacy',
        content: [
            'Cargo-Core is not intended for children under 18 years of age. We do not knowingly collect personal information from children. If we become aware that a child has provided us with personal information, we will delete it immediately.',
            'If you believe a child has submitted information to us, please contact us at <a href="mailto:privacy@cargo-core.io" class="legal-link">privacy@cargo-core.io</a>.'
        ]
    },
    {
        id: 'changes',
        title: 'Changes to This Policy',
        content: [
            'We may update this Privacy Policy from time to time to reflect changes in our practices or applicable laws. We will notify you of material changes by posting the new policy with an updated date and, where appropriate, sending an email notification.',
            'Your continued use of Cargo-Core after changes are posted constitutes acceptance of the updated policy.'
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
.blob-1 { width: 700px; height: 700px; background: #22d3ee; top: -200px; left: -200px; }
.blob-2 { width: 500px; height: 500px; background: #6366f1; bottom: -100px; right: -100px; }

/* ── Hero ───────────────────────────────────── */
.hero {
    position: relative; z-index: 1; text-align: center;
    padding: 7rem 1.5rem 3.5rem; max-width: 700px; margin: 0 auto;
}
.hero-tag {
    display: inline-block; font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #22d3ee; border: 1px solid rgba(34,211,238,0.3); border-radius: 999px;
    padding: 0.25rem 0.9rem; margin-bottom: 1.25rem;
}
.hero-title { font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; margin-bottom: 1rem; }
.gradient-text { background: linear-gradient(135deg, #22d3ee 0%, #1CE783 60%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
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
.toc-link:hover { color: #22d3ee; background: rgba(34,211,238,0.05); border-left-color: rgba(34,211,238,0.4); }

/* ── Legal Body ─────────────────────────────── */
.legal-body { display: flex; flex-direction: column; gap: 2.5rem; }
.glass-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 1.25rem; backdrop-filter: blur(12px); padding: 1.5rem; }
.intro-card p { font-size: 0.95rem; color: rgba(148,163,184,0.75); line-height: 1.75; }
.legal-section {}
.section-heading { display: flex; align-items: center; gap: 0.75rem; font-size: 1.1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 1rem; }
.section-num { font-size: 0.65rem; font-weight: 600; color: #22d3ee; background: rgba(34,211,238,0.1); border: 1px solid rgba(34,211,238,0.25); padding: 0.2rem 0.5rem; border-radius: 0.35rem; letter-spacing: 0.05em; flex-shrink: 0; }
.section-body { margin-bottom: 0.75rem; }
.section-body p { font-size: 0.9rem; color: rgba(148,163,184,0.7); line-height: 1.8; }
.legal-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
.legal-list li { display: flex; align-items: flex-start; gap: 0.6rem; font-size: 0.875rem; color: rgba(148,163,184,0.7); line-height: 1.65; }
.legal-list li::before { content: '–'; color: #22d3ee; flex-shrink: 0; margin-top: 0.05rem; }
.legal-link { color: #1CE783; text-decoration: none; }
.legal-link:hover { text-decoration: underline; }
.contact-block { display: flex; align-items: flex-start; gap: 1rem; }
.contact-icon { width: 44px; height: 44px; flex-shrink: 0; border-radius: 0.75rem; background: rgba(34,211,238,0.1); border: 1px solid rgba(34,211,238,0.25); display: flex; align-items: center; justify-content: center; color: #22d3ee; }
.contact-icon svg { width: 20px; height: 20px; }
.contact-label { font-size: 0.8rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.3rem; }
.contact-value { font-size: 0.85rem; color: rgba(148,163,184,0.7); line-height: 1.6; }

/* ── Footer strip ───────────────────────────── */
.footer-strip { position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: center; max-width: 1100px; margin: 0 auto; padding: 1.5rem 1.5rem 3rem; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.8rem; color: rgba(255,255,255,0.3); }
.footer-links { display: flex; align-items: center; gap: 0.5rem; }
.footer-link { color: rgba(255,255,255,0.35); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: #22d3ee; }
.footer-sep { color: rgba(255,255,255,0.15); }
</style>
