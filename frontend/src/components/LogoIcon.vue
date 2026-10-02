<template>
  <svg
    class="logo-icon"
    :class="$attrs.class"
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-label="智学环 LearnLoop Logo"
  >
    <defs>
      <linearGradient id="learnloop-main" x1="10" y1="8" x2="54" y2="56" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#3b82f6" />
        <stop offset="50%" stop-color="#6366f1" />
        <stop offset="100%" stop-color="#8b5cf6" />
      </linearGradient>
      <linearGradient id="learnloop-soft" x1="16" y1="14" x2="48" y2="50" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95" />
        <stop offset="100%" stop-color="#dbeafe" stop-opacity="0.65" />
      </linearGradient>
      <filter id="learnloop-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#4f46e5" flood-opacity="0.25" />
      </filter>
    </defs>

    <rect
      x="6"
      y="6"
      width="52"
      height="52"
      rx="16"
      fill="url(#learnloop-main)"
      filter="url(#learnloop-shadow)"
    />

    <circle cx="32" cy="32" r="20" fill="white" opacity="0.10" />
    <circle cx="22" cy="18" r="10" fill="white" opacity="0.10" />

    <path
      d="M44.5 25.2C42.1 19.9 36.6 16.5 30.7 17.2C23.8 18 18.6 23.8 18.6 30.8C18.6 38.5 24.9 44.8 32.6 44.8C37.3 44.8 41.5 42.5 44 38.9"
      stroke="url(#learnloop-soft)"
      stroke-width="4.2"
      stroke-linecap="round"
    />

    <path
      d="M43.6 18.4L45.7 26.5L37.6 24.5"
      stroke="white"
      stroke-width="3.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      opacity="0.95"
    />

    <path
      d="M25.2 28.2C25.2 26.9 26.3 25.9 27.6 26.1C29.3 26.3 30.9 26.9 32 28C33.1 26.9 34.7 26.3 36.4 26.1C37.7 25.9 38.8 26.9 38.8 28.2V39.1C38.8 39.9 38.1 40.4 37.4 40.3C35.5 40 33.6 40.3 32 41.4C30.4 40.3 28.5 40 26.6 40.3C25.9 40.4 25.2 39.9 25.2 39.1V28.2Z"
      fill="white"
      opacity="0.92"
    />

    <path
      d="M32 28.4V41.1"
      stroke="#6366f1"
      stroke-width="1.8"
      stroke-linecap="round"
      opacity="0.85"
    />

    <circle cx="20.2" cy="34.5" r="2.5" fill="#ffffff" opacity="0.95" />
    <circle cx="43.8" cy="34.5" r="2.5" fill="#ffffff" opacity="0.95" />
    <circle cx="32" cy="18.7" r="2.3" fill="#ffffff" opacity="0.95" />

    <path
      d="M47.8 43.2L49 45.9L51.7 47.1L49 48.3L47.8 51L46.6 48.3L43.9 47.1L46.6 45.9L47.8 43.2Z"
      fill="white"
      opacity="0.9"
    />
  </svg>
</template>

<script setup>
defineOptions({ inheritAttrs: false })

defineProps({
  size: {
    type: [Number, String],
    default: 40
  }
})
</script>

<style scoped>
.logo-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
