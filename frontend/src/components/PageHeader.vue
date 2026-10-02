<template>
  <header class="page-header" :class="{ 'page-header--compact': compact }">
    <div class="page-header-main">
      <div class="page-header-title-row">
        <span class="page-header-mark"></span>
        <h1 class="page-title">{{ title }}</h1>
      </div>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.extra" class="page-header-extra">
      <slot name="extra" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.page-header { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; margin-bottom:22px; }
.page-header--compact { margin-bottom:16px; }
.page-header-main { flex:1; min-width:0; }
.page-header-title-row { display:flex; align-items:center; gap:12px; }
.page-header-mark { width:4px; height:22px; border-radius:999px; background: var(--gradient); flex-shrink:0; }
.page-title { font-size:24px; font-weight:700; color:var(--text-primary); line-height:1.25; letter-spacing:-.02em; }
.page-subtitle { color:var(--text-secondary); font-size:14px; margin-top:8px; line-height:1.7; max-width: 920px; }
.page-header-extra { flex-shrink:0; display:flex; align-items:center; gap:10px; }
@media (max-width: 768px) { .page-header { flex-direction:column; gap:14px; } .page-title { font-size:22px; } }
</style>
