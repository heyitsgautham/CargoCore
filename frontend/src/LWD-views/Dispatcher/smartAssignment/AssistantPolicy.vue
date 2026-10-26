<template>
    <div class="glass-panel rounded-xl p-6">
        <h3 class="mb-4 font-bold text-gray-900 dark:text-white">AI Dispatch Assistant Policy</h3>
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">Rules</div>
                <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                    Order must be accepted and ready. Standard warehouse flow requires a released vehicle lock. Direct recurring/vendor non-packing flow allows dispatcher vehicle selection with AI support.
                </div>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">AI Support</div>
                <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                    AI recommends the best available driver, predicts dispatch delay, flags missing resources, and explains why the recommendation fits the job.
                </div>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-white/5 dark:bg-white/5">
                <div class="mb-2 text-sm font-bold text-gray-900 dark:text-white">Dispatcher Decision</div>
                <div class="text-[11px] leading-5 text-gray-500 dark:text-gray-400">
                    Dispatcher reviews the AI suggestion, confirms the one-to-one assignment, and hands off the trip to the driver for pickup, transit, and unloading.
                </div>
            </div>
        </div>
    </div>
</template>
