/**
 * Staff and vendor accounts: create, edit, deactivate, delete and vendor approval.
 */

import { apiRequest, authHeaders } from './api'
import {
    asStringId,
    asWarehouseId,
    normalizeDriverLoginId,
    normalizeDriverPin,
    persistCredentialCache,
    roleApiValue,
    roleLabel,
} from './mappers'

export function useLogisticUsers({ users, credentialCache, refresh }) {
    function normalizeUserRecord(user) {
        const cachedCredentials = credentialCache.value[String(user.email || '').toLowerCase()] || null
        return {
            id: asStringId(user.id),
            hubId: asWarehouseId(user.hub_id ?? user.warehouse_id),
            name: user.name,
            email: user.email,
            role: roleLabel(user.role),
            status: user.status || (user.is_active ? 'Active' : 'Inactive'),
            lastLogin: user.last_login || '',
            username: user.username,
            password: cachedCredentials?.password || '',
            pending_payout: user.pending_payout ?? 0,
            mobile: user.mobile ?? user.phone,
            mobileVerified: user.mobile_verified ?? Boolean(user.phone || user.mobile),
            emailVerified: user.email_verified ?? true,
            avatar: user.avatar,
            approvalStatus: user.approval_status || 'APPROVED',
            approvalNote: user.approval_note || '',
            approvalReviewedAt: user.approval_reviewed_at || '',
            companyName: user.company_name || '',
            taxId: user.tax_id || '',
            contactPerson: user.contact_person || '',
            businessEmail: user.business_email || '',
            businessPhone: user.business_phone || '',
            submittedAt: user.submitted_at || user.created_at || '',
        }
    }

    function upsertUserRecord(user) {
        const mappedUser = normalizeUserRecord(user)
        const existingIndex = users.value.findIndex((item) => item.id === mappedUser.id)
        const existingUser = existingIndex === -1 ? null : users.value[existingIndex]
        const mergedUser = existingUser ? {
            ...existingUser,
            ...mappedUser,
            avatar: mappedUser.avatar || existingUser.avatar,
            lastLogin: mappedUser.lastLogin || existingUser.lastLogin,
            pending_payout: user.pending_payout ?? existingUser.pending_payout,
            submittedAt: mappedUser.submittedAt || existingUser.submittedAt,
        } : mappedUser
        if (existingIndex === -1) {
            users.value.unshift(mergedUser)
        } else {
            users.value.splice(existingIndex, 1, mergedUser)
        }
        return mergedUser
    }

    async function addUser(userData) {
        const apiRole = roleApiValue(userData.role)
        const isDriver = apiRole === 'DRIVER'
        const driverId = normalizeDriverLoginId(userData.username, userData.email)
        const credentialValue = isDriver
            ? normalizeDriverPin(userData.password)
            : (userData.password || '12345678')
        const created = await apiRequest('/users', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                name: userData.name,
                username: isDriver ? (driverId || null) : (userData.username || null),
                email: userData.email,
                phone: userData.mobile || userData.phone || null,
                password: credentialValue,
                role: apiRole,
                warehouse_id: userData.hubId && userData.hubId !== 'all' ? userData.hubId : null,
            }),
        })

        if (userData.email && credentialValue) {
            credentialCache.value[String(userData.email).toLowerCase()] = {
                username: created?.username || (isDriver ? driverId : userData.username) || '',
                password: credentialValue,
            }
            persistCredentialCache(credentialCache.value)
        }

        await refresh()
        return created
    }

    async function updateUser(email, updates) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        const updated = await apiRequest(`/users/${user.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                name: updates.name,
                phone: updates.mobile || updates.phone || null,
                is_active: updates.status ? updates.status === 'Active' : undefined,
            }),
        })
        upsertUserRecord(updated)
    }

    async function deleteUser(email) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        await apiRequest(`/users/${user.id}`, {
            method: 'DELETE',
            headers: authHeaders(),
        })
        delete credentialCache.value[String(email).toLowerCase()]
        persistCredentialCache(credentialCache.value)
        await refresh()
    }

    async function toggleUserStatus(email) {
        const user = users.value.find((item) => item.email === email)
        if (!user) return
        const updated = await apiRequest(`/users/${user.id}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ is_active: user.status !== 'Active' }),
        })
        upsertUserRecord(updated)
    }

    async function approveVendor(userId, note = '') {
        const updated = await apiRequest(`/users/${userId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                approval_status: 'APPROVED',
                approval_note: note || null,
                is_active: true,
            }),
        })
        return upsertUserRecord(updated)
    }

    async function rejectVendor(userId, note = '') {
        const updated = await apiRequest(`/users/${userId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                approval_status: 'REJECTED',
                approval_note: note || null,
                is_active: false,
            }),
        })
        return upsertUserRecord(updated)
    }

    return { normalizeUserRecord, addUser, updateUser, deleteUser, toggleUserStatus, approveVendor, rejectVendor }
}
