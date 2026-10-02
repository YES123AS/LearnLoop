<template>
  <div class="profile-center">
    <div class="center-header glass-panel">
      <div class="avatar-ring">
        <el-icon :size="32"><Cpu /></el-icon>
      </div>
      <div>
        <h3>画像概览</h3>
        <p class="profile-summary">
          <template v-if="hasProfileData">
            {{ profile.grade || '—' }} · {{ profile.major || '—' }} · {{ profile.course || '—' }}
          </template>
          <template v-else>画像信息待完善</template>
        </p>
        <span class="ai-badge">学习档案 · 实时同步</span>
      </div>
    </div>

    <div class="card-panel chart-card">
      <h4 class="section-heading">能力雷达图</h4>
      <div ref="radarRef" class="radar-chart"></div>
    </div>

    <div class="card-panel">
      <h4 class="section-heading">知识掌握图谱</h4>
      <div v-if="knowledgeItems.length" class="knowledge-cloud">
        <span
          v-for="item in knowledgeItems"
          :key="item.name"
          class="bubble"
          :class="item.level"
        >{{ item.name }}</span>
      </div>
      <p v-else class="empty-hint">完善薄弱知识点后将在此展示</p>
    </div>

    <div class="card-panel">
      <h4 class="section-heading">学习风格标签</h4>
      <div class="style-tags">
        <span v-for="tag in styleTags" :key="tag" class="style-tag">{{ tag }}</span>
      </div>
    </div>

    <details class="json-fold card-panel">
      <summary>画像数据详情</summary>
      <pre class="json-preview">{{ JSON.stringify(profile, null, 2) }}</pre>
    </details>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  profile: { type: Object, default: () => ({}) }
})

const radarRef = ref(null)
let radarChart = null

const hasProfileData = computed(() => {
  const p = props.profile || {}
  return Boolean(
    p.grade || p.major || p.course || p.level || p.goal || p.learning_style ||
    (p.weak_points && p.weak_points.length)
  )
})

const knowledgeItems = computed(() => {
  const weak = props.profile.weak_points || []
  if (!weak.length) return []
  return weak.map(name => ({
    name: name.length > 8 ? name.slice(0, 8) + '…' : name,
    level: 'weak'
  }))
})

const styleTags = computed(() => {
  const style = props.profile.learning_style || ''
  const tags = []
  if (style.includes('案例') || style.includes('通俗')) tags.push('案例学习')
  if (style.includes('图表') || style.includes('视觉')) tags.push('视觉学习')
  if (style.includes('自主') || style.includes('探索')) tags.push('自主探索')
  if (!tags.length && style) tags.push('个性化学习')
  if (!tags.length) return ['待完善学习风格']
  return tags
})

function initRadar() {
  if (!radarRef.value) return
  radarChart = radarChart || echarts.init(radarRef.value)
  const level = props.profile.level || ''
  let base = 60
  if (level.includes('较弱') || level.includes('零基础')) base = 45
  else if (level.includes('较好') || level.includes('优秀')) base = 75
  else if (!level) base = 50

  radarChart.setOption({
    radar: {
      indicator: [
        { name: '基础知识', max: 100 },
        { name: '实践能力', max: 100 },
        { name: '理论理解', max: 100 },
        { name: '学习主动性', max: 100 },
        { name: '综合掌握', max: 100 }
      ],
      radius: '65%',
      splitArea: { areaStyle: { color: ['rgba(99,102,241,0.03)', 'rgba(99,102,241,0.06)'] } },
      axisLine: { lineStyle: { color: 'rgba(99,102,241,0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(99,102,241,0.1)' } },
      axisName: { color: '#6b7280' }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [base, base - 8, base + 5, base + 10, base - 5],
        name: '当前能力',
        areaStyle: { color: 'rgba(99, 102, 241, 0.18)' },
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#8b5cf6' }
      }]
    }]
  }, true)
}

watch(() => props.profile, () => nextTick(initRadar), { deep: true })

onMounted(() => {
  nextTick(initRadar)
  window.addEventListener('resize', resizeRadar)
})

function resizeRadar() {
  radarChart?.resize()
}

onActivated(() => nextTick(resizeRadar))

onUnmounted(() => {
  window.removeEventListener('resize', resizeRadar)
  radarChart?.dispose()
})
</script>

<style scoped>
.profile-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.center-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.avatar-ring {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: var(--gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.22);
}

.center-header h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-summary {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0 8px;
  line-height: 1.5;
}

.radar-chart {
  height: 260px;
}

.knowledge-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 8px 0;
  min-height: 48px;
}

.bubble {
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
}

.bubble.weak {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #dc2626;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 0;
}

.style-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.style-tag {
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: 500;
  font-size: 13px;
  background: var(--gradient-soft);
  border: 1px solid var(--border-soft);
  color: var(--primary-dark);
}

.json-fold summary {
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  user-select: none;
}

.json-fold summary:hover {
  color: var(--primary);
}

.json-preview {
  margin-top: 12px;
  background: #f3f4f6;
  color: #374151;
  padding: 16px;
  border-radius: 12px;
  font-size: 12px;
  overflow: auto;
  max-height: 200px;
  border: 1px solid var(--border);
}
</style>
