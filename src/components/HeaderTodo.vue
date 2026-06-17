<template>
    <div class="relative" ref="popoverRef">
        <!-- Trigger Button -->
        <button @click="togglePopover"
            class="relative w-9 h-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            :class="{ 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white': isOpen }">
            <span class="material-symbols-outlined text-[20px]">task_alt</span>
            <!-- Active Tasks Badge -->
            <span v-if="activeTasksCount > 0"
                class="absolute top-0 right-0 w-4 h-4 bg-primary text-white text-[10px] font-bold flex items-center justify-center rounded-full border-2 border-surface-light dark:border-background-dark">
                {{ activeTasksCount }}
            </span>
        </button>

        <!-- Popover -->
        <div v-show="isOpen"
            class="absolute right-0 mt-2 w-96 bg-white dark:bg-card-darker rounded-2xl shadow-xl border border-gray-200 dark:border-white/10 overflow-hidden z-50 transform origin-top-right transition-all duration-200"
            :class="isOpen ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none'">

            <!-- Header -->
            <div
                class="p-4 border-b border-gray-100 dark:border-white/5 flex justify-between items-center bg-gray-50/50 dark:bg-black/20">
                <h3 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">checklist</span>
                    My Tasks
                </h3>
                <button @click="openAddForm" v-if="editingTaskId === null"
                    class="text-xs font-semibold px-2 py-1 rounded-md transition-colors"
                    :class="isAddingTask ? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400' : 'bg-primary/10 text-primary hover:bg-primary/20'">
                    {{ isAddingTask ? 'Cancel' : '+ Add Task' }}
                </button>
            </div>

            <!-- Add/Edit Task Form -->
            <div v-if="isAddingTask || editingTaskId !== null"
                class="p-4 bg-gray-50 dark:bg-white/5 border-b border-gray-100 dark:border-white/5 space-y-3">

                <h4 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                    {{ isAddingTask ? 'Create New Task' : 'Edit Task' }}
                </h4>

                <input v-model="draftTask.text" type="text" placeholder="What needs to be done?" autofocus
                    class="w-full bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 transition-colors">

                <div class="flex gap-2">
                    <select v-model="draftTask.status"
                        class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50 transition-colors cursor-pointer">
                        <option value="Backlog" class="bg-white dark:bg-gray-800 text-gray-500">Backlog</option>
                        <option value="To Do" class="bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">To Do
                        </option>
                        <option value="In Progress" class="bg-white dark:bg-gray-800 text-blue-500">In Progress</option>
                        <option value="Priority" class="bg-white dark:bg-gray-800 text-red-500">Priority</option>
                        <option value="Done" v-if="editingTaskId !== null"
                            class="bg-white dark:bg-gray-800 text-green-500">Done
                        </option>
                    </select>

                    <input v-model="draftTask.dateString" type="date"
                        class="w-32 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50 transition-colors cursor-pointer">
                </div>

                <div class="flex gap-2 items-center">
                    <input v-model="draftTask.timeString" type="time"
                        class="w-24 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50 transition-colors cursor-pointer"
                        :disabled="!draftTask.dateString" :title="!draftTask.dateString ? 'Select a date first' : ''">

                    <select v-model="draftTask.repeat"
                        class="flex-1 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 focus:outline-none focus:border-primary/50 transition-colors cursor-pointer"
                        :disabled="!draftTask.timeString" :title="!draftTask.timeString ? 'Select a time first' : ''">
                        <option value="none" class="bg-white dark:bg-gray-800">No Repeat</option>
                        <option value="5m" class="bg-white dark:bg-gray-800">Every 5 min</option>
                        <option value="15m" class="bg-white dark:bg-gray-800">Every 15 min</option>
                        <option value="30m" class="bg-white dark:bg-gray-800">Every 30 min</option>
                        <option value="60m" class="bg-white dark:bg-gray-800">Every 1 hour</option>
                        <option value="120m" class="bg-white dark:bg-gray-800">Every 2 hours</option>
                    </select>
                </div>

                <div class="flex justify-end gap-2 pt-2">
                    <button @click="cancelEdit"
                        class="text-xs font-semibold px-3 py-1.5 rounded-lg text-gray-500 hover:bg-gray-200 dark:hover:bg-white/10 transition-colors">
                        Cancel
                    </button>
                    <button @click="saveTask" :disabled="!draftTask.text || isSaving"
                        class="bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold py-1.5 px-4 rounded-lg transition-colors shadow-sm">
                        {{ isSaving ? 'Saving...' : (isAddingTask ? 'Save Task' : 'Update Task') }}
                    </button>
                </div>
            </div>

            <!-- Task List -->
            <div class="max-h-[360px] overflow-y-auto no-scrollbar" v-if="!isAddingTask && editingTaskId === null">
                <div v-if="tasks.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">done_all</span>
                    <p class="text-sm">You have no tasks.</p>
                </div>

                <div v-else class="divide-y divide-gray-100 dark:divide-white/5">
                    <div v-for="task in sortedTasks" :key="task.id"
                        class="p-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors group"
                        :class="{ 'opacity-60': task.status === 'Done' }">

                        <div class="flex items-start gap-3">
                            <!-- Status Toggle/Checkbox -->
                            <button @click="toggleTaskStatus(task)"
                                class="mt-0.5 w-5 h-5 rounded-full border flex flex-shrink-0 items-center justify-center transition-colors"
                                :class="task.status === 'Done' ? 'bg-green-500 border-green-500 text-white' : 'border-gray-300 dark:border-gray-600 hover:border-primary dark:hover:border-primary text-transparent'">
                                <span class="material-symbols-outlined text-[14px]">check</span>
                            </button>

                            <div class="flex-1 min-w-0">
                                <p class="text-sm font-medium transition-all duration-300 cursor-pointer select-none"
                                    :class="task.status === 'Done' ? 'text-gray-400 dark:text-gray-500 line-through' : 'text-gray-900 dark:text-white'"
                                    @click.stop="handleTaskClick($event, task)" title="Triple click to edit task">
                                    {{ task.text }}
                                </p>

                                <div class="flex flex-wrap items-center gap-2 mt-1.5">
                                    <!-- Inline Status Dropdown (Smart Update) -->
                                    <select v-model="task.status" @change="onInlineStatusChange(task)" @click.stop
                                        class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border-none focus:ring-0 cursor-pointer appearance-none bg-transparent -ml-2"
                                        :class="getStatusColor(task.status)">
                                        <option value="Backlog" class="bg-white dark:bg-gray-800 text-gray-500">Backlog
                                        </option>
                                        <option value="To Do"
                                            class="bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300">To Do
                                        </option>
                                        <option value="In Progress" class="bg-white dark:bg-gray-800 text-blue-500">In
                                            Progress</option>
                                        <option value="Priority" class="bg-white dark:bg-gray-800 text-red-500">Priority
                                        </option>
                                        <option value="Done" class="bg-white dark:bg-gray-800 text-green-500">Done
                                        </option>
                                    </select>

                                    <span v-if="task.targetTime"
                                        class="text-xs font-medium flex items-center gap-1 inline-block select-none cursor-pointer"
                                        :class="isTaskOverdue(task) && task.status !== 'Done' ? 'text-red-500 animate-pulse' : 'text-gray-500 dark:text-gray-400 hover:text-primary'"
                                        @click.stop="handleTaskClick($event, task)" title="Triple click to edit time">
                                        <span class="material-symbols-outlined text-[12px]">schedule</span>
                                        {{ formatDateTime(task.targetTime) }}
                                        <span v-if="task.repeat !== 'none'"
                                            class="material-symbols-outlined text-[12px] opacity-70 ml-0.5"
                                            title="Repeating">autorenew</span>
                                    </span>

                                    <!-- Quick Actions -->
                                    <button v-if="task.status !== 'Done' && task.targetTime"
                                        @click.stop="snoozeTask(task)"
                                        class="text-gray-400 hover:text-blue-500 rounded transition-colors flex items-center"
                                        title="Remind in 1 hour">
                                        <span class="material-symbols-outlined text-[16px]">update</span>
                                    </button>
                                    <button v-if="task.status !== 'Done' && task.targetTime"
                                        @click.stop="silenceTask(task)"
                                        class="text-gray-400 hover:text-orange-500 rounded transition-colors flex items-center"
                                        :title="task.silenced ? 'Unmute alerts' : 'Silence alerts'">
                                        <span class="material-symbols-outlined text-[16px]">
                                            {{ task.silenced ? 'notifications_active' : 'notifications_off' }}
                                        </span>
                                    </button>
                                </div>
                            </div>

                            <div class="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all">
                                <button @click.stop="deleteTask(task.id)"
                                    class="text-gray-400 hover:text-red-500 p-1 rounded hover:bg-gray-200 dark:hover:bg-white/10 transition-colors"
                                    title="Delete task">
                                    <span class="material-symbols-outlined text-[16px]">delete</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="p-3 bg-gray-50 dark:bg-white/5 border-t border-gray-100 dark:border-white/5 text-center">
                <button v-if="tasks.filter(t => t.status === 'Done').length > 0" @click="clearDoneTasks"
                    class="text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white font-medium transition-colors">
                    Clear completed tasks
                </button>
                <span v-else class="text-xs text-gray-400 italic">Manage your day efficiently</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLogisticStore } from '@/stores/logisticStore'
