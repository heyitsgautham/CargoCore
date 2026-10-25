<template>
  <div>
      <div class="glass-panel p-5 rounded-xl lg:sticky lg:top-[5.5rem] z-10">
          <h3 class="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-blue-400 text-[18px]">calculate</span>
              Live Quotation
          </h3>
          <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20">
              <span class="material-symbols-outlined text-blue-500 text-sm">route</span>
              <span class="text-xs font-bold text-blue-700 dark:text-blue-400">{{ distanceKm }} km</span>
              <span class="text-xs text-gray-500">(road distance · ₹{{ rates.perKmRate ?? 12 }}/km)</span>
              <span v-if="distanceLoading" class="ml-auto text-xs text-gray-400 animate-pulse">calculating...</span>
          </div>
          <div class="space-y-2 mb-4">
              <div class="flex justify-between text-xs"><span class="text-gray-500">Base
                      Transport</span><span class="text-gray-900 dark:text-white">₹{{
                          quote.baseTransport.toLocaleString() }}</span></div>
              <div class="flex justify-between text-xs"><span class="text-gray-500">Labor
                      Charges</span><span class="text-gray-900 dark:text-white">₹{{
                          quote.laborCharges.toLocaleString() }}</span></div>
              <div class="flex justify-between text-xs"><span class="text-gray-500">Packing
                      Fee</span><span class="text-gray-900 dark:text-white">₹{{
                          quote.packingFee.toLocaleString() }}</span></div>
              <div class="flex justify-between text-xs"><span class="text-gray-500">Insurance</span><span
                      class="text-gray-900 dark:text-white">₹{{ quote.insurance.toLocaleString() }}</span>
              </div>
              <div
                  class="border-t border-gray-200 dark:border-white/10 pt-2 flex justify-between font-bold">
                  <span class="text-gray-700 dark:text-gray-200 text-sm">Total Estimate</span><span
                      class="text-blue-500 text-lg">₹{{ quote.total.toLocaleString() }}</span>
              </div>
          </div>
          <div v-if="bookingNotice" class="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
              {{ bookingNotice }}
          </div>
          <div v-if="!formValid" class="mb-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div class="text-xs text-yellow-600 dark:text-yellow-400 font-medium">Required fields
                  missing</div>
              <ul class="text-xs text-yellow-500 mt-1 list-disc list-inside">
                  <li v-for="e in validationErrors" :key="e">{{ e }}</li>
              </ul>
          </div>
          <button @click="$emit('submit')" :disabled="!formValid || warehouseBookingBlocked"
              class="w-full py-3 rounded-xl font-bold text-sm transition-all"
              :class="(!formValid || warehouseBookingBlocked) ? 'bg-gray-200 dark:bg-white/10 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg'">
              {{ warehouseBookingBlocked ? 'Shipment Booking Unavailable' : 'Confirm Shipment' }}
          </button>
          <button @click="$emit('save-draft')"
              class="mt-2 w-full py-2.5 rounded-xl border border-gray-200 dark:border-white/10 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5 text-sm font-medium transition-colors">Save
              Draft</button>
      </div>
  </div>
</template>

<script setup>
defineProps({
    quote: { type: Object, required: true },
    rates: { type: Object, required: true },
    bookingNotice: { type: String, required: true },
    formValid: { type: Boolean, required: true },
    validationErrors: { type: Array, required: true },
    warehouseBookingBlocked: { type: Boolean, required: true },
    distanceLoading: { type: Boolean, required: true },
    distanceKm: { type: Number, default: null },
})
defineEmits(['save-draft', 'submit'])
</script>
