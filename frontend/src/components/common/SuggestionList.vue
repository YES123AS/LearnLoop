<template>
  <div v-if="visible" class="card-panel section-card suggestion-card" :class="[`layout-${layout}`]">
    <div class="suggestion-head">
      <div>
        <h3 v-if="title" class="section-heading">{{ title }}</h3>
        <p v-if="description" class="suggestion-desc">{{ description }}</p>
      </div>
    </div>

    <div v-if="normalizedItems.length" class="suggestion-list" :class="[`suggestion-list--${layout}`]">
      <button
        v-for="item in normalizedItems"
        :key="item.__key"
        class="suggestion-item"
        :class="{ active: isActive(item), disabled: disabled }"
        :disabled="disabled"
        @click="selectItem(item)"
      >
        <strong class="suggestion-label">{{ item.__label }}</strong>
        <p v-if="item.__desc" class="suggestion-description">{{ item.__desc }}</p>
      </button>
    </div>

    <p v-else class="suggestion-empty">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  layout: { type: String, default: 'vertical' },
  itemLabelKey: { type: String, default: 'label' },
  itemDescKey: { type: String, default: 'description' },
  itemKeyKey: { type: String, default: 'key' },
  disabled: { type: Boolean, default: false },
  activeKey: { type: [String, Number, Object], default: null },
  emptyText: { type: String, default: '暂无可用建议' },
  visible: { type: Boolean, default: true }
})

const emit = defineEmits(['select'])

const normalizedItems = computed(() => (props.items || []).map((item, index) => {
  const label = item?.[props.itemLabelKey] ?? item?.label ?? item?.title ?? String(item)
  const desc = item?.[props.itemDescKey] ?? item?.description ?? item?.desc ?? ''
  const key = item?.[props.itemKeyKey] ?? item?.key ?? index
  return { ...item, __label: label, __desc: desc, __key: key }
}))

function selectItem(item) {
  if (props.disabled) return
  emit('select', item)
}

function isActive(item) {
  if (props.activeKey === null || props.activeKey === undefined) return false
  return item.__key === props.activeKey || item.key === props.activeKey
}
</script>

<style scoped>
.suggestion-card { padding: 14px; }
.suggestion-head { margin-bottom: 10px; }
.suggestion-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-top: 4px; }
.suggestion-list { display: flex; gap: 10px; }
.suggestion-list--grid { flex-wrap: wrap; }
.suggestion-list--vertical { flex-direction: column; }
.suggestion-list--inline { flex-wrap: wrap; }
.suggestion-item {
  text-align: left;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.84);
  border-radius: 14px;
  padding: 12px;
  cursor: pointer;
  transition: 0.18s ease;
}
.suggestion-item:hover:not(.disabled), .suggestion-item.active {
  border-color: rgba(99,102,241,.25);
  background: rgba(99,102,241,.08);
}
.suggestion-item.disabled { cursor: not-allowed; opacity: .78; }
.suggestion-label { display: block; margin-bottom: 6px; font-size: 14px; color: var(--text-primary); }
.suggestion-description { font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.suggestion-empty { font-size: 13px; color: var(--text-secondary); padding: 8px 2px; }
</style>
