<template>
    <transition name="slide-left">
    <div v-show="show" class="w-80 bg-white dark:bg-card-dark border-r border-gray-200 dark:border-white/5 flex flex-col z-10 glass-panel flex-shrink-0">
        <div class="p-4 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">{{ showAllDrivers ? 'All Drivers' : 'Available Drivers' }} ({{ filteredDrivers.length }})</h3>
            <button @click="showAllDrivers = !showAllDrivers" class="text-xs text-primary hover:underline">{{ showAllDrivers ? 'Show Available' : 'View All' }}</button>
        </div>

        <div class="p-3 bg-gray-50 dark:bg-white/5">
            <div class="relative">
                <span
                    class="material-symbols-outlined absolute left-2 top-1.5 text-gray-500 text-[18px]">search</span>
                <input v-model="driverSearch" type="text" placeholder="Search driver..."
                    class="w-full bg-gray-100 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-md py-1.5 pl-8 pr-3 text-xs text-gray-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
            </div>
        </div>

        <div class="flex-1 overflow-y-auto no-scrollbar p-2 space-y-2"
            @dragover.prevent="$emit('panel-dragover', $event)" @drop="$emit('panel-drop', $event)">
            <!-- Driver Card -->
            <div v-for="driver in filteredDrivers" :key="driver.id"
                @click="$emit('select', driver)"
                :class="[
                    selectedDriver?.id === driver.id ? 'border-primary/50 bg-primary/5' : 'border-gray-200/60 dark:border-transparent',
                    dragOverDriver === driver.id ? 'ring-2 ring-primary/50 scale-[1.02]' : '',
                    driver.isAssignable ? 'hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-300 dark:hover:border-white/10 cursor-pointer' : 'opacity-70 cursor-not-allowed'
                ]"
                class="p-3 rounded-lg bg-gray-50 dark:bg-white/5 border transition-all group"
                @dragover.prevent="$emit('driver-dragover', $event, driver)" @dragleave="$emit('driver-dragleave')"
                @drop.stop="$emit('driver-drop', $event, driver)">
                <DriverCardBody :driver="driver" @view="$emit('view', $event)" @chat="$emit('chat', $event)" />
            </div>
        </div>
    </div>
    </transition>
</template>

<script setup>
import DriverCardBody from './DriverCardBody.vue'

const showAllDrivers = defineModel('showAll', { type: Boolean, required: true })
const driverSearch = defineModel('search', { type: String, required: true })

defineProps({
    show: { type: Boolean, default: false },
    filteredDrivers: { type: Array, required: true },
    selectedDriver: { type: Object, default: null },
    dragOverDriver: { type: [String, Number], default: null },
})

defineEmits(['select', 'panel-dragover', 'panel-drop', 'driver-dragover', 'driver-dragleave', 'driver-drop', 'view', 'chat'])
</script>

<style scoped>
.slide-left-enter-active, .slide-left-leave-active {
    transition: width 0.3s ease, opacity 0.3s ease;
    overflow: hidden;
}
.slide-left-enter-from, .slide-left-leave-to {
    width: 0 !important;
    opacity: 0;
}
</style>
