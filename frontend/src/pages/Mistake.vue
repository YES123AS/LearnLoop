<template>
  <div class="page-container mistake-page" v-loading="pageLoading">
    <PageHeader :title="PAGE_HEADERS.mistakes.title" :subtitle="PAGE_HEADERS.mistakes.subtitle" />

    <div class="stats-row">
      <div class="stat-card card-panel">
        <span class="stat-num">{{ stats.total }}</span>
        <span class="stat-label">全部错题</span>
      </div>
      <div class="stat-card card-panel">
        <span class="stat-num unfixed">{{ stats.unfixed }}</span>
        <span class="stat-label">未修复</span>
      </div>
      <div class="stat-card card-panel">
        <span class="stat-num fixed">{{ stats.fixed }}</span>
        <span class="stat-label">已修复</span>
      </div>
      <div class="stat-card card-panel">
        <span class="stat-num">{{ stats.knowledgePoints }}</span>
        <span class="stat-label">涉及知识点</span>
      </div>
    </div>

    <div class="toolbar card-panel">
      <div class="filter-group">
        <el-radio-group v-model="statusFilter" @change="loadList">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="未修复">未修复</el-radio-button>
          <el-radio-button label="已修复">已修复</el-radio-button>
        </el-radio-group>
        <el-select v-model="tagFilter" placeholder="标签筛选" clearable style="width: 180px" @change="loadList">
          <el-option label="高难度题" value="difficulty" />
          <el-option label="高创新题" value="innovation" />
          <el-option label="高频重点考点" value="importance" />
          <el-option label="高综合度题" value="integration" />
        </el-select>
      </div>
      <el-button plain :loading="listLoading" @click="refreshAll">刷新</el-button>
    </div>

    <div v-if="!listLoading && mistakes.length" class="mistake-list">
      <div v-for="item in mistakes" :key="item.mistake_id" class="mistake-item card-panel">
        <div class="item-header">
          <div class="item-tags">
            <el-tag size="small" type="primary" effect="light">{{ getKnowledgePoint(item) }}</el-tag>
            <el-tag size="small" effect="plain">{{ getQuestionType(item) }}</el-tag>
            <el-tag size="small" :type="getMistakeStatus(item) === '已修复' ? 'success' : 'warning'" effect="light">
              {{ getMistakeStatus(item) }}
            </el-tag>
          </div>
          <span v-if="item.created_at" class="item-time">{{ item.created_at }}</span>
        </div>

        <p class="item-stem">{{ getStem(item) }}</p>

        <div class="item-tag-summary">
          <el-tag size="small" effect="light" type="info">{{ tagSummary(item) }}</el-tag>
        </div>

        <QuestionTagMetrics :question="item.question || item.raw_question || item" />

        <div class="item-answers">
          <span><strong>你的答案：</strong>{{ item.user_answer || '—' }}</span>
          <span><strong>标准答案：</strong>{{ getStandardAnswer(item) }}</span>
        </div>

        <div v-if="getErrorTypes(item).length" class="item-errors">
          <el-tag v-for="t in getErrorTypes(item)" :key="t" size="small" type="danger" effect="light">{{ t }}</el-tag>
        </div>

        <el-button type="primary" plain size="small" class="detail-btn" @click="openDetail(item)">
          查看详情
        </el-button>
      </div>
    </div>

    <EmptyState
      v-else-if="!listLoading"
      title="当前暂无错题记录"
      hint="在题目练习中答错的题目会自动加入错题集"
      :icon="Warning"
    >
      <el-button type="primary" class="gradient-btn" @click="$router.push(APP_ROUTES.quiz)">去练习题目</el-button>
    </EmptyState>

    <el-drawer v-model="drawerVisible" title="错题详情" size="520px" direction="rtl" destroy-on-close>
      <div v-if="detailLoading" class="drawer-loading">
        <AiLoading text="正在加载错题详情…" />
      </div>
      <div v-else-if="detail" class="drawer-body">
        <section class="detail-section">
          <h4 class="section-heading">题目信息</h4>
          <p class="detail-text">{{ getStem(detail) }}</p>
          <QuestionTagMetrics :question="detail.question || detail.raw_question || detail" />
          <div class="detail-kv">
            <div><span class="kv-label">你的答案</span><span>{{ detail.user_answer || '—' }}</span></div>
            <div><span class="kv-label">标准答案</span><span>{{ getStandardAnswer(detail) }}</span></div>
            <div v-if="getAnalysis(detail)"><span class="kv-label">解析</span><span>{{ getAnalysis(detail) }}</span></div>
          </div>
        </section>

        <section v-if="detail.diagnosis" class="detail-section">
          <h4 class="section-heading">错因诊断</h4>
          <p class="detail-text">{{ detail.diagnosis }}</p>
          <div v-if="getErrorTypes(detail).length" class="tag-row">
            <el-tag v-for="t in getErrorTypes(detail)" :key="t" size="small" type="danger" effect="light">{{ t }}</el-tag>
          </div>
        </section>

        <section v-if="getMissingPoints(detail).length" class="detail-section">
          <h4 class="section-heading">缺失知识点</h4>
          <div class="tag-row">
            <el-tag v-for="p in getMissingPoints(detail)" :key="p" size="small" effect="light">{{ p }}</el-tag>
          </div>
        </section>

        <section v-if="hasMicroLesson(detail)" class="detail-section">
          <h4 class="section-heading">补救微课</h4>
          <div class="micro-lesson glass-panel">
            <template v-if="typeof detail.remediation_micro_lesson === 'object'">
              <h5 v-if="detail.remediation_micro_lesson.title">{{ detail.remediation_micro_lesson.title }}</h5>
              <p v-if="detail.remediation_micro_lesson.target"><strong>目标：</strong>{{ detail.remediation_micro_lesson.target }}</p>
              <p v-if="detail.remediation_micro_lesson.explanation">{{ detail.remediation_micro_lesson.explanation }}</p>
              <ul v-if="detail.remediation_micro_lesson.steps?.length">
                <li v-for="(step, i) in detail.remediation_micro_lesson.steps" :key="i">{{ step }}</li>
              </ul>
            </template>
            <p v-else>{{ detail.remediation_micro_lesson }}</p>
          </div>
        </section>

        <section v-if="detail.recommended_practice" class="detail-section">
          <h4 class="section-heading">推荐练习</h4>
          <p class="detail-text">{{ detail.recommended_practice }}</p>
        </section>

        <section v-if="getVariants(detail).length" class="detail-section">
          <h4 class="section-heading">变式题重练</h4>
          <div v-for="(vq, idx) in getVariants(detail)" :key="idx" class="variant-card glass-panel">
            <div class="variant-head">
              <el-tag size="small" effect="plain">变式题 {{ idx + 1 }}</el-tag>
              <el-tag size="small" type="info" effect="light">{{ vq.type || '题目' }}</el-tag>
            </div>
            <p class="variant-question">{{ vq.question || '（题目内容缺失）' }}</p>

            <div v-if="isChoiceQuestion(vq)" class="variant-options">
              <el-radio-group v-model="variantAnswers[idx]">
                <el-radio v-for="(opt, oi) in vq.options" :key="oi" :label="opt" class="variant-option">
                  {{ opt }}
                </el-radio>
              </el-radio-group>
            </div>
            <el-input v-else v-model="variantAnswers[idx]" type="textarea" :rows="2" placeholder="请输入你的答案" />

            <el-button
              type="primary"
              class="gradient-btn variant-submit"
              size="small"
              :loading="retryLoading === idx"
              @click="submitVariant(idx)"
            >
              提交重练答案
            </el-button>
          </div>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { getMistakeBook, getMistakeDetail, retryMistake } from '@/api/index'
