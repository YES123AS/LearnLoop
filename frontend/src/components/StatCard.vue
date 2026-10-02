<template>
  <div class="stat-card card-panel">
    <div class="stat-icon" :style="{ background: iconBg }">
      <el-icon :size="24"><component :is="icon" /></el-icon>
    </div>
    <div class="stat-info">
      <div class="stat-value-row">
        <span class="stat-value">{{ value }}</span>
        <span v-if="trend" class="stat-trend" :class="trend > 0 ? 'up' : 'down'">
          <el-icon><component :is="trend > 0 ? 'Top' : 'Bottom'" /></el-icon>
          {{ Math.abs(trend) }}%
        </span>
      </div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: 'DataAnalysis' },
  iconBg: { type: String, default: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
  trend: { type: Number, default: 0 }
})
</script>

<style scoped>
.stat-card { display:flex; align-items:center; gap:16px; padding:20px 22px; min-height: 96px; }
.stat-icon { width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center; color:#fff; flex-shrink:0; box-shadow:0 4px 14px rgba(99,102,241,.2); }
.stat-value-row { display:flex; align-items:baseline; gap:10px; }
.stat-value { font-size:28px; font-weight:700; color:var(--text-primary); line-height:1.1; font-variant-numeric:tabular-nums; }
.stat-trend { display:inline-flex; align-items:center; gap:2px; font-size:12px; font-weight:600; padding:2px 8px; border-radius:12px; }
.stat-trend.up { color:#16a34a; background:rgba(34,197,94,.1); }
.stat-trend.down { color:#dc2626; background:rgba(239,68,68,.1); }
.stat-label { font-size:13px; color:var(--text-secondary); margin-top:4px; font-weight:500; }
@media (max-width: 768px) { .stat-card { padding:18px; } .stat-value { font-size:24px; } }
</style>
