// The bulk editor tab: sample upload batches, their entries, the edit dialog and the summary charts.
import { computed, ref } from 'vue'

export function useBulkUploads(isDark) {
    const expandedSample = ref(null)
    const expandedUpload = ref(null)
    const expandedEntry = ref(null)
    const editingEntry = ref(null)
    const showEditModal = ref(false)

    const bulkUploads = ref([
        {
            id: 1, fileName: 'commercial_batch_01.csv', type: 'CSV', size: '45 KB', date: '28 Feb, 10:30 AM', entries: [
                { orderId: 'ORD_2026_001', date: '28-Feb-2026', category: 'Commercial', description: 'Electronics - Laptops', hsnCode: '8471', palletCount: 10, weight: 500, declaredValue: 125000, insuranceRequired: 'Yes', pickupHub: 'Mumbai Hub', destination: 'Tech Park', destinationCity: 'Bangalore', pincode: '560100', pickupDate: '2026-03-01', priority: 'Express', paymentMode: 'Invoice', packingRequired: true, laborRequired: true, laborCount: 2, quotedPrice: 8750 },
                { orderId: 'ORD_2026_002', date: '28-Feb-2026', category: 'Commercial', description: 'Office Furniture', hsnCode: '9403', palletCount: 8, weight: 400, declaredValue: 50000, insuranceRequired: 'No', pickupHub: 'Delhi Hub', destination: 'Business Center', destinationCity: 'Noida', pincode: '201301', pickupDate: '2026-03-02', priority: 'Standard', paymentMode: 'COD', packingRequired: false, laborRequired: false, laborCount: 1, quotedPrice: 4500 }
            ]
        },
        {
            id: 2, fileName: 'palletized_batch_15.xlsx', type: 'XLSX', size: '78 KB', date: '27 Feb, 03:45 PM', entries: [
                { orderId: 'ORD_2026_003', date: '27-Feb-2026', category: 'Palletized', description: 'FMCG Products', hsnCode: '2106', palletCount: 25, weight: 1200, declaredValue: 200000, insuranceRequired: 'Yes', pickupHub: 'Pune Hub', destination: 'Distribution Warehouse', destinationCity: 'Mumbai', pincode: '400001', pickupDate: '2026-03-03', priority: 'Standard', paymentMode: 'Invoice', packingRequired: true, laborRequired: true, laborCount: 4, quotedPrice: 18500 }
            ]
        },
        {
            id: 3, fileName: 'b2c_orders_08.json', type: 'JSON', size: '102 KB', date: '26 Feb, 09:15 AM', entries: [
                { orderId: 'ORD_2026_004', date: '26-Feb-2026', category: 'B2C', description: 'Home Appliances', hsnCode: '', palletCount: 0, weight: 35, declaredValue: 15000, insuranceRequired: 'Yes', pickupHub: 'Mumbai Hub', destination: 'Residential', destinationCity: 'Chennai', pincode: '600001', pickupDate: '2026-03-05', priority: 'Urgent', paymentMode: 'Full Payment', packingRequired: true, laborRequired: false, laborCount: 0, quotedPrice: 1200 },
                { orderId: 'ORD_2026_005', date: '26-Feb-2026', category: 'B2C', description: 'Fashion Apparels', hsnCode: '', palletCount: 0, weight: 12, declaredValue: 5000, insuranceRequired: 'No', pickupHub: 'Delhi Hub', destination: 'Home Address', destinationCity: 'Gurgaon', pincode: '122001', pickupDate: '2026-03-04', priority: 'Express', paymentMode: 'COD', packingRequired: false, laborRequired: false, laborCount: 0, quotedPrice: 450 }
            ]
        }
    ])

    const barChartData = computed(() => ({
        labels: ['Commercial', 'Palletized', 'B2C'],
        datasets: [{ label: 'Shipment Count', data: [2, 1, 2], backgroundColor: ['#3B82F6', '#10B981', '#8B5CF6'] }]
    }))

    const barChartOptions = computed(() => ({
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { ticks: { color: isDark.value ? '#9ca3af' : '#374151' }, grid: { color: isDark.value ? 'rgba(255,255,255,0.07)' : 'rgba(107,114,128,0.15)' } }, x: { ticks: { color: isDark.value ? '#9ca3af' : '#374151' }, grid: { display: false } } }
    }))

    const doughnutChartData = computed(() => ({
        labels: ['Commercial', 'Palletized', 'B2C'],
        datasets: [{ data: [2, 1, 2], backgroundColor: ['#3B82F6', '#10B981', '#8B5CF6'] }]
    }))

    const doughnutChartOptions = computed(() => ({
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: isDark.value ? '#9ca3af' : '#374151', padding: 15 } } }
    }))

    function toggleSample(category) {
        expandedSample.value = expandedSample.value === category ? null : category
    }

    function toggleUpload(id) {
        expandedUpload.value = expandedUpload.value === id ? null : id
        expandedEntry.value = null
    }

    function toggleEntry(orderId) {
        expandedEntry.value = expandedEntry.value === orderId ? null : orderId
    }

    function openEditModal(entry) {
        editingEntry.value = JSON.parse(JSON.stringify(entry))
        showEditModal.value = true
    }

    function saveEdit() {
        const upload = bulkUploads.value.find(u => u.entries.some(e => e.orderId === editingEntry.value.orderId))
        if (upload) {
            const idx = upload.entries.findIndex(e => e.orderId === editingEntry.value.orderId)
            if (idx !== -1) upload.entries[idx] = editingEntry.value
        }
        showEditModal.value = false
        editingEntry.value = null
    }

    function deleteUpload(id) {
        if (!confirm('Delete this upload and all its entries?')) return
        bulkUploads.value = bulkUploads.value.filter(u => u.id !== id)
    }

    function deleteEntry(uploadId, orderId) {
        if (!confirm('Delete this entry?')) return
        const upload = bulkUploads.value.find(u => u.id === uploadId)
        if (upload) upload.entries = upload.entries.filter(e => e.orderId !== orderId)
    }

    return {
        bulkUploads,
        expandedSample,
        expandedUpload,
        expandedEntry,
        editingEntry,
        showEditModal,
        barChartData,
        barChartOptions,
        doughnutChartData,
        doughnutChartOptions,
        toggleSample,
        toggleUpload,
        toggleEntry,
        openEditModal,
        saveEdit,
        deleteUpload,
        deleteEntry,
    }
}
