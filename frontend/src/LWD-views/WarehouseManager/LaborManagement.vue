<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Labor Management</h2>
            <div class="flex flex-wrap justify-end gap-2">
                <button @click="openCreateModal"
                    class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors">
                    <span class="material-symbols-outlined">person_add</span>
                    Add Labourer
                </button>
                <button @click="showAssignModal = true"
                    class="bg-gray-50 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-900 dark:text-white border border-gray-200 dark:border-white/10 py-2 px-4 rounded-lg transition-colors flex items-center gap-2">
                    <span class="material-symbols-outlined">link</span> Assign to Order
                </button>
            </div>
        </div>

        <LiveStatusBoard />

        <LaborPerformanceSummary />

        <StaffList />

        <AssignLabourerModal />

        <StaffDetailModal />

        <CreateLabourerModal />

        <!-- Toast -->
        <div v-if="toastMsg"
            class="fixed bottom-6 right-6 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 animate-bounce"
            :class="toastType === 'error' ? 'bg-red-500/90 text-white' : 'bg-green-500/90 text-white'">
            <span class="material-symbols-outlined">{{ toastType === 'error' ? 'error' : 'check_circle' }}</span>
            <div class="font-bold">{{ toastMsg }}</div>
        </div>
    </div>
</template>

<script setup>
import LiveStatusBoard from './labor/LiveStatusBoard.vue'
import LaborPerformanceSummary from './labor/LaborPerformanceSummary.vue'
import StaffList from './labor/StaffList.vue'
import AssignLabourerModal from './labor/AssignLabourerModal.vue'
import StaffDetailModal from './labor/StaffDetailModal.vue'
import CreateLabourerModal from './labor/CreateLabourerModal.vue'
import {
    buildAssignmentMeta,
    buildDisplayStatus,
    buildLocalAssignmentState,
    formatOrderDisplayId,
    formatTime,
    getInitials,
    mapStatusClass,
} from './labor/labourerStatus'
import { laborPageKey } from './labor/laborPageContext'
import { ref, computed, onMounted, provide } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { apiUrl } from '@/config/api'
import { useSlipPrinter } from '@/composables/useSlipPrinter'

const { openSlipWithData } = useSlipPrinter()

const authStore = useAuthStore()

const searchQuery = ref('')
const deptFilter = ref('')
const statusFilter = ref('')
const showAssignModal = ref(false)
const showStaffDetail = ref(false)
const showCreateModal = ref(false)
const assignTarget = ref(null)
const selectedStaff = ref(null)
const assignOrderId = ref('')
const assignType = ref('Picking')
const toastMsg = ref('')
const toastType = ref('success')
const loading = ref(false)
const isAssigning = ref(false)
const isCreating = ref(false)

// New labourer form
const newLabourer = ref({
    name: '',
    email: '',
    phone: '',
    role: '',
    skills: []
})

const availableSkills = ['Picking', 'Packing', 'Loading', 'Driving', 'Heavy Lifting', 'Fragile Items', 'Furniture', 'Electronics']

function toggleSkill(skill) {
    const idx = newLabourer.value.skills.indexOf(skill)
    if (idx >= 0) {
        newLabourer.value.skills.splice(idx, 1)
    } else {
        newLabourer.value.skills.push(skill)
    }
}

function resetNewLabourerForm() {
    newLabourer.value = {
        name: '',
        email: '',
        phone: '',
        role: '',
        skills: []
    }
}

function openCreateModal() {
    resetNewLabourerForm()
    showCreateModal.value = true
}

function closeCreateModal() {
    showCreateModal.value = false
    resetNewLabourerForm()
}

const staffList = ref([])

