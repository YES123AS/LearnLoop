<template>
  <div class="empty-state glass-panel" :class="{ 'empty-state--compact': compact }">
    <el-icon v-if="icon" :size="iconSize" :color="iconColor">
      <component :is="icon" />
    </el-icon>
    <p class="empty-title">{{ title }}</p>
    <p v-if="hint" class="empty-hint">{{ hint }}</p>
    <div v-if="$slots.default" class="empty-actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  hint: { type: String, default: '' },
  icon: { type: [Object, String], default: null },
  iconSize: { type: Number, default: 48 },
  iconColor: { type: String, default: '#6366f1' },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px 24px;
  gap: 10px;
  color: var(--text-secondary);
  text-align: center;
}

.empty-state--compact {
  padding: 40px 20px;
}

.empty-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.empty-hint {
  font-size: 13px;
  color: var(--text-secondary);
  opacity: 0.85;
  line-height: 1.6;
  max-width: 360px;
}

.empty-actions {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
</style>
