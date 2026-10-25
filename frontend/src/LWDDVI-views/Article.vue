<template>
    <div class="article-page">

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
                <router-link to="/article" class="nav-link nav-link--active">Article</router-link>
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
            <p class="hero-tag">Cargo-Core Blog</p>
            <h1 class="hero-title">
                Insights on<br />
                <span class="gradient-text">Logistics & Technology</span>
            </h1>
            <p class="hero-desc">
                Deep-dives into fleet management, last-mile delivery, AI in logistics, and building the
                next generation of freight platforms.
            </p>
        </section>

        <!-- Filter Tags -->
        <section class="section">
            <div class="tag-filter">
                <button
                    v-for="tag in tags" :key="tag"
                    class="tag-btn"
                    :class="{ 'tag-btn--active': activeTag === tag }"
                    @click="activeTag = tag"
                >{{ tag }}</button>
            </div>
        </section>

        <!-- Featured Article -->
        <section class="section">
            <div class="featured-card" @click="openArticle(featured)">
                <div class="featured-badge">Featured</div>
                <div class="featured-body">
                    <div class="article-meta">
                        <span class="meta-tag">{{ featured.tag }}</span>
                        <span class="meta-sep">·</span>
                        <span class="meta-date">{{ featured.date }}</span>
                        <span class="meta-sep">·</span>
                        <span class="meta-read">{{ featured.read }}</span>
                    </div>
                    <h2 class="featured-title">{{ featured.title }}</h2>
                    <p class="featured-excerpt">{{ featured.excerpt }}</p>
                    <button class="read-more-btn">Read Article →</button>
                </div>
                <div class="featured-visual" aria-hidden="true">
                    <div class="visual-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                            <path stroke-linecap="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                        </svg>
                    </div>
                </div>
            </div>
        </section>

        <!-- Article Grid -->
        <section class="section">
            <div class="section-header">
                <h2>Latest Articles</h2>
                <span class="article-count">{{ filteredArticles.length }} articles</span>
            </div>
            <div class="articles-grid">
                <article
                    v-for="article in filteredArticles" :key="article.id"
                    class="article-card"
                    @click="openArticle(article)"
                >
                    <div class="article-card-header">
                        <span class="meta-tag">{{ article.tag }}</span>
                        <span class="meta-date">{{ article.date }}</span>
                    </div>
                    <h3>{{ article.title }}</h3>
                    <p>{{ article.excerpt }}</p>
                    <div class="article-card-footer">
                        <span class="meta-read">{{ article.read }}</span>
                        <span class="arrow-link">→</span>
                    </div>
                </article>
            </div>
        </section>

        <!-- Newsletter CTA -->
        <section class="section newsletter-section">
            <div class="newsletter-card">
                <h3>Stay in the loop</h3>
                <p>Get logistics insights and platform updates delivered to your inbox.</p>
                <form class="newsletter-form" @submit.prevent="subscribe">
                    <input
                        v-model="email"
                        type="email"
                        placeholder="your@email.com"
                        class="newsletter-input"
                        required
                    />
                    <button type="submit" class="newsletter-btn">Subscribe</button>
                </form>
                <p v-if="subscribed" class="subscribed-msg">You're subscribed!</p>
            </div>
        </section>

        <!-- Footer -->
        <footer class="page-footer">
            <p>&copy; 2026 Cargo-Core Technologies Pvt. Ltd. · All rights reserved.</p>
        </footer>

        <!-- ── Article Reader Modal ──────────────── -->
        <Transition name="modal-slide">
            <div v-if="showModal" class="modal-backdrop" @click.self="closeArticle" role="dialog" aria-modal="true">
                <div class="modal-panel">
                    <button class="modal-close" @click="closeArticle" aria-label="Close">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>

                    <div class="modal-scroll">
                        <div class="modal-meta">
                            <span class="meta-tag">{{ selectedArticle.tag }}</span>
                            <span class="meta-sep">·</span>
                            <span class="meta-date">{{ selectedArticle.date }}</span>
                            <span class="meta-sep">·</span>
                            <span class="meta-read">{{ selectedArticle.read }}</span>
                        </div>
                        <h1 class="modal-title">{{ selectedArticle.title }}</h1>
                        <p class="modal-lead">{{ selectedArticle.excerpt }}</p>
                        <div class="modal-divider"></div>
                        <div class="modal-body" v-html="selectedArticle.body"></div>
                    </div>
                </div>
            </div>
        </Transition>

    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