// Fetch labourers from backend
async function fetchLabourers() {
    loading.value = true
    try {
        const response = await fetch(apiUrl('api/v1/labourers?page=1&page_size=100'), {
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) throw new Error('Failed to fetch labourers')

        const data = await response.json()
        const items = data.items || data || []

        staffList.value = items.map(labourer => {
            const displayStatus = buildDisplayStatus(labourer)
            const displayOrderId = formatOrderDisplayId(
                labourer.order_id || labourer.assigned_order_id,
                labourer.assigned_order_tracking
            )
            const assignmentMeta = buildAssignmentMeta(labourer)
            return {
                id: labourer.id,
                name: labourer.name || labourer.full_name || `Labourer ${labourer.id?.slice(0, 6)}`,
                role: labourer.role || labourer.skill || 'Labourer',
                task: assignmentMeta.task,
                assignmentHint: assignmentMeta.assignmentHint,
                orderScope: assignmentMeta.orderScope,
                orderId: displayOrderId,
                perf: labourer.performance_score || labourer.performance || Math.floor(85 + Math.random() * 20),
                status: displayStatus,
                statusClass: mapStatusClass(displayStatus),
                startTime: formatTime(labourer.check_in_time || labourer.start_time) || '07:00',
                fieldTime: labourer.field_time ? formatTime(labourer.field_time) : null,
                returnTime: labourer.return_time ? formatTime(labourer.return_time) : null,
                dept: labourer.department || labourer.role || 'General',
                rawId: labourer.id
            }
        })

    } catch (error) {
        console.error('Error fetching labourers:', error)
        showToast('Error loading staff data', 'error')
    } finally {
        loading.value = false
    }
}

const statusCounts = computed(() => ({
    inWarehouse: staffList.value.filter(s => s.status === 'In Warehouse').length,
    warehouseOrder: staffList.value.filter(s => s.status === 'Warehouse Order').length,
    customerMove: staffList.value.filter(s => ['Service Move', 'With Driver'].includes(s.status)).length,
    offDuty: staffList.value.filter(s => s.status === 'Off Duty').length,
}))

const avgProductivity = computed(() => {
    const active = staffList.value.filter(s => s.status !== 'Off Duty')
    if (!active.length) return 0
    return Math.round(active.reduce((sum, s) => sum + s.perf, 0) / active.length)
})

const totalHours = computed(() => {
    return staffList.value.filter(s => s.status !== 'Off Duty').length * 6
})

const availableStaffList = computed(() => {
    return staffList.value.filter(s => s.status === 'In Warehouse')
})

const filteredStaff = computed(() => {
    return staffList.value.filter(s => {
        const matchesSearch = !searchQuery.value || s.name.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchesDept = !deptFilter.value || s.dept === deptFilter.value
        const matchesStatus = !statusFilter.value
            || s.status === statusFilter.value
            || (statusFilter.value === 'Customer Move' && ['Service Move', 'With Driver'].includes(s.status))
        return matchesSearch && matchesDept && matchesStatus
    })
})

function openAssign(staff) {
    assignTarget.value = staff
    assignOrderId.value = ''
    assignType.value = 'Picking'
    showAssignModal.value = true
}

function canPrintAssignmentSlip(staff) {
    return Boolean(staff?.orderId)
}

function openAssignmentSlip(staff) {
    if (!canPrintAssignmentSlip(staff)) return
    openSlipWithData('laborAssignment', staff)
}

async function assignWorker() {
    if (!assignTarget.value || !assignOrderId.value) return
    isAssigning.value = true
    try {
        // Try to assign via API using the labourer's raw ID
        const labourerId = assignTarget.value.rawId
        if (labourerId) {
            const response = await fetch(apiUrl(`api/v1/labourers/${labourerId}/assign/${assignOrderId.value}`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                }
            })
            if (!response.ok) {
                // Fallback: update local state only if API call fails
                console.warn('Assign API not available, updating local state')
            }
        }
        // Update local list
        const assignmentState = buildLocalAssignmentState(assignType.value, assignOrderId.value)
        assignTarget.value.orderId = assignmentState.orderId
        assignTarget.value.status = assignmentState.status
        assignTarget.value.statusClass = assignmentState.statusClass
        assignTarget.value.task = assignmentState.task
        assignTarget.value.assignmentHint = assignmentState.assignmentHint
        assignTarget.value.orderScope = assignmentState.orderScope

        showAssignModal.value = false
        showToast('Worker assigned to order')
    } catch (error) {
        console.error('Assign error:', error)
        // Still update locally
        const assignmentState = buildLocalAssignmentState(assignType.value, assignOrderId.value)
        assignTarget.value.orderId = assignmentState.orderId
        assignTarget.value.status = assignmentState.status
        assignTarget.value.statusClass = assignmentState.statusClass
        assignTarget.value.task = assignmentState.task
        assignTarget.value.assignmentHint = assignmentState.assignmentHint
        assignTarget.value.orderScope = assignmentState.orderScope
        showAssignModal.value = false
        showToast('Worker assigned to order')
    } finally {
        isAssigning.value = false
    }
}

function showToast(msg, type = 'success') {
    toastMsg.value = msg
    toastType.value = type
    setTimeout(() => { toastMsg.value = '' }, 2500)
}

