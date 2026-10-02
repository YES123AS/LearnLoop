<template>
  <div class="page-container">
    <PageHeader :title="PAGE_HEADERS.recommend.title" :subtitle="PAGE_HEADERS.recommend.subtitle" />

    <el-row :gutter="24">
      <el-col :span="8">
        <ProfileCard :profile="store.student_profile" />
        <div class="card-panel" style="margin-top: 16px">
          <h4 class="section-label">薄弱知识点</h4>
          <div class="tag-list">
            <el-tag v-for="p in store.weak_points" :key="p" type="danger" effect="dark">{{ p }}</el-tag>
            <span v-if="!store.weak_points.length" class="empty">暂无薄弱点</span>
          </div>
          <h4 class="section-label" style="margin-top: 16px">已掌握知识点</h4>
          <div class="tag-list">
            <el-tag v-for="p in store.mastered_points" :key="p" type="success" effect="dark">{{ p }}</el-tag>
            <span v-if="!store.mastered_points.length" class="empty">暂无（可通过学情分析更新）</span>
          </div>
          <el-button type="primary" class="gradient-btn" :loading="loading" style="width:100%;margin-top:20px" @click="generate">生成学习推荐</el-button>
        </div>
        <div class="card-panel mistake-review" style="margin-top: 16px">
          <h4 class="section-heading">基于错题的复习建议</h4>
          <template v-if="unresolvedStats.unresolved > 0">
            <p class="review-summary">待修复错题 <strong>{{ unresolvedStats.unresolved }}</strong> 道</p>
            <div v-if="unresolvedStats.topWeakPoints.length" class="review-block"><span class="block-label">薄弱知识点</span><div class="tag-list"><el-tag v-for="p in unresolvedStats.topWeakPoints.slice(0, 3)" :key="p" type="warning" effect="light">{{ p }}</el-tag></div></div>
            <div v-if="topErrorSummary.length" class="review-block"><span class="block-label">错因类型</span><div class="tag-list"><el-tag v-for="t in topErrorSummary" :key="t.name" size="small" effect="plain">{{ t.name }}</el-tag></div></div>
            <div v-if="recentUnresolved.length" class="recent-list"><span class="block-label">最近错题</span><div v-for="item in recentUnresolved" :key="item.mistake_id" class="recent-item glass-panel"><div class="recent-meta"><el-tag size="small" type="primary" effect="light">{{ getKnowledgePoint(item) }}</el-tag><el-tag size="small" effect="plain">{{ getQuestionType(item) }}</el-tag><el-tag size="small" type="warning" effect="light">{{ getMistakeStatus(item) }}</el-tag></div><p class="recent-stem">{{ getStem(item) }}</p><el-button size="small" type="primary" link @click="$router.push('/mistakes')">进入错题集</el-button></div></div>
            <div class="review-actions"><el-button type="primary" class="gradient-btn" style="width:100%" @click="$router.push('/mistakes')">进入错题集</el-button><el-button plain style="width:100%;margin-top:8px;margin-left:0" @click="$router.push('/quiz')">开始针对性练习</el-button></div>
          </template>
          <template v-else>
            <p class="review-empty">暂无待修复错题，可以继续练习巩固知识点</p>
            <el-button type="primary" class="gradient-btn" style="width:100%" @click="$router.push('/quiz')">生成练习题</el-button>
          </template>
        </div>
      </el-col>

      <el-col :span="16">
        <div class="card-panel result-panel">
          <AiLoading v-if="loading" text="AI 智能体正在生成学习推荐..." />
          <div v-else-if="hasRecommendation" class="recommend-content">
            <div class="recommend-toolbar">
              <el-tag v-if="isDemoRecommend" type="info" size="small" effect="light">预览推荐</el-tag>
              <div class="recommend-actions"><el-button size="small" @click="copyRecommend">复制内容</el-button><el-button size="small" type="primary" @click="downloadRecommend">下载学习推荐 Markdown</el-button></div>
            </div>
            <MarkdownViewer :content="displayRecommendation" />
          </div>
          <EmptyState v-else-if="!store.hasProfile" title="暂无推荐数据" hint="请先完成学习画像构建" :icon="Star"><el-button type="primary" class="gradient-btn" @click="$router.push('/profile')">前往构建画像</el-button></EmptyState>
          <div v-else-if="store.demo_mode" class="recommend-preview"><h3 class="section-heading">推荐结构预览</h3><div class="roadmap"><div v-for="(step, i) in previewSteps" :key="i" class="roadmap-step glass-panel"><div class="step-num">{{ i + 1 }}</div><div class="step-body"><strong>{{ step.title }}</strong><p>{{ step.desc }}</p><div class="step-meta"><el-tag size="small" type="warning">优先级 {{ step.priority }}</el-tag><el-tag size="small" effect="plain">预计收益：{{ step.benefit }}</el-tag></div></div></div></div><div class="task-cards"><div v-for="task in previewTasks" :key="task.title" class="task-card glass-panel"><h4>{{ task.title }}</h4><p class="task-reason">推荐原因：{{ task.reason }}</p><p class="task-action">{{ task.action }}</p></div></div><p class="preview-hint">点击「生成学习推荐」，AI 将根据你的画像生成个性化建议</p></div>
          <EmptyState v-else title="暂无推荐数据" hint="点击「生成学习推荐」获取个性化建议" :icon="Star" />
          <div v-if="hasRecommendation" class="bottom-action"><el-button type="primary" class="gradient-btn" @click="goPath">一键生成学习路径</el-button></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useStudentStore } from '@/store/student'
