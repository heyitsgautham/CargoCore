// The pick list modal: loading a wave's items, confirming picks by button or scan,
// printing the list and moving the wave on once every item is picked.
import { ref, computed, watch } from 'vue'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import {
    formatLocation,
    getPickItemKey,
    getItemRequiredQuantity,
    getItemRemainingQuantity,
} from './pickingFormat'
import { canConfirmPick, mergePickListWithProgress } from './pickingBoard'
import * as api from './pickingApi'

export function usePickList({ token, getWarehouseId, flashAction, openScanner, lastGlobalScan, runWaveAction }) {
    const { openSlipWithData } = useSlipPrinter()
    const scannerTargetSku = ref('')
    const scannerTargetItemKey = ref('')
    const showPickListModal = ref(false)
    const selectedWave = ref(null)
    const pickListItems = ref([])
    const pickListLoading = ref(false)

    const allPickListItemsComplete = computed(() =>
        pickListItems.value.length > 0 && pickListItems.value.every(item => item.is_complete)
    )
    const pickListActionDisabled = computed(() => {
        if (pickListLoading.value || !selectedWave.value) return true
        if (selectedWave.value.status === 'PICKING') return !allPickListItemsComplete.value
        return false
    })

    function requestItemScan(item) {
        if (!canConfirmPick(selectedWave.value, item)) {
            flashAction(selectedWave.value?.status === 'PICKING'
                ? `${item.sku} is already fully confirmed`
                : 'Start picking before confirming items')
            return
        }

        if (!openScanner) {
            flashAction('Scanner is unavailable in this layout')
            return
        }

        scannerTargetSku.value = (item.scan_code || item.sku || '').toLowerCase()
        scannerTargetItemKey.value = getPickItemKey(item)
        openScanner('scan')
    }

    watch(lastGlobalScan, async (scanValue) => {
        if (!scanValue || !scannerTargetSku.value) return

        const scannedCode = String(scanValue).trim().toLowerCase()
        const item = pickListItems.value.find(candidate => getPickItemKey(candidate) === scannerTargetItemKey.value)

        if (item && scannedCode === scannerTargetSku.value) {
            await toggleItemPicked(item, 'scan')
        } else {
            flashAction(`Scanned code "${scanValue}" does not match ${scannerTargetSku.value.toUpperCase()}`)
        }

        scannerTargetSku.value = ''
        scannerTargetItemKey.value = ''
        if (lastGlobalScan?.value !== undefined) {
            lastGlobalScan.value = null
        }
    })

    async function openPickList(wave) {
        selectedWave.value = wave
        showPickListModal.value = true
        pickListLoading.value = true
        pickListItems.value = []

        try {
            const [items, progress] = await Promise.all([
                api.fetchPickListItems(token(), wave.rawId),
                api.fetchPickProgress(token(), getWarehouseId(), wave.rawId),
            ])
            pickListItems.value = mergePickListWithProgress(items, progress?.items || [], wave.status)
        } catch (error) {
            console.error('Error fetching pick list:', error)
            flashAction(error.message || 'Unable to load pick list')
        } finally {
            pickListLoading.value = false
        }
    }

    async function toggleItemPicked(item, source = 'button') {
        if (!selectedWave.value) return

        const warehouseId = getWarehouseId()
        if (!warehouseId) return

        if (selectedWave.value.status !== 'PICKING') {
            flashAction('Start picking before confirming items')
            return
        }

        const quantityToConfirm = getItemRemainingQuantity(item)
        if (quantityToConfirm <= 0) {
            flashAction(`${item.sku} is already fully confirmed`)
            return
        }

        item.syncing = true

        try {
            const data = await api.confirmPickItem(token(), warehouseId, selectedWave.value.rawId, {
                sku: item.sku,
                quantity_picked: quantityToConfirm,
                location: item.location_path || formatLocation(item),
                notes: null
            })
            item.quantity_required = data.quantity_required ?? getItemRequiredQuantity(item)
            item.required_quantity = data.quantity_required ?? getItemRequiredQuantity(item)
            item.quantity_picked = data.quantity_picked
            item.picked_by = data.picked_by
            item.picker_name = data.picker_name
            item.picked_record_id = data.id
            item.is_complete = Boolean(data.is_complete)
            item.picked = item.is_complete
            item.location_path = data.location || item.location_path
            flashAction(source === 'scan' ? `${item.sku} scan confirmed` : `${item.sku} marked picked`)
        } catch (error) {
            console.error('Error confirming pick:', error)
            flashAction(error.message || 'Unable to confirm pick')
        } finally {
            item.syncing = false
        }
    }


    /** Per-wave "Print" button inside the pick list modal */
    async function printPickList() {
        const items = pickListItems.value.map(item => ({
            ...item,
            location_path: item.location_path || formatLocation(item),
        }))
        await openSlipWithData('digitalPickList', { wave: selectedWave.value, items })
    }

    async function completePickList() {
        if (!selectedWave.value) return

        const warehouseId = getWarehouseId()
        if (!warehouseId) return

        try {
            if (selectedWave.value.status === 'PICKING') {
                const progress = await api.fetchPickProgress(token(), warehouseId, selectedWave.value.rawId)
                if (progress?.items) {
                    pickListItems.value = mergePickListWithProgress(
                        pickListItems.value,
                        progress.items,
                        selectedWave.value.status
                    )
                }

                if (progress && !progress.is_complete) {
                    flashAction(`${progress.picked_items}/${progress.total_items} items confirmed. Complete all items first.`, 3000)
                    return
                }

                if (!progress && !allPickListItemsComplete.value) {
                    flashAction('Please mark all items as picked before completing')
                    return
                }
            }

            const actionSucceeded = await runWaveAction(selectedWave.value)
            if (actionSucceeded) {
                showPickListModal.value = false
            }
        } catch (error) {
            console.error('Error checking pick progress:', error)
            flashAction(error.message || 'Unable to complete pick list', 3000)
        }
    }

    return {
        showPickListModal,
        selectedWave,
        pickListItems,
        pickListLoading,
        pickListActionDisabled,
        requestItemScan,
        openPickList,
        toggleItemPicked,
        printPickList,
        completePickList,
    }
}