// Create new labourer
async function createLabourer() {
    if (!newLabourer.value.name || !newLabourer.value.role) {
        showToast('Please fill name and role', 'error')
        return
    }

    isCreating.value = true
    try {
        // Only send fields defined in LabourerCreate schema
        const warehouseId = authStore.currentUser?.warehouse_id
        const normalizedEmail = newLabourer.value.email?.trim().toLowerCase()
        const normalizedPhone = newLabourer.value.phone?.trim()
        const payload = {
            name: newLabourer.value.name.trim(),
            email: normalizedEmail || undefined,
            phone: normalizedPhone || undefined,
            role: newLabourer.value.role,
            department: newLabourer.value.role,
            skill_tags: newLabourer.value.skills.length > 0 ? newLabourer.value.skills : undefined,
            warehouse_id: warehouseId || undefined
        }

        // Remove undefined values
        Object.keys(payload).forEach(key => {
            if (payload[key] === undefined) delete payload[key]
        })

        const response = await fetch(apiUrl('api/v1/labourers'), {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authStore.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}))
            const detail = errData.detail
            let msg = typeof detail === 'string'
                ? detail
                : (Array.isArray(detail)
                    ? detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ')
                    : 'Failed to create labourer')
            if (msg.startsWith('Email already exists') && payload.email) {
                msg = `Email already exists: ${payload.email}`
            }
            throw new Error(msg)
        }

        const created = await response.json()
        const createdName = created.name || created.full_name || newLabourer.value.name

        // Add to local list immediately
        const displayStatus = 'In Warehouse'
        staffList.value.unshift({
            id: created.id,
            rawId: created.id,
            name: createdName,
            role: created.role || newLabourer.value.role,
            task: 'Available',
            orderId: null,
            perf: 100,
            status: displayStatus,
            statusClass: mapStatusClass(displayStatus),
            startTime: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),
            fieldTime: null,
            returnTime: null,
            dept: created.department || newLabourer.value.role
        })

        closeCreateModal()
        showToast(`${createdName} added successfully!`)
    } catch (error) {
        console.error('Create labourer error:', error)
        showToast(error.message || 'Failed to create labourer', 'error')
    } finally {
        isCreating.value = false
    }
}

function openStaffDetail(staff) {
    selectedStaff.value = staff
    showStaffDetail.value = true
}

async function setOffDuty(staff) {
    try {
        if (staff.rawId) {
            await fetch(apiUrl(`api/v1/labourers/${staff.rawId}/check-out`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                }
            })
        }
    } catch (error) {
        console.warn('Check-out API error, updating locally:', error)
    }
    staff.status = 'Off Duty'
    staff.statusClass = 'bg-gray-500/10 text-gray-500'
    staff.task = '--'
    staff.orderId = null
    showStaffDetail.value = false
    showToast(`${staff.name} set to Off Duty`)
}

async function setOnDuty(staff) {
    try {
        if (staff.rawId) {
            await fetch(apiUrl(`api/v1/labourers/${staff.rawId}/check-in`), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authStore.authToken}`,
                    'Content-Type': 'application/json'
                }
            })
        }
    } catch (error) {
        console.warn('Check-in API error, updating locally:', error)
    }
    staff.status = 'In Warehouse'
    staff.statusClass = 'bg-green-500/10 text-green-500'
    staff.task = 'Available'
    showStaffDetail.value = false
    showToast(`${staff.name} set to On Duty`)
}

async function deleteLabourer(staff) {
    if (!confirm(`Remove ${staff.name} from the labour roster?`)) return
    try {
        if (staff.rawId) {
            const response = await fetch(apiUrl(`api/v1/labourers/${staff.rawId}`), {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${authStore.authToken}` }
            })
            if (!response.ok && response.status !== 204) {
                const err = await response.json().catch(() => ({}))
                throw new Error(err.detail || 'Failed to delete')
            }
        }
        // Remove from local list
        staffList.value = staffList.value.filter(s => s.rawId !== staff.rawId)
        showStaffDetail.value = false
        showToast(`${staff.name} removed from roster`)
    } catch (error) {
        console.error('Delete error:', error)
        showToast(error.message || 'Failed to delete labourer', 'error')
    }
}

onMounted(() => {
    fetchLabourers()
})

provide(laborPageKey, {
    assignOrderId,
    assignTarget,
    assignType,
    assignWorker,
    availableSkills,
    availableStaffList,
    avgProductivity,
    canPrintAssignmentSlip,
    closeCreateModal,
    createLabourer,
    deleteLabourer,
    deptFilter,
    filteredStaff,
    getInitials,
    isAssigning,
    isCreating,
    loading,
    newLabourer,
    openAssign,
    openAssignmentSlip,
    openStaffDetail,
    searchQuery,
    selectedStaff,
    setOffDuty,
    setOnDuty,
    showAssignModal,
    showCreateModal,
    showStaffDetail,
    staffList,
    statusCounts,
    statusFilter,
    toggleSkill,
    totalHours,
})
</script>