import { getStudentId } from '@/utils/studentId'
import { getQuestionTagSummary, normalizeQuestionTags } from '@/utils/questionTags'
import {
  getStem,
  getStandardAnswer,
  getKnowledgePoint,
  getQuestionType,
  getErrorTypes,
  getMistakeStatus
} from '@/utils/mistakeStats'
import { notifyMistakeBookChanged } from '@/utils/mistakeRefresh'
import { useMistakeSummary } from '@/composables/useMistakeSummary'
import AiLoading from '@/components/AiLoading.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import QuestionTagMetrics from '@/components/QuestionTagMetrics.vue'
import { PAGE_HEADERS } from '@/constants/brand'
import { APP_ROUTES } from '@/constants/routes'

const pageLoading = ref(false)
const listLoading = ref(false)
const detailLoading = ref(false)
const retryLoading = ref(-1)
const statusFilter = ref('')
const tagFilter = ref('')
const mistakes = ref([])

const { stats: summaryStats, refresh: refreshSummaryStats } = useMistakeSummary({ silent: true })
const stats = computed(() => ({
  total: summaryStats.value.total,
  unfixed: summaryStats.value.unresolved,
  fixed: summaryStats.value.resolved,
  knowledgePoints: summaryStats.value.knowledgePoints.length
}))

const drawerVisible = ref(false)
const detail = ref(null)
const variantAnswers = ref({})

