<template>
  <aside
    class="w-64 h-screen bg-surface-light dark:bg-card-darker border-r border-gray-200 dark:border-white/5 flex flex-col fixed left-0 top-0 z-50 transition-transform duration-300 transform lg:translate-x-0"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
  >
    <div class="h-16 flex items-center justify-between px-6 border-b border-gray-200 dark:border-white/5">
      <div class="flex items-center gap-3">
        <img src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg" alt="Cargo Core Logo" class="h-8 w-8 rounded-md object-cover">
        <div class="text-xl font-bold text-primary">Cargo-Core</div>
      </div>
      <button class="lg:hidden text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white" @click="$emit('close')">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <nav class="flex-1 overflow-y-auto py-4 no-scrollbar">
      <ul class="space-y-1 px-3">
        <li v-for="item in menuItems" :key="item.route">
          <component
            :is="'router-link'"
            :to="item.route"
            class="w-full flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group relative text-left"
            :class="$route.path === item.route ? 'bg-green-500/10 text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'"
          >
            <div v-if="$route.path === item.route" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-green-500 rounded-r-full" />
            <span class="material-symbols-outlined mr-3 text-[20px]" :class="$route.path === item.route ? 'text-green-500' : 'text-gray-500 group-hover:text-gray-900 dark:group-hover:text-white'">{{ item.icon }}</span>
            <span class="text-sm font-medium">{{ item.label }}</span>
          </component>
        </li>
      </ul>

      <div class="mt-8 px-4">
        <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Move Metrics</div>
        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="metric in moveMetrics"
            :key="metric.id"
            class="bg-gray-100 dark:bg-white/5 rounded p-2 text-center border border-gray-200 dark:border-white/5"
          >
            <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">{{ metric.name }}</div>
            <div class="font-bold mt-1" :class="metric.color">{{ metric.value }}</div>
          </div>
        </div>
      </div>
    </nav>

    <div
      class="p-4 border-t border-gray-200 dark:border-white/5 relative"
      @mouseenter="isMenuOpen = true"
      @mouseleave="isMenuOpen = false"
    >
      <transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="transform scale-95 opacity-0 translate-y-2"
        enter-to-class="transform scale-100 opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="transform scale-100 opacity-100 translate-y-0"
        leave-to-class="transform scale-95 opacity-0 translate-y-2"
      >
        <div
          v-if="isMenuOpen"
          class="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-card-darker rounded-xl shadow-xl border border-gray-200 dark:border-white/10 overflow-hidden z-50"
        >
          <div class="py-1">
            <button
              class="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3 transition-colors"
              @click="showProfileModal = true"
            >
              <span class="material-symbols-outlined text-[20px] text-green-500 dark:text-green-400">person</span>
              Profile
            </button>

            <button
              class="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3 transition-colors"
              @click="showIdCardModal = true"
            >
              <span class="material-symbols-outlined text-[20px] text-green-500 dark:text-green-400">badge</span>
              Customer ID Card
            </button>

            <div class="w-full px-4 py-2.5 flex items-center gap-3">
              <span class="material-symbols-outlined text-[20px] text-green-500 dark:text-green-400">
                {{ isDark ? 'dark_mode' : 'light_mode' }}
              </span>
              <span class="text-sm text-gray-700 dark:text-gray-200 flex-1">Appearance</span>
              <ThemeToggle />
            </div>

            <div class="border-t border-gray-200 dark:border-white/5 my-1"></div>

            <button
              class="w-full text-left px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors"
              @click="showLogoutConfirm = true"
            >
              <span class="material-symbols-outlined text-[20px]">logout</span>
              Logout
            </button>
          </div>
        </div>
      </transition>

      <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 cursor-pointer transition-colors relative z-10">
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
          <span class="font-bold text-xs text-white">{{ store.userInitials }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ store.user.name }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-500 truncate">Individual User</div>
        </div>
        <span class="material-symbols-outlined text-gray-500 dark:text-gray-400">more_vert</span>
      </div>
    </div>
  </aside>

  <Teleport to="body">
    <BaseModal :isOpen="showProfileModal" @close="showProfileModal = false">
      <template #title>My Profile</template>
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-2xl font-bold text-white border-2 border-green-500/30">
            {{ store.userInitials }}
          </div>
          <div>
            <h4 class="text-xl font-bold text-white">{{ store.user.name }}</h4>
            <p class="text-gray-400">Individual User</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Email</div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">{{ store.user.email }}</div>
          </div>
          <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Phone</div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">{{ store.user.phone }}</div>
          </div>
          <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg md:col-span-2">
            <div class="text-xs text-gray-500 mb-1">Address</div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">{{ store.user.address }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          class="px-4 py-2 text-gray-300 hover:text-white transition-colors"
          @click="showProfileModal = false"
        >
          Close
        </button>
      </template>
    </BaseModal>
  </Teleport>

  <Teleport to="body">
    <BaseModal :isOpen="showIdCardModal" @close="showIdCardModal = false">
      <template #title>Customer ID Card</template>
      <div class="flex justify-center w-full">
        <IdCard :employee="idCardData" />
      </div>
      <template #footer>
        <button
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          @click="showIdCardModal = false"
        >
          Close
        </button>
      </template>
    </BaseModal>
  </Teleport>

  <Teleport to="body">
    <div
      v-if="showLogoutConfirm"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      @click.self="showLogoutConfirm = false"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden border border-gray-100 dark:border-white/10 p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center">
            <span class="material-symbols-outlined text-red-500 text-2xl">logout</span>
          </div>
          <div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Confirm Logout</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Are you sure you want to sign out?</p>
          </div>
        </div>
        <div class="flex gap-3">
          <button
            class="flex-1 py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors"
            @click="showLogoutConfirm = false"
          >
            Cancel
          </button>
          <button
            class="flex-1 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl transition-colors"
            @click="handleLogout"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseModal from '@/components/BaseModal.vue'
