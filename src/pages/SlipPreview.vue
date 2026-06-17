<!-- Renders a CargoCore HTML slip stored in localStorage by useSlipPrinter.
     Opened in a new tab via /slip-preview?k=<key>.
     Survives browser refresh because the route is a real URL and
     localStorage persists across refreshes within the same origin. -->
<template>
  <iframe ref="frame" style="position:fixed;inset:0;width:100%;height:100%;border:none;" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const frame = ref(null)
const route = useRoute()

onMounted(() => {
  const key = route.query.k
  const html = key ? localStorage.getItem(key) : null

  if (html && frame.value) {
    frame.value.srcdoc = html
  } else {
    document.body.innerHTML = '<div style="font-family:sans-serif;padding:40px;color:#555"><h2>Slip not found</h2><p>This slip may have expired. Please reopen it from the app.</p></div>'
  }
})
</script>
