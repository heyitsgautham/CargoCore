/**
 * The logistics manager's task list: load, create, edit, delete and clear finished tasks.
 */

import { apiRequest, authHeaders } from './api'
import { asArray } from './mappers'

export function useLogisticTasks({ tasks }) {
    function taskFromApi(item) {
        return {
            id: String(item.id),
            text: item.text,
            status: item.status || 'To Do',
            targetTime: item.target_time ? new Date(item.target_time).getTime() : null,
            repeat: item.repeat || 'none',
            createdAt: item.created_at ? new Date(item.created_at).getTime() : Date.now(),
            lastAlertTime: item.last_alert_time ? new Date(item.last_alert_time).getTime() : null,
            silenced: item.silenced || false,
            remaining: '',
        }
    }

    async function fetchTasks() {
        const data = await apiRequest('/logistics/tasks', { headers: authHeaders() })
        tasks.value = asArray(data).map(taskFromApi)
    }

    async function createTask(payload) {
        const body = {
            text: payload.text,
            status: payload.status || 'To Do',
            target_time: payload.targetTime ? new Date(payload.targetTime).toISOString() : null,
            repeat: payload.repeat || 'none',
        }
        const data = await apiRequest('/logistics/tasks', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        tasks.value.unshift(taskFromApi(data))
    }

    async function deleteTask(id) {
        await apiRequest(`/logistics/tasks/${id}`, { method: 'DELETE', headers: authHeaders() })
        tasks.value = tasks.value.filter((t) => t.id !== String(id))
    }

    async function patchTask(id, updates) {
        const body = {}
        if (updates.status !== undefined) body.status = updates.status
        if (updates.silenced !== undefined) body.silenced = updates.silenced
        if (updates.text !== undefined) body.text = updates.text
        if (updates.targetTime !== undefined) body.target_time = updates.targetTime ? new Date(updates.targetTime).toISOString() : null
        if (updates.repeat !== undefined) body.repeat = updates.repeat
        if (updates.lastAlertTime !== undefined) body.last_alert_time = updates.lastAlertTime ? new Date(updates.lastAlertTime).toISOString() : null
        const data = await apiRequest(`/logistics/tasks/${id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(body),
        })
        const t = tasks.value.find((t) => t.id === String(id))
        if (t && data) Object.assign(t, taskFromApi(data))
    }

    async function clearDoneTasks() {
        const doneIds = tasks.value.filter((t) => t.status === 'Done').map((t) => t.id)
        tasks.value = tasks.value.filter((t) => t.status !== 'Done')
        await Promise.all(doneIds.map((id) => apiRequest(`/logistics/tasks/${id}`, { method: 'DELETE', headers: authHeaders() }).catch(() => {})))
    }

    return { fetchTasks, createTask, deleteTask, patchTask, clearDoneTasks }
}