let _prevBg = ''

const tags = ['All', 'AI & ML', 'Fleet Ops', 'Last Mile', 'Platform', 'Industry']
const activeTag = ref('All')
const email = ref('')
const subscribed = ref(false)
const showModal = ref(false)
const selectedArticle = ref(null)

const featured = {
    id: 0,
    tag: 'Platform',
    date: 'Feb 2026',
    read: '8 min read',
    title: 'How Cargo-Core Unifies 6 Roles into One Intelligent Logistics Platform',
    excerpt: 'From drivers on the road to executives in the control tower — every stakeholder is now connected through a single, AI-powered logistics engine. Here\'s how we architected it.',
    body: `
        <p>When we set out to build Cargo-Core, the logistics industry had a fundamental problem: every role operated in its own silo. Drivers used one app, dispatchers used another, warehouse managers had spreadsheets, and executives had no real-time visibility into anything.</p>
        <h2>The 6-Role Architecture</h2>
        <p>Cargo-Core is built around six core roles — Logistics Manager, Dispatcher, Warehouse Manager, Driver, Vendor, and Individual Customer. Each role has its own dashboard, feature set, and permission boundary. But all six share the same underlying data model, event bus, and API layer.</p>
        <p>This means when a driver marks a delivery as completed, the dispatcher's live board updates instantly, the warehouse logs the return, and the customer receives a notification — all from a single database write.</p>
        <h2>AI as the Connective Tissue</h2>
        <p>The AI layer sits above all roles. It watches every event — driver location pings, geofence triggers, delay flags — and surfaces intelligent recommendations to the right person at the right time. A dispatcher gets a route swap suggestion. A logistics manager sees a cost anomaly. A warehouse manager is alerted to a capacity risk.</p>
        <h2>What's Next</h2>
        <p>Phase 2 brings a real-time AI voice assistant for drivers, multi-tenant fleet support, and a public API for vendor integrations. The platform is designed to scale from a 5-truck operation to a 5,000-vehicle enterprise without architectural changes.</p>
    `
}

