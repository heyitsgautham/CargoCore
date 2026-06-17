<template>
    <div class="min-h-screen bg-white dark:bg-background-dark p-6 md:p-10 lg:p-16 space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white">API Documentation</h2>
                <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">Integrate QuadCore shipment services directly with your ERP or platform.</p>
            </div>
            <router-link to="/vendor/bulk-upload" class="px-4 py-2 bg-gray-100 dark:bg-white/5 rounded-lg text-sm font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px]">arrow_back</span> Back to Bulk Upload
            </router-link>
        </div>

        <!-- Quick Start Banner -->
        <div class="glass-panel rounded-xl p-6 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
            <div class="flex items-start gap-4">
                <div class="p-3 bg-blue-500/20 rounded-xl text-blue-500 shrink-0">
                    <span class="material-symbols-outlined text-3xl">rocket_launch</span>
                </div>
                <div class="flex-1">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1">Quick Start</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">Base URL: <code class="px-2 py-0.5 bg-black/10 dark:bg-white/10 rounded text-blue-500 font-mono text-xs">https://api.quadcore.logistics/v2</code></p>
                    <div class="flex flex-wrap gap-2">
                        <span class="px-2.5 py-1 bg-green-500/20 text-green-600 dark:text-green-400 rounded text-[10px] font-bold uppercase">REST API</span>
                        <span class="px-2.5 py-1 bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded text-[10px] font-bold uppercase">JSON</span>
                        <span class="px-2.5 py-1 bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded text-[10px] font-bold uppercase">OAuth 2.0</span>
                        <span class="px-2.5 py-1 bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 rounded text-[10px] font-bold uppercase">Webhooks</span>
                    </div>
                </div>
                <div class="shrink-0 flex flex-col gap-2">
                    <button @click="copyApiKey" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">key</span> Copy API Key
                    </button>
                    <button @click="downloadSDK" class="px-4 py-2 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 text-gray-700 dark:text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5">
                        <span class="material-symbols-outlined text-[14px]">download</span> Download SDK
                    </button>
                </div>
            </div>
        </div>

        <!-- Sidebar + Content Layout -->
        <div class="flex flex-col md:flex-row gap-6">
            <!-- Navigation Sidebar -->
            <div class="w-full md:w-56 shrink-0 space-y-1">
                <button v-for="section in sections" :key="section.id"
                    @click="activeSection = section.id"
                    class="w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    :class="activeSection === section.id ? 'bg-blue-500/10 text-blue-500 font-bold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'">
                    <span class="material-symbols-outlined text-[16px]">{{ section.icon }}</span>
                    {{ section.label }}
                </button>
            </div>

            <!-- Content Area -->
            <div class="flex-1 min-w-0">

                <!-- Authentication Section -->
                <div v-if="activeSection === 'auth'" class="space-y-6">
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-500">lock</span> Authentication
                        </h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">All API requests require a Bearer token in the <code class="px-1.5 py-0.5 bg-gray-100 dark:bg-white/10 rounded font-mono text-xs">Authorization</code> header. Obtain your token from the Settings page or use the button above.</p>

                        <div class="bg-gray-900 dark:bg-black/40 rounded-lg p-4 mb-4 overflow-x-auto">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-[10px] text-gray-400 font-bold uppercase">Request Header</span>
                                <button @click="copySnippet('auth')" class="text-[10px] text-blue-400 hover:text-blue-300 font-bold">Copy</button>
                            </div>
                            <pre class="text-green-400 text-xs font-mono leading-relaxed"><span class="text-gray-500">GET</span> /v2/shipments
