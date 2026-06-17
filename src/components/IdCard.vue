<template>
  <div class="flex items-center justify-center p-6 id-card-container font-sans leading-[1.5]">
    <!-- Card Holder Container -->
    <div class="relative">
      <!-- Premium Card Holder Frame -->
      <div class="relative p-6 bg-gradient-to-b from-slate-50 to-white rounded-2xl shadow-2xl border border-gray-200">
        <!-- Corner Brackets - Top Left -->
        <div
          class="absolute top-3 left-3 w-8 h-8 border-l-[3px] border-t-[3px] border-[#3D5A99] rounded-tl-lg opacity-60">
        </div>
        <!-- Corner Brackets - Top Right -->
        <div
          class="absolute top-3 right-3 w-8 h-8 border-r-[3px] border-t-[3px] border-[#3D5A99] rounded-tr-lg opacity-60">
        </div>
        <!-- Corner Brackets - Bottom Left -->
        <div
          class="absolute bottom-3 left-3 w-8 h-8 border-l-[3px] border-b-[3px] border-[#3D5A99] rounded-bl-lg opacity-60">
        </div>
        <!-- Corner Brackets - Bottom Right -->
        <div
          class="absolute bottom-3 right-3 w-8 h-8 border-r-[3px] border-b-[3px] border-[#3D5A99] rounded-br-lg opacity-60">
        </div>

        <!-- Elegant Side Strip -->
        <div
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-32 bg-gradient-to-b from-[#3D5A99] via-[#4FC3F7] to-[#3D5A99] rounded-r-full shadow-lg">
        </div>

        <!-- 3D Flip Container -->
        <div class="relative w-[340px] h-[214px] cursor-pointer group" style="perspective: 2000px;" @click="toggleFlip">
          <!-- Flip Card Inner -->
          <div class="relative w-full h-full transition-all duration-700 preserve-3d"
            :style="{ transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }">
            <!-- ==================== FRONT CARD ==================== -->
            <div class="absolute inset-0 w-full h-full backface-hidden"
              style="-webkit-backface-visibility: hidden; backface-visibility: hidden;">
              <div class="relative w-full h-full bg-white rounded-lg shadow-xl overflow-hidden ring-1 ring-gray-200"
                :style="{ background: 'linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%)' }">
                <!-- Security Watermark -->
                <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-[0.12]" viewBox="0 0 340 214"
                  preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
                  <path d="M-50,107 Q50,40 150,107 T350,107 Q450,174 550,107 L550,300 L-50,300 Z" fill="#3D5A99" />
                  <path d="M-50,140 Q80,70 210,140 T550,140 L550,300 L-50,300 Z" fill="#4FC3F7" opacity="0.6" />
                </svg>

                <!-- Content container -->
                <div class="relative z-10 h-full flex flex-col">
                  <!-- Wave Gradient Header -->
                  <div class="relative h-[28px] overflow-hidden">
                    <div class="absolute inset-0"
                      style="background: linear-gradient(90deg, #0D3B66 0%, #1A5C8A 35%, #4FC3F7 100%)" />
                    <svg class="absolute bottom-0 left-0 w-full h-3 opacity-20" viewBox="0 0 1200 24"
                      preserveAspectRatio="none">
                      <path d="M0,12 Q200,0 400,12 T800,12 T1200,12 L1200,24 L0,24 Z" fill="white" />
                    </svg>
                    <div class="relative z-10 h-full flex items-center justify-center">
                      <h2 class="text-white text-[9px] font-bold tracking-widest uppercase">
                        {{ employee.cardTitle || 'Employee ID Card' }}
                      </h2>
                    </div>
                  </div>

                  <!-- Verified Badge -->
                  <div class="absolute top-2 right-2 z-20">
                    <div class="relative">
                      <div
                        class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 shadow-lg">
                        <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clip-rule="evenodd" />
                        </svg>
                        <span class="text-white text-[7px] font-bold uppercase tracking-wide">Verified</span>
                      </div>
                      <div class="absolute inset-0 rounded-full bg-emerald-400 opacity-30 blur-sm -z-10"></div>
                    </div>
                  </div>

                  <!-- Main content grid -->
                  <div class="flex-1 px-3 py-2 grid grid-cols-[1fr_auto] gap-2">
                    <!-- Left Column -->
                    <div class="flex flex-col">
                      <!-- Logo Section -->
                      <div class="flex items-start gap-2 mb-2">
                        <img :src="cargoCoreLogo" alt="CargoCore Logo" class="w-12 h-12" />
                        <div class="flex flex-col justify-center">
                          <div class="text-[#3D5A99] font-bold text-[13px] leading-tight">
                            CargoCore
                          </div>
                          <div class="text-gray-600 text-[7px] leading-tight">
                            Moving What Matters
                          </div>
                        </div>
                      </div>

                      <!-- Employee Details -->
                      <div class="flex-1 flex flex-col justify-center">
                        <h3 class="text-[#2C3E50] font-extrabold text-[14px] leading-tight mb-0.5">
                          {{ employee.name }}
                        </h3>
                        <p class="text-[#3D5A99] font-bold text-[9px] leading-tight mb-1.5">
                          {{ employee.designation }}
                        </p>
                        <div class="flex items-center gap-1.5">
                          <span
                            class="inline-flex items-center px-2 py-0.5 rounded-full bg-[#4FC3F7] text-white text-[8px] font-bold">
                            {{ employee.id }}
                          </span>
                          <span
                            class="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-200 text-[#2C3E50] text-[8px] font-semibold">
                            {{ employee.department }}
                          </span>
                        </div>
                      </div>

                      <!-- Authorization -->
                      <div class="mt-auto">
                        <div class="flex justify-end">
                          <div class="w-[130px]">
                            <div class="text-[6px] text-gray-500 uppercase tracking-wide mb-0.5">
                              Authorized By
                            </div>
                            <div class="border-t border-gray-400 mb-1"></div>
                            <div class="text-[10px] italic text-[#2C3E50] mb-0.5"
                              style="font-family: 'Dancing Script', cursive">
                              {{ employee.authorizedBy?.name || 'CargoCore Operations' }}
                            </div>
                            <div class="text-[6px] text-gray-600">
                              {{ employee.authorizedBy?.title || 'Access Management' }}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Right Column - Photo -->
                    <div class="flex items-start pt-1">
                      <div
                        class="w-[76px] h-[95px] bg-gray-200 rounded border-2 border-[#3D5A99] flex items-center justify-center">
                        <svg class="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                            clip-rule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- ==================== BACK CARD ==================== -->
            <div class="absolute inset-0 w-full h-full backface-hidden"
              style="-webkit-backface-visibility: hidden; backface-visibility: hidden; transform: rotateY(180deg);">
              <div class="relative w-full h-full bg-white rounded-lg shadow-xl overflow-hidden ring-1 ring-gray-200"
                :style="{ background: 'linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%)' }">
                <!-- Security Watermark -->
                <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-[0.12]" viewBox="0 0 340 214"
                  preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
                  <path d="M-50,107 Q50,40 150,107 T350,107 Q450,174 550,107 L550,300 L-50,300 Z" fill="#3D5A99" />
                  <path d="M-50,140 Q80,70 210,140 T550,140 L550,300 L-50,300 Z" fill="#4FC3F7" opacity="0.6" />
                </svg>

                <!-- Content container -->
                <div class="relative z-10 h-full flex flex-col">
                  <!-- Wave Gradient Header -->
                  <div class="relative h-[28px] overflow-hidden">
                    <div class="absolute inset-0"
                      style="background: linear-gradient(90deg, #0D3B66 0%, #1A5C8A 35%, #4FC3F7 100%)" />
                    <svg class="absolute bottom-0 left-0 w-full h-3 opacity-20" viewBox="0 0 1200 24"
                      preserveAspectRatio="none">
                      <path d="M0,12 Q200,0 400,12 T800,12 T1200,12 L1200,24 L0,24 Z" fill="white" />
                    </svg>
                    <div class="relative z-10 h-full flex items-center justify-center">
                      <h2 class="text-white text-[9px] font-bold tracking-widest uppercase">
                        {{ employee.infoTitle || 'Employee Information' }}
                      </h2>
                    </div>
                  </div>

                  <!-- Main content -->
                  <div class="flex-1 px-3 py-2 flex flex-col overflow-hidden">
                    <!-- Contact Information -->
                    <div class="space-y-0.5 mb-1.5">
                      <div class="text-[8px]">
                        <span class="text-[#3D5A99] font-bold">Address: </span>
                        <span class="text-[#2C3E50]">{{ employee.address }}</span>
                      </div>
                      <div class="text-[8px]">
                        <span class="text-[#3D5A99] font-bold">Phone: </span>
                        <span class="text-[#2C3E50]">{{ employee.phone }}</span>
                      </div>
                      <div class="text-[8px]">
                        <span class="text-[#3D5A99] font-bold">Email: </span>
                        <span class="text-[#2C3E50]">{{ employee.email }}</span>
                      </div>
                    </div>

                    <!-- Employment Details -->
                    <div class="space-y-0.5 mb-1.5 pb-1.5 border-b border-gray-300">
                      <div class="text-[8px]">
                        <span class="text-[#3D5A99] font-bold">Date of Joining: </span>
                        <span class="text-[#2C3E50]">{{ employee.joinDate }}</span>
                      </div>
                      <div class="text-[8px]">
                        <span class="text-[#3D5A99] font-bold">Valid Until: </span>
                        <span class="text-[#4FC3F7] font-bold">{{ employee.validUntil }}</span>
                      </div>
                    </div>

                    <!-- Emergency Contact -->
                    <div class="bg-red-50 border-2 border-red-500 rounded px-2 py-1 mb-1.5">
                      <div class="text-red-700 font-bold text-[7px] uppercase tracking-wide mb-0.5">
                        In Case of Emergency
                      </div>
                      <div class="text-[#2C3E50] font-bold text-[7px] mb-0.5">
                        {{ employee.emergencyContact.name }} ({{ employee.emergencyContact.relation }})
                      </div>
                      <div class="text-[#2C3E50] text-[7px]">
                        {{ employee.emergencyContact.phone }}
                      </div>
                    </div>

                    <!-- Footer -->
                    <div class="mt-auto flex items-end justify-between gap-1.5 pb-2">
                      <div class="flex-1">
                        <div class="text-[5px] text-gray-600 italic leading-[1.2]">
                          <div class="font-semibold text-[#3D5A99]">Property of CargoCore</div>
                          <div>If found, report it to the registered CargoCore support desk.</div>
                        </div>
                      </div>
                      <div class="flex flex-col items-center flex-shrink-0">
                        <div class="bg-white p-0.5 rounded shadow-sm">
                          <QrcodeVue :value="qrData" :size="64" level="M" render-as="svg" class="w-[26px] h-[26px]" />
                        </div>
                        <div class="text-[5px] text-gray-500 mt-0.5">Scan to Verify</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Hover Indicator -->
          <div
            class="absolute -bottom-10 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div class="flex items-center gap-1.5 px-3 py-1 bg-white rounded-full shadow-md border border-gray-200">
              <svg class="w-3.5 h-3.5 text-[#4FC3F7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span class="text-[#3D5A99] text-xs font-semibold">Click to flip</span>
            </div>
          </div>
        </div>

        <!-- Professional Badge -->
        <div class="mt-3 flex items-center justify-center gap-2">
          <div class="h-px w-16 bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
          <span class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">{{ employee.footerBadge || 'Verified Access' }}</span>
          <div class="h-px w-16 bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import QrcodeVue from 'qrcode.vue'
import cargoCoreLogo from '@/assets/cargo-core-logo.png'

const props = defineProps({
  employee: {
    type: Object,
    required: true
  }
})

const isFlipped = ref(false)

const toggleFlip = () => {
  isFlipped.value = !isFlipped.value
}

// QR Code data
const qrData = computed(() => {
  return JSON.stringify({
    id: props.employee.id,
    name: props.employee.name,
    designation: props.employee.designation,
    cardTitle: props.employee.cardTitle,
    validUntil: props.employee.validUntil,
    company: 'CargoCore'
  })
})
</script>

<style scoped>
.preserve-3d {
  transform-style: preserve-3d;
}

.backface-hidden {
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}
</style>

<style>
/* Print styles for ID Card isolated to not affect other globals */
@media print {
  @page {
    size: 85.6mm 54mm;
    margin: 0;
  }

  body {
    margin: 0;
    padding: 0;
  }

  .no-print {
    display: none !important;
  }

  /* Hide everything except the ID cards container */
  body>div:not(:has(.id-card-container)) {
    display: none;
  }
}
</style>