const articles = [
    {
        id: 1,
        tag: 'AI & ML',
        date: 'Jan 2026',
        read: '6 min read',
        title: 'Predictive Delay Detection: Stopping Problems Before They Happen',
        excerpt: 'Our risk engine analyzes weather, traffic, and driver behavior in real-time to flag delays up to 45 minutes before they occur.',
        body: `
            <p>Delays are the silent killer of logistics margins. A single delayed vehicle cascades into missed SLAs, unhappy customers, and overtime costs. The question was: can we see it coming?</p>
            <h2>The Risk Engine</h2>
            <p>Cargo-Core's risk engine is a scoring model that runs every 60 seconds per active vehicle. It ingests four primary signals: current GPS velocity vs expected velocity, traffic layer data from the routing API, historical delay probability for the current route segment, and driver behavior score (harsh braking, idling, speed variance).</p>
            <p>When the combined score crosses a configurable threshold, a delay alert fires. The dispatcher sees it immediately with an estimated impact time and suggested mitigation — usually a route swap or a customer ETA update.</p>
            <h2>Results in Testing</h2>
            <p>In our internal fleet simulation we achieved a 78% true positive rate on delay prediction with a 45-minute advance warning window. False positives were reduced by incorporating driver experience level as a weighting factor — experienced drivers recover from traffic faster than the model naively predicts.</p>
        `
    },
    {
        id: 2,
        tag: 'Last Mile',
        date: 'Jan 2026',
        read: '5 min read',
        title: 'Geofence Automation in Last-Mile Delivery',
        excerpt: 'How Cargo-Core uses geofencing to auto-trigger arrival events, notify customers, and capture proof of delivery — without any manual input.',
        body: `
            <p>Manual status updates are a last-mile anti-pattern. Drivers forget, customers call in, dispatchers chase. Geofencing eliminates the entire category of problem.</p>
            <h2>How It Works</h2>
            <p>Each delivery stop has a geofence polygon configured at the time of route creation. When the driver's GPS coordinate crosses the boundary, Cargo-Core automatically triggers the arrival flow: the driver's screen switches to the delivery task list, the customer receives a "driver nearby" SMS, and the stop clock starts for SLA tracking.</p>
            <p>On exit from the geofence after a successful delivery, the system auto-captures the departure timestamp and marks the stop complete if proof of delivery (photo + signature) has been uploaded.</p>
            <h2>Edge Cases</h2>
            <p>GPS drift in dense urban areas created false triggers in early testing. We resolved this with a 3-point confirmation — the device must log three consecutive GPS readings inside the polygon before the trigger fires. This added ~4 seconds of latency but eliminated false positives entirely.</p>
        `
    },
    {
        id: 3,
        tag: 'Fleet Ops',
        date: 'Dec 2025',
        read: '7 min read',
        title: 'Real-Time Fleet Monitoring: Building the Live Map View',
        excerpt: 'Behind the scenes of our live map — GPS polling, vehicle clustering, route overlays, and alert propagation across the dashboard.',
        body: `
            <p>The live map view is the most complex component in the Cargo-Core dispatcher dashboard. It must display dozens of moving vehicles, their routes, stops, and real-time status — all updating simultaneously without performance degradation.</p>
            <h2>GPS Polling Architecture</h2>
            <p>Driver devices send GPS pings every 15 seconds via a lightweight WebSocket connection. The backend aggregates these into a Redis-backed position cache, which the map component polls via a Server-Sent Events stream. This avoids the overhead of a full WebSocket on the client side for read-only data.</p>
            <h2>Vehicle Clustering</h2>
            <p>At zoom levels below 12, nearby vehicles are clustered into count badges. We used a custom clustering algorithm tuned for geographic density patterns typical of urban delivery fleets. The cluster boundaries update dynamically as the map is panned.</p>
            <h2>Route Overlays</h2>
            <p>Each vehicle's planned route is rendered as a polyline, color-coded by status: green for on-track, amber for at-risk, red for delayed. Completed segments are dimmed. The overlay updates whenever the route plan changes — which can happen mid-shift when the AI suggests a route swap.</p>
        `
    },
    {
        id: 4,
        tag: 'Platform',
        date: 'Dec 2025',
        read: '4 min read',
        title: 'Offline-First: How We Built PWA Sync for Field Drivers',
        excerpt: 'Drivers in remote areas can\'t always rely on connectivity. Our service worker queues all actions and syncs automatically when back online.',
        body: `
            <p>Cargo-Core's driver app is a Progressive Web App. This means it runs in a mobile browser with full offline support — no app store required, and it works even when the driver has no signal.</p>
            <h2>The Offline Queue</h2>
            <p>Every driver action — delivery status update, photo upload, signature capture, geofence event — is first written to IndexedDB locally. A background service worker monitors connectivity and flushes the queue to the server whenever a connection is available.</p>
            <p>The queue is ordered and deduplicated. If a driver scans the same barcode twice while offline, only one event is queued. If connectivity is restored mid-queue, the flush is atomic — partial syncs are retried automatically.</p>
            <h2>Conflict Resolution</h2>
            <p>When a queued event arrives at the server after a delay, the backend checks for conflicting state. If the stop was already marked complete by a supervisor override, the driver's queued event is logged but not applied. The driver sees a sync notification explaining the discrepancy.</p>
        `
    },
    {
        id: 5,
        tag: 'Industry',
        date: 'Nov 2025',
        read: '9 min read',
        title: 'The Economics of Routing: Why 5% Better Routes = 20% Better Margins',
        excerpt: 'An analysis of how small improvements in route optimization compound into massive financial gains across a mid-size fleet operation.',
        body: `
            <p>Route optimization is one of the highest-leverage activities in logistics. A 5% reduction in total distance driven across a mid-size fleet of 50 vehicles delivers compounding benefits that most operators severely underestimate.</p>
            <h2>The Math</h2>
            <p>Consider a fleet averaging 200km per vehicle per day at a total operating cost of ₹18/km (fuel, driver time, maintenance amortized). 50 vehicles × 200km × ₹18 = ₹180,000/day. A 5% route improvement saves 500km/day = ₹9,000/day = ₹2.7M/year.</p>
            <p>But direct cost is only part of the story. Better routes mean faster deliveries, which means higher stop density per shift, which means more revenue per vehicle per day without adding headcount.</p>
            <h2>Why Most Fleets Don't Capture This</h2>
            <p>Legacy dispatch is manual. Dispatchers optimize by intuition, not algorithm. Our analysis shows manually-dispatched routes average 23% longer than algorithmically-optimized routes for the same stop set. That gap is pure waste.</p>
            <p>Cargo-Core's route optimization engine uses a variant of the Vehicle Routing Problem solver with time-window constraints, load balancing, and driver skill matching. For a typical 15-stop route, it evaluates over 10,000 permutations in under 300ms.</p>
        `
    },
    {
        id: 6,
        tag: 'AI & ML',
        date: 'Nov 2025',
        read: '6 min read',
        title: 'AI Voice Assistant for Drivers: Hands-Free Logistics Commands',
        excerpt: 'We built a voice-driven co-pilot for drivers — capable of updating delivery status, logging issues, and navigating — entirely hands-free.',
        body: `
            <p>Drivers cannot safely interact with a screen while driving. Yet logistics apps demand constant interaction — status updates, issue logging, navigation adjustments. The AI voice assistant was built to eliminate this conflict entirely.</p>
            <h2>What the Assistant Can Do</h2>
            <p>The voice assistant handles four categories of command: navigation ("Take me to the next stop"), status updates ("Mark this delivery as completed"), issue logging ("Log a damaged package at stop 4"), and queries ("How many stops are left today?").</p>
            <p>Commands are processed on-device using a fine-tuned intent classification model, so they work offline. Only complex queries that require server data are routed through the API.</p>
            <h2>Wake Word & Safety</h2>
            <p>The assistant is activated by the wake word "Hey Cargo" and auto-mutes when the vehicle is stationary for more than 30 seconds (assumed to be at a stop, where screen interaction is safe). This prevents accidental voice commands during deliveries while keeping the assistant available during transit.</p>
            <p>In user testing with 12 drivers over a 4-week period, average screen-touch interactions per shift dropped by 67%. Driver satisfaction scores increased significantly, particularly among drivers handling high stop-count urban routes.</p>
        `
    },
]

const filteredArticles = computed(() => {
    if (activeTag.value === 'All') return articles
    return articles.filter(a => a.tag === activeTag.value)
})

const openArticle = (article) => {
    selectedArticle.value = article
    showModal.value = true
    document.body.style.overflow = 'hidden'
}

const closeArticle = () => {
    showModal.value = false
    document.body.style.overflow = ''
}

const onKeyDown = (e) => { if (e.key === 'Escape') closeArticle() }
onMounted(() => {
    _prevBg = document.body.style.backgroundColor
    document.body.style.backgroundColor = '#000'
    window.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
    window.removeEventListener('keydown', onKeyDown)
    document.body.style.backgroundColor = _prevBg
    document.body.style.overflow = ''
})

const subscribe = () => {
    subscribed.value = true
    email.value = ''
    setTimeout(() => { subscribed.value = false }, 4000)
}
</script>

<style scoped src="./styles/Article.page.css"></style>
<style scoped src="./styles/Article.cards.css"></style>
