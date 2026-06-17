import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  deleteContactSubmission,
  fetchContactSubmissions,
  replyContactSubmission,
  submitPublicContactForm,
  updateContactSubmission,
} from '@/utils/aiApi'

export const useContactStore = defineStore('contact', () => {
  const submissions = ref([])
  const agents = ref([])
  const loading = ref(false)
  const error = ref('')
  const initialized = ref(false)

  const stats = computed(() => ({
    total: submissions.value.length,
    new: submissions.value.filter((item) => item.status === 'new').length,
    inProgress: submissions.value.filter((item) => item.status === 'in_progress').length,
    resolved: submissions.value.filter((item) => item.status === 'resolved').length,
    urgent: submissions.value.filter((item) => item.priority === 'urgent').length,
  }))

  async function load(force = false) {
    if (initialized.value && !force) return
    loading.value = true
    error.value = ''
    try {
      const response = await fetchContactSubmissions()
      submissions.value = response.submissions || []
      agents.value = response.agents || []
      initialized.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load contact submissions'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    await load(true)
  }

  async function submit(form) {
    const created = await submitPublicContactForm({
      name: form.name ?? '',
      email: form.email ?? '',
      phone: form.phone ?? '',
      category: form.category ?? 'general',
      subject: form.subject ?? 'General Inquiry',
      priority: form.priority ?? 'medium',
      message: form.message ?? '',
    })

    submissions.value.unshift(created)
    initialized.value = true
    return created.reference_code
  }

  async function update(id, payload) {
    const updated = await updateContactSubmission(id, payload)
    const index = submissions.value.findIndex((item) => item.id === updated.id)
    if (index === -1) {
      submissions.value.unshift(updated)
    } else {
      submissions.value.splice(index, 1, updated)
    }
    return updated
  }

  async function reply(id, message) {
    const updated = await replyContactSubmission(id, message)
    const index = submissions.value.findIndex((item) => item.id === updated.id)
    if (index === -1) {
      submissions.value.unshift(updated)
    } else {
      submissions.value.splice(index, 1, updated)
    }
    return updated
  }

  async function remove(id) {
    await deleteContactSubmission(id)
    submissions.value = submissions.value.filter((item) => item.id !== id)
  }

  async function clearResolved() {
    const resolvedIds = submissions.value
      .filter((item) => item.status === 'resolved')
      .map((item) => item.id)

    for (const id of resolvedIds) {
      await deleteContactSubmission(id)
    }

    submissions.value = submissions.value.filter((item) => item.status !== 'resolved')
  }

  return {
    submissions,
    agents,
    loading,
    error,
    initialized,
    stats,
    load,
    refresh,
    submit,
    update,
    reply,
    remove,
    clearResolved,
  }
})
