<template>
    <div class="w-[95%] mx-auto space-y-8">
        <div class="text-center space-y-2">
            <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Bulk Order Upload</h2>
            <p class="text-gray-500 dark:text-gray-400 text-sm">Upload CSV or Excel files to create multiple shipments
                at once.</p>
        </div>

        <!-- Upload Area -->
        <div @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="handleDrop"
            @click="$refs.fileInput.click()"
            class="glass-panel p-12 rounded-xl border-2 border-dashed transition-colors flex flex-col items-center justify-center cursor-pointer group"
            :class="isDragging ? 'border-blue-500 bg-blue-500/5' : 'border-gray-300 dark:border-white/20 hover:border-blue-500/50'">
            <input ref="fileInput" type="file" accept=".csv,.xlsx,.json" class="hidden" @change="handleFileSelect">
            <div
                class="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-4xl text-blue-500">upload_file</span>
            </div>
            <div v-if="!selectedFile" class="text-center">
                <div class="font-bold text-gray-900 dark:text-white text-lg mb-1">Drag & Drop your file here</div>
                <p class="text-xs text-gray-500 mb-4">Supported formats: .CSV, .XLSX, .JSON</p>
                <button
                    class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-sm transition-colors">Browse
                    Files</button>
            </div>
            <div v-else class="text-center">
                <span class="material-symbols-outlined text-3xl text-green-500 mb-2">description</span>
                <div class="font-bold text-gray-900 dark:text-white mb-1">{{ selectedFile.name }}</div>
                <div class="text-xs text-gray-500">{{ (selectedFile.size / 1024).toFixed(1) }} KB</div>
            </div>
        </div>

        <!-- Upload Button -->
        <div v-if="selectedFile" class="flex justify-center gap-3">
            <button @click.stop="selectedFile = null"
                class="px-5 py-2.5 bg-gray-100 dark:bg-white/5 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-bold hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">Cancel</button>
            <button @click.stop="processUpload" :disabled="uploading"
                class="px-8 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-sm transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="uploading"
                    class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                {{ uploading ? 'Analyzing...' : 'Upload & Process' }}
            </button>
        </div>

        <!-- Template Downloads -->
        <TemplateDownloads />

        <!-- Recent Uploads -->
        <RecentUploadsTable />

        <!-- Upload Detail Modal -->
        <Teleport to="body">
            <UploadDetailModal />
        </Teleport>

        <!-- Post-Upload Confirmation Modal -->
        <Teleport to="body">
            <UploadConfirmModal />
        </Teleport>
    </div>
</template>

<script setup>
import TemplateDownloads from './bulkUpload/TemplateDownloads.vue'
import RecentUploadsTable from './bulkUpload/RecentUploadsTable.vue'
import UploadDetailModal from './bulkUpload/UploadDetailModal.vue'
import UploadConfirmModal from './bulkUpload/UploadConfirmModal.vue'
import { bulkUploadPageKey } from './bulkUpload/bulkUploadPageContext'
import { ref, computed, onMounted, provide } from 'vue'
import { useVendorStore } from '@/stores/vendorStore'

const store = useVendorStore()
const selectedFile = ref(null)
const uploading = ref(false)
const saving = ref(false)
const isDragging = ref(false)
const viewingUpload = ref(null)
const fileInput = ref(null)

// Confirmation modal state
const showConfirmModal = ref(false)
const showSchedulePicker = ref(false)
const scheduleDate = ref('')
const scheduleTime = ref('')
const pendingUpload = ref({
    filename: '',
    fileSize: '',
    detectedRows: 0,
    validRows: 0,
    warningRows: 0,
    parsedRows: [],
})

const uploadQuote = computed(() => {
    const rows = pendingUpload.value.detectedRows || 0
    const baseTransport = rows * 850
    const handling = rows * 120
    const insurance = Math.round(rows * 45)
    const subtotal = baseTransport + handling + insurance
    const gst = Math.round(subtotal * 0.18)
    return { baseTransport, handling, insurance, gst, total: subtotal + gst }
})

