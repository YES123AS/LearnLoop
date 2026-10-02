<template>
  <div class="state-card glass-panel state-loading">
    <h3 v-if="title" class="state-title">{{ title }}</h3>
    <p v-if="description" class="state-description">{{ description }}</p>
    <div class="state-loading-row">
      <el-icon :size="20" class="state-spinner"><Loading /></el-icon>
      <span class="state-loading-text">{{ loadingText }}</span>
    </div>
    <p v-if="stageText" class="state-stage">{{ stageText }}</p>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  loadingText: { type: String, default: '加载中...' },
  stageText: { type: String, default: '' }
})
</script>

<style scoped>
.state-card { padding: 20px; }
.state-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; color: var(--text-primary); }
.state-description, .state-stage { font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.state-loading-row { display: flex; align-items: center; gap: 8px; margin-top: 12px; }
.state-spinner { animation: spin 1s linear infinite; color: var(--primary); }
.state-loading-text { font-size: 14px; color: var(--text-primary); }
.state-stage { margin-top: 10px; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
