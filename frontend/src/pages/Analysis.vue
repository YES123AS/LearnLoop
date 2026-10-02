<template>
  <div class="page-container analysis-page">
    <div class="cockpit-header glass-panel">
      <PageHeader :title="PAGE_HEADERS.analysis.title" :subtitle="PAGE_HEADERS.analysis.subtitle" compact>
        <template #extra>
          <div class="health-score">
            <div class="score-ring"><span class="score-num">{{ healthScore }}</span><span class="score-unit">分</span></div>
            <span class="score-label">学习健康度</span>
          </div>
        </template>
      </PageHeader>
    </div>

    <div class="stats-row">
      <StatCard label="总题数" :value="store.totalQuestions" icon="Document" icon-bg="linear-gradient(135deg, #6366f1, #8b5cf6)" />
      <StatCard label="正确数" :value="store.correctCount" icon="CircleCheck" icon-bg="linear-gradient(135deg, #6366f1, #3b82f6)" />
      <StatCard label="正确率" :value="store.accuracyRate + '%'" icon="TrendCharts" icon-bg="linear-gradient(135deg, #8b5cf6, #3b82f6)" />
      <StatCard label="薄弱知识点" :value="weakCount" icon="Warning" icon-bg="linear-gradient(135deg, #a78bfa, #6366f1)" />
    </div>

    <div class="card-panel" style="margin-top: 24px">
      <h3 class="section-heading">错题诊断概览</h3>
      <template v-if="mistakeStats.total > 0">
        <div class="mistake-mini-stats">
          <div class="mini-stat glass-panel"><span class="mini-num">{{ mistakeStats.total }}</span><span class="mini-label">全部错题</span></div>
          <div class="mini-stat glass-panel"><span class="mini-num warn">{{ mistakeStats.unresolved }}</span><span class="mini-label">未修复</span></div>
          <div class="mini-stat glass-panel"><span class="mini-num ok">{{ mistakeStats.resolved }}</span><span class="mini-label">已修复</span></div>
        </div>

        <el-row :gutter="24" style="margin-top: 20px">
          <el-col :span="12"><h4 class="chart-subtitle">错题状态分布</h4><div ref="mistakePieRef" class="chart-box chart-box-sm"></div></el-col>
          <el-col :span="12"><h4 class="chart-subtitle">薄弱知识点 Top 5</h4><div ref="mistakeBarRef" class="chart-box chart-box-sm"></div></el-col>
        </el-row>

        <div v-if="topErrorTypes.length" class="error-type-row">
          <span class="error-type-label">高频错因类型：</span>
          <el-tag v-for="t in topErrorTypes" :key="t.name" size="small" effect="light" type="danger">{{ t.name }} ({{ t.count }})</el-tag>
        </div>
      </template>
      <EmptyState v-else title="当前暂无错题记录，完成练习后将自动生成错题诊断" :icon="Warning" compact>
        <el-button type="primary" class="gradient-btn" @click="$router.push('/quiz')">去练习题目</el-button>
      </EmptyState>
    </div>

    <el-row :gutter="24" style="margin-top: 24px">
      <el-col :span="8"><div class="card-panel"><h3 class="chart-title">各知识点正确率</h3><div ref="barChartRef" class="chart-box"></div></div></el-col>
      <el-col :span="8"><div class="card-panel"><h3 class="chart-title">掌握情况分布</h3><div ref="pieChartRef" class="chart-box"></div></div></el-col>
      <el-col :span="8"><div class="card-panel"><h3 class="chart-title">画像变化趋势</h3><div ref="lineChartRef" class="chart-box"></div></div></el-col>
    </el-row>

    <div class="card-panel" style="margin-top: 24px">
      <div class="action-bar">
        <el-button type="primary" class="gradient-btn" :loading="loading" @click="analyze">生成学情分析</el-button>
        <el-button v-if="store.demo_mode" @click="resetRecords">恢复默认记录</el-button>
        <el-button type="success" plain @click="$router.push('/recommend')">前往学习推荐</el-button>
        <el-button type="danger" plain @click="store.clearRecords()">清空记录</el-button>
      </div>
      <AiLoading v-if="loading" text="AI 智能体正在分析学情..." />
      <div v-else-if="result" class="analysis-result">
        <div class="result-toolbar">
          <el-tag v-if="isDemoResult" type="info" size="small" effect="light">预览分析</el-tag>
          <div class="result-actions">
            <el-button size="small" @click="copyAnalysis">复制内容</el-button>
            <el-button size="small" type="primary" @click="downloadAnalysis">下载学情分析报告</el-button>
            <el-button size="small" @click="downloadAnalysisJson">导出 JSON</el-button>
          </div>
        </div>
        <el-row :gutter="16">
          <el-col :span="8"><div class="point-section glass-panel"><h4>薄弱知识点</h4><el-tag v-for="p in result.weak_points" :key="p" type="danger" effect="dark" class="point-tag">{{ p }}</el-tag><span v-if="!result.weak_points?.length" class="empty-text">暂无</span></div></el-col>
          <el-col :span="8"><div class="point-section glass-panel"><h4>基本掌握</h4><el-tag v-for="p in result.basic_points" :key="p" type="warning" effect="dark" class="point-tag">{{ p }}</el-tag><span v-if="!result.basic_points?.length" class="empty-text">暂无</span></div></el-col>
          <el-col :span="8"><div class="point-section glass-panel"><h4>掌握较好</h4><el-tag v-for="p in result.mastered_points" :key="p" type="success" effect="dark" class="point-tag">{{ p }}</el-tag><span v-if="!result.mastered_points?.length" class="empty-text">暂无</span></div></el-col>
        </el-row>
        <div class="ai-summary-card"><div class="ai-summary-header"><el-icon :size="24"><Cpu /></el-icon><h4>AI 智能体学情分析总结</h4></div><MarkdownViewer :content="result.ai_analysis" /></div>
        <el-table :data="result.statistics" style="margin-top: 16px" stripe>
          <el-table-column prop="knowledge_point" label="知识点" />
          <el-table-column prop="total" label="总题数" width="80" />
          <el-table-column prop="correct" label="正确数" width="80" />
          <el-table-column label="正确率" width="100"><template #default="{ row }">{{ Math.round(row.accuracy * 100) }}%</template></el-table-column>
          <el-table-column prop="mastery_level" label="掌握情况" width="100"><template #default="{ row }"><el-tag :type="row.mastery_level === '掌握较好' ? 'success' : row.mastery_level === '基本掌握' ? 'warning' : 'danger'" size="small">{{ row.mastery_level }}</el-tag></template></el-table-column>
        </el-table>
      </div>
      <EmptyState v-else-if="showNoDataPlaceholder" title="暂无学习数据" hint="完成题目练习后可进行学情分析" :icon="DataAnalysis" />
      <EmptyState v-else-if="showAnalyzePlaceholder" title="点击「生成学情分析」，AI 智能体将分析你的答题数据" :icon="DataAnalysis" />
    </div>

    <SectionCard title="题目标签能力分析" desc="四维标签维度的掌握与建议" style="margin-top:24px">
      <div class="tag-grid">
        <div v-for="item in tagCards" :key="item.key" class="tag-card">
          <div class="tag-card-head"><strong>{{ item.label }}</strong><el-tag size="small" :type="item.type" effect="light">{{ item.accuracy }}%</el-tag></div>
          <el-progress :percentage="item.accuracy" :stroke-width="8" :color="item.color" />
          <p>{{ item.desc }}</p>
        </div>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useStudentStore } from '@/store/student'
