/**
 * Chat threads between the logistics manager, hubs and drivers.
 */

import { apiRequest, authHeaders } from './api'
import { asWarehouseId } from './mappers'

export function useLogisticChats({ chats }) {
    function getManagerDriverThreadName(driverOrName) {
        const rawName = typeof driverOrName === 'string'
            ? driverOrName
            : driverOrName?.name
        const safeName = String(rawName || '').trim()
        return safeName || 'Unknown Driver'
    }

    function findManagerDriverThread(driver) {
        if (!driver) return null
        const threadName = getManagerDriverThreadName(driver)
        // Match by exact name OR the legacy "LM Driver: X" format
        return chats.value.find(
            (chat) => chat.name === threadName || chat.name === `LM Driver: ${threadName}`
        ) || null
    }

    async function fetchWmChats() {
        const data = await apiRequest('/logistics/chats', { headers: authHeaders() })
        chats.value = (Array.isArray(data) ? data : []).map((item) => ({
            id: String(item.id),
            hubId: asWarehouseId(item.hub_id),
            name: item.name,
            time: item.time || '',
            lastMessage: item.last_message || '',
            status: item.status || 'Offline',
            phone: item.phone || null,
            muted: item.muted || false,
            messages: (item.messages || []).map((m) => ({
                id: String(m.id),
                text: m.text,
                sender: m.sender,
                time: m.time,
            })),
        }))
        return chats.value
    }

    async function sendChatMessage(threadId, text) {
        const updated = await apiRequest(`/logistics/chats/${threadId}/messages`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ text, sender: 'me' }),
        })
        const mappedMessages = (updated.messages || []).map((m) => ({
            id: String(m.id),
            text: m.text,
            sender: m.sender,
            time: m.time,
        }))
        // Sync local state
        const idx = chats.value.findIndex((c) => c.id === String(threadId))
        if (idx !== -1) {
            chats.value[idx].messages = mappedMessages
            chats.value[idx].lastMessage = updated.last_message || text
            chats.value[idx].time = updated.time || 'Just now'
        }
        return { messages: mappedMessages }
    }

    async function createChatThread(name, phone = null, warehouseId = null) {
        const created = await apiRequest('/logistics/chats', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ name, phone, warehouse_id: warehouseId }),
        })
        const mappedThread = {
            id: String(created.id),
            hubId: asWarehouseId(created.hub_id),
            name: created.name,
            time: created.time || 'Just now',
            lastMessage: created.last_message || '',
            status: created.status || 'Online',
            phone: created.phone || null,
            muted: false,
            messages: (created.messages || []).map((m) => ({
                id: String(m.id),
                text: m.text,
                sender: m.sender,
                time: m.time,
            })),
        }
        const existingIdx = chats.value.findIndex((chat) => chat.id === String(created.id))
        if (existingIdx !== -1) {
            chats.value[existingIdx] = mappedThread
        } else {
            chats.value.unshift(mappedThread)
        }
        return mappedThread
    }

    async function ensureManagerDriverThread(driver) {
        if (!driver?.name) throw new Error('Driver context is required')

        const existing = findManagerDriverThread(driver)
        if (existing) return existing

        const created = await createChatThread(
            getManagerDriverThreadName(driver),
            driver.phone || null,
            driver.hubId || driver.warehouseId || null,
        )
        return created
    }

    async function deleteChatThread(threadId) {
        await apiRequest(`/logistics/chats/${threadId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        chats.value = chats.value.filter((c) => c.id !== String(threadId))
    }

    async function muteChatThread(threadId, muted) {
        const updated = await apiRequest(`/logistics/chats/${threadId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ muted }),
        })
        const chat = chats.value.find((c) => c.id === String(threadId))
        if (chat) chat.muted = updated.muted
    }

    return { getManagerDriverThreadName, findManagerDriverThread, fetchWmChats, sendChatMessage, createChatThread, ensureManagerDriverThread, deleteChatThread, muteChatThread }
}
