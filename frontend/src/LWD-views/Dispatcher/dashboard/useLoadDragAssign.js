// Dragging a pending load onto a driver card in the roster to assign it.
import { ref } from 'vue'

export function useLoadDragAssign({ store, isDriverAssignable }) {
    const draggingLoad = ref(null)
    const dragOverDriver = ref(null)
    const dragAssignToast = ref('')

    function onDragStart(event, load) {
        draggingLoad.value = load
        event.dataTransfer.effectAllowed = 'move'
        event.dataTransfer.setData('text/plain', load.id)
    }

    function onDragEnd() {
        draggingLoad.value = null
        dragOverDriver.value = null
    }

    function onDriverPanelDragOver(event) {
        event.dataTransfer.dropEffect = 'move'
    }

    function onDriverDragOver(event, driver) {
        if (!isDriverAssignable(driver)) {
            event.dataTransfer.dropEffect = 'none'
            dragOverDriver.value = null
            return
        }
        event.dataTransfer.dropEffect = 'move'
        dragOverDriver.value = driver.id
    }

    function onDropOnDriverPanel(_event) {
        dragOverDriver.value = null
    }

    async function onDropOnDriver(event, driver) {
        event.preventDefault()
        dragOverDriver.value = null
        if (!draggingLoad.value) return
        if (!isDriverAssignable(driver)) {
            dragAssignToast.value = `${driver.name} is already assigned or unavailable`
            draggingLoad.value = null
            setTimeout(() => { dragAssignToast.value = '' }, 2500)
            return
        }
        const load = draggingLoad.value
        draggingLoad.value = null
        const ok = await store.assignOrder(load.id, driver.id)
        if (ok) {
            dragAssignToast.value = `${load.id} → ${driver.name}`
            setTimeout(() => { dragAssignToast.value = '' }, 2500)
        } else {
            dragAssignToast.value = `Failed to assign ${load.id}`
            setTimeout(() => { dragAssignToast.value = '' }, 2500)
        }
    }

    return {
        draggingLoad,
        dragOverDriver,
        dragAssignToast,
        onDragStart,
        onDragEnd,
        onDriverPanelDragOver,
        onDriverDragOver,
        onDropOnDriverPanel,
        onDropOnDriver,
    }
}