<span class="text-purple-400">Authorization:</span> Bearer YOUR_API_KEY
<span class="text-purple-400">Content-Type:</span> application/json
<span class="text-purple-400">X-Vendor-ID:</span> VND-XXXX-XXXX</pre>
                        </div>

                        <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 flex items-start gap-2">
                            <span class="material-symbols-outlined text-yellow-500 text-[16px] mt-0.5">warning</span>
                            <p class="text-xs text-yellow-700 dark:text-yellow-400">Never expose your API key in client-side code. Always use server-to-server calls for production integrations.</p>
                        </div>
                    </div>

                    <div class="glass-panel rounded-xl p-6">
                        <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-3">Rate Limits</h4>
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead class="text-[10px] uppercase text-gray-500 bg-gray-50 dark:bg-white/5">
                                    <tr><th class="px-4 py-2 text-left">Plan</th><th class="px-4 py-2 text-left">Requests / Min</th><th class="px-4 py-2 text-left">Burst</th><th class="px-4 py-2 text-left">Daily Limit</th></tr>
                                </thead>
                                <tbody class="divide-y divide-gray-100 dark:divide-white/5 text-xs">
                                    <tr><td class="px-4 py-2.5 font-bold text-gray-900 dark:text-white">Free</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">30</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">50</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">5,000</td></tr>
                                    <tr><td class="px-4 py-2.5 font-bold text-gray-900 dark:text-white">Standard</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">120</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">200</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">50,000</td></tr>
                                    <tr><td class="px-4 py-2.5 font-bold text-blue-500">Enterprise</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">Unlimited</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">Unlimited</td><td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">Unlimited</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Endpoints Section -->
                <div v-if="activeSection === 'endpoints'" class="space-y-4">
                    <div v-for="ep in endpoints" :key="ep.method + ep.path" class="glass-panel rounded-xl overflow-hidden">
                        <button @click="toggleEndpoint(ep.path)" class="w-full p-5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                            <div class="flex items-center gap-3">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide" :class="methodClass(ep.method)">{{ ep.method }}</span>
                                <code class="text-sm font-mono text-gray-900 dark:text-white">{{ ep.path }}</code>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-xs text-gray-500 hidden sm:block">{{ ep.summary }}</span>
                                <span class="material-symbols-outlined text-gray-400 transition-transform duration-300" :class="{ 'rotate-180': openEndpoint === ep.path }">expand_more</span>
                            </div>
                        </button>
                        <div v-show="openEndpoint === ep.path" class="border-t border-gray-100 dark:border-white/5 p-5 space-y-4">
                            <p class="text-sm text-gray-600 dark:text-gray-400">{{ ep.description }}</p>

                            <!-- Parameters -->
                            <div v-if="ep.params && ep.params.length">
                                <h5 class="text-xs font-bold text-gray-900 dark:text-white mb-2 uppercase">Parameters</h5>
                                <div class="overflow-x-auto">
                                    <table class="w-full text-xs">
                                        <thead class="text-[10px] uppercase text-gray-500 bg-gray-50 dark:bg-white/5">
                                            <tr><th class="px-3 py-1.5 text-left">Name</th><th class="px-3 py-1.5 text-left">Type</th><th class="px-3 py-1.5 text-left">Required</th><th class="px-3 py-1.5 text-left">Description</th></tr>
                                        </thead>
                                        <tbody class="divide-y divide-gray-100 dark:divide-white/5">
                                            <tr v-for="p in ep.params" :key="p.name">
                                                <td class="px-3 py-2 font-mono font-bold text-blue-500">{{ p.name }}</td>
                                                <td class="px-3 py-2 text-gray-500">{{ p.type }}</td>
                                                <td class="px-3 py-2"><span :class="p.required ? 'text-red-500' : 'text-gray-400'">{{ p.required ? 'Yes' : 'No' }}</span></td>
                                                <td class="px-3 py-2 text-gray-600 dark:text-gray-400">{{ p.desc }}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Request Example -->
                            <div v-if="ep.request">
                                <h5 class="text-xs font-bold text-gray-900 dark:text-white mb-2 uppercase">Request Body</h5>
                                <div class="bg-gray-900 dark:bg-black/40 rounded-lg p-4 overflow-x-auto">
                                    <pre class="text-green-400 text-xs font-mono leading-relaxed">{{ ep.request }}</pre>
                                </div>
                            </div>

                            <!-- Response Example -->
                            <div>
                                <h5 class="text-xs font-bold text-gray-900 dark:text-white mb-2 uppercase">Response <span class="text-green-500">200</span></h5>
                                <div class="bg-gray-900 dark:bg-black/40 rounded-lg p-4 overflow-x-auto">
                                    <pre class="text-green-400 text-xs font-mono leading-relaxed">{{ ep.response }}</pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Webhooks Section -->
                <div v-if="activeSection === 'webhooks'" class="space-y-6">
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-purple-500">webhook</span> Webhooks
                        </h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">Register webhook URLs to receive real-time push notifications when shipment events occur. Configure webhooks from the Settings page or via the API.</p>

                        <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-3">Available Events</h4>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                            <div v-for="evt in webhookEvents" :key="evt.event" class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                                <span class="w-2 h-2 rounded-full shrink-0" :class="evt.color"></span>
                                <div>
                                    <div class="text-xs font-bold font-mono text-gray-900 dark:text-white">{{ evt.event }}</div>
                                    <div class="text-[10px] text-gray-500">{{ evt.desc }}</div>
                                </div>
                            </div>
                        </div>

                        <h4 class="font-bold text-gray-900 dark:text-white text-sm mb-3">Payload Example</h4>
                        <div class="bg-gray-900 dark:bg-black/40 rounded-lg p-4 overflow-x-auto">
                            <pre class="text-green-400 text-xs font-mono leading-relaxed">{{ webhookPayload }}</pre>
                        </div>
                    </div>
                </div>

                <!-- Error Codes Section -->
                <div v-if="activeSection === 'errors'" class="glass-panel rounded-xl p-6">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined text-red-500">error</span> Error Codes
                    </h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-sm">
                            <thead class="text-[10px] uppercase text-gray-500 bg-gray-50 dark:bg-white/5">
                                <tr><th class="px-4 py-2 text-left">Code</th><th class="px-4 py-2 text-left">Status</th><th class="px-4 py-2 text-left">Description</th><th class="px-4 py-2 text-left">Resolution</th></tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-white/5 text-xs">
                                <tr v-for="err in errorCodes" :key="err.code">
                                    <td class="px-4 py-2.5 font-mono font-bold" :class="err.code >= 500 ? 'text-red-500' : err.code >= 400 ? 'text-yellow-500' : 'text-green-500'">{{ err.code }}</td>
                                    <td class="px-4 py-2.5 font-bold text-gray-900 dark:text-white">{{ err.status }}</td>
                                    <td class="px-4 py-2.5 text-gray-600 dark:text-gray-400">{{ err.desc }}</td>
                                    <td class="px-4 py-2.5 text-gray-500">{{ err.resolution }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- SDKs Section -->
                <div v-if="activeSection === 'sdks'" class="space-y-6">
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-green-500">terminal</span> SDKs & Libraries
                        </h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">Official client libraries to integrate with QuadCore in your preferred language.</p>
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            <div v-for="sdk in sdks" :key="sdk.lang" class="p-4 bg-gray-50 dark:bg-white/5 rounded-xl border border-gray-100 dark:border-white/5 hover:border-blue-500/30 transition-colors group">
                                <div class="flex items-center gap-3 mb-3">
                                    <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold" :class="sdk.bgColor">{{ sdk.icon }}</div>
                                    <div>
                                        <div class="font-bold text-gray-900 dark:text-white text-sm">{{ sdk.lang }}</div>
                                        <div class="text-[10px] text-gray-500">{{ sdk.version }}</div>
                                    </div>
                                </div>
                                <div class="bg-gray-900 dark:bg-black/40 rounded p-2 mb-3">
                                    <code class="text-[10px] text-green-400 font-mono">{{ sdk.install }}</code>
                                </div>
                                <button @click="showToast(`Downloading ${sdk.lang} SDK...`)" class="w-full text-center py-1.5 text-xs font-bold text-blue-500 hover:text-blue-400 transition-colors">Download →</button>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

const activeSection = ref('auth')
const openEndpoint = ref(null)

const sections = [
    { id: 'auth', label: 'Authentication', icon: 'lock' },
    { id: 'endpoints', label: 'Endpoints', icon: 'api' },
    { id: 'webhooks', label: 'Webhooks', icon: 'webhook' },
    { id: 'errors', label: 'Error Codes', icon: 'error' },
    { id: 'sdks', label: 'SDKs', icon: 'terminal' },
]

const toggleEndpoint = (path) => { openEndpoint.value = openEndpoint.value === path ? null : path }

const methodClass = m => ({
    GET: 'bg-green-500/20 text-green-600 dark:text-green-400',
    POST: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    PUT: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    PATCH: 'bg-orange-500/20 text-orange-600 dark:text-orange-400',
    DELETE: 'bg-red-500/20 text-red-600 dark:text-red-400',
}[m] || 'bg-gray-500/20 text-gray-500')

const endpoints = [
    {
        method: 'POST', path: '/v2/shipments', summary: 'Create a new shipment',
        description: 'Creates a single shipment order with the provided origin, destination, cargo details, and scheduling preferences. Returns the created shipment object with a tracking ID.',
        params: [
            { name: 'origin', type: 'string', required: true, desc: 'Pickup address or hub code' },
            { name: 'destination', type: 'string', required: true, desc: 'Delivery address with pincode' },
            { name: 'weight_kg', type: 'number', required: true, desc: 'Total cargo weight in kilograms' },
            { name: 'category', type: 'string', required: false, desc: 'One of: general, palletized, hazmat, cold_chain, b2c' },
            { name: 'pickup_date', type: 'ISO 8601', required: true, desc: 'Scheduled pickup date and time' },
            { name: 'special_handling', type: 'array', required: false, desc: 'e.g. ["Fragile", "Temperature Controlled"]' },
        ],
        request: `{
  "origin": "Mumbai Hub - BKC",
  "destination": "Pune, MH 411001",
  "weight_kg": 250,
  "category": "general",
  "pickup_date": "2026-03-05T09:00:00Z",
  "declared_value": 45000,
  "insurance": true,
  "special_handling": ["Fragile"],
  "notes": "Handle with care — glass items"
}`,
        response: `{
  "id": "SHP-2026-0847",
  "status": "Booked",
  "tracking_id": "QC7X9K2M",
  "origin": "Mumbai Hub - BKC",
  "destination": "Pune, MH 411001",
  "estimated_delivery": "2026-03-06T18:00:00Z",
  "created_at": "2026-03-02T09:15:00Z"
}`
    },
    {
        method: 'POST', path: '/v2/shipments/bulk', summary: 'Bulk create shipments',
        description: 'Accepts an array of shipment objects (max 500 per request). Returns a batch ID and per-item status for validation. Use this endpoint as an alternative to CSV uploads.',
        params: [
            { name: 'shipments', type: 'array', required: true, desc: 'Array of shipment objects (same schema as single create)' },
            { name: 'validate_only', type: 'boolean', required: false, desc: 'If true, validates without creating' },
        ],
        request: `{
  "shipments": [
    { "origin": "Delhi Hub", "destination": "Jaipur, RJ 302001", "weight_kg": 120, "pickup_date": "2026-03-05T10:00:00Z" },
    { "origin": "Delhi Hub", "destination": "Chandigarh, PB 160001", "weight_kg": 85, "pickup_date": "2026-03-05T10:00:00Z" }
  ],
  "validate_only": false
}`,
        response: `{
  "batch_id": "BATCH-2026-0291",
  "total": 2,
  "created": 2,
  "failed": 0,
  "results": [
    { "index": 0, "id": "SHP-2026-0848", "status": "Booked" },
    { "index": 1, "id": "SHP-2026-0849", "status": "Booked" }
  ]
}`
    },
    {
        method: 'GET', path: '/v2/shipments/:id', summary: 'Get shipment status',
        description: 'Retrieves the full details and current status of a shipment by its ID or tracking code. Includes the complete status history timeline.',
        params: [
            { name: 'id', type: 'string', required: true, desc: 'Shipment ID (e.g., SHP-2026-0847) or tracking code' },
        ],
        response: `{
  "id": "SHP-2026-0847",
  "status": "In Transit",
  "tracking_id": "QC7X9K2M",
  "origin": "Mumbai Hub - BKC",
  "destination": "Pune, MH 411001",
  "driver": { "name": "Rajesh Kumar", "phone": "+91 0000000000" },
  "eta": "2026-03-06T18:00:00Z",
  "status_history": [
    { "status": "Booked", "timestamp": "2026-03-02T09:15:00Z" },
    { "status": "Picked Up", "timestamp": "2026-03-05T09:30:00Z" },
    { "status": "In Transit", "timestamp": "2026-03-05T10:00:00Z", "location": "19.076°N, 72.877°E" }
  ]
}`
    },
    {
        method: 'GET', path: '/v2/shipments', summary: 'List all shipments',
        description: 'Returns a paginated list of all shipments for the authenticated vendor. Supports filtering by status, date range, and origin/destination.',
        params: [
            { name: 'status', type: 'string', required: false, desc: 'Filter by status: Booked, In Transit, Delivered, Cancelled' },
            { name: 'from_date', type: 'ISO 8601', required: false, desc: 'Start of date range' },
            { name: 'to_date', type: 'ISO 8601', required: false, desc: 'End of date range' },
            { name: 'page', type: 'integer', required: false, desc: 'Page number (default: 1)' },
            { name: 'limit', type: 'integer', required: false, desc: 'Items per page (default: 25, max: 100)' },
        ],
        response: `{
  "data": [ { "id": "SHP-2026-0847", "status": "In Transit", "..." : "..." } ],
  "pagination": { "page": 1, "limit": 25, "total": 142, "pages": 6 }
}`
    },
    {
        method: 'PATCH', path: '/v2/shipments/:id/cancel', summary: 'Cancel a shipment',
        description: 'Cancels a shipment that has not yet been picked up. Once a shipment enters "In Transit" status, cancellation is no longer possible via API.',
        params: [
            { name: 'id', type: 'string', required: true, desc: 'Shipment ID to cancel' },
            { name: 'reason', type: 'string', required: true, desc: 'Reason for cancellation' },
        ],
        request: `{ "reason": "Customer requested cancellation" }`,
        response: `{
  "id": "SHP-2026-0847",
  "status": "Cancelled",
  "cancelled_at": "2026-03-03T11:00:00Z",
  "refund_status": "Processing"
}`
    },
]

const webhookEvents = [
    { event: 'shipment.booked', desc: 'New shipment created', color: 'bg-blue-500' },
    { event: 'shipment.picked_up', desc: 'Driver picked up cargo', color: 'bg-yellow-500' },
    { event: 'shipment.in_transit', desc: 'Shipment is moving', color: 'bg-purple-500' },
    { event: 'shipment.delivered', desc: 'Successfully delivered', color: 'bg-green-500' },
    { event: 'shipment.failed', desc: 'Delivery attempt failed', color: 'bg-red-500' },
    { event: 'shipment.cancelled', desc: 'Shipment was cancelled', color: 'bg-gray-500' },
]

const webhookPayload = `{
  "event": "shipment.delivered",
  "timestamp": "2026-03-06T17:45:00Z",
  "data": {
    "shipment_id": "SHP-2026-0847",
    "tracking_id": "QC7X9K2M",
    "status": "Delivered",
    "delivered_to": "Amit Shah",
    "pod_url": "https://cdn.quadcore.logistics/pod/QC7X9K2M.pdf",
    "signature": "base64_encoded_signature..."
  }
}`

const errorCodes = [
    { code: 200, status: 'OK', desc: 'Request succeeded', resolution: '—' },
    { code: 201, status: 'Created', desc: 'Resource created successfully', resolution: '—' },
    { code: 400, status: 'Bad Request', desc: 'Invalid request body or missing required fields', resolution: 'Check your request payload against the schema' },
    { code: 401, status: 'Unauthorized', desc: 'Missing or invalid API key', resolution: 'Verify your Authorization header' },
    { code: 403, status: 'Forbidden', desc: 'Insufficient permissions for this resource', resolution: 'Contact support to upgrade your API plan' },
    { code: 404, status: 'Not Found', desc: 'Resource does not exist', resolution: 'Verify the shipment ID or endpoint path' },
    { code: 409, status: 'Conflict', desc: 'Duplicate order reference detected', resolution: 'Use a unique reference for each shipment' },
    { code: 422, status: 'Unprocessable', desc: 'Validation failed on one or more fields', resolution: 'Check the errors array in the response body' },
    { code: 429, status: 'Rate Limited', desc: 'Too many requests', resolution: 'Implement exponential backoff or upgrade plan' },
    { code: 500, status: 'Server Error', desc: 'Internal server failure', resolution: 'Retry after 30s; contact support if persistent' },
]

const sdks = [
    { lang: 'Node.js', version: 'v3.2.1', icon: 'JS', bgColor: 'bg-yellow-500/20 text-yellow-600', install: 'npm install @quadcore/sdk' },
    { lang: 'Python', version: 'v2.8.0', icon: 'PY', bgColor: 'bg-blue-500/20 text-blue-600', install: 'pip install quadcore-sdk' },
    { lang: 'Java', version: 'v1.5.2', icon: 'JV', bgColor: 'bg-red-500/20 text-red-600', install: 'mvn: com.quadcore:sdk:1.5.2' },
    { lang: 'PHP', version: 'v2.1.0', icon: 'PH', bgColor: 'bg-purple-500/20 text-purple-600', install: 'composer require quadcore/sdk' },
    { lang: 'Go', version: 'v1.3.0', icon: 'GO', bgColor: 'bg-cyan-500/20 text-cyan-600', install: 'go get github.com/quadcore/sdk' },
    { lang: 'C# / .NET', version: 'v2.0.4', icon: 'C#', bgColor: 'bg-green-500/20 text-green-600', install: 'dotnet add package QuadCore.SDK' },
]

function copyApiKey() { navigator.clipboard?.writeText('qc_live_k8x7m2n9p4q1r6s3t5u0'); showToast('API key copied to clipboard!') }
function copySnippet() { showToast('Snippet copied!') }
function downloadSDK() { showToast('Opening SDK download...') }

function showToast(msg) {
    const t = document.createElement('div')
    t.className = 'fixed bottom-4 right-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}
</script>