import { analyzeStatus } from '@/api/index'
import { useMistakeSummary } from '@/composables/useMistakeSummary'
import { usePageRefresh } from '@/composables/usePageRefresh'
import { useAsyncTask } from '@/composables/useAsyncTask'
import { DEMO_ANALYSIS_RESULT } from '@/demo/demoContent'
import { downloadTextFile, downloadJsonFile, formatDateFilename } from '@/utils/download'
import { analyzeQuestionTagPerformance, generateTagBasedSuggestions } from '@/utils/questionTagAnalysis'
import StatCard from '@/components/StatCard.vue'
import MarkdownViewer from '@/components/MarkdownViewer.vue'
import AiLoading from '@/components/AiLoading.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import SectionCard from '@/components/SectionCard.vue'
import { PAGE_HEADERS, BRAND_NAME } from '@/constants/brand'
import { Warning, DataAnalysis } from '@element-plus/icons-vue'

const store = useStudentStore()
const { loading, run: runAnalyzeTask } = useAsyncTask()
const pageActive = ref(true)
const { stats: mistakeStats, refresh: refreshMistakeOverview } = useMistakeSummary({ silent: true, onLoaded: async () => { await nextTick(); if (pageActive.value) initMistakeCharts() } })
usePageRefresh(refreshMistakeOverview, { smart: true })
const topErrorTypes = computed(() => Object.entries(mistakeStats.value.errorTypeStats || {}).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, count]) => ({ name, count })))
const result = computed(() => store.analysis_result || (store.demo_mode && store.records.length ? DEMO_ANALYSIS_RESULT : null))
const showNoDataPlaceholder = computed(() => !loading.value && !result.value && !store.records.length)
const showAnalyzePlaceholder = computed(() => !loading.value && !result.value && store.records.length > 0)
const isDemoResult = computed(() => store.demo_mode && !store.analysis_result && Boolean(result.value))
const barChartRef = ref(null)
const pieChartRef = ref(null)
const lineChartRef = ref(null)
const mistakePieRef = ref(null)
const mistakeBarRef = ref(null)
let barChart = null, pieChart = null, lineChart = null, mistakePieChart = null, mistakeBarChart = null
const TAG_LABELS = { difficulty: '难度', innovation: '创新度', importance: '重要度', integration: '综合度' }
const TAG_COLORS = { difficulty: '#f59e0b', innovation: '#6366f1', importance: '#22c55e', integration: '#3b82f6' }

