<template>
    <div class="archived-shell">
        <div class="ambient-grid" aria-hidden="true"></div>
        <div class="ambient-orb ambient-orb--left" aria-hidden="true"></div>
        <div class="ambient-orb ambient-orb--right" aria-hidden="true"></div>

        <div v-if="isChecking" class="status-overlay">
            <div class="status-spinner"></div>
            <p>Checking live hub access...</p>
        </div>

        <div v-else class="archived-layout">
            <section class="hero-copy">
                <div class="topline">
                    <span class="status-pill">Hub Archived</span>
                    <span class="role-pill">{{ roleLabel }}</span>
                </div>

                <h1>{{ hubName }} is paused for live operations.</h1>
                <p class="lead">
                    {{ roleLabel }} access is temporarily locked because this hub has been archived by Logistics
                    Manager. The dashboard, live workflows, and new assignments stay offline until the hub is restored.
                </p>

                <div class="hub-meta">
                    <div class="meta-card">
                        <span class="meta-label">Hub</span>
                        <strong>{{ hubName }}</strong>
                    </div>
                    <div class="meta-card">
                        <span class="meta-label">Current State</span>
                        <strong>{{ hubStatus }}</strong>
                    </div>
                    <div class="meta-card">
                        <span class="meta-label">Access Scope</span>
                        <strong>{{ roleLabel }}</strong>
                    </div>
                </div>

                <div class="action-row">
                    <button class="primary-btn" @click="refreshAccess">Check Again</button>
                    <button class="secondary-btn" @click="returnToLogin">Back to Login</button>
                </div>

                <p class="support-note">
                    Access will return automatically after Logistics Manager restores this hub and reopens operations.
                </p>
            </section>

            <section class="animation-stage" aria-hidden="true">
                <div class="signal-stack">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>

                <div class="shutdown-ring shutdown-ring--outer"></div>
                <div class="shutdown-ring shutdown-ring--inner"></div>

                <div class="warehouse-core">
                    <div class="core-roof"></div>
                    <div class="core-body">
                        <div class="scanner-beam"></div>
                        <div class="bay bay--left"></div>
                        <div class="bay bay--center"></div>
                        <div class="bay bay--right"></div>
                    </div>
                </div>

                <div class="route-network">
                    <span class="route-line route-line--one"></span>
                    <span class="route-line route-line--two"></span>
                    <span class="route-line route-line--three"></span>
                    <span class="route-node route-node--one"></span>
                    <span class="route-node route-node--two"></span>
                    <span class="route-node route-node--three"></span>
                </div>

                <div class="crate-lane">
                    <div class="crate crate--one"></div>
                    <div class="crate crate--two"></div>
                    <div class="crate crate--three"></div>
                    <div class="crate crate--four"></div>
                    <div class="crate crate--five"></div>
                </div>

                <div class="status-marquee">
                    <span>Signals suspended</span>
                    <span>Routing frozen</span>
                    <span>Hub in archive state</span>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isChecking = ref(true)

const isDispatcherRoute = computed(() => route.path.startsWith('/dispatcher'))
const roleLabel = computed(() => (isDispatcherRoute.value ? 'Dispatcher' : 'Warehouse Manager'))
const archivedRoute = computed(() => (isDispatcherRoute.value ? '/dispatcher/archived-access' : '/warehouse/archived-access'))
const dashboardRoute = computed(() => (isDispatcherRoute.value ? '/dispatcher/dashboard' : '/warehouse/dashboard'))
const hubName = computed(() =>
    authStore.assignedHubAccess?.warehouseName
    || authStore.currentUser?.warehouse_name
    || 'Assigned Hub'
)
const hubStatus = computed(() => authStore.currentUser?.warehouse_status || 'Archived')

async function verifyArchivedAccess(force = true) {
    if (!authStore.isAuthenticated) {
        router.replace('/login')
        return
    }

    isChecking.value = true
    const access = await authStore.ensureHubOperationalAccess(force)

    if (!access?.isArchived) {
        router.replace(dashboardRoute.value)
        return
    }

    if (route.path !== archivedRoute.value) {
        router.replace(archivedRoute.value)
        return
    }

    isChecking.value = false
}

function refreshAccess() {
    verifyArchivedAccess(true)
}

function returnToLogin() {
    const loginPath = authStore.logout()
    router.replace(loginPath)
}

onMounted(() => {
    verifyArchivedAccess(true)
})
</script>

<style scoped src="./styles/HubArchivedAccess.layout.css"></style>
<style scoped src="./styles/HubArchivedAccess.scene.css"></style>
