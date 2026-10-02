<template>
  <div class="state-card glass-panel state-error">
    <h3 v-if="title" class="state-title">{{ title }}</h3>
    <p v-if="message" class="state-message">{{ message }}</p>
    <p v-if="details" class="state-details">{{ details }}</p>
    <div v-if="hasRetry || $slots.default" class="state-actions">
      <slot />
      <el-button v-if="hasRetry" type="primary" plain @click="emit('retry')">重试</el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  details: { type: String, default: '' },
  hasRetry: { type: Boolean, default: false }
})

const emit = defineEmits(['retry'])
</script>

<style scoped>
.state-card { padding: 20px; }
.state-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; color: var(--text-primary); }
.state-message { font-size: 13px; line-height: 1.6; color: #b45309; }
.state-details { font-size: 12px; line-height: 1.6; color: var(--text-secondary); margin-top: 6px; white-space: pre-wrap; word-break: break-word; }
.state-actions { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
</style>
