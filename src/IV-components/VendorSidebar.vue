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
            :class="$route.path === item.route ? 'bg-blue-500/10 text-blue-500' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'"
          >
            <div v-if="$route.path === item.route" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-r-full" />
            <span class="material-symbols-outlined mr-3 text-[20px]" :class="$route.path === item.route ? 'text-blue-500' : 'text-gray-500 group-hover:text-gray-900 dark:group-hover:text-white'">{{ item.icon }}</span>
            <span class="text-sm font-medium">{{ item.label }}</span>
          </component>
        </li>
      </ul>

      <div class="mt-8 px-4">
        <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Vendor Metrics</div>
        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="metric in vendorMetrics"
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
              <span class="material-symbols-outlined text-[20px] text-blue-500 dark:text-blue-400">person</span>
              Profile
            </button>

            <button
              class="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 flex items-center gap-3 transition-colors"
              @click="showIdCardModal = true"
            >
              <span class="material-symbols-outlined text-[20px] text-blue-500 dark:text-blue-400">badge</span>
              Business ID Card
            </button>

            <div class="w-full px-4 py-2.5 flex items-center gap-3">
              <span class="material-symbols-outlined text-[20px] text-blue-500 dark:text-blue-400">
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
        <div class="w-9 h-9 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
          <span class="font-bold text-xs text-blue-600 dark:text-blue-400">{{ vendorInitials }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ vendorName }}</div>
          <div class="text-xs text-gray-500 dark:text-gray-500 truncate">Vendor Account</div>
        </div>
        <span class="material-symbols-outlined text-gray-500 dark:text-gray-400">more_vert</span>
      </div>
    </div>
  </aside>

  <Teleport to="body">
    <BaseModal :isOpen="showProfileModal" @close="showProfileModal = false">
      <template #title>Vendor Profile</template>
      <div class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-20 h-20 rounded-xl bg-blue-500/20 border-2 border-blue-500/30 flex items-center justify-center text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ vendorInitials }}
          </div>
          <div>
            <h4 class="text-xl font-bold text-white">{{ vendorName }}</h4>
            <p class="text-gray-400">Vendor Account</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Email</div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">{{ vendorEmail }}</div>
          </div>
          <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
            <div class="text-xs text-gray-500 mb-1">Credit Balance</div>
            <div class="font-medium text-sm text-gray-900 dark:text-white">Rs. {{ store.creditBalance.toLocaleString() }}</div>
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
      <template #title>Business ID Card</template>
      <div class="flex justify-center w-full">
        <IdCard :employee="vendorCardData" />
      </div>
      <template #footer>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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
import { useVendorStore } from '@/stores/vendorStore'
import { buildIdCardProfile } from '@/utils/idCardProfile'

defineProps({ isOpen: Boolean })
defineEmits(['close'])

const router = useRouter()
const authStore = useAuthStore()
const store = useVendorStore()

const isMenuOpen = ref(false)
const showProfileModal = ref(false)
const showIdCardModal = ref(false)
const showLogoutConfirm = ref(false)
const isDark = ref(true)
let themeObserver = null

const menuItems = [
  { label: 'Dashboard', icon: 'dashboard', route: '/vendor/dashboard' },
  { label: 'Create Shipment', icon: 'add_box', route: '/vendor/create-shipment' },
  { label: 'Orders', icon: 'list_alt', route: '/vendor/orders' },
  { label: 'Recurring Orders', icon: 'update', route: '/vendor/recurring' },
  { label: 'Bulk Upload', icon: 'upload_file', route: '/vendor/bulk-upload' },
  { label: 'Shipment Tracking', icon: 'local_shipping', route: '/vendor/tracking' },
  { label: 'Wallet', icon: 'account_balance_wallet', route: '/vendor/wallet' },
  { label: 'Invoices', icon: 'receipt', route: '/vendor/invoices' },
  { label: 'Analytics', icon: 'analytics', route: '/vendor/analytics' },
  { label: 'Support', icon: 'support_agent', route: '/vendor/support' },
]

const currentUser = computed(() => authStore.currentUser || JSON.parse(localStorage.getItem('auth_user') || 'null'))
const vendorName = computed(() => currentUser.value?.name || currentUser.value?.company_name || 'Vendor')
const vendorEmail = computed(() => currentUser.value?.email || currentUser.value?.business_email || 'support@cargocore.local')
const vendorInitials = computed(() => vendorName.value.split(' ').map((part) => part[0]).join('').toUpperCase().slice(0, 2))

const vendorMetrics = computed(() => ([
  { id: 'active', name: 'Active', value: String(store.activeShipments.length), color: 'text-blue-500' },
  { id: 'pending', name: 'Pending', value: String(store.pendingShipments.length), color: 'text-amber-500' },
  { id: 'done', name: 'Delivered', value: String(store.deliveredShipments.length), color: 'text-green-500' },
  { id: 'issues', name: 'Overdue', value: String(store.overdueInvoices.length), color: store.overdueInvoices.length ? 'text-red-500' : 'text-green-500' },
]))

const vendorCardData = computed(() => buildIdCardProfile({
  user: currentUser.value,
  role: 'VENDOR',
  name: vendorName.value,
  email: vendorEmail.value,
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
