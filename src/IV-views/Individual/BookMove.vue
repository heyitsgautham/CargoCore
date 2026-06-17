<template>
    <div class="space-y-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Book a Move</h2>

        <!-- AI Pre-fill Banner -->
        <Transition enter-active-class="transition-all duration-500" enter-from-class="opacity-0 -translate-y-2" leave-active-class="transition-all duration-300" leave-to-class="opacity-0 -translate-y-2">
            <div v-if="aiPrefillApplied"
                class="flex items-center gap-3 px-4 py-3 bg-purple-50 dark:bg-purple-500/10 border border-purple-300 dark:border-purple-500/30 rounded-xl">
                <span class="material-symbols-outlined text-purple-500">psychology</span>
                <div>
                    <p class="text-sm font-bold text-purple-700 dark:text-purple-300">✨ AI Estimator pre-filled your booking!</p>
                    <p class="text-xs text-purple-600 dark:text-purple-400">Vehicle, labor count, cargo type, and volume estimate were carried in from your room scan. You can adjust anything below.</p>
                </div>
            </div>
        </Transition>

        <!-- Move Type Toggle -->

        <div class="glass-panel p-4 rounded-xl">
            <div class="flex gap-2 p-1 bg-gray-100 dark:bg-white/5 rounded-lg w-fit">
                <button @click="moveType = 'house-shift'"
                    class="px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2"
                    :class="moveType === 'house-shift' ? 'bg-green-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                    <span class="material-symbols-outlined text-lg">home</span> Complete House Shift
                </button>
                <button @click="moveType = 'small-package'"
                    class="px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2"
                    :class="moveType === 'small-package' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'">
                    <span class="material-symbols-outlined text-lg">package_2</span> Small Package / Parcel
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main Form -->
            <div class="lg:col-span-2 space-y-6">

                <!-- ===== HOUSE SHIFT FORM ===== -->
                <template v-if="moveType === 'house-shift'">
                    <!-- Section 1: Cargo Type -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">1</span>
                            Select Cargo Type
                        </h3>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                            <button v-for="type in cargoTypes" :key="type.name"
                                class="p-3 sm:p-4 rounded-xl border transition-all flex flex-col items-center gap-2 group"
                                :class="form.cargoType === type.name
                                    ? 'bg-green-500/10 border-green-500 dark:bg-green-500/10 dark:border-green-500'
                                    : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-green-500/50'"
                                @click="form.cargoType = type.name">
                                <span class="material-symbols-outlined text-2xl sm:text-3xl"
                                    :class="form.cargoType === type.name ? 'text-green-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                                    {{ type.icon }}
                                </span>
                                <span class="text-xs font-medium"
                                    :class="form.cargoType === type.name ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'">
                                    {{ type.name }}
                                </span>
                            </button>
                        </div>
                    </div>

                    <!-- Section 2: Vehicle Type -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">2</span>
                            Select Vehicle / Truck
                        </h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <button v-for="v in store.vehicleTypes" :key="v.key"
                                class="p-4 rounded-xl border transition-all text-left relative overflow-hidden group"
                                :class="form.vehicleType === v.key
                                    ? 'border-green-500 bg-green-500/5 dark:bg-green-500/10 ring-1 ring-green-500/30'
                                    : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/50'"
                                @click="form.vehicleType = v.key">
                                <div v-if="v.key === 'tempo'"
                                    class="absolute top-0 right-0 px-2 py-0.5 bg-amber-500 text-white text-[8px] font-bold rounded-bl-lg">
                                    POPULAR</div>
                                <div class="flex items-center gap-3 mb-2">
                                    <span class="material-symbols-outlined text-3xl"
                                        :class="form.vehicleType === v.key ? 'text-green-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                                        {{ v.icon }}
                                    </span>
                                    <div>
                                        <div class="font-bold text-sm text-gray-900 dark:text-white">{{ v.name }}</div>
                                        <div class="text-xs text-gray-500 dark:text-gray-400">{{ v.capacity }}</div>
                                    </div>
                                </div>
                                <div class="flex items-center justify-between text-xs">
                                    <span class="text-gray-500 dark:text-gray-400"><span
                                            class="material-symbols-outlined text-[11px] align-middle">airline_seat_recline_extra</span>
                                        {{ v.seats }} seats</span>
                                    <span class="font-mono font-bold"
                                        :class="form.vehicleType === v.key ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">×{{
                                        v.priceMultiplier }}</span>
                                </div>
                                <div class="text-[10px] text-gray-400 mt-1">{{ v.desc }}</div>
                            </button>
                        </div>
                    </div>

                    <!-- Section 3: Route Details -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">3</span>
                            Route Details
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Hub Assignment</label>
                                <select v-model="form.hubId"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all">
                                    <option value="">Auto-select best available hub</option>
                                    <option v-for="warehouse in store.warehouses" :key="warehouse.id" :value="warehouse.id">
                                        {{ warehouse.name }}
                                    </option>
                                </select>
                            </div>
                            <div class="rounded-lg border border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/5 px-4 py-3">
                                <div class="text-[11px] uppercase tracking-wider font-bold text-green-700 dark:text-green-300">
                                    {{ routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'Routing Preview' }}
                                </div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                                    {{ routingPreview?.warehouse_name || 'Resolving best available hub...' }}
                                </div>
                                <div class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                                    {{ routingPreview?.message || 'We will choose the best available operational hub if you do not select one.' }}
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Pickup
                                    Address</label>
                                <div class="relative">
                                    <span
                                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-green-500 text-lg">trip_origin</span>
                                    <button type="button" @click="openMapPicker('pickup')"
                                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all flex items-center justify-between"
                                        title="Select pickup on map">
                                        <span :class="form.pickup ? '' : 'text-gray-400'">{{ form.pickup || 'Select pickup on map' }}</span>
                                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label
                                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Destination
                                    Address</label>
                                <div class="relative">
                                    <span
                                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-500 text-lg">location_on</span>
                                    <button type="button" @click="openMapPicker('destination')"
                                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all flex items-center justify-between"
                                        title="Select destination on map">
                                        <span :class="form.destination ? '' : 'text-gray-400'">{{ form.destination || 'Select destination on map' }}</span>
                                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Move
                                    Date</label>
                                <input v-model="form.date" type="date"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all" />
                            </div>
                            <div>
                                <label
                                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium flex items-center gap-2">
                                    Time Window
                                    <span
                                        class="px-1.5 py-0.5 text-[10px] bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded font-bold flex items-center gap-0.5">
                                        <span class="material-symbols-outlined text-[10px]">auto_awesome</span> AI Smart
                                    </span>
                                </label>
                                <div class="grid grid-cols-2 gap-2">
                                    <button v-for="slot in timeSlots" :key="slot.value" type="button"
                                        @click="form.timeWindow = slot.value"
                                        class="relative p-2.5 rounded-lg border text-left transition-all text-xs"
                                        :class="form.timeWindow === slot.value
                                            ? 'border-green-500 bg-green-500/5 dark:bg-green-500/10'
                                            : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 hover:border-green-500/50'">
                                        <div v-if="slot.recommended"
                                            class="absolute -top-2 right-2 px-1.5 py-0.5 bg-purple-500 text-white text-[8px] font-bold rounded-full">
                                            AI Pick</div>
                                        <div class="font-medium text-gray-900 dark:text-white">{{ slot.label }}</div>
                                        <div class="flex items-center justify-between mt-1">
                                            <span class="text-[10px]" :class="slot.demandColor">{{ slot.demand }}</span>
                                            <span class="text-[10px] font-mono" :class="slot.priceColor">{{
                                                slot.priceTag }}</span>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Section 4: Service Customization -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">4</span>
                            Customize Service
                        </h3>
                        <div class="mb-6">
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Packing
                                Service</label>
                            <div class="flex flex-col sm:flex-row gap-3">
                                <label
                                    class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 flex-1 transition-all"
                                    :class="!form.packingRequired ? 'border-green-500 bg-green-500/5' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5'">
                                    <input type="radio" :value="false" v-model="form.packingRequired"
                                        class="accent-green-500" />
                                    <div><span class="text-sm text-gray-900 dark:text-white font-medium">I will pack
                                            myself</span>
                                        <p class="text-xs text-gray-500">No packing charges</p>
                                    </div>
                                </label>
                                <label
                                    class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 flex-1 transition-all"
                                    :class="form.packingRequired ? 'border-green-500 bg-green-500/5' : 'border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5'">
                                    <input type="radio" :value="true" v-model="form.packingRequired"
                                        class="accent-green-500" />
                                    <div><span class="text-sm text-gray-900 dark:text-white font-medium">We pack for
                                            you</span>
                                        <p class="text-xs text-gray-500">Professional packing team</p>
                                    </div>
                                </label>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label
                                    class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Additional
                                    Labor (Helpers)</label>
                                <div class="flex items-center gap-4">
                                    <button @click="form.laborCount > 0 ? form.laborCount-- : null"
                                        class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white flex items-center justify-center text-xl font-bold transition-colors">−</button>
                                    <span class="text-2xl font-bold text-gray-900 dark:text-white w-8 text-center">{{
                                        form.laborCount }}</span>
                                    <button @click="form.laborCount++"
                                        class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 text-gray-700 dark:text-white flex items-center justify-center text-xl font-bold transition-colors">+</button>
                                </div>
                                <p class="text-xs text-gray-500 mt-2">₹{{ (rates.individualLaborRate ?? 800).toLocaleString() }}/helper per move</p>
                            </div>
                            <div v-if="form.packingRequired">
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Packing
                                    Materials</label>
                                <div class="space-y-2 max-h-44 overflow-y-auto no-scrollbar">
                                    <div v-if="packingCatalogLoading" class="text-xs text-gray-400 py-2 text-center">Loading materials...</div>
                                    <div v-for="mat in packingCatalog" :key="mat.key"
                                        class="flex justify-between items-center text-sm p-2 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-100 dark:border-white/5">
                                        <div class="flex items-center gap-2"><span
                                                class="material-symbols-outlined text-sm text-gray-400">{{ mat.icon
                                                }}</span><span
                                                class="text-gray-700 dark:text-gray-300 text-xs sm:text-sm">{{ mat.name
                                                }}</span>
                                            <span v-if="mat.stock !== null" class="text-[10px] font-mono" :class="mat.stock <= 5 ? 'text-red-400' : 'text-gray-500'">({{ mat.stock }} in stock)</span>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <span class="text-xs text-gray-400">₹{{ mat.price }}/{{ mat.unit }}</span>
                                            <input type="number" :value="form.materials[mat.key] || 0"
                                                @input="form.materials[mat.key] = parseInt($event.target.value) || 0"
                                                min="0" :max="mat.stock ?? 9999"
                                                class="w-14 bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded px-2 py-1 text-right text-gray-900 dark:text-white text-sm" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">
                                    Approx. Cargo Weight (kg)
                                </label>
                                <input
                                    v-model.number="form.cargoWeightKg"
                                    type="number"
                                    min="0"
                                    step="0.1"
                                    placeholder="e.g. 650"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all"
                                />
                                <p class="text-[11px] text-gray-500 mt-1">Recommended for dispatch planning and vehicle fit.</p>
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">
                                    Approx. Cargo Volume (m³)
                                </label>
                                <input
                                    v-model.number="form.cargoVolumeM3"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    placeholder="e.g. 8.5"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500/50 focus:border-green-500 outline-none transition-all"
                                />
                                <p class="text-[11px] text-gray-500 mt-1">AI room scan can prefill this when available.</p>
                            </div>
                        </div>
                    </div>

                    <!-- Section 5: Instructions -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">5</span>
                            Special Instructions
                        </h3>
                        <textarea v-model="form.instructions" rows="3"
                            placeholder="e.g., Handle fragile items carefully, use service elevator..."
                            class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-green-500/50 outline-none resize-none"></textarea>
                    </div>

                    <!-- Section 6: Payment Mode -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span
                                class="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center font-bold">6</span>
                            Payment Mode
                        </h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                            <label v-for="mode in paymentModes" :key="mode.value"
                                class="p-3 rounded-xl border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 transition-all flex items-center gap-3"
                                :class="form.paymentMode === mode.value ? 'border-green-500 bg-green-500/5' : 'border-gray-200 dark:border-white/10'">
                                <input type="radio" :value="mode.value" v-model="form.paymentMode"
                                    class="accent-green-500" />
                                <div><span class="text-sm text-gray-900 dark:text-white font-medium">{{ mode.label
                                        }}</span>
                                    <p class="text-xs text-gray-500">{{ mode.desc }}</p>
                                </div>
                            </label>
                        </div>
                        <!-- Dummy Payment removed -->
                    </div>
                </template>

                <!-- ===== SMALL PACKAGE FORM ===== -->
                <template v-else>
                    <div class="glass-panel p-4 sm:p-6 rounded-xl border-l-4 border-blue-500">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-500">package_2</span>
                            Small Package Details
                        </h3>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">Send books, documents, small boxes, or
                            parcels. Auto-scheduled pickup with estimated delivery.</p>
                        
                        <div class="mb-5">
                            <label class="block text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Package Type</label>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                <button v-for="type in pkgTypes" :key="type.name"
                                    class="p-2.5 rounded-xl border transition-all flex flex-col items-center gap-1.5 group"
                                    :class="pkg.packageType === type.name
                                        ? 'bg-blue-500/10 border-blue-500 dark:bg-blue-500/10 dark:border-blue-500'
                                        : 'bg-gray-50 dark:bg-white/5 border-gray-200 dark:border-white/10 hover:border-blue-500/50'"
                                    @click="pkg.packageType = type.name">
                                    <span class="material-symbols-outlined text-xl sm:text-2xl"
                                        :class="pkg.packageType === type.name ? 'text-blue-500' : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-700 dark:group-hover:text-white'">
                                        {{ type.icon }}
                                    </span>
                                    <span class="text-[11px] font-medium"
                                        :class="pkg.packageType === type.name ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'">
                                        {{ type.name }}
                                    </span>
                                </button>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Package
                                    Description</label>
                                <input v-model="pkg.description" type="text" placeholder="e.g., 3 books, 1 envelope"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 outline-none" />
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Approx.
                                    Weight (kg)</label>
                                <input v-model.number="pkg.weight" type="number" min="0.1" step="0.1" placeholder="2.5"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50 outline-none" />
                            </div>
                        </div>
                    </div>

                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-500">route</span> Pickup & Delivery
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Hub Assignment</label>
                                <select v-model="form.hubId"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all">
                                    <option value="">Auto-select best available hub</option>
                                    <option v-for="warehouse in store.warehouses" :key="warehouse.id" :value="warehouse.id">
                                        {{ warehouse.name }}
                                    </option>
                                </select>
                            </div>
                            <div class="rounded-lg border border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/5 px-4 py-3">
                                <div class="text-[11px] uppercase tracking-wider font-bold text-blue-700 dark:text-blue-300">
                                    {{ routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'Routing Preview' }}
                                </div>
                                <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                                    {{ routingPreview?.warehouse_name || 'Resolving best available hub...' }}
                                </div>
                                <div class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                                    {{ routingPreview?.message || 'We will choose the best available operational hub if you do not select one.' }}
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Pickup
                                    Address</label>
                                <div class="relative">
                                    <span
                                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-green-500 text-lg">trip_origin</span>
                                    <button type="button" @click="openMapPicker('pickup')"
                                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all flex items-center justify-between"
                                        title="Select pickup on map">
                                        <span :class="form.pickup ? '' : 'text-gray-400'">{{ form.pickup || 'Select pickup on map' }}</span>
                                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label
                                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Delivery
                                    Address</label>
                                <div class="relative">
                                    <span
                                        class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-red-500 text-lg">location_on</span>
                                    <button type="button" @click="openMapPicker('destination')"
                                        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-left text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all flex items-center justify-between"
                                        title="Select destination on map">
                                        <span :class="form.destination ? '' : 'text-gray-400'">{{ form.destination || 'Select destination on map' }}</span>
                                        <span class="material-symbols-outlined text-xl text-gray-400">map</span>
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label
                                    class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Preferred
                                    Pickup Date</label>
                                <input v-model="pkg.preferredDate" type="date"
                                    class="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-50 dark:bg-white/5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none" />
                            </div>
                            <div>
                                <label class="block text-sm text-gray-600 dark:text-gray-400 mb-1.5 font-medium">Est.
                                    Delivery</label>
                                <div
                                    class="px-4 py-2.5 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 text-blue-700 dark:text-blue-400 font-bold text-sm flex items-center gap-2">
                                    <span class="material-symbols-outlined text-lg">schedule</span>
                                    {{ estimatedDelivery || 'Select pickup date' }}
                                </div>
                            </div>
                        </div>
                        <div
                            class="mt-4 p-3 bg-blue-50 dark:bg-blue-500/5 border border-blue-200 dark:border-blue-500/20 rounded-lg flex items-center gap-3 text-sm">
                            <span class="material-symbols-outlined text-blue-500">info</span>
                            <span class="text-gray-700 dark:text-gray-300">Auto-scheduled pickup. Our driver will
                                collect from your address on the selected date.</span>
                        </div>
                    </div>

                    <!-- Package Payment -->
                    <div class="glass-panel p-4 sm:p-6 rounded-xl">
                        <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-blue-500">payments</span> Payment
                        </h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                            <label v-for="mode in paymentModes" :key="mode.value"
                                class="p-3 rounded-xl border cursor-pointer hover:bg-gray-50 dark:hover:bg-white/5 transition-all flex items-center gap-3"
                                :class="form.paymentMode === mode.value ? 'border-blue-500 bg-blue-500/5' : 'border-gray-200 dark:border-white/10'">
                                <input type="radio" :value="mode.value" v-model="form.paymentMode"
                                    class="accent-blue-500" />
                                <div><span class="text-sm text-gray-900 dark:text-white font-medium">{{ mode.label
                                        }}</span>
                                    <p class="text-xs text-gray-500">{{ mode.desc }}</p>
                                </div>
                            </label>
                        </div>
                        <!-- Dummy Payment removed -->
                    </div>
                </template>
            </div>

            <!-- Price Preview Sidebar -->
            <div>
                <div class="glass-panel p-4 sm:p-6 rounded-xl flex flex-col sticky top-[5.5rem] z-10">
                    <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined"
                            :class="moveType === 'house-shift' ? 'text-green-500' : 'text-blue-500'">receipt_long</span>
                        {{ moveType === 'house-shift' ? 'Estimated Cost' : 'Package Cost' }}
                    </h3>
                    <div
                        class="mb-4 rounded-lg border px-4 py-3"
                        :class="moveType === 'house-shift'
                            ? 'border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/5'
                            : 'border-blue-200 dark:border-blue-500/20 bg-blue-50 dark:bg-blue-500/5'">
                        <div
                            class="text-[11px] uppercase tracking-wider font-bold"
                            :class="moveType === 'house-shift' ? 'text-green-700 dark:text-green-300' : 'text-blue-700 dark:text-blue-300'">
                            {{ routingPreview?.assignment_type === 'selected' ? 'Selected Hub' : 'This Order Will Go To' }}
                        </div>
                        <div class="text-sm font-bold text-gray-900 dark:text-white mt-1">
                            {{ routingPreview?.warehouse_name || 'Resolving best available hub...' }}
                        </div>
                        <div class="text-xs text-gray-600 dark:text-gray-300 mt-1">
                            {{ routingPreview?.message || 'We will choose the best available operational hub if you do not select one.' }}
                        </div>
                    </div>

                    <!-- House Shift Pricing -->
                    <template v-if="moveType === 'house-shift'">
                        <!-- Distance badge -->
                        <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20">
                            <span class="material-symbols-outlined text-green-500 text-sm">route</span>
                            <span class="text-xs font-bold text-green-700 dark:text-green-400">{{ distanceKm }} km</span>
                            <span class="text-xs text-gray-500">(road estimate)</span>
                        </div>
                        <div v-else class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
                            <span class="material-symbols-outlined text-amber-500 text-sm">info</span>
                            <span class="text-xs text-amber-700 dark:text-amber-400">Select pickup &amp; destination to get exact pricing</span>
                        </div>
                        <div class="space-y-3 mb-4">
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Base Fare</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ quote.base.toLocaleString()
                                    }}</span></div>
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Vehicle ({{ selectedVehicle?.name
                                    }})</span><span class="text-gray-900 dark:text-white font-mono">₹{{
                                    quote.vehicle.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Labor ({{ form.laborCount }} ×
                                    ₹{{ (rates.individualLaborRate ?? 800).toLocaleString() }})</span><span class="text-gray-900 dark:text-white font-mono">₹{{
                                    quote.labor.toLocaleString() }}</span></div>
                            <div v-if="form.packingRequired" class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Packing Service</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ quote.packing.toLocaleString()
                                    }}</span></div>
                            <div v-if="materialsCostTotal > 0" class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Materials</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{
                                    materialsCostTotal.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Platform Fee</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ quote.platformFee.toLocaleString() }}</span></div>
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">GST (18%)</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ quote.taxes.toLocaleString() }}</span></div>
                            <div v-if="carryForwardCharge > 0" class="flex justify-between text-sm">
                                <span class="text-amber-600 dark:text-amber-300">Previous rejected-claim transport charge</span>
                                <span class="text-amber-600 dark:text-amber-300 font-mono">₹{{ carryForwardCharge.toLocaleString() }}</span>
                            </div>
                        </div>
                        <div class="border-t border-gray-200 dark:border-white/10 pt-4 mb-2">
                            <div class="flex justify-between items-end">
                                <span class="text-lg font-bold text-gray-900 dark:text-white">Total</span>
                                <span class="text-3xl font-bold text-green-600 dark:text-primary">₹{{
                                    bookingTotal.toLocaleString() }}</span>
                            </div>
                            <div class="text-xs text-gray-500 text-right mt-1">*Dedicated truck — no batching</div>
                        </div>
                        <div
                            class="text-xs bg-purple-50 dark:bg-purple-500/5 border border-purple-200 dark:border-purple-500/20 rounded-lg p-2 mb-4 flex items-center gap-2">
                            <span class="material-symbols-outlined text-purple-500 text-sm">timer</span>
                            <span class="text-purple-700 dark:text-purple-300">Service time block: {{ serviceTimeBlock
                                }}</span>
                        </div>
                    </template>

                    <!-- Small Package Pricing -->
                    <template v-else>
                        <!-- Distance badge -->
                        <div v-if="distanceKm" class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20">
                            <span class="material-symbols-outlined text-blue-500 text-sm">route</span>
                            <span class="text-xs font-bold text-blue-700 dark:text-blue-400">{{ distanceKm }} km</span>
                            <span class="text-xs text-gray-500">(road estimate)</span>
                        </div>
                        <div v-else class="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
                            <span class="material-symbols-outlined text-amber-500 text-sm">info</span>
                            <span class="text-xs text-amber-700 dark:text-amber-400">Select pickup &amp; destination for delivery fee</span>
                        </div>
                        <div class="space-y-3 mb-4">
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Base (by weight)</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ pkgBase.toLocaleString()
                                    }}</span></div>
                            <div class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Delivery Fee{{ distanceKm ? ' (' + distanceKm + ' km × ₹' + (rates.smallPackagePerKmRate ?? 12) + ')' : '' }}</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ pkgDeliveryFee.toLocaleString() }}</span></div>
                            <div v-if="pkgMinimumAdjustment > 0" class="flex justify-between text-sm"><span
                                    class="text-gray-500 dark:text-gray-400">Minimum Charge Adjustment</span><span
                                    class="text-gray-900 dark:text-white font-mono">₹{{ pkgMinimumAdjustment.toLocaleString() }}</span></div>
                            <div v-if="carryForwardCharge > 0" class="flex justify-between text-sm">
                                <span class="text-amber-600 dark:text-amber-300">Previous rejected-claim transport charge</span>
                                <span class="text-amber-600 dark:text-amber-300 font-mono">₹{{ carryForwardCharge.toLocaleString() }}</span>
                            </div>
                        </div>
                        <div class="border-t border-gray-200 dark:border-white/10 pt-4 mb-4">
                            <div class="flex justify-between items-end">
                                <span class="text-lg font-bold text-gray-900 dark:text-white">Total</span>
                                <span class="text-3xl font-bold text-blue-600 dark:text-blue-400">₹{{
                                    bookingTotal.toLocaleString() }}</span>
                            </div>
                            <div class="text-xs text-gray-500 text-right mt-1">Auto-pickup scheduled</div>
                        </div>
                    </template>

                    <!-- Dummy Payment text removed -->

                    <button @click="handleBookingClick"
                        class="w-full py-3 font-bold rounded-xl transition-colors text-lg mb-2 shadow-sm"
                        :class="moveType === 'house-shift' ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'">
                        {{ moveType === 'house-shift' ? 'Confirm Booking' : 'Schedule Pickup' }}
                    </button>
                    <button @click="saveQuote"
                        class="w-full py-2.5 bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 text-gray-700 dark:text-white font-bold rounded-xl transition-colors mb-2">
                        Save as Quote
                    </button>
                    <button @click="resetForm"
                        class="w-full py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 font-bold rounded-xl transition-colors text-sm flex items-center justify-center gap-1.5">
                        <span class="material-symbols-outlined text-sm">cancel</span> Cancel / Reset
                    </button>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <Teleport to="body">
            <transition enter-active-class="transition duration-300 ease-out" enter-from-class="translate-y-4 opacity-0"
                enter-to-class="translate-y-0 opacity-100" leave-active-class="transition duration-200 ease-in"
                leave-from-class="translate-y-0 opacity-100" leave-to-class="translate-y-4 opacity-0">
                <div v-if="toast.show"
                    class="fixed bottom-6 right-6 z-[100] flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl border max-w-sm"
                    :class="toast.type === 'success' ? 'bg-green-600 text-white border-green-500' : 'bg-red-600 text-white border-red-500'">
                    <span class="material-symbols-outlined">{{ toast.type === 'success' ? 'check_circle' : 'error'
                        }}</span>
                    <span class="text-sm font-medium">{{ toast.message }}</span>
                </div>
            </transition>
        </Teleport>

        <!-- Confirmation Modal -->
        <Teleport to="body">
            <BaseModal :isOpen="showConfirmModal" @close="showConfirmModal = false">
                <template #title>{{ moveType === 'house-shift' ? 'Booking Confirmed! 🎉' : 'Pickup Scheduled! 📦'
                    }}</template>
                <div class="space-y-4">
                    <div class="text-center py-4">
                        <div class="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3"
                            :class="moveType === 'house-shift' ? 'bg-green-500/20 text-green-500' : 'bg-blue-500/20 text-blue-500'">
                            <span class="material-symbols-outlined text-3xl">task_alt</span>
                        </div>
                        <p class="text-gray-700 dark:text-gray-300">
                            {{ moveType === 'house-shift' ? 'Your move has been booked!'
                            : 'Auto-pickup scheduled!' }}</p>
                        <div class="text-2xl font-mono font-bold mt-2"
                            :class="moveType === 'house-shift' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                            {{ confirmedOrderId }}</div>
                    </div>
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500 mb-1">Type</div>
                            <div class="font-medium text-gray-900 dark:text-white">
                                {{ moveType === 'house-shift' ? form.cargoType : 'Small Package' }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500 mb-1">Total</div>
                            <div class="font-bold"
                                :class="moveType === 'house-shift' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'">
                                ₹{{ bookingTotal.toLocaleString() }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500 mb-1">
                                {{ moveType === 'house-shift' ? 'Vehicle' : 'Est. Delivery' }}</div>
                            <div class="font-medium text-gray-900 dark:text-white">
                                {{ moveType === 'house-shift' ? selectedVehicle?.name : estimatedDelivery }}</div>
                        </div>
                        <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg">
                            <div class="text-xs text-gray-500 mb-1">{{ moveType === 'house-shift' ? 'Helpers' : 'Weight'
                                }}
                            </div>
                            <div class="font-medium text-gray-900 dark:text-white">{{ moveType === 'house-shift' ?
                                form.laborCount : pkg.weight + ' kg' }}</div>
                        </div>
                    </div>
                    <div class="p-3 bg-gray-50 dark:bg-white/5 rounded-lg text-sm">
                        <div class="text-xs text-gray-500 mb-1">Assigned Hub</div>
                        <div class="font-medium text-gray-900 dark:text-white">
                            {{ confirmedOrder?.warehouseName || routingPreview?.warehouse_name || 'Pending assignment' }}
                        </div>
                    </div>
                    <!-- Dummy text removed -->
                </div>
                <template #footer>
                    <div class="flex gap-3 w-full flex-wrap">
                        <button @click="openSlipWithData('bookingConfirmation', confirmedOrder, authStore.currentUser)"
                            class="flex-1 py-2 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg text-sm font-bold transition-colors flex items-center justify-center gap-1.5 hover:bg-indigo-500/20">
                            <span class="material-symbols-outlined text-sm">receipt_long</span> Booking Slip
                        </button>
                        <router-link to="/individual/orders"
                            class="flex-1 py-2 rounded-lg hover:opacity-90 transition text-sm font-bold text-center text-white"
                            :class="moveType === 'house-shift' ? 'bg-green-600' : 'bg-blue-600'">View Orders</router-link>
                        <button @click="showConfirmModal = false"
                            class="flex-1 py-2 bg-gray-100 dark:bg-white/10 text-gray-700 dark:text-white rounded-lg text-sm font-medium">Close</button>
                    </div>
                </template>
            </BaseModal>
        </Teleport>

        <!-- Razorpay Checkout -->
        <RazorpayCheckout
            v-model="showPaymentModal"
            :amount="paymentAmount"
            :description="moveType === 'house-shift' ? 'House Shift — ' + form.cargoType : 'Small Package'"
            :name="authStore.currentUser?.name || ''"
            :email="authStore.currentUser?.email || ''"
            :wallet-balance="store.walletBalance"
            @success="onRazorpaySuccess"
        />


        <!-- Map Picker Modal -->
        <MapPicker 
            :isOpen="showMapPicker" 
            :title="mapPickerTitle"
            @close="showMapPicker = false"
            @select="handleMapSelect"
        />
    </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { apiUrl, getStoredAccessToken } from '@/config/api'
import { useIndividualStore } from '@/stores/individualStore'
import { useAuthStore } from '@/stores/authStore'
import { useSlipPrinter } from '@/composables/useSlipPrinter'
import { fetchRoadDistanceKm } from '@/composables/useOsrmDistance'
import { useRates } from '@/composables/useRates'
import BaseModal from '@/components/BaseModal.vue'
import MapPicker from '@/components/MapPicker.vue'
import RazorpayCheckout from '@/components/RazorpayCheckout.vue'

const store = useIndividualStore()
const { rates } = useRates()
const moveType = ref('house-shift')

// Show AI prefill banner temporarily
const aiPrefillApplied = ref(false)

const form = reactive({
    cargoType: 'Household Goods', pickup: '', destination: '', date: '',
    timeWindow: '09:00 AM - 12:00 PM', laborCount: 2, packingRequired: true, vehicleType: 'tempo',
    materials: {},
    cargoWeightKg: null, cargoVolumeM3: null,
    instructions: '', paymentMode: 'Full Payment', isDummyPayment: false, hubId: '',
})

// Coordinates from MapPicker for distance calculation
const pickupCoords = ref(null)   // { lat, lon }
const destCoords   = ref(null)   // { lat, lon }

// Road distance via OSRM (async). Falls back to Haversine × 1.35 if OSRM fails.
const distanceKm = ref(null)
const distanceLoading = ref(false)

watch([pickupCoords, destCoords], async ([p, d]) => {
    if (!p || !d) { distanceKm.value = null; return }
    distanceLoading.value = true
    distanceKm.value = await fetchRoadDistanceKm(p.lat, p.lon, d.lat, d.lon)
    distanceLoading.value = false
})

// Map picker state
const showMapPicker = ref(false)
const mapPickerType = ref('pickup') // 'pickup' or 'destination'
const mapPickerTitle = computed(() => 
    mapPickerType.value === 'pickup' ? 'Select Pickup Location' : 'Select Destination Location'
)

function openMapPicker(type) {
    mapPickerType.value = type
    showMapPicker.value = true
}

function handleMapSelect(data) {
    if (mapPickerType.value === 'pickup') {
        form.pickup = data.address
        pickupCoords.value = { lat: data.lat, lon: data.lon }
    } else {
        form.destination = data.address
        destCoords.value = { lat: data.lat, lon: data.lon }
    }
    showMapPicker.value = false
}

const pkg = reactive({ description: '', weight: 2.5, preferredDate: '', packageType: 'Document' })

const cargoTypes = [
    { name: 'Household Goods', icon: 'chair' }, { name: 'Furniture', icon: 'table_restaurant' },
    { name: 'Luggage / Boxes', icon: 'package_2' }, { name: 'Fragile Items', icon: 'priority_high' },
    { name: 'Mixed Items', icon: 'category' },
]

const pkgTypes = [
    { name: 'Document', icon: 'description' }, { name: 'Fragile Item', icon: 'wine_bar' },
    { name: 'Soft Item', icon: 'checkroom' }, { name: 'Hard Item', icon: 'inventory_2' },
]

const paymentModes = [
    { value: 'Full Payment', label: 'Full Payment', desc: 'Pay the full amount now' },
    { value: 'Partial', label: 'Partial Payment', desc: '50% now, rest on delivery' },
    { value: 'COD', label: 'Cash on Delivery', desc: 'Pay when delivered' },
]

const timeSlots = [
    { value: '06:00 AM - 09:00 AM', label: '6 – 9 AM', demand: 'Low Demand', demandColor: 'text-green-500', priceTag: '-5%', priceColor: 'text-green-600 dark:text-green-400', recommended: false },
    { value: '09:00 AM - 12:00 PM', label: '9 – 12 PM', demand: 'Medium', demandColor: 'text-amber-500', priceTag: 'Standard', priceColor: 'text-gray-500', recommended: false },
    { value: '12:00 PM - 03:00 PM', label: '12 – 3 PM', demand: 'Low Demand', demandColor: 'text-green-500', priceTag: '-8%', priceColor: 'text-green-600 dark:text-green-400', recommended: true },
    { value: '03:00 PM - 06:00 PM', label: '3 – 6 PM', demand: 'High Demand', demandColor: 'text-red-500', priceTag: '+10%', priceColor: 'text-red-500', recommended: false },
]

const routingPreview = computed(() => store.assignmentPreview)

const selectedVehicle = computed(() => store.vehicleTypes.find(v => v.key === form.vehicleType))
const serviceTimeBlock = computed(() => { const v = selectedVehicle.value; return v?.key === 'hcv' ? '4-5 hours' : v?.key === 'lcv' ? '3-4 hours' : v?.key === 'tempo' ? '2-3 hours' : '1-2 hours' })

const materialsCostTotal = computed(() => { let t = 0; for (const mat of packingCatalog.value) { t += (form.materials[mat.key] || 0) * mat.price }; return t })
// Use real distance if both locations selected, otherwise fall back to 10 km minimum
const effectiveDistanceKm = computed(() => distanceKm.value ?? 10)
const quote = computed(() => store.calculateQuote(effectiveDistanceKm.value, form.laborCount, form.packingRequired, materialsCostTotal.value, form.vehicleType, rates.value))
const totalCost = computed(() => quote.value.total)

// Small Package pricing — base by weight + per-km delivery fee (from rate governance)
const pkgBase = computed(() => Math.round((pkg.weight || 1) * (rates.value.smallPackagePerKgRate ?? 120)))
const pkgDeliveryFee = computed(() => distanceKm.value ? Math.round(distanceKm.value * (rates.value.smallPackagePerKmRate ?? 12)) : 50)
const pkgSubtotal = computed(() => pkgBase.value + pkgDeliveryFee.value)
const pkgMinimumAdjustment = computed(() => Math.max((rates.value.minimumCharge ?? 500) - pkgSubtotal.value, 0))
const pkgTotal = computed(() => pkgSubtotal.value + pkgMinimumAdjustment.value)
const carryForwardCharge = computed(() => Number(store.pendingTransportCharge || 0))
const bookingBaseTotal = computed(() => moveType.value === 'house-shift' ? totalCost.value : pkgTotal.value)
const bookingTotal = computed(() => bookingBaseTotal.value + carryForwardCharge.value)
const estimatedDelivery = computed(() => {
    if (!pkg.preferredDate) return null
    const d = new Date(pkg.preferredDate); d.setDate(d.getDate() + 2)
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
})

const toast = reactive({ show: false, message: '', type: 'success' })
function showToast(message, type = 'success') { toast.show = true; toast.message = message; toast.type = type; setTimeout(() => { toast.show = false }, 3000) }

const authStore = useAuthStore()
const { openSlipWithData } = useSlipPrinter()
const showConfirmModal = ref(false)
const confirmedOrderId = ref('')
const confirmedOrder = ref(null)

const showPaymentModal = ref(false)
const isProcessingPayment = ref(false)

const paymentAmount = computed(() => {
    if (form.paymentMode === 'Partial') return Math.round((bookingBaseTotal.value / 2) + carryForwardCharge.value)
    return bookingTotal.value
})

function handleBookingClick() {
    if (!form.pickup || !form.destination) { showToast('Please fill pickup and destination.', 'error'); return }
    if (moveType.value === 'house-shift' && !form.date) { showToast('Please select a date.', 'error'); return }
    if (moveType.value === 'small-package' && !pkg.preferredDate) { showToast('Please select a pickup date.', 'error'); return }

    if (form.paymentMode === 'COD') {
        confirmBooking()
    } else {
        showPaymentModal.value = true
    }
}

const razorpayMethod = ref('Online')

function onRazorpaySuccess({ payment_id, method, amount }) {
    razorpayMethod.value = method
    showPaymentModal.value = false
    confirmBooking(payment_id, method)
}

async function confirmBooking(payment_id = null, method = null) {
    try {
        const order = await store.createOrder({
            moveType: moveType.value, cargoType: moveType.value === 'house-shift' ? form.cargoType : pkg.packageType,
            pickup: form.pickup, destination: form.destination,
            date: moveType.value === 'house-shift' ? form.date : pkg.preferredDate,
            timeWindow: moveType.value === 'house-shift' ? form.timeWindow : 'Auto-Scheduled',
            laborCount: moveType.value === 'house-shift' ? form.laborCount : 0,
            packingRequired: moveType.value === 'house-shift' ? form.packingRequired : false,
            vehicleType: moveType.value === 'house-shift' ? form.vehicleType : 'mini-truck',
            materials: moveType.value === 'house-shift' ? { ...form.materials } : {},
            materialItems: moveType.value === 'house-shift'
                ? packingCatalog.value
                    .filter(m => (form.materials[m.key] || 0) > 0)
                    .map(m => ({
                        id: m.id || m.key,
                        key: m.key,
                        name: m.name,
                        sku: m.sku || '',
                        quantity: form.materials[m.key],
                    }))
                : [],
            cost: moveType.value === 'house-shift' ? { ...quote.value } : { base: pkgBase.value, labor: 0, materials: 0, packing: 0, vehicle: 0, total: pkgTotal.value },
            carryForwardChargeAmount: carryForwardCharge.value,
            paymentMode: form.paymentMode, isDummyPayment: false,
            preferredPickupDate: moveType.value === 'small-package' ? pkg.preferredDate : null,
            estimatedDelivery: moveType.value === 'small-package' ? estimatedDelivery.value : null,
            paymentStatus: form.paymentMode === 'COD' ? 'pending' : (form.paymentMode === 'Partial' ? 'partial' : 'paid'),
            paymentAmount: form.paymentMode === 'COD' ? 0 : paymentAmount.value,
            paymentRef: payment_id,
            paymentMethod: method || razorpayMethod.value || 'Online',
            packageWeight: moveType.value === 'small-package' ? pkg.weight : null,
            cargoWeightKg: moveType.value === 'house-shift' ? form.cargoWeightKg : null,
            cargoVolumeM3: moveType.value === 'house-shift' ? form.cargoVolumeM3 : null,
            warehouseId: form.hubId || null,
        })

        confirmedOrderId.value = order.id
        confirmedOrder.value = order
        showConfirmModal.value = true
        showToast('Order created successfully!', 'success')
    } catch (error) {
        console.error('Failed to create order:', error)
        const msg = error?.message || 'Failed to create order. Please try again.'
        showToast(msg.length > 80 ? msg.substring(0, 80) + '…' : msg, 'error')
    }
}

function saveQuote() {
    const total = moveType.value === 'house-shift' ? totalCost.value : pkgTotal.value
    store.addQuote({ 
        cargoType: moveType.value === 'house-shift' ? form.cargoType : pkg.packageType, 
        from: form.pickup || 'Not specified', 
        to: form.destination || 'Not specified', 
        laborCount: moveType.value === 'house-shift' ? form.laborCount : 0, 
        packing: moveType.value === 'house-shift' ? form.packingRequired : false, 
        total: total 
    })
    showToast('Quote saved successfully!')
}

function resetForm() {
    form.pickup = ''; form.destination = ''; form.date = ''; form.laborCount = 2
    form.packingRequired = true; form.cargoType = 'Household Goods'; form.vehicleType = 'tempo'
    form.cargoWeightKg = null; form.cargoVolumeM3 = null
    form.materials = {}
    form.instructions = ''; form.paymentMode = 'Full Payment'; form.isDummyPayment = false; form.hubId = ''
    pkg.description = ''; pkg.weight = 2.5; pkg.preferredDate = ''; pkg.packageType = 'Document'
    pickupCoords.value = null; destCoords.value = null
    showToast('Form reset.', 'success')
}

watch(
    () => store.aiPrefill,
    (prefill) => {
        if (!prefill) return
        moveType.value = 'house-shift'
        form.vehicleType = prefill.vehicleType || form.vehicleType
        form.laborCount = Number(prefill.laborCount || form.laborCount)
        form.cargoType = prefill.cargoType || form.cargoType
        form.packingRequired = Boolean(prefill.packingRequired)
        if (prefill.estimatedVolumeM3 !== null && prefill.estimatedVolumeM3 !== undefined) {
            const normalizedVolume = Number(prefill.estimatedVolumeM3)
            form.cargoVolumeM3 = Number.isFinite(normalizedVolume) && normalizedVolume > 0
                ? normalizedVolume
                : form.cargoVolumeM3
        }
        aiPrefillApplied.value = true
        window.setTimeout(() => {
            aiPrefillApplied.value = false
        }, 5000)
        store.clearAiPrefill()
    },
    { deep: true }
)

watch(() => form.hubId, async (hubId) => {
    const preview = await store.fetchOrderAssignmentPreview(hubId || null).catch(() => null)
    form.materials = {}
    await fetchPackingCatalog(hubId || preview?.warehouse_id || null)
})

// Packing materials — fetched from real WM inventory so customer sees exact same items
const packingCatalog = ref([])
const packingCatalogLoading = ref(false)

const PACKING_KEYWORDS = ['pack', 'wrap', 'box', 'carton', 'tape', 'label', 'blanket', 'crate', 'film', 'pallet', 'protector', 'bag', 'rope', 'bubble', 'foam', 'sheet']
const MATERIAL_ICONS = { box: 'inventory_2', carton: 'inventory_2', wrap: 'bubble_chart', bubble: 'bubble_chart', tape: 'straighten', blanket: 'bedding', crate: 'deployed_code', pallet: 'pallet', bag: 'shopping_bag', foam: 'layers', sheet: 'layers', default: 'package_2' }

function iconForItem(name) {
    const lower = (name || '').toLowerCase()
    for (const [kw, icon] of Object.entries(MATERIAL_ICONS)) {
        if (lower.includes(kw)) return icon
    }
    return MATERIAL_ICONS.default
}

async function fetchPackingCatalog(warehouseId = null) {
    packingCatalogLoading.value = true
    try {
        const token = getStoredAccessToken()
        const query = warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''
        const res = await fetch(apiUrl(`api/v1/inventory/packing-catalog${query}`), {
            headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
        })
        if (res.ok) {
            const items = await res.json()
            packingCatalog.value = items.map(item => {
                // Price: inventory selling_price → matched rates catalog → fallback 50
                const ratesMat = rates.value.materials?.find?.(m =>
                    (item.name || '').toLowerCase().includes(m.id.toLowerCase()) ||
                    (item.sku || '').toLowerCase().includes(m.id.toLowerCase())
                )
                const price = (item.selling_price && item.selling_price > 0)
                    ? item.selling_price
                    : (ratesMat?.rate || 50)
                return {
                    key: item.id,
                    name: item.name,
                    sku: item.sku,
                    price,
                    unit: item.unit || ratesMat?.unit || 'pcs',
                    stock: item.stock,
                    icon: iconForItem(item.name)
                }
            })
        }
    } catch (e) {
        // silently fall back below
    }
    // Fallback to rates catalog if inventory unavailable
    if (packingCatalog.value.length === 0) {
        packingCatalog.value = store.materialsCatalog
    }
    packingCatalogLoading.value = false
}

onMounted(async () => {
    await store.fetchWarehouses()
    const preview = await store.fetchOrderAssignmentPreview(form.hubId || null)
    await store.fetchWalletBalance()
    await fetchPackingCatalog(form.hubId || preview?.warehouse_id || null)
})
</script>
