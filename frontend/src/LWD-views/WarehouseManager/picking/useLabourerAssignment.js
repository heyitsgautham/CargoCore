// The assign labourers modal for on-hold waves that need more hands.
import { ref, computed } from 'vue'
import * as api from './pickingApi'

export function useLabourerAssignment({ token, getWarehouseId, labourers, fetchLabourers, actionToast, flashAction, refresh }) {
    const labourersLoading = ref(false)
    const assigningPicker = ref(false)

    // Multi-Labourer assignment modal state
    const showMultiLabourerModal = ref(false)
    const multiLabourerWave = ref(null)
    const selectedLabourers = ref([])

    const availableLabourersForMulti = computed(() => labourers.value.filter(l => l.is_active && !l.assigned_order_id))

    function openAssignLabourers(wave) {
        multiLabourerWave.value = wave
        selectedLabourers.value = wave.laborAssigned ? [...wave.laborAssigned] : []
        showMultiLabourerModal.value = true
        fetchAvailableLabourersForMulti()
    }

    async function fetchAvailableLabourersForMulti() {
        labourersLoading.value = true
        const warehouseId = getWarehouseId()

        if (!warehouseId) {
            labourersLoading.value = false
            return
        }

        try {
            await fetchLabourers(warehouseId)
        } finally {
            labourersLoading.value = false
        }
    }

    function toggleLabourerSelection(labourer) {
        const idx = selectedLabourers.value.findIndex(l => l.id === labourer.id)
        if (idx >= 0) {
            selectedLabourers.value.splice(idx, 1)
        } else {
            selectedLabourers.value.push(labourer)
        }
    }

    async function assignMultipleLabourers() {
        if (!multiLabourerWave.value || selectedLabourers.value.length < (multiLabourerWave.value.laborRequired || 1)) {
            return
        }

        assigningPicker.value = true

        try {
            for (const labourer of selectedLabourers.value) {
                if (!(await api.assignLabourer(token(), labourer.id, multiLabourerWave.value.rawId))) {
                    console.warn(`Failed to assign labourer ${labourer.id}`)
                }
            }

            showMultiLabourerModal.value = false
            actionToast.value = `${selectedLabourers.value.length} labourer(s) assigned to ${multiLabourerWave.value.id}`
            await refresh()
            setTimeout(() => { actionToast.value = '' }, 2500)
        } catch (error) {
            console.error('Error assigning labourers:', error)
            flashAction(error.message || 'Unable to assign labourers')
        } finally {
            assigningPicker.value = false
        }
    }

    return {
        labourersLoading,
        assigningPicker,
        showMultiLabourerModal,
        multiLabourerWave,
        selectedLabourers,
        availableLabourersForMulti,
        openAssignLabourers,
        toggleLabourerSelection,
        assignMultipleLabourers,
    }
}
