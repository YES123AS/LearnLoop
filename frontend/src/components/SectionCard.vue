<template>
  <section class="section-card card-panel" :class="[`section-card--${padding}`, className]">
    <header v-if="title || desc || $slots.header" class="section-card-header">
      <slot name="header">
        <h2 v-if="title" class="section-heading">{{ title }}</h2>
        <p v-if="desc" class="section-desc">{{ desc }}</p>
      </slot>
    </header>
    <div class="section-card-body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  desc: { type: String, default: '' },
  padding: { type: String, default: 'normal' },
  className: { type: String, default: '' }
})
</script>

<style scoped>
.section-card-header { margin-bottom: 16px; }
.section-card-header:empty { display:none; }
.section-desc { font-size:13px; color:var(--text-secondary); margin-top:6px; line-height:1.7; }
.section-card--compact { padding:16px 20px; }
.section-card--normal { }
.section-card-body:empty { display:none; }
.section-card { margin-bottom: 16px; }
</style>