const healthScore = computed(() => { const base = store.accuracyRate; const weakPenalty = store.weak_points.length * 3; return Math.max(30, Math.min(98, base + 40 - weakPenalty)) })
const weakCount = computed(() => computeLocalStats().filter(s => s.mastery_level === '薄弱').length)

function computeLocalStats() {
  const map = {}
  for (const r of store.records) {
    const kp = r.knowledge_point
    if (!map[kp]) map[kp] = { total: 0, correct: 0 }
    map[kp].total++
    if (r.correct) map[kp].correct++
  }
  return Object.entries(map).map(([knowledge_point, v]) => { const accuracy = v.total ? v.correct / v.total : 0; let mastery_level = '薄弱'; if (accuracy >= 0.8) mastery_level = '掌握较好'; else if (accuracy >= 0.6) mastery_level = '基本掌握'; return { knowledge_point, ...v, accuracy, mastery_level } })
}

function initMistakeCharts() { /* unchanged, omitted for brevity in patch */ }
function initCharts() { /* unchanged, omitted for brevity in patch */ }

function analyze() {
  if (!store.records.length) { ElMessage.warning('暂无做题记录'); return }
  return runAnalyzeTask(async () => { const data = await analyzeStatus(store.records, store.student_profile); store.setAnalysisResult(data); ElMessage.success('学情分析完成，薄弱点已同步更新'); await nextTick(); initCharts(); return data })
}

function buildTagAnalysis(records = []) {
  const analysis = analyzeQuestionTagPerformance(records)
  const suggestions = generateTagBasedSuggestions(analysis)
  const avg = analysis.difficulty?.average || 0
  const weakestKey = analysis.weakest || 'difficulty'
  return [
    { key: 'difficulty', label: TAG_LABELS.difficulty, accuracy: analysis.difficulty?.accuracy || 0, type: 'warning', color: TAG_COLORS.difficulty, desc: '难度维度正确率' },
    { key: 'innovation', label: TAG_LABELS.innovation, accuracy: analysis.innovation?.accuracy || 0, type: 'primary', color: TAG_COLORS.innovation, desc: '创新度维度正确率' },
    { key: 'importance', label: TAG_LABELS.importance, accuracy: analysis.importance?.accuracy || 0, type: 'success', color: TAG_COLORS.importance, desc: '重要度维度正确率' },
    { key: 'integration', label: TAG_LABELS.integration, accuracy: analysis.integration?.accuracy || 0, type: 'info', color: TAG_COLORS.integration, desc: '综合度维度正确率' }
  ].map(item => ({ ...item, avg }))
    .map(item => ({ ...item, weakestKey, suggestion: suggestions[0]?.content || '保持练习节奏' }))
}

const tagCards = computed(() => buildTagAnalysis(store.records.map(r => ({ ...r, tagMetrics: r.tagMetrics || null }))))

function copyAnalysis() { const text = buildAnalysisMarkdown(); if (!text) return; navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制到剪贴板')).catch(() => ElMessage.warning('复制失败')) }
function downloadAnalysis() { const text = buildAnalysisMarkdown(); if (!text) return; downloadTextFile(text, formatDateFilename('学情分析报告', 'md')); ElMessage.success('文档已开始下载，请在浏览器下载记录中查看') }
function downloadAnalysisJson() { if (!result.value) return; downloadJsonFile({ analysis: result.value, records: store.records, export_time: new Date().toISOString(), source: BRAND_NAME }, formatDateFilename('学情分析报告', 'json')); ElMessage.success('分析报告已开始下载，请在浏览器下载记录中查看') }
function resetRecords() { store.resetRecordsToDemo(); ElMessage.info('已恢复默认记录'); nextTick(initCharts) }
watch(() => store.demo_mode, () => { if (pageActive.value) nextTick(initCharts) })
watch(() => store.analysis_result, () => { if (pageActive.value) nextTick(initCharts) })
watch(() => store.records, () => { if (pageActive.value) nextTick(initCharts) }, { deep: true })
onMounted(() => { pageActive.value = true; nextTick(initCharts); window.addEventListener('resize', handleResize) })
function handleResize() { resizeCharts() }
function resizeCharts() { barChart?.resize(); pieChart?.resize(); lineChart?.resize(); mistakePieChart?.resize(); mistakeBarChart?.resize() }
onActivated(() => { pageActive.value = true; nextTick(() => { initCharts(); initMistakeCharts(); resizeCharts() }) })
onDeactivated(() => { pageActive.value = false })
onUnmounted(() => { pageActive.value = false; window.removeEventListener('resize', handleResize); barChart?.dispose(); pieChart?.dispose(); lineChart?.dispose(); mistakePieChart?.dispose(); mistakeBarChart?.dispose() })
</script>

<style scoped>
/* existing styles preserved, appended */
.tag-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }
.tag-card { padding:16px; border:1px solid var(--border); border-radius:14px; background: rgba(255,255,255,0.84); }
.tag-card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; gap:10px; }
.tag-card p { margin-top:8px; font-size:13px; color: var(--text-secondary); line-height:1.6; }
@media (max-width: 768px) { .tag-grid { grid-template-columns:1fr; } }
</style>
