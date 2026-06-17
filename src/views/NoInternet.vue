<template>
    <div
        class="fixed inset-0 overflow-hidden flex items-center justify-center p-6 text-white" style="background:#000;">
        <!-- Decorative background blobs -->
        <div class="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-20">
            <div class="w-[800px] h-[800px] bg-orange-500/30 rounded-full blur-[120px] absolute -top-40 -left-60"></div>
            <div class="w-[600px] h-[600px] bg-red-500/20 rounded-full blur-[100px] absolute -bottom-40 -right-60">
            </div>
        </div>

        <div class="max-w-xl w-full text-center relative z-10 px-4">

            <!-- Eyes animation -->
            <div class="flex justify-center mb-4">
                <span class="loader"></span>
            </div>

            <!-- Signal bars + slash -->
            <div class="flex justify-center mb-6">
                <div class="signal-wrap relative w-36 h-16 flex items-end justify-center gap-[6px]">
                    <div :class="['signal-bar bar1', isOnline ? 'online' : '']"></div>
                    <div :class="['signal-bar bar2', isOnline ? 'online' : '']"></div>
                    <div :class="['signal-bar bar3', isOnline ? 'online' : '']"></div>
                    <div :class="['signal-bar bar4', isOnline ? 'online' : '']"></div>
                    <div v-if="!isOnline" class="slash"></div>
                </div>
            </div>

            <h1 class="text-3xl sm:text-4xl font-bold mb-3 tracking-tight">
                {{ isOnline ? 'Signal Restored!' : 'No Internet Connection' }}
            </h1>

            <p class="text-lg mb-6 max-w-md mx-auto transition-colors duration-500"
                :class="isOnline ? 'text-green-400' : 'text-gray-500'">
                {{ isOnline ? 'Back online — resuming your route…' : 'Your cargo can\'t move without a signal. Waiting for connection…' }}
            </p>

            <!-- Status indicator -->
            <div class="flex items-center justify-center gap-2">
                <span
                    :class="['inline-block w-2.5 h-2.5 rounded-full transition-colors duration-500', isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse']"></span>
                <span class="text-sm font-medium transition-colors duration-500"
                    :class="isOnline ? 'text-green-500' : 'text-gray-500'">
                    {{ isOnline ? 'Redirecting…' : 'Offline' }}
                </span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isOnline = ref(navigator.onLine)

// If somehow landed here while online, redirect immediately
if (navigator.onLine) {
    router.back()
}

const handleOnline = () => {
    isOnline.value = true
    // Let the green signal animation play briefly, then redirect
    setTimeout(() => router.back(), 1800)
}

const handleOffline = () => {
    isOnline.value = false
}

onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
/* ── Eyes animation ─────────────────────────────────── */
.loader {
    position: relative;
    width: 108px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.loader::after,
.loader::before {
    content: "";
    display: inline-block;
    width: 48px;
    height: 48px;
    background-color: #fff;
    background-image: radial-gradient(circle 14px, #0d161b 100%, transparent 0);
    background-repeat: no-repeat;
    border-radius: 50%;
    animation: eyeMove 10s infinite, blink 10s infinite;
}

@keyframes eyeMove {
    0%,   10% { background-position:   0px  0px; }
    13%,  40% { background-position: -15px  0px; }
    43%,  70% { background-position:  15px  0px; }
    73%,  90% { background-position:   0px 15px; }
    93%, 100% { background-position:   0px  0px; }
}

@keyframes blink {
    0%,  10%, 12%, 20%, 22%, 40%, 42%,
    60%, 62%, 70%, 72%, 90%, 92%, 98%, 100% { height: 48px; }
    11%, 21%, 41%, 61%, 71%, 91%, 99%       { height: 18px; }
}

/* ── Signal bars ────────────────────────────────────── */
.signal-wrap {
    padding-bottom: 4px;
}

.signal-bar {
    width: 18px;
    background: currentColor;
    border-radius: 4px 4px 2px 2px;
    opacity: 0.15;
    animation: pulse-bar 1.6s ease-in-out infinite;
    transition: background 0.4s ease, opacity 0.4s ease;
}

/* Green state when online */
.signal-bar.online {
    background: #22c55e;
    animation: signal-gain 0.4s ease-in-out infinite alternate;
}

.bar1 { height: 30%; animation-delay: 0s;   }
.bar2 { height: 52%; animation-delay: 0.2s; }
.bar3 { height: 73%; animation-delay: 0.4s; }
.bar4 { height: 95%; animation-delay: 0.6s; }

.bar1.online { animation-delay: 0s;   }
.bar2.online { animation-delay: 0.1s; }
.bar3.online { animation-delay: 0.2s; }
.bar4.online { animation-delay: 0.3s; }

@keyframes pulse-bar {
    0%,  100% { opacity: 0.12; }
    50%       { opacity: 0.35; }
}

@keyframes signal-gain {
    from { opacity: 0.5;  transform: scaleY(0.9); }
    to   { opacity: 1;    transform: scaleY(1);   }
}

.slash {
    position: absolute;
    width: 4px;
    height: 130%;
    background: linear-gradient(to bottom, #ef4444, #f97316);
    border-radius: 99px;
    top: -10%;
    left: 50%;
    transform: translateX(-50%) rotate(35deg);
    box-shadow: 0 0 12px 3px rgba(239, 68, 68, 0.4);
}


</style>
