<template>
  <Background image-url="https://images.unsplash.com/photo-1611216625141-d52dc0441830?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuaWdodCUyMGhpZ2h3YXklMjB0cnVjayUyMGxpZ2h0cyUyMGJva2VofGVufDF8fHx8MTc3MTM4NTQxOHww&ixlib=rb-4.1.0&q=80&w=1080">
    <Navbar />
    <AIHelpOrb />

    <div class="min-h-screen flex items-center justify-center px-8 pt-20 pb-20 overflow-hidden">
      <div class="w-full max-w-4xl">
        <!-- Logo -->
        <div
          v-motion
          :initial="{ scale: 0.8, opacity: 0 }"
          :enter="{ scale: 1, opacity: 1, transition: { delay: 200, type: 'spring', stiffness: 200 } }"
          class="flex justify-center mb-8"
        >
          <img
            src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
            alt="Cargo Core Logo"
            class="h-16 w-auto opacity-70"
          />
        </div>

        <!-- Main Content -->
        <GlassCard class-name="p-8 md:p-12" :animate="false">
          <!-- Header Text -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 300 } }"
            class="text-center mb-12"
          >
            <h1 class="text-7xl md:text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#00C4FF] to-[#FF9500] mb-4 tracking-tight">
              404
            </h1>
            <h2 class="text-2xl md:text-3xl font-bold text-white mb-3">
              Oops! Wrong Route
            </h2>
            <p class="text-white/70 text-lg">
              This delivery seems to have taken a detour...
            </p>
          </div>

          <!-- Animated Truck Scene -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 400 } }"
            class="flex justify-center mb-12"
          >
            <div class="loader">
              <div class="truckWrapper">
                <div class="truckBody">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 198 93" class="trucksvg">
                    <path stroke-width="3" stroke="#282828" fill="#F83D3D" d="M135 22.5H177.264C178.295 22.5 179.22 23.133 179.594 24.0939L192.33 56.8443C192.442 57.1332 192.5 57.4404 192.5 57.7504V89C192.5 90.3807 191.381 91.5 190 91.5H135C133.619 91.5 132.5 90.3807 132.5 89V25C132.5 23.6193 133.619 22.5 135 22.5Z"></path>
                    <path stroke-width="3" stroke="#282828" fill="#7D7C7C" d="M146 33.5H181.741C182.779 33.5 183.709 34.1415 184.078 35.112L190.538 52.112C191.16 53.748 189.951 55.5 188.201 55.5H146C144.619 55.5 143.5 54.3807 143.5 53V36C143.5 34.6193 144.619 33.5 146 33.5Z"></path>
                    <path stroke-width="2" stroke="#282828" fill="#282828" d="M150 65C150 65.39 149.763 65.8656 149.127 66.2893C148.499 66.7083 147.573 67 146.5 67C145.427 67 144.501 66.7083 143.873 66.2893C143.237 65.8656 143 65.39 143 65C143 64.61 143.237 64.1344 143.873 63.7107C144.501 63.2917 145.427 63 146.5 63C147.573 63 148.499 63.2917 149.127 63.7107C149.763 64.1344 150 64.61 150 65Z"></path>
                    <rect stroke-width="2" stroke="#282828" fill="#FFFCAB" rx="1" height="7" width="5" y="63" x="187"></rect>
                    <rect stroke-width="2" stroke="#282828" fill="#282828" rx="1" height="11" width="4" y="81" x="193"></rect>
                    <rect stroke-width="3" stroke="#282828" fill="#DFDFDF" rx="2.5" height="90" width="121" y="1.5" x="6.5"></rect>
                    <rect stroke-width="2" stroke="#282828" fill="#DFDFDF" rx="2" height="4" width="6" y="84" x="1"></rect>
                  </svg>
                </div>
                <div class="truckTires">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 30 30" class="tiresvg">
                    <circle stroke-width="3" stroke="#282828" fill="#282828" r="13.5" cy="15" cx="15"></circle>
                    <circle fill="#DFDFDF" r="7" cy="15" cx="15"></circle>
                  </svg>
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 30 30" class="tiresvg">
                    <circle stroke-width="3" stroke="#282828" fill="#282828" r="13.5" cy="15" cx="15"></circle>
                    <circle fill="#DFDFDF" r="7" cy="15" cx="15"></circle>
                  </svg>
                </div>
                <div class="road"></div>
                <svg xml:space="preserve" viewBox="0 0 453.459 453.459" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://www.w3.org/2000/svg" id="Capa_1" version="1.1" fill="#000000" class="lampPost">
                  <path d="M252.882,0c-37.781,0-68.686,29.953-70.245,67.358h-6.917v8.954c-26.109,2.163-45.463,10.011-45.463,19.366h9.993c-1.65,5.146-2.507,10.54-2.507,16.017c0,28.956,23.558,52.514,52.514,52.514c28.956,0,52.514-23.558,52.514-52.514c0-5.478-0.856-10.872-2.506-16.017h9.992c0-9.354-19.352-17.204-45.463-19.366v-8.954h-6.149C200.189,38.779,223.924,16,252.882,16c29.952,0,54.32,24.368,54.32,54.32c0,28.774-11.078,37.009-25.105,47.437c-17.444,12.968-37.216,27.667-37.216,78.884v113.914h-0.797c-5.068,0-9.174,4.108-9.174,9.177c0,2.844,1.293,5.383,3.321,7.066c-3.432,27.933-26.851,95.744-8.226,115.459v11.202h45.75v-11.202c18.625-19.715-4.794-87.527-8.227-115.459c2.029-1.683,3.322-4.223,3.322-7.066c0-5.068-4.107-9.177-9.176-9.177h-0.795V196.641c0-43.174,14.942-54.283,30.762-66.043c14.793-10.997,31.559-23.461,31.559-60.277C323.202,31.545,291.656,0,252.882,0zM232.77,111.694c0,23.442-19.071,42.514-42.514,42.514c-23.442,0-42.514-19.072-42.514-42.514c0-5.531,1.078-10.957,3.141-16.017h78.747C231.693,100.736,232.77,106.162,232.77,111.694z"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Error Message -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 600 } }"
            class="text-center mb-8"
          >
            <div class="inline-block px-6 py-3 bg-[#FF9500]/10 rounded-lg border border-[#FF9500]/30 mb-6">
              <p class="text-white/90 text-base">
                🚧 <span class="font-semibold">Delivery Failed:</span> The page you're looking for is not on our route map
              </p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 20 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 700 } }"
            class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-xl mx-auto"
          >
            <GlassButton
              variant="primary"
              :icon="Home"
              class-name="w-full"
              @click="router.push('/')"
            >
              Return to Home
            </GlassButton>

            <button
              @click="router.back()"
              class="w-full px-6 py-3.5 rounded-lg bg-white/5 backdrop-blur-xl border border-white/10 hover:border-[#00C4FF]/50 hover:bg-white/10 transition-all duration-300 flex items-center justify-center gap-2 group"
            >
              <ArrowLeft class="w-5 h-5 text-[#00C4FF] group-hover:-translate-x-1 transition-transform duration-300" />
              <span class="text-white/90 font-medium">Go Back</span>
            </button>
          </div>

          <!-- Help Text -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 800 } }"
            class="mt-8 pt-6 border-t border-white/10 text-center"
          >
            <p class="text-white/50 text-sm">
              Need assistance? Our AI support is ready to help guide you back on track 👇
            </p>
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { Home, ArrowLeft } from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassButton from '../components/GlassButton.vue';

