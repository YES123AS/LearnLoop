<template>
  <div class="error-state glass-panel">
    <el-icon v-if="icon" :size="48" color="#f59e0b">
      <component :is="icon" />
    </el-icon>
    <p class="error-title">{{ title }}</p>
    <p v-if="hint" class="error-hint">{{ hint }}</p>
    <div v-if="$slots.default" class="error-body">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  hint: { type: String, default: '' },
  icon: { type: [Object, String], default: null }
})
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 40px 24px;
  gap: 12px;
  color: var(--text-secondary);
  text-align: center;
}

.error-title {
  font-size: 15px;
  font-weight: 600;
  color: #b45309;
}

.error-hint {
  font-size: 13px;
  opacity: 0.85;
  line-height: 1.6;
}

.error-body {
  margin-top: 8px;
  width: 100%;
  text-align: left;
}
</style>
