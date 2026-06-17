<template>
    <svg :class="className" viewBox="0 0 3787 2842" fill="none" xmlns="http://www.w3.org/2000/svg"
        class="pointer-events-none absolute z-[1] w-[138%] h-[169%] opacity-0 animate-spotlight">
        <g filter="url(#filter0_f_107_7424)">
            <ellipse cx="1924.71" cy="273.501" rx="1924.71" ry="273.501"
                transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)" fill="white"
                fill-opacity="0.21" />
        </g>
        <defs>
            <filter id="filter0_f_107_7424" x="0.860352" y="0.838989" width="3785.16" height="2840.26"
                filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
                <feFlood flood-opacity="0" result="BackgroundImageFix" />
                <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
                <feGaussianBlur stdDeviation="151" result="effect1_foregroundBlur_107_7424" />
            </filter>
        </defs>
    </svg>
</template>

<script setup>
defineProps({
    className: {
        type: String,
        default: ''
    }
})
</script>

<style scoped>
@keyframes spotlight {
    0% {
        opacity: 0;
        transform: translate(-72%, -62%) scale(0.5);
    }

    100% {
        opacity: 1;
        transform: translate(-50%, -40%) scale(1);
    }
}

.animate-spotlight {
    animation: spotlight 2s ease .75s 1 forwards;
}
</style>