const router = useRouter();
</script>

<style scoped>
.loader {
  width: fit-content;
  height: fit-content;
  display: flex;
  align-items: center;
  justify-content: center;
}

.truckWrapper {
  width: 200px;
  height: 100px;
  display: flex;
  flex-direction: column;
  position: relative;
  align-items: center;
  justify-content: flex-end;
  overflow-x: hidden;
}

/* truck upper body */
.truckBody {
  width: 130px;
  height: fit-content;
  margin-bottom: 6px;
  animation: motion 1s linear infinite;
}

/* truck suspension animation */
@keyframes motion {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(3px);
  }
  100% {
    transform: translateY(0px);
  }
}

/* truck's tires */
.truckTires {
  width: 130px;
  height: fit-content;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0px 10px 0px 15px;
  position: absolute;
  bottom: 0;
}

.truckTires svg {
  width: 24px;
}

.road {
  width: 100%;
  height: 1.5px;
  background-color: #282828;
  position: relative;
  bottom: 0;
  align-self: flex-end;
  border-radius: 3px;
}

.road::before {
  content: "";
  position: absolute;
  width: 20px;
  height: 100%;
  background-color: #282828;
  right: -50%;
  border-radius: 3px;
  animation: roadAnimation 1.4s linear infinite;
  border-left: 10px solid white;
}

.road::after {
  content: "";
  position: absolute;
  width: 10px;
  height: 100%;
  background-color: #282828;
  right: -65%;
  border-radius: 3px;
  animation: roadAnimation 1.4s linear infinite;
  border-left: 4px solid white;
}

.lampPost {
  position: absolute;
  bottom: 0;
  right: -90%;
  height: 90px;
  animation: roadAnimation 1.4s linear infinite;
}

@keyframes roadAnimation {
  0% {
    transform: translateX(0px);
  }
  100% {
    transform: translateX(-350px);
  }
}
</style>