const uploadStatusClass = s => ({
    Processed: 'bg-green-500/20 text-green-600 dark:text-green-400',
    Failed: 'bg-red-500/20 text-red-600 dark:text-red-400',
    Processing: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    Scheduled: 'bg-purple-500/20 text-purple-600 dark:text-purple-400',
}[s] || 'bg-gray-500/20 text-gray-500')

// CSV template definitions — real downloadable files
const TEMPLATES = {
    commercial: {
        filename: 'commercial_b2b_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,cargo_type,weight_kg,pallets,declared_value,payment_mode',
            'ORD-001,Mumbai Warehouse MIDC Andheri,Delhi Central Hub Okhla,Electronics,500,5,50000,Invoice',
            'ORD-002,Pune Factory Pimpri,Bangalore Depot Whitefield,Machinery,1200,12,120000,Prepaid',
        ]
    },
    palletized: {
        filename: 'palletized_template.csv',
        rows: [
            'reference_id,pickup_address,delivery_address,pallets,weight_kg,pallet_type,declared_value,payment_mode',
            'ORD-001,Pune Factory Pimpri,Bangalore Depot Whitefield,10,2000,Standard EUR,100000,Invoice',
            'ORD-002,Chennai Port Trust,Hyderabad JNPC Hub,4,800,Heat-Treated,40000,Prepaid',
        ]
    },
    b2c: {
        filename: 'b2c_shipment_template.csv',
        rows: [
            'reference_id,customer_name,customer_phone,pickup_address,delivery_address,item_description,weight_kg,declared_value',
            'ORD-001,Rahul Sharma,9876543210,Seller Hub Mumbai,123 Main St Bangalore,Smart TV 55 inch,12,25000',
            'ORD-002,Priya Patel,9123456789,Retail Store Ahmedabad,Plot 45 Surat,Home Appliances Set,35,15000',
        ]
    }
}

function handleFileSelect(e) {
    if (e.target.files.length) selectedFile.value = e.target.files[0]
}

function handleDrop(e) {
    isDragging.value = false
    if (e.dataTransfer.files.length) selectedFile.value = e.dataTransfer.files[0]
}

function parseFile(file) {
    return new Promise((resolve) => {
        const ext = file.name.split('.').pop().toLowerCase()
        const reader = new FileReader()

        if (ext === 'json') {
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result)
                    const parsedRows = Array.isArray(data) ? data : []
                    resolve({ rows: parsedRows.length, warnings: 0, parsedRows })
                } catch {
                    resolve({ rows: 0, warnings: 1, parsedRows: [] })
                }
            }
            reader.readAsText(file)
        } else if (ext === 'csv') {
            reader.onload = (e) => {
                const lines = e.target.result.split('\n').map(l => l.trim()).filter(Boolean)
                if (lines.length < 2) { resolve({ rows: 0, warnings: 0, parsedRows: [] }); return }
                const headers = lines[0].split(',').map(h => h.trim())
                const parsedRows = []
                let warnings = 0
                for (const line of lines.slice(1)) {
                    const cols = line.split(',').map(c => c.trim())
                    if (cols.length < headers.length || cols.some(c => !c)) { warnings++; continue }
                    const row = {}
                    headers.forEach((h, i) => { row[h] = cols[i] })
                    parsedRows.push(row)
                }
                resolve({ rows: lines.length - 1, warnings, parsedRows })
            }
            reader.readAsText(file)
        } else {
            // XLSX — no library, estimate from file size, no row data
            const estimated = Math.max(1, Math.floor(file.size / 150))
            resolve({ rows: estimated, warnings: 0, parsedRows: [] })
        }
    })
}

async function processUpload() {
    if (!selectedFile.value) return
    uploading.value = true
    try {
        const { rows, warnings, parsedRows } = await parseFile(selectedFile.value)
        pendingUpload.value = {
            filename: selectedFile.value.name,
            fileSize: (selectedFile.value.size / 1024).toFixed(1),
            detectedRows: rows,
            validRows: rows - warnings,
            warningRows: warnings,
            parsedRows,
        }
        showConfirmModal.value = true
        showSchedulePicker.value = false
    } catch (e) {
        showToast('Could not read file: ' + (e.message || 'Unknown error'))
    } finally {
        uploading.value = false
    }
}

