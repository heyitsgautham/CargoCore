import { defineStore } from 'pinia'
import { useToast } from '@/composables/useToast'

export const useUiStore = defineStore('ui', () => {
    const toast = useToast()

    function showToast(message, type = 'info', _duration = 3500) {
        const fn = toast[type] ?? toast.info
        fn(message)
    }

    return { showToast }
})