import IdCard from '@/components/IdCard.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/authStore'
import { useIndividualStore } from '@/stores/individualStore'
import { buildIdCardProfile } from '@/utils/idCardProfile'

defineProps({ isOpen: Boolean })
defineEmits(['close'])

const router = useRouter()
const authStore = useAuthStore()
const store = useIndividualStore()

const isMenuOpen = ref(false)
const showProfileModal = ref(false)
const showIdCardModal = ref(false)
const showLogoutConfirm = ref(false)
const isDark = ref(true)
let themeObserver = null

const menuItems = [
  { label: 'Dashboard', icon: 'dashboard', route: '/individual/dashboard' },
  { label: 'Book a Move', icon: 'local_shipping', route: '/individual/book-move' },
  { label: 'My Orders', icon: 'receipt_long', route: '/individual/orders' },
  { label: 'Quotes', icon: 'request_quote', route: '/individual/quotes' },
  { label: 'AI Estimator', icon: 'auto_awesome', route: '/individual/estimator' },
  { label: 'Tracking', icon: 'gps_fixed', route: '/individual/tracking' },
  { label: 'Wallet', icon: 'account_balance_wallet', route: '/individual/wallet' },
  { label: 'Payments', icon: 'credit_card', route: '/individual/payments' },
  { label: 'Damage Report', icon: 'report', route: '/individual/damage-report' },
  { label: 'Support Chat', icon: 'support_agent', route: '/individual/support' },
  { label: 'Profile', icon: 'person', route: '/individual/profile' },
  { label: 'Settings', icon: 'settings', route: '/individual/settings' },
]

const moveMetrics = computed(() => ([
  { id: 'active', name: 'Active', value: String(store.activeOrders.length), color: 'text-blue-500' },
  { id: 'pending', name: 'Pending', value: String(store.pendingOrders.length), color: 'text-amber-500' },
  { id: 'done', name: 'Delivered', value: String(store.deliveredOrders.length), color: 'text-green-500' },
  { id: 'issues', name: 'Issues', value: String(store.damageReports.length), color: store.damageReports.length ? 'text-red-500' : 'text-green-500' },
]))

const idCardData = computed(() => buildIdCardProfile({
  user: store.user,
  role: 'INDIVIDUAL',
}))

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
  themeObserver = new MutationObserver(() => {
    isDark.value = document.documentElement.classList.contains('dark')
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  if (themeObserver) themeObserver.disconnect()
})

function handleLogout() {
  showLogoutConfirm.value = false
  isMenuOpen.value = false
  const loginPath = authStore.logout()
  router.replace(loginPath)
}
</script>