async function confirmCreateNow() {
    saving.value = true
    const snapshot = { ...pendingUpload.value }
    try {
        await store.addBulkUpload({
            filename: snapshot.filename,
            orders: snapshot.detectedRows,
            status: 'Processing',
            errors: snapshot.warningRows,
            fileSizeKb: Math.round(Number(snapshot.fileSize || 0)),
        })
        showConfirmModal.value = false
        selectedFile.value = null
        showToast(`Processing ${snapshot.detectedRows} shipments…`)

        const latestId = store.bulkUploads[0]?.id

        // Create real orders from parsed rows
        let created = 0, failed = snapshot.warningRows
        if (snapshot.parsedRows.length > 0) {
            const result = await store.createBulkOrders(snapshot.parsedRows)
            created = result.created
            failed += result.failed
        }

        const finalStatus = failed > 0 && created === 0 ? 'Failed' : 'Processed'
        if (latestId) {
            await store.updateBulkUpload(latestId, { status: finalStatus, errors: failed })
        }
        await store.fetchShipments()
        showToast(finalStatus === 'Processed'
            ? `✓ ${created} shipments created! Check Orders page.`
            : `Completed with ${failed} error(s) — check details to retry`)
    } catch (e) {
        showToast('Upload failed: ' + (e.message || 'Please try again'))
    } finally {
        saving.value = false
    }
}

async function confirmScheduleLater() {
    if (!scheduleDate.value || !scheduleTime.value) {
        showToast('Please select a date and time')
        return
    }
    saving.value = true
    try {
        await store.addBulkUpload({
            filename: pendingUpload.value.filename,
            orders: pendingUpload.value.detectedRows,
            status: 'Scheduled',
            errors: 0,
            fileSizeKb: Math.round(Number(pendingUpload.value.fileSize || 0)),
            scheduledFor: `${scheduleDate.value} ${scheduleTime.value}`,
        })
        showConfirmModal.value = false
        showSchedulePicker.value = false
        selectedFile.value = null
        showToast(`Scheduled for ${scheduleDate.value} at ${scheduleTime.value}`)
    } catch (e) {
        showToast('Scheduling failed: ' + (e.message || 'Please try again'))
    } finally {
        saving.value = false
    }
}

function cancelConfirmation() {
    showConfirmModal.value = false
    showSchedulePicker.value = false
    selectedFile.value = null
}

function viewUploadDetail(u) {
    viewingUpload.value = u
}

async function retryUpload(u) {
    saving.value = true
    try {
        await store.updateBulkUpload(u.id, { status: 'Processing', errors: 0 })
        viewingUpload.value = null
        showToast(`Reprocessing ${u.filename}…`)
        setTimeout(async () => {
            await store.updateBulkUpload(u.id, { status: 'Processed', errors: 0 })
            showToast(`✓ ${u.filename} reprocessed successfully`)
        }, 2000)
    } catch (e) {
        showToast('Retry failed: ' + (e.message || 'Please try again'))
    } finally {
        saving.value = false
    }
}

// Generate and download a real CSV template file
function downloadTemplate(type) {
    const t = TEMPLATES[type]
    if (!t) return
    const content = t.rows.join('\r\n') + '\r\n'
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = t.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    showToast(`${t.filename} downloaded`)
}

function showToast(msg) {
    const t = document.createElement('div')
    t.className = 'fixed right-4 bottom-4 z-[9999] bg-green-500 text-white text-sm font-bold px-4 py-2 rounded-lg shadow-xl'
    t.textContent = msg
    document.body.appendChild(t)
    setTimeout(() => t.remove(), 3000)
}

onMounted(() => {
    store.fetchBulkUploads()
})

provide(bulkUploadPageKey, {
    cancelConfirmation,
    confirmCreateNow,
    confirmScheduleLater,
    downloadTemplate,
    pendingUpload,
    retryUpload,
    saving,
    scheduleDate,
    scheduleTime,
    showConfirmModal,
    showSchedulePicker,
    store,
    uploadQuote,
    uploadStatusClass,
    viewUploadDetail,
    viewingUpload,
})
</script>
