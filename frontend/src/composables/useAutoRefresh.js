import { ref } from 'vue'

/**
 * Re-run `refresh` every `seconds` while enabled, with a countdown for the UI.
 * `isBusy` skips a tick when the previous load is still running.
 * Call stop() when the owning component unmounts.
 */
export function useAutoRefresh(refresh, { seconds = 30, isBusy = () => false } = {}) {
    const enabled = ref(true)
    const countdown = ref(seconds)
    let refreshTimer = null
    let countdownTimer = null

    function stop() {
        if (refreshTimer) {
            clearInterval(refreshTimer)
            refreshTimer = null
        }
        if (countdownTimer) {
            clearInterval(countdownTimer)
            countdownTimer = null
        }
    }

    function start() {
        stop()
        countdown.value = seconds
        countdownTimer = setInterval(() => {
            countdown.value--
            if (countdown.value <= 0) countdown.value = seconds
        }, 1000)
        refreshTimer = setInterval(async () => {
            if (!isBusy()) await refresh()
            countdown.value = seconds
        }, seconds * 1000)
    }

    function toggle() {
        enabled.value = !enabled.value
        if (enabled.value) start()
        else stop()
    }

    return { enabled, countdown, start, stop, toggle }
}
