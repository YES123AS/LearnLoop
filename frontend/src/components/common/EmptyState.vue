<template>
  <div class="state-card glass-panel state-empty">
    <el-icon v-if="icon" :size="iconSize" class="state-icon">
      <component :is="icon" />
    </el-icon>
    <h3 v-if="title" class="state-title">{{ title }}</h3>
    <p v-if="description" class="state-description">{{ description }}</p>
    <div v-if="hasAction" class="state-actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  icon: { type: [Object, String], default: null },
  iconSize: { type: Number, default: 42 },
  hasAction: { type: Boolean, default: false }
})
</script>

<style scoped>
.state-card { padding: 24px; text-align: center; }
.state-icon { margin-bottom: 8px; color: var(--primary); }
.state-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; color: var(--text-primary); }
.state-description { font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.state-actions { margin-top: 12px; display: flex; justify-content: center; }
</style>