function getMissingPoints(item) { return Array.isArray(item?.missing_points) ? item.missing_points.filter(Boolean) : [] }
function getVariants(item) { return Array.isArray(item?.variant_questions) ? item.variant_questions : [] }
function hasMicroLesson(item) { const ml = item?.remediation_micro_lesson; return !!(ml && (typeof ml === 'string' ? ml.trim().length > 0 : Object.keys(ml).length > 0)) }
function isChoiceQuestion(vq) { return vq?.type === '选择题' && Array.isArray(vq.options) && vq.options.length > 0 }
function getAnalysis(item) { return item?.standard_analysis || item?.analysis || item?.question?.analysis || '' }
function tagSummary(item) { return getQuestionTagSummary(item.question || item.raw_question || item) }
function matchTagFilter(item) {
  if (!tagFilter.value) return true
  const tags = normalizeQuestionTags(item.question || item.raw_question || item)
  const checks = {
    difficulty: tags.difficulty >= 4,
    innovation: tags.innovation >= 4,
    importance: tags.importance >= 4,
    integration: tags.integration >= 4
  }
  return checks[tagFilter.value]
}

async function refreshAll() {
  pageLoading.value = true
  try {
    await refreshSummaryStats()
    await loadList()
  } finally {
    pageLoading.value = false
  }
}
async function loadList() {
  listLoading.value = true
  try {
    const status = statusFilter.value || undefined
    const data = await getMistakeBook(getStudentId(), status)
    mistakes.value = (data.mistakes || []).filter(matchTagFilter)
  } catch {
    mistakes.value = []
  } finally {
    listLoading.value = false
  }
}

async function openDetail(item) {
  drawerVisible.value = true
  detail.value = item
  variantAnswers.value = {}
  detailLoading.value = true
  try {
    if (item.mistake_id) detail.value = await getMistakeDetail(item.mistake_id)
  } catch {
    detail.value = item
  } finally {
    detailLoading.value = false
  }
}

async function submitVariant(index) {
  if (!detail.value?.mistake_id) return
  const answer = variantAnswers.value[index]
  if (answer == null || String(answer).trim() === '') { ElMessage.warning('请先输入或选择答案'); return }
  retryLoading.value = index
  try {
    const result = await retryMistake({ mistake_id: detail.value.mistake_id, variant_index: index + 1, user_answer: answer })
    if (result.correct) {
      ElMessage.success('回答正确，错题已修复')
      detail.value = await getMistakeDetail(detail.value.mistake_id)
      notifyMistakeBookChanged()
      await refreshAll()
    } else {
      ElMessage.warning(result.reason || result.message || '回答尚未正确，请继续练习')
    }
  } catch {
    /* request 层已提示 */
  } finally {
    retryLoading.value = -1
  }
}

async function refreshListQuietly() { await refreshSummaryStats(); await loadList() }
let mistakePageReady = false
onMounted(async () => { await refreshAll(); mistakePageReady = true })
onActivated(() => { if (!mistakePageReady) return; refreshListQuietly() })
</script>

<style scoped>
.mistake-page .page-title { background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { text-align: center; padding: 20px 16px; }
.stat-num { display:block; font-size:28px; font-weight:700; color: var(--text-primary); line-height: 1.2; }
.stat-num.unfixed { color: #d97706; }
.stat-num.fixed { color: #16a34a; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 6px; }
.toolbar { display:flex; align-items:center; justify-content:space-between; padding:16px 20px; margin-bottom:20px; }
.filter-group { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.mistake-list { display:flex; flex-direction:column; gap:16px; }
.mistake-item { padding:20px; }
.item-header { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
.item-tags { display:flex; flex-wrap:wrap; gap:8px; }
.item-time { font-size:12px; color: var(--text-secondary); }
.item-stem { font-size:15px; font-weight:500; line-height:1.6; margin-bottom:12px; color: var(--text-primary); }
.item-tag-summary { margin-bottom: 10px; }
.item-answers { display:flex; flex-direction:column; gap:6px; font-size:13px; color: var(--text-secondary); margin-bottom:12px; }
.item-errors { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
.detail-btn { margin-top:4px; }
.drawer-loading { padding:40px 0; }
.drawer-body { padding:0 4px 24px; }
.detail-section { margin-bottom:24px; }
.detail-text { font-size:14px; line-height:1.7; color: var(--text-primary); }
.detail-kv { display:flex; flex-direction:column; gap:10px; margin-top:12px; font-size:13px; line-height:1.6; }
.kv-label { display:block; font-size:11px; font-weight:600; color: var(--text-secondary); text-transform:uppercase; letter-spacing:0.03em; margin-bottom:2px; }
.tag-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.micro-lesson { padding:16px; font-size:14px; line-height:1.7; }
.micro-lesson h5 { font-size:15px; font-weight:600; margin-bottom:8px; color: var(--text-primary); }
.micro-lesson ul { padding-left:20px; margin-top:8px; }
.variant-card { padding:16px; margin-bottom:12px; }
.variant-head { display:flex; gap:8px; margin-bottom:10px; }
.variant-question { font-size:14px; line-height:1.6; margin-bottom:12px; }
.variant-options { margin-bottom:12px; }
.variant-option { display:block; margin-bottom:8px; white-space:normal; height:auto; line-height:1.5; }
.variant-submit { margin-top:8px; }
@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
</style>