import { storeToRefs } from 'pinia'

const logisticStore = useLogisticStore()
const { tasks } = storeToRefs(logisticStore)

const isOpen = ref(false)
const isSaving = ref(false)
const tasksLoaded = ref(false)
const popoverRef = ref(null)

// Form State
const isAddingTask = ref(false)
const editingTaskId = ref(null)

const defaultDraft = {
    id: null,
    text: '',
    status: 'To Do',
    dateString: '', // "YYYY-MM-DD"
    timeString: '', // "HH:MM"
    repeat: 'none'
}

const draftTask = ref({ ...defaultDraft })

// Helper to format Date -> YYYY-MM-DD
const toDateString = (date) => {
    const d = new Date(date)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// Helper to format Date -> HH:MM
const toTimeString = (date) => {
    const d = new Date(date)
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// --- Computed ---
const activeTasksCount = computed(() => tasks.value.filter(t => t.status !== 'Done').length)

const sortedTasks = computed(() => {
    return [...tasks.value].sort((a, b) => {
        if (a.status === 'Done' && b.status !== 'Done') return 1;
        if (b.status === 'Done' && a.status !== 'Done') return -1;

        const statusMap = { 'Priority': 1, 'In Progress': 2, 'To Do': 3, 'Backlog': 4, 'Done': 5 }
        if (statusMap[a.status] !== statusMap[b.status]) {
            return statusMap[a.status] - statusMap[b.status]
        }

        if (a.targetTime && b.targetTime) return a.targetTime - b.targetTime;
        if (a.targetTime) return -1;
        if (b.targetTime) return 1;

        return b.createdAt - a.createdAt;
    })
})

// --- Methods ---
const togglePopover = async () => {
    isOpen.value = !isOpen.value
    if (!isOpen.value) {
        cancelEdit()
    } else if (!tasksLoaded.value) {
        // Load tasks from backend on first open
        logisticStore.fetchTasks().then(() => { tasksLoaded.value = true }).catch(() => { tasksLoaded.value = true })
    }
}

const openAddForm = () => {
    isAddingTask.value = !isAddingTask.value
    if (isAddingTask.value) {
        editingTaskId.value = null
        draftTask.value = { ...defaultDraft, dateString: toDateString(new Date()) }
    } else {
        cancelEdit()
    }
}

const openEditForm = (task) => {
    // Cannot edit if done - smartly disables
    if (task.status === 'Done') return

    isAddingTask.value = false
    editingTaskId.value = task.id

    let dString = ''
    let tString = ''
    if (task.targetTime) {
        dString = toDateString(task.targetTime)
        tString = toTimeString(task.targetTime)
    }

    draftTask.value = {
        id: task.id,
        text: task.text,
        status: task.status,
        dateString: dString,
        timeString: tString,
        repeat: task.repeat
    }
}

const handleTaskClick = (e, task) => {
    if (task.status === 'Done') return

    // the 'detail' property on click events returns the current click count natively
    if (e.detail === 3) {
        openEditForm(task)
    }
}

const cancelEdit = () => {
    isAddingTask.value = false
    editingTaskId.value = null
    draftTask.value = { ...defaultDraft }
}

const saveTask = async () => {
    if (!draftTask.value.text || isSaving.value) return

    let targetTimeMs = null
    if (draftTask.value.dateString && draftTask.value.timeString) {
        const [year, month, day] = draftTask.value.dateString.split('-')
        const [hours, minutes] = draftTask.value.timeString.split(':')
        const t = new Date()
        t.setFullYear(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10))
        t.setHours(parseInt(hours, 10), parseInt(minutes, 10), 0, 0)
        targetTimeMs = t.getTime()
    }

    isSaving.value = true
    try {
        if (isAddingTask.value) {
            await logisticStore.createTask({
                text: draftTask.value.text,
                status: draftTask.value.status,
                targetTime: targetTimeMs,
                repeat: draftTask.value.repeat,
            })
        } else if (editingTaskId.value !== null) {
            const task = tasks.value.find(t => t.id === editingTaskId.value)
            if (task) {
                // Optimistic update
                task.text = draftTask.value.text
                task.status = draftTask.value.status
                task.targetTime = targetTimeMs
                task.repeat = draftTask.value.repeat
                task.lastAlertTime = null
                task.silenced = false
                await logisticStore.patchTask(editingTaskId.value, {
                    text: draftTask.value.text,
                    status: draftTask.value.status,
                    targetTime: targetTimeMs,
                    repeat: draftTask.value.repeat,
                    lastAlertTime: null,
                }).catch(() => {})
            }
        }
        cancelEdit()
    } finally {
        isSaving.value = false
    }
}

const toggleTaskStatus = async (task) => {
    const newStatus = task.status === 'Done' ? 'To Do' : 'Done'
    task.status = newStatus
    task.lastAlertTime = null
    await logisticStore.patchTask(task.id, { status: newStatus, last_alert_time: null }).catch(() => {})
}

const onInlineStatusChange = async (task) => {
    task.lastAlertTime = null
    await logisticStore.patchTask(task.id, { status: task.status }).catch(() => {})
}

const deleteTask = async (id) => {
    tasks.value = tasks.value.filter(t => t.id !== id)
    await logisticStore.deleteTask(id).catch(() => {})
}

const snoozeTask = async (task) => {
    if (!task.targetTime) return
    task.targetTime += 3600000
    task.lastAlertTime = null
    task.silenced = false
    await logisticStore.patchTask(task.id, { targetTime: task.targetTime, lastAlertTime: null }).catch(() => {})
}

const silenceTask = async (task) => {
    task.silenced = !task.silenced
    await logisticStore.patchTask(task.id, { silenced: task.silenced }).catch(() => {})
}

const clearDoneTasks = async () => {
    await logisticStore.clearDoneTasks().catch(() => {})
}

// --- Display Helpers ---
const formatDateTime = (ms) => {
    if (!ms) return ''
    const d = new Date(ms)
    const today = new Date()
    const isToday = d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear()

    const timeStr = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    if (isToday) return `Today, ${timeStr}`

    const dateStr = d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    return `${dateStr}, ${timeStr}`
}

const isTaskOverdue = (task) => {
    if (!task.targetTime) return false
    return Date.now() >= task.targetTime
}

const getStatusColor = (status) => {
    switch (status) {
        case 'Priority': return 'bg-red-500/10 text-red-500 border border-red-500/20'
        case 'In Progress': return 'bg-blue-500/10 text-blue-500 border border-blue-500/20'
        case 'To Do': return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
        case 'Backlog': return 'bg-gray-100 dark:bg-white/5 text-gray-500 border border-gray-200 dark:border-white/10'
        case 'Done': return 'bg-green-500/10 text-green-500 border border-green-500/20'
        default: return 'bg-gray-100 text-gray-600'
    }
}

// --- Alert System ---
let checkInterval = null
const dummyBeep = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU')

const playAlert = () => {
    if (navigator.vibrate) {
        navigator.vibrate([200, 100, 200])
    }
    try {
        dummyBeep.play().catch(e => console.warn('Audio play blocked/failed:', e))
    } catch (e) { }
}

const checkReminders = () => {
    const now = Date.now()

    tasks.value.forEach(task => {
        if (task.status === 'Done' || !task.targetTime || task.silenced) return

        if (now >= task.targetTime) {
            // First time alert or Login alert
            if (!task.lastAlertTime) {
                playAlert()
                task.lastAlertTime = now
            }
            // Repeat logic if interval exists
            else if (task.repeat !== 'none') {
                const timeSinceLastAlert = now - task.lastAlertTime

                let repeatMs = 0
                if (task.repeat === '5m') repeatMs = 5 * 60000
                if (task.repeat === '15m') repeatMs = 15 * 60000
                if (task.repeat === '30m') repeatMs = 30 * 60000
                if (task.repeat === '60m') repeatMs = 60 * 60000
                if (task.repeat === '120m') repeatMs = 120 * 60000

                // If time since last alert is greater than repeat interval, alert again
                if (repeatMs > 0 && timeSinceLastAlert >= repeatMs) {
                    playAlert()
                    task.lastAlertTime = now
                }
            }
        }
    })
}

// Click outside handler
const handleClickOutside = (event) => {
    // Use composedPath() instead of contains(event.target) because Vue may have already 
    // removed the clicked DOM node (like moving a task or opening edit mode) before 
    // this event bubbles up to document, which would erroneously cause a close.
    if (popoverRef.value && !event.composedPath().includes(popoverRef.value)) {
        isOpen.value = false
    }
}

onMounted(() => {
    document.addEventListener('click', handleClickOutside)
    // Run immediately on mount (simulates the "login" vibration for overdue tasks)
    checkReminders()
    // Check every 5 seconds for precise alerting
    checkInterval = setInterval(checkReminders, 5000)
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
    if (checkInterval) {
        clearInterval(checkInterval)
    }
})
</script>
