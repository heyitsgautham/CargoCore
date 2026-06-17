<template>
  <div class="relative flex items-center gap-3">
    <div class="hidden md:flex flex-col text-right border-r border-gray-200 dark:border-white/10 pr-4">
      <span class="text-sm font-bold text-gray-900 dark:text-white leading-none">{{ currentTime }}</span>
      <span class="text-[10px] text-gray-500 uppercase tracking-widest mt-1">{{ currentDate }}</span>
    </div>

    <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/5" :title="weather.detail">
      <span class="material-symbols-outlined text-gray-500 dark:text-gray-400 text-[18px]" :class="weather.loading ? 'animate-spin' : ''">{{ weather.icon }}</span>
      <div>
        <div class="text-sm font-bold text-gray-700 dark:text-gray-200 leading-none">{{ weather.tempLabel }}</div>
        <div class="text-[10px] text-gray-500 truncate max-w-[120px]">{{ weather.detail }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { apiUrl } from '@/config/api'

defineProps({
  hubId: {
    type: [String, Number],
    default: null,
  },
})

const WEATHER_CACHE_KEY = 'header_weather_cache'
const WEATHER_CACHE_MAX_AGE_MS = 15 * 60 * 1000
const WEATHER_REFRESH_MS = 10 * 60 * 1000

const currentTime = ref('')
const currentDate = ref('')
const weather = ref({
  tempLabel: '--',
  detail: 'Locating weather...',
  icon: 'progress_activity',
  loading: true,
})

let timeInterval = null
let weatherInterval = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  currentDate.value = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
}

function readWeatherCache() {
  if (typeof window === 'undefined') return null

  try {
    const raw = localStorage.getItem(WEATHER_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed?.timestamp || !parsed?.payload) return null
    if (Date.now() - parsed.timestamp > WEATHER_CACHE_MAX_AGE_MS) return null
    return parsed.payload
  } catch {
    return null
  }
}

function writeWeatherCache(payload) {
  if (typeof window === 'undefined') return
  localStorage.setItem(WEATHER_CACHE_KEY, JSON.stringify({
    timestamp: Date.now(),
    payload,
  }))
}

function getWeatherPresentation(code, isDay) {
  if (code === 0) {
    return {
      condition: 'Clear',
      icon: isDay ? 'sunny' : 'clear_night',
    }
  }

  if ([1, 2, 3].includes(code)) {
    return {
      condition: code === 1 ? 'Mostly Clear' : 'Partly Cloudy',
      icon: isDay ? 'partly_cloudy_day' : 'partly_cloudy_night',
    }
  }

  if ([45, 48].includes(code)) {
    return { condition: 'Foggy', icon: 'foggy' }
  }

  if ([51, 53, 55, 56, 57].includes(code)) {
    return { condition: 'Drizzle', icon: 'grain' }
  }

  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) {
    return { condition: 'Rain', icon: 'rainy' }
  }

  if ([71, 73, 75, 77, 85, 86].includes(code)) {
    return { condition: 'Snow', icon: 'weather_snowy' }
  }

  if ([95, 96, 99].includes(code)) {
    return { condition: 'Storm', icon: 'thunderstorm' }
  }

  return { condition: 'Weather Live', icon: 'cloud' }
}

function getLocationLabel(address = {}) {
  return (
    address.city
    || address.town
    || address.village
    || address.suburb
    || address.state
    || 'Live Location'
  )
}

function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation unsupported'))
      return
    }

    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: WEATHER_CACHE_MAX_AGE_MS,
    })
  })
}

async function fetchLocationLabel(latitude, longitude) {
  try {
    const response = await fetch(apiUrl(`api/v1/geocoding/reverse?lat=${latitude}&lon=${longitude}`))
    if (!response.ok) throw new Error('Reverse geocoding failed')
    const data = await response.json()
    return getLocationLabel(data.address || {})
  } catch {
    return 'Live Location'
  }
}

async function fetchWeather(latitude, longitude) {
  const response = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true&timezone=auto`
  )
  if (!response.ok) {
    throw new Error('Weather lookup failed')
  }

  const data = await response.json()
  const currentWeather = data.current_weather
  if (!currentWeather) {
    throw new Error('Missing weather payload')
  }

  return currentWeather
}

async function refreshWeather() {
  weather.value = {
    ...weather.value,
    loading: true,
    icon: 'progress_activity',
  }

  try {
    const position = await getCurrentPosition()
    const latitude = position.coords.latitude
    const longitude = position.coords.longitude

    const [currentWeather, locationLabel] = await Promise.all([
      fetchWeather(latitude, longitude),
      fetchLocationLabel(latitude, longitude),
    ])

    const presentation = getWeatherPresentation(
      Number(currentWeather.weathercode),
      Number(currentWeather.is_day) === 1
    )

    const payload = {
      tempLabel: `${Math.round(Number(currentWeather.temperature))}°C`,
      detail: `${locationLabel} · ${presentation.condition}`,
      icon: presentation.icon,
      loading: false,
    }

    weather.value = payload
    writeWeatherCache(payload)
  } catch (_) {
    const cached = readWeatherCache()
    if (cached) {
      weather.value = {
        ...cached,
        loading: false,
      }
      return
    }

    weather.value = {
      tempLabel: '--',
      detail: 'Location weather unavailable',
      icon: 'location_off',
      loading: false,
    }
  }
}

onMounted(() => {
  updateTime()
  const cached = readWeatherCache()
  if (cached) {
    weather.value = {
      ...cached,
      loading: false,
    }
  }
  timeInterval = setInterval(updateTime, 1000)
  refreshWeather().catch(() => {})
  weatherInterval = setInterval(() => {
    refreshWeather().catch(() => {})
  }, WEATHER_REFRESH_MS)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (weatherInterval) clearInterval(weatherInterval)
})
</script>
