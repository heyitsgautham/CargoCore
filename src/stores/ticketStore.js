import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { fetchTickets, createTicket, updateTicket, replyTicket, deleteTicket } from '@/utils/aiApi'

export const useTicketStore = defineStore('ticket', () => {
  const tickets = ref([])
  const agents = ref([])
  const loading = ref(false)
  const error = ref('')
  const initialized = ref(false)

  const stats = computed(() => ({
    total: tickets.value.length,
    new: tickets.value.filter(t => t.status === 'new').length,
    in_progress: tickets.value.filter(t => t.status === 'in_progress').length,
    resolved: tickets.value.filter(t => t.status === 'resolved').length,
    urgent: tickets.value.filter(t => t.priority === 'urgent').length,
  }))

  const newTickets = computed(() => tickets.value.filter(t => t.status === 'new'))
  const inProgressTickets = computed(() => tickets.value.filter(t => t.status === 'in_progress'))
  const resolvedTickets = computed(() => tickets.value.filter(t => t.status === 'resolved'))

  async function load(force = false) {
    if (initialized.value && !force) return
    loading.value = true
    error.value = ''
    try {
      const response = await fetchTickets()
      tickets.value = response.tickets || []
      agents.value = response.agents || []
      initialized.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load tickets'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const created = await createTicket(payload)
    tickets.value.unshift(created)
    return created
  }

  async function update(id, payload) {
    const updated = await updateTicket(id, payload)
    const idx = tickets.value.findIndex(t => t.id === id)
    if (idx !== -1) tickets.value.splice(idx, 1, updated)
    else tickets.value.unshift(updated)
    return updated
  }

  async function remove(id) {
    await deleteTicket(id)
    tickets.value = tickets.value.filter(t => t.id !== id)
  }

  async function reply(id, message) {
    const updated = await replyTicket(id, message)
    const idx = tickets.value.findIndex(t => t.id === id)
    if (idx !== -1) tickets.value.splice(idx, 1, updated)
    else tickets.value.unshift(updated)
    return updated
  }

  return {
    tickets,
    agents,
    loading,
    error,
    initialized,
    stats,
    newTickets,
    inProgressTickets,
    resolvedTickets,
    load,
    create,
    update,
    reply,
    remove,
  }
})
