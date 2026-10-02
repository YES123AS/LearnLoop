<template>
  <div class="page-container">
    <PageHeader :title="PAGE_HEADERS.quiz.title" :subtitle="PAGE_HEADERS.quiz.subtitle" />

    <div class="practice-stats">
      <div class="ps-card glass-panel">
        <span class="ps-num">{{ answeredCount }}</span>
        <span class="ps-label">已完成</span>
      </div>
      <div class="ps-card glass-panel">
        <span class="ps-num">{{ store.accuracyRate }}%</span>
        <span class="ps-label">正确率</span>
      </div>
      <div class="ps-card glass-panel">
        <span class="ps-num">{{ difficulty }}</span>
        <span class="ps-label">当前难度</span>
      </div>
      <div class="ps-card glass-panel">
        <span class="ps-num">{{ store.records.length }}</span>
        <span class="ps-label">累计记录</span>
      </div>
    </div>

    <el-row :gutter="24">
      <el-col :span="7">
        <div class="card-panel">
          <el-form label-position="top">
            <el-form-item label="知识点">
              <div class="inline-input-row">
                <el-input :model-value="topic" placeholder="如：LZW算法" @update:model-value="handleTopicInput" />
                <SpeechInputButton size="small" :text="false" :model-value="topic" @start="handleQuizSpeechStart" @interim="handleQuizSpeechInterim" @result="handleQuizSpeechResult" @stop="handleQuizSpeechStop" @error="handleQuizSpeechError" />
              </div>
            </el-form-item>
            <el-form-item label="题型">
              <el-checkbox-group v-model="questionTypes">
                <el-checkbox v-for="t in typeOptions" :key="t" :label="t" />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="题目数量">
              <el-input-number v-model="count" :min="1" :max="10" />
            </el-form-item>
            <el-form-item label="难度">
              <el-radio-group v-model="difficulty">
                <el-radio v-for="d in difficultyOptions" :key="d" :label="d">{{ d }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <div class="form-actions">
              <el-button type="primary" class="gradient-btn" :loading="loading" @click="generate">生成题目</el-button>
              <el-button type="success" plain @click="$router.push('/analysis')">前往学情分析</el-button>
              <el-button v-if="store.records.length" plain @click="exportRecords">导出练习记录</el-button>
            </div>
          </el-form>

          <div v-if="questions.length" class="progress-section">
            <div class="progress-label">学习进度 {{ answeredInSession }}/{{ questions.length }}</div>
            <el-progress :percentage="progressPercent" :stroke-width="10" striped striped-flow />
          </div>

          <div class="records-summary">
            <h4>答题记录 ({{ store.records.length }})</h4>
            <el-table :data="store.records.slice(-5)" size="small" max-height="180">
              <el-table-column prop="knowledge_point" label="知识点" width="90" />
              <el-table-column prop="question_type" label="题型" width="70" />
              <el-table-column label="结果" width="60">
                <template #default="{ row }">
                  <el-tag :type="row.correct ? 'success' : 'danger'" size="small">{{ row.correct ? '对' : '错' }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>

      <el-col :span="17">
        <div class="card-panel quiz-area">
          <LoadingState
            v-if="loading"
            title="生成中"
            description="AI 智能体正在生成练习题。"
            loading-text="题目生成中，请稍候..."
            stage-text="正在解析知识点与题型"
          />
          <div v-else-if="questions.length">
            <div class="quiz-toolbar">
              <el-tag v-if="isDemoQuiz" type="info" size="small" effect="light">预览题目</el-tag>
              <el-button size="small" type="primary" @click="downloadQuiz">下载练习题</el-button>
            </div>
            <QuizCard
              v-for="(q, i) in normalizedQuestions"
              :key="q.id || i"
              :question="q"
              :index="i + 1"
              :topic="topic"
              :difficulty="difficulty"
              :show-answer="showAnswers[i]"
              @submit="onSubmit"
              @toggle-answer="toggleAnswer(i)"
            />

            <SectionCard title="题目标签分析" desc="基于本次练习的多维标签结果" style="margin-top:16px">
              <div class="tag-analysis-grid">
                <div class="analysis-block">
                  <strong>本次练习平均难度</strong>
                  <p>{{ tagAnalysis.averageDifficulty }}/5</p>
                </div>
                <div class="analysis-block">
                  <strong>高频薄弱维度</strong>
                  <p>{{ tagAnalysis.weakestLabel }}</p>
                </div>
                <div class="analysis-block">
                  <strong>错题集中维度</strong>
                  <p>{{ tagAnalysis.wrongSummary }}</p>
                </div>
                <div class="analysis-block full">
                  <strong>建议补强方向</strong>
                  <p>{{ tagAnalysis.suggestion }}</p>
                </div>
              </div>
            </SectionCard>
          </div>
          <ErrorState
            v-else-if="parseError"
            title="解析失败"
            :message="parseError"
            :details="rawResponse"
            :has-retry="true"
            @retry="generate"
          />
          <EmptyState
            v-else
            title="配置参数后点击「生成题目」"
            description="AI 将根据你的画像生成个性化检测题。"
            :icon="EditPen"
            :has-action="false"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useStudentStore } from '@/store/student'
import { generateQuiz, diagnoseMistake } from '@/api/index'
import { useAsyncTask } from '@/composables/useAsyncTask'
import { getStudentId } from '@/utils/studentId'
import { DEMO_QUIZ_QUESTIONS } from '@/demo/demoContent'
import { downloadTextFile, downloadJsonFile, sanitizeFilename, formatDateFilename } from '@/utils/download'
import { parseQuizResponse } from '@/utils/quizParser'
import { normalizeQuestionTags } from '@/utils/questionTags'
import { analyzeQuestionTagPerformance, generateTagBasedSuggestions } from '@/utils/questionTagAnalysis'
import QuizCard from '@/components/QuizCard.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import SectionCard from '@/components/SectionCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import SpeechInputButton from '@/components/SpeechInputButton.vue'
import { PAGE_HEADERS, BRAND_NAME } from '@/constants/brand'
import { EditPen } from '@element-plus/icons-vue'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { useSpeechInputField } from '@/composables/useSpeechInputField'

const store = useStudentStore()
const route = useRoute()
const topic = ref(store.demo_mode ? 'LZW算法' : '')
const speech = useSpeechInput()
const speechField = useSpeechInputField(speech, { getValue: () => topic.value, setValue: (val) => { topic.value = val } })
const questionTypes = ref(['选择题', '填空题', '简答题'])
const typeOptions = ['选择题', '填空题', '简答题']
const count = ref(3)
const difficulty = ref('简单')
const difficultyOptions = ['简单', '中等', '困难']
const { loading, run: runGenerateTask } = useAsyncTask()
const questions = ref([])
const showAnswers = ref({})
const answeredInSession = ref(0)
const fromApi = ref(false)
const parseError = ref('')
const rawResponse = ref('')

const isDemoQuiz = computed(() => store.demo_mode && !fromApi.value && questions.value.length > 0)
const answeredCount = computed(() => store.records.length)
const progressPercent = computed(() => !questions.value.length ? 0 : Math.round((answeredInSession.value / questions.value.length) * 100))
const normalizedQuestions = computed(() => questions.value.map(q => ({ ...q, tagMetrics: normalizeQuestionTags(q) })))

const tagAnalysis = computed(() => {
  const records = store.records.map((r, idx) => {
    const q = normalizedQuestions.value[idx] || normalizedQuestions.value[normalizedQuestions.value.length - 1] || {}
    return { ...r, ...q, correct: Boolean(r.correct) }
  })
  const analysis = analyzeQuestionTagPerformance(records)
  const suggestions = generateTagBasedSuggestions(analysis)
  const avgDifficulty = normalizedQuestions.value.length
    ? (normalizedQuestions.value.reduce((sum, q) => sum + normalizeQuestionTags(q).difficulty, 0) / normalizedQuestions.value.length).toFixed(1)
    : '0.0'
  return {
    averageDifficulty: avgDifficulty,
    weakestLabel: ({ difficulty: '难度', innovation: '创新度', importance: '重要度', integration: '综合度' }[analysis.weakest] || '难度'),
    wrongSummary: suggestions[0]?.title || '暂无明显薄弱维度',
    suggestion: suggestions.map(i => i.content).join('；')
  }
})

function resetSpeechState() { speechField.resetSpeechState() }
function handleQuizSpeechStart() { speechField.handleSpeechStart(topic.value) }
function handleQuizSpeechInterim(text) { speechField.handleSpeechInterim(text) }
function handleQuizSpeechResult(text) { speechField.handleSpeechResult(text) }
function handleQuizSpeechStop() { speechField.handleSpeechStop() }
function handleQuizSpeechError(message) { speechField.handleSpeechError(message); if (message) ElMessage.warning(message) }
function handleTopicInput(value) { topic.value = value; speechField.handleManualInput(value) }

function applyDemoQuestions() {
  speechField.cancelSpeech()
  parseError.value = ''
  rawResponse.value = ''
  if (store.demo_mode && store.hasProfile && !fromApi.value) {
    questions.value = DEMO_QUIZ_QUESTIONS.map((q, i) => ({
      id: q.id ?? i + 1,
      type: q.type || '简答题',
      question: q.question || '',
      options: Array.isArray(q.options) ? [...q.options] : [],
      answer: q.answer || '',
      analysis: q.analysis || q.explanation || '',
      knowledge_point: q.knowledge_point || topic.value || '未知知识点',
      tagMetrics: q.tagMetrics || null
    }))
    showAnswers.value = {}
    answeredInSession.value = 0
  } else if (!fromApi.value) {
    questions.value = []
  }
}

async function generate() {
  if (!topic.value.trim()) { ElMessage.warning('请输入知识点'); return }
  if (!questionTypes.value.length) { ElMessage.warning('请至少选择一种题型'); return }
  speechField.cancelSpeech()
  questions.value = []
  showAnswers.value = {}
  answeredInSession.value = 0
  fromApi.value = false
  parseError.value = ''
  rawResponse.value = ''
  try {
    await runGenerateTask(async () => {
      const data = await generateQuiz(topic.value, questionTypes.value, count.value, difficulty.value, store.student_profile)
      const parsed = parseQuizResponse(data)
      rawResponse.value = parsed.rawContent || JSON.stringify(data, null, 2)

      if (parsed.questions.length) {
        questions.value = parsed.questions.map((q, idx) => ({
          ...q,
          knowledge_point: q.knowledge_point || topic.value,
          tagMetrics: normalizeQuestionTags(q),
          id: q.id ?? idx + 1
        }))
        fromApi.value = true
        parseError.value = ''
        ElMessage.success(`成功生成 ${parsed.questions.length} 道题目`)
        return parsed.questions
      }
      parseError.value = parsed.error || '未能解析题目，请查看下方返回详情'
      ElMessage.warning(parseError.value)
      throw new Error(parseError.value)
    })
  } catch {
    /* api 层已提示 */
  }
}

function buildDiagnoseQuestion(record) {
  const raw = record.raw_question || {}
  return {
    id: raw.id ?? raw.question_id ?? Date.now(),
    question_id: String(raw.id ?? raw.question_id ?? ''),
    knowledge_point: record.knowledge_point || raw.knowledge_point || topic.value || '未知知识点',
    type: record.question_type || raw.type || '简答题',
    question: record.question || raw.question || '',
    options: record.options || raw.options || [],
    answer: record.standard_answer || raw.answer || '',
    analysis: record.analysis || raw.analysis || '',
    tagMetrics: record.tagMetrics || raw.tagMetrics || null
  }
}

function saveMistakeAsync(record) {
  if (store.demo_mode || record.correct) return

  ElMessage.info('已加入错题集，AI 正在生成错因诊断…')

  diagnoseMistake({
    student_id: getStudentId(),
    question: buildDiagnoseQuestion(record),
    user_answer: record.user_answer ?? '',
    difficulty: record.difficulty || difficulty.value || '简单',
    judge_reason: '与标准答案不一致',
    student_profile: store.student_profile
  }, { silent: true })
    .then(() => {
      ElMessage.success('错题已保存，可在错题集中查看')
    })
    .catch(() => {
      ElMessage.warning('错题保存失败，可稍后重试')
    })
}

function onSubmit(record) {
  store.addRecord({
    knowledge_point: record.knowledge_point,
    question_type: record.question_type,
    correct: record.correct
  })
  answeredInSession.value++
  ElMessage.success('答题记录已保存')
  saveMistakeAsync(record)
}

function toggleAnswer(i) { showAnswers.value[i] = !showAnswers.value[i] }

function buildQuizMarkdown() {
  const lines = [`# ${topic.value} 练习题`, '']
  normalizedQuestions.value.forEach((q, i) => {
    lines.push(`## 第 ${i + 1} 题（${q.type || '题目'}）`, '', q.question || '', '')
    if (q.options?.length) {
      q.options.forEach((opt, j) => lines.push(`${String.fromCharCode(65 + j)}. ${opt}`))
      lines.push('')
    }
    if (q.answer) lines.push(`**答案：** ${q.answer}`, '')
    if (q.analysis) lines.push(`**解析：** ${q.analysis}`, '')
    lines.push('')
  })
  return lines.join('\n')
}

function downloadQuiz() {
  if (!questions.value.length) return
  downloadTextFile(buildQuizMarkdown(), `${sanitizeFilename(topic.value)}_练习题.md`)
  ElMessage.success('文档已开始下载，请在浏览器下载记录中查看')
}

function exportRecords() {
  if (!store.records.length) return
  downloadJsonFile({
    records: store.records,
    export_time: new Date().toISOString(),
    source: BRAND_NAME
  }, formatDateFilename('练习记录', 'json'))
  ElMessage.success('练习记录已开始下载，请在浏览器下载记录中查看')
}

watch(() => store.demo_mode, () => {
  speechField.cancelSpeech()
  if (!store.demo_mode) topic.value = ''
  else if (store.hasProfile) topic.value = 'LZW算法'
  speechField.resetSpeechState()
  applyDemoQuestions()
})
watch(() => store.reset_version, () => {
  speechField.cancelSpeech()
  fromApi.value = false
  topic.value = store.demo_mode ? 'LZW算法' : ''
  applyDemoQuestions()
})
watch(() => route.query.topic, (nextTopic) => {
  if (typeof nextTopic === 'string' && nextTopic.trim()) {
    speechField.cancelSpeech()
    topic.value = nextTopic
    speechField.resetSpeechState()
  }
}, { immediate: true })

onMounted(() => {
  applyDemoQuestions()
})
onBeforeUnmount(() => speechField.cancelSpeech())
</script>

<style scoped>
.practice-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.ps-card { text-align: center; padding: 16px; }
.ps-num { display: block; font-size: 24px; font-weight: 800; color: var(--primary-dark); }
.ps-label { font-size: 12px; color: var(--text-secondary); }
.progress-section { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); }
.progress-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.records-summary { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); }
.records-summary h4 { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.form-actions { display: flex; flex-direction: column; gap: 12px; }
.form-actions .el-button { width: 100%; margin-left: 0 !important; }
.quiz-area { min-height: 500px; }
.quiz-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.raw-collapse { margin-top: 8px; width: 100%; }
.raw-content { max-height: 320px; overflow: auto; padding: 12px; background: #0f172a; color: #e2e8f0; border-radius: 8px; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.tag-analysis-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.analysis-block { padding: 14px; border: 1px solid var(--border); border-radius: 12px; background: rgba(99,102,241,0.04); }
.analysis-block strong { display:block; margin-bottom: 6px; font-size: 13px; }
.analysis-block p { font-size: 14px; color: var(--text-primary); line-height: 1.6; }
.analysis-block.full { grid-column: 1 / -1; }
.inline-input-row { display:flex; align-items:center; gap:10px; }
.inline-input-row :deep(.el-input) { flex:1; }
</style>
