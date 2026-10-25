<template>
  <div
      class="bg-white dark:bg-white/5 border border-gray-100 dark:border-white/10 rounded-2xl shadow-sm overflow-hidden animate-fade-in-up">
      <div class="p-4 border-b border-gray-100 dark:border-white/10 bg-gray-50 dark:bg-white/5">
          <h3 class="font-bold text-gray-900 dark:text-white">Operational Entity Overview</h3>
      </div>
      <table class="w-full text-left text-xs">
          <thead class="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-bold uppercase">
              <tr>
                  <th class="p-4">Entity Type</th>
                  <th class="p-4 text-center">Active Count</th>
                  <th class="p-4 text-center">Issues</th>
                  <th class="p-4 text-right">Performance/Status</th>
              </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-white/5">
              <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td class="p-4 font-bold">Drivers</td>
                  <td class="p-4 text-center">{{ store.filteredDrivers.length }}</td>
                  <td class="p-4 text-center text-red-500 font-bold">{{store.filteredDrivers.filter(d => d.status !== 'Active').length }}</td>
                  <td class="p-4 text-right text-green-600 font-mono">{{ avgDriverEfficiency }}% Efficiency</td>
              </tr>
              <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td class="p-4 font-bold">Vehicles</td>
                  <td class="p-4 text-center">{{ store.filteredVehicles.length }}</td>
                  <td class="p-4 text-center text-yellow-500 font-bold">{{store.filteredVehicles.filter(v => v.status !== 'Active').length }}</td>
                  <td class="p-4 text-right font-mono">{{ vehiclesInMaintenance }} In Shop</td>
              </tr>
              <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td class="p-4 font-bold">Returns (RMA)</td>
                  <td class="p-4 text-center">{{ store.filteredReturns.length }}</td>
                  <td class="p-4 text-center text-blue-500 font-bold">{{store.filteredReturns.filter(r => r.status === 'Pending').length }}</td>
                  <td class="p-4 text-right font-mono">Processing</td>
              </tr>
              <tr class="hover:bg-gray-50 dark:hover:bg-white/5">
                  <td class="p-4 font-bold">Inventory</td>
                  <td class="p-4 text-center">{{ store.filteredInventory.length }} items</td>
                  <td class="p-4 text-center text-red-500 font-bold">{{store.filteredInventory.filter(i => i.status.includes('Low')).length }}</td>
                  <td class="p-4 text-right font-mono">Stock Level OK</td>
              </tr>
          </tbody>
      </table>
  </div>
</template>

<script setup>
defineProps({
    store: { type: Object, required: true },
    avgDriverEfficiency: { type: Number, required: true },
    vehiclesInMaintenance: { type: Number, required: true },
})

</script>
