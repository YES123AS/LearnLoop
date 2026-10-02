<template>
  <div class="quiz-card card-panel">
    <div class="quiz-header">
      <div class="quiz-head-left">
        <el-tag size="small" effect="dark">{{ displayType }}</el-tag>
        <span class="quiz-index">第 {{ index }} 题</span>
      </div>
      <el-tag v-if="question.knowledge_point" size="small" effect="light" type="info">{{ question.knowledge_point }}</el-tag>
    </div>

    <div class="quiz-question">{{ displayQuestion }}</div>

    <QuestionTagMetrics :question="question" />

    <div v-if="showChoiceOptions" class="quiz-options">
      <div
        v-for="(opt, optIdx) in question.options"
        :key="`${index}-opt-${optIdx}`"
        class="option-item"
        :class="{
          selected: selectedOption === opt,
          correct: showAnswer && isCorrectOption(opt),
          wrong: showAnswer && selectedOption === opt && !isCorrectOption(opt)
        }"
        @click="selectOption(opt)"
      >
        {{ opt }}
      </div>
    </div>

    <div v-else-if="isFillBlank" class="quiz-input">
      <el-input
        v-model="fillAnswer"
        placeholder="请输入答案"
        :disabled="showAnswer"
        @keyup.enter="submitFill"
      />
    </div>

    <div v-else class="quiz-input">
      <el-input
        v-model="subjectiveAnswer"
        type="textarea"
        :rows="3"
        placeholder="请输入你的答案"
        :disabled="showAnswer"
      />
    </div>

    <div class="quiz-actions">
      <el-button v-if="!showAnswer" type="primary" @click="submitAnswer">提交答案</el-button>
      <el-button v-if="!showAnswer" @click="$emit('toggle-answer')">查看答案</el-button>
      <el-button v-else @click="$emit('toggle-answer')">隐藏答案</el-button>
    </div>

    <div v-if="showAnswer" class="quiz-answer">
      <div class="answer-row">
        <strong>标准答案：</strong>{{ displayAnswer }}
      </div>
      <div class="analysis-row">
        <strong>解析：</strong>{{ displayAnalysis }}
      </div>
      <el-tag v-if="answered" :type="isCorrect ? 'success' : 'danger'" size="small">
        {{ isCorrect ? '回答正确' : '回答错误' }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import QuestionTagMetrics from '@/components/QuestionTagMetrics.vue'

const props = defineProps({
  question: { type: Object, required: true },
  index: { type: Number, required: true },
  showAnswer: { type: Boolean, default: false },
  topic: { type: String, default: '' },
  difficulty: { type: String, default: '简单' }
})

const emit = defineEmits(['submit', 'toggle-answer'])

const selectedOption = ref('')
const fillAnswer = ref('')
const subjectiveAnswer = ref('')
const answered = ref(false)
const isCorrect = ref(false)

const displayType = computed(() => props.question.type || '简答题')
const displayQuestion = computed(() => props.question.question || '（题目内容缺失）')
const displayAnswer = computed(() => props.question.answer?.trim() ? props.question.answer : '暂无参考答案')
const displayAnalysis = computed(() => props.question.analysis?.trim() ? props.question.analysis : '暂无解析')

const showChoiceOptions = computed(() =>
  props.question.type === '选择题' && Array.isArray(props.question.options) && props.question.options.length > 0
)

const isFillBlank = computed(() => props.question.type === '填空题')

function isCorrectOption(opt) {
  const ans = (props.question.answer || '').trim()
  if (!ans) return false
  return opt.startsWith(ans) || opt.includes(`${ans}.`) || opt === ans || opt.includes(ans)
}

function selectOption(opt) {
  if (props.showAnswer) return
  selectedOption.value = opt
}

function checkCorrect(userAns) {
  const standard = (props.question.answer || '').trim().toLowerCase()
  const user = (userAns || '').trim().toLowerCase()
  if (!standard) return false

  if (showChoiceOptions.value) {
    return isCorrectOption(userAns)
  }
  return standard === user || standard.includes(user) || user.includes(standard)
}

function submitAnswer() {
  if (answered.value) return

  let userAns = ''
  if (showChoiceOptions.value) {
    userAns = selectedOption.value
    if (!userAns) return
  } else if (isFillBlank.value) {
    userAns = fillAnswer.value
    if (!userAns.trim()) return
  } else {
    userAns = subjectiveAnswer.value
  }

  isCorrect.value = checkCorrect(userAns)
  answered.value = true

  emit('submit', {
    knowledge_point: props.topic,
    question_type: props.question.type || '简答题',
    correct: isCorrect.value,
    question: props.question.question || '',
    user_answer: userAns,
    standard_answer: props.question.answer || '',
    analysis: props.question.analysis || '',
    options: Array.isArray(props.question.options) ? [...props.question.options] : [],
    difficulty: props.difficulty || '简单',
    raw_question: { ...props.question },
    tagMetrics: props.question.tagMetrics || props.question.tags || null
  })
}

function submitFill() {
  submitAnswer()
}

watch(() => props.question, () => {
  selectedOption.value = ''
  fillAnswer.value = ''
  subjectiveAnswer.value = ''
  answered.value = false
  isCorrect.value = false
}, { deep: true })
</script>

<style scoped>
.quiz-card {
  border-left: 4px solid #14B8A6;
  margin-bottom: 16px;
}

.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.quiz-head-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.quiz-index {
  font-size: 13px;
  color: var(--text-secondary);
}

.quiz-question {
  font-size: 15px;
  font-weight: 500;
  line-height: 1.7;
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.option-item {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s, color 0.2s;
  font-size: 14px;
}

.option-item:hover { border-color: var(--primary); background: #f8fafc; }
.option-item.selected { border-color: var(--primary); background: #F0FDFA; }
.option-item.correct { border-color: #22c55e; background: #f0fdf4; }
.option-item.wrong { border-color: #ef4444; background: #fef2f2; }
.quiz-input { margin-bottom: 16px; }
.quiz-actions { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.quiz-answer { padding: 16px; background: #f8fafc; border-radius: 10px; font-size: 14px; line-height: 1.7; }
.answer-row, .analysis-row { margin-bottom: 8px; }
.analysis-row { color: var(--text-secondary); }
</style>
