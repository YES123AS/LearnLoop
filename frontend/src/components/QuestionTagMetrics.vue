<template>
  <div class="tag-metrics">
    <el-tooltip v-for="item in metrics" :key="item.key" :content="item.tip" placement="top">
      <div class="metric-item">
        <div class="metric-top">
          <span class="metric-name">{{ item.label }}</span>
          <el-tag :type="item.type" size="small" effect="light">{{ item.score }}/5</el-tag>
        </div>
        <el-progress :percentage="item.score * 20" :stroke-width="6" :show-text="false" :color="item.color" />
        <div class="metric-desc">{{ item.level }}</div>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { normalizeQuestionTags, getTagLevel, getTagColor } from '@/utils/questionTags'

const props = defineProps({
  question: { type: Object, default: () => ({}) }
})

const colorMap = {
  info: '#94a3b8',
  warning: '#f59e0b',
  primary: '#6366f1',
  success: '#22c55e'
}

const labelMap = {
  difficulty: '难度',
  innovation: '创新度',
  importance: '重要度',
  integration: '综合度'
}

const tipMap = {
  difficulty: '题目难度越高，对基础与思维要求越高',
  innovation: '创新度越高，题目变化与新情境越多',
  importance: '重要度越高，越接近核心高频考点',
  integration: '综合度越高，越需要多知识点联动'
}

const metrics = computed(() => {
  const tags = normalizeQuestionTags(props.question)
  return Object.entries(tags).map(([key, score]) => ({
    key,
    label: labelMap[key],
    score,
    level: getTagLevel(score),
    type: getTagColor(score),
    color: colorMap[getTagColor(score)],
    tip: tipMap[key]
  }))
})
</script>

<style scoped>
.tag-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 12px 0;
}

.metric-item {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
}

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.metric-name {
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-desc {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

@media (max-width: 900px) {
  .tag-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