import { recommendNext } from '@/api/index'
import { getKnowledgePoint, getQuestionType, getStem, getMistakeStatus } from '@/utils/mistakeStats'
import { useMistakeSummary } from '@/composables/useMistakeSummary'
import { usePageRefresh } from '@/composables/usePageRefresh'
import { useAsyncTask } from '@/composables/useAsyncTask'
import { DEMO_RECOMMENDATION } from '@/demo/demoContent'
import { downloadTextFile, formatDateFilename } from '@/utils/download'
import ProfileCard from '@/components/ProfileCard.vue'
import MarkdownViewer from '@/components/MarkdownViewer.vue'
import AiLoading from '@/components/AiLoading.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { PAGE_HEADERS } from '@/constants/brand'
import { Star } from '@element-plus/icons-vue'
import { analyzeQuestionTagPerformance, generateTagBasedSuggestions } from '@/utils/questionTagAnalysis'

const store = useStudentStore(); const router = useRouter(); const { loading, run: runRecommendTask } = useAsyncTask(); const { stats: unresolvedStats, refresh: refreshUnresolvedMistakes } = useMistakeSummary({ defaultStatus: '未修复', silent: true }); usePageRefresh(refreshUnresolvedMistakes, { smart: true })
const recentUnresolved = computed(() => unresolvedStats.value.recentMistakes.slice(0, 3))
const topErrorSummary = computed(() => Object.entries(unresolvedStats.value.errorTypeStats || {}).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([name]) => ({ name })))
const displayRecommendation = computed(() => store.recommendation?.trim() || (store.demo_mode && store.hasProfile ? DEMO_RECOMMENDATION : ''))
const hasRecommendation = computed(() => Boolean(displayRecommendation.value.trim()))
const isDemoRecommend = computed(() => store.demo_mode && !store.recommendation?.trim() && hasRecommendation.value)
const previewSteps = [ { title: '优先学习 LZW 算法', desc: '薄弱知识点，建议从基础概念入手', priority: '高', benefit: '掌握率 +25%' }, { title: '复习 JPEG 压缩流程', desc: '结合案例理解编码步骤', priority: '高', benefit: '掌握率 +20%' }, { title: '巩固霍夫曼编码', desc: '通过练习题强化理解', priority: '中', benefit: '掌握率 +15%' } ]
const previewTasks = [ { title: '学习资料生成', reason: 'LZW 为当前最薄弱知识点', action: '生成 LZW 算法完整学习资料' }, { title: '针对性练习', reason: 'JPEG 正确率为 0%', action: '完成 5 道 JPEG 相关检测题' }, { title: '智能辅导问答', reason: '霍夫曼编码理解不足', action: '向 AI 提问编码原理' } ]
const tagAnalysis = computed(() => analyzeQuestionTagPerformance(store.records))
const tagSuggestions = computed(() => generateTagBasedSuggestions(tagAnalysis.value))
async function generate() { try { await runRecommendTask(async () => { const data = await recommendNext(store.student_profile, store.weak_points, store.mastered_points); store.setRecommendation(data.recommendation || ''); ElMessage.success('推荐生成成功'); return data }) } catch {} }
function copyRecommend() { if (!hasRecommendation.value) return; navigator.clipboard.writeText(displayRecommendation.value).then(() => ElMessage.success('已复制到剪贴板')).catch(() => ElMessage.warning('复制失败')) }
function downloadRecommend() { if (!hasRecommendation.value) return; downloadTextFile(displayRecommendation.value, formatDateFilename('学习推荐', 'md')); ElMessage.success('文档已开始下载，请在浏览器下载记录中查看') }
function goPath() { const weak = store.weak_points[0] || 'LZW算法'; router.push({ path: '/path', query: { goal: `掌握${weak}` } }) }
</script>

<style scoped>
/* existing styles preserved; add tag-based recommendation */
.tag-driven { margin-top: 16px; }
.tag-driven .section-heading { margin-bottom: 12px; }
.tag-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.tag-item { padding: 14px; border:1px solid var(--border); border-radius: 12px; background: rgba(255,255,255,0.82); }
.tag-item strong { display:block; margin-bottom: 6px; }
.tag-item p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
@media (max-width: 768px) { .tag-grid { grid-template-columns: 1fr; } }
</style>
