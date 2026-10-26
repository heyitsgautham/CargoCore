<template>
    <!-- 2. Payroll Rates (Cost Side) -->
    <div class="glass-panel rounded-xl overflow-hidden">
        <div
            class="p-4 border-b border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-black/20 flex items-center gap-3">
            <div
                class="w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 flex items-center justify-center">
                <span class="material-symbols-outlined text-[20px]">payments</span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white text-lg">Payroll Control <span
                    class="text-xs font-normal text-gray-500 ml-2">(Cost Basis)</span></h3>
        </div>

        <div class="p-6 space-y-8">
            <!-- Driver Pay -->
            <div>
                <h4
                    class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                    A. Driver Compensation</h4>
                <div class="space-y-4">
                    <div class="flex flex-col gap-1">
                        <label class="text-xs font-bold text-gray-500 uppercase">Payout Structure</label>
                        <select :disabled="!isEditMode" v-model="rates.driver.type"
                            class="w-full lg:w-1/2 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-primary/20 outline-none">
                            <option value="per_km" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Per KM Model</option>
                            <option value="per_delivery" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Per Delivery Target</option>
                            <option value="salary_bonus" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Fixed Salary (Base + HRA/DA + Bonus)</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4"
                        v-if="rates.driver.type === 'salary_bonus'">
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Base Salary (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.baseSalary"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">HRA (₹)</label>
                            <input type="number" :disabled="!isEditMode" v-model.number="rates.driver.hra"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">DA (₹)</label>
                            <input type="number" :disabled="!isEditMode" v-model.number="rates.driver.da"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Perf. Bonus (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.performanceBonus"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4" v-if="rates.driver.type === 'per_km'">
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Rate (₹ / KM)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.kmRate"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Fuel Incentive (₹ / Day)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.fuelIncentive"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono outline-none">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4" v-if="rates.driver.type === 'per_delivery'">
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Base Drop Rate (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.deliveryBaseRate"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Heavy Item Bonus (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.driver.heavyItemBonus"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm font-mono outline-none">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Labor Pay -->
            <div>
                <h4
                    class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                    B. Labor / Mover Wage</h4>
                <div class="space-y-4">
                    <div class="flex flex-col gap-1">
                        <label class="text-xs font-bold text-gray-500 uppercase">Payout Structure</label>
                        <select :disabled="!isEditMode" v-model="rates.labor.type"
                            class="w-full lg:w-1/2 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-primary/20 outline-none">
                            <option value="hourly" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Hourly Contract</option>
                            <option value="salary_bonus" class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">Fixed Salary (Base + HRA/DA + Bonus)</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4"
                        v-if="rates.labor.type === 'salary_bonus'">
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Base Salary (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.labor.baseSalary"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">HRA (₹)</label>
                            <input type="number" :disabled="!isEditMode" v-model.number="rates.labor.hra"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">DA (₹)</label>
                            <input type="number" :disabled="!isEditMode" v-model.number="rates.labor.da"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                        <div>
                            <label class="block text-xs text-gray-500 mb-1">Bonus (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.labor.performanceBonus"
                                class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-lg p-2 text-sm font-mono outline-none">
                        </div>
                    </div>
                    <div class="grid grid-cols-2 lg:grid-cols-3 gap-4" v-if="rates.labor.type === 'hourly'">
                        <div
                            class="bg-gray-50 dark:bg-white/5 p-3 rounded-xl border border-gray-100 dark:border-white/5">
                            <label class="block text-[10px] text-gray-500 uppercase mb-1">Hourly Wage
                                (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.labor.hourlyWage"
                                class="w-full bg-transparent border-b border-gray-200 dark:border-white/10 py-1 text-sm font-mono outline-none">
                        </div>
                        <div
                            class="bg-gray-50 dark:bg-white/5 p-3 rounded-xl border border-gray-100 dark:border-white/5">
                            <label class="block text-[10px] text-gray-500 uppercase mb-1">Overtime
                                (x)</label>
                            <input type="number" :disabled="!isEditMode" step="0.1"
                                v-model.number="rates.labor.overtimeMul"
                                class="w-full bg-transparent border-b border-gray-200 dark:border-white/10 py-1 text-sm font-mono outline-none">
                        </div>
                        <div
                            class="bg-gray-50 dark:bg-white/5 p-3 rounded-xl border border-gray-100 dark:border-white/5">
                            <label class="block text-[10px] text-gray-500 uppercase mb-1">Field Allow.
                                (₹)</label>
                            <input type="number" :disabled="!isEditMode"
                                v-model.number="rates.labor.fieldAllowance"
                                class="w-full bg-transparent border-b border-gray-200 dark:border-white/10 py-1 text-sm font-mono outline-none">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Management & Dispatch -->
            <div>
                <h4
                    class="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4 border-b border-gray-100 dark:border-white/5 pb-2">
                    C. Management & Dispatch Executives</h4>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="space-y-4">
                        <h5
                            class="text-xs font-bold text-gray-500 uppercase bg-gray-100 dark:bg-white/5 inline-block px-2 py-1 rounded">
                            Warehouse Manager</h5>
                        <div class="grid grid-cols-2 gap-3">
                            <div><label class="block text-[10px] text-gray-500">Base Salary</label><input
                                    type="number" v-model.number="rates.managers.warehouseBase"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label class="block text-[10px] text-gray-500">HRA</label><input
                                    type="number" v-model.number="rates.managers.warehouseHra"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label class="block text-[10px] text-gray-500">DA</label><input
                                    type="number" v-model.number="rates.managers.warehouseDa"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label class="block text-[10px] text-gray-500 text-blue-500 font-bold">Max
                                    SLA Bonus</label><input type="number" :disabled="!isEditMode"
                                    v-model.number="rates.managers.warehouseBonus"
                                    class="w-full bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-1.5 text-sm font-mono font-bold text-blue-700 dark:text-blue-300 outline-none">
                            </div>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <h5
                            class="text-xs font-bold text-gray-500 uppercase bg-gray-100 dark:bg-white/5 inline-block px-2 py-1 rounded">
                            Fleet Dispatcher</h5>
                        <div class="grid grid-cols-2 gap-3">
                            <div><label class="block text-[10px] text-gray-500">Base Salary</label><input
                                    type="number" v-model.number="rates.managers.dispatcherBase"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label class="block text-[10px] text-gray-500">HRA</label><input
                                    type="number" v-model.number="rates.managers.dispatcherHra"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label class="block text-[10px] text-gray-500">DA</label><input
                                    type="number" v-model.number="rates.managers.dispatcherDa"
                                    class="w-full bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded p-1.5 text-sm font-mono outline-none">
                            </div>
                            <div><label
                                    class="block text-[10px] text-gray-500 text-blue-500 font-bold">Efficiency
                                    Bonus</label><input type="number" :disabled="!isEditMode"
                                    v-model.number="rates.managers.dispatcherBonus"
                                    class="w-full bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-1.5 text-sm font-mono font-bold text-blue-700 dark:text-blue-300 outline-none">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { inject } from 'vue'
import { rateGovernancePageKey } from './rateGovernancePageContext'

const { isEditMode, rates } = inject(rateGovernancePageKey)
</script>
