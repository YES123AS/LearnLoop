<template>
  <div class="page-container profile-page">
    <section class="profile-hero card-panel">
      <div class="profile-hero-content">
        <div class="profile-hero-kicker">LearnLoopAI · 学习画像构建中心</div>
        <h1 class="profile-hero-title">学习画像构建</h1>
        <p class="profile-hero-desc">通过多轮对话自主构建结构化学习画像，并流转至学习路径规划与学习工作台。</p>
        <div class="profile-mode-tabs">
          <button class="profile-mode-tab" :class="{ active: profileMode === 'chat' }" @click="profileMode = 'chat'">对话式画像</button>
          <button class="profile-mode-tab" :class="{ active: profileMode === 'form' }" @click="profileMode = 'form'">表单生成（备用）</button>
        </div>
      </div>
    </section>

    <div class="profile-layout">
      <div class="profile-main-panel">
        <template v-if="profileMode === 'chat'">
          <div class="card-panel profile-chat-panel">
            <div class="profile-chat-header">
              <div>
                <h3>对话式画像构建</h3>
                <p>通过 AI 多轮追问逐步完善学习档案</p>
              </div>
              <div class="header-meta">
                <el-tag type="primary" effect="light">{{ currentProgressText }}</el-tag>
                <el-button size="small" plain @click="restartConversation">重新开始画像构建</el-button>
              </div>
            </div>

            <div class="profile-chat-progress">
              <div class="progress-row">
                <span>当前采集：{{ currentStepLabel }}</span>
                <span>{{ currentStepNumber }} / {{ profileQuestions.length }}</span>
              </div>
              <el-progress :percentage="progressPercent" :stroke-width="8" :color="'var(--primary)'" />
            </div>

            <div ref="messageListRef" class="profile-message-list">
              <div v-for="(message, index) in profileChatMessages" :key="`${message.role}-${index}-${message.step || 'msg'}`" class="profile-message" :class="message.role">
                <div class="profile-message-avatar">
                  <el-icon v-if="message.role === 'assistant'"><Cpu /></el-icon>
                  <span v-else>我</span>
                </div>
                <div class="profile-message-bubble">
                  <p>{{ message.content }}</p>
                  <small>{{ formatTime(message.time) }}<span v-if="message.stepLabel"> · {{ message.stepLabel }}</span></small>
                </div>
              </div>

              <div v-if="isAssistantTyping" class="profile-message assistant typing-message">
                <div class="profile-message-avatar"><el-icon><Cpu /></el-icon></div>
                <div class="profile-message-bubble typing-bubble">
                  <span>AI 正在生成画像问题</span><i class="typing-dots"><i></i><i></i><i></i></i>
                </div>
              </div>
            </div>

            <div v-if="showQuickReplies" class="profile-quick-replies">
              <el-tag v-for="item in quickReplies" :key="item" effect="light" class="quick-reply-tag" @click="fillQuickReply(item)">{{ item }}</el-tag>
            </div>

            <div class="profile-chat-input-bar">
              <el-input :model-value="chatInput" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" :placeholder="chatPlaceholder" :disabled="isAssistantTyping" @update:model-value="handleChatInputUpdate" @keydown.enter.exact.prevent="handleSendProfileMessage" @keydown.shift.enter.stop />
              <div class="input-actions">
                <SpeechInputButton :text="true" size="small" :model-value="chatInput" @start="handleSpeechStart" @interim="handleSpeechInterim" @result="handleSpeechResult" @stop="handleSpeechStop" @error="handleSpeechError" />
                <el-button size="small" plain :disabled="isAssistantTyping || !canReanswer" @click="reanswerCurrentStep">重新回答当前项</el-button>
                <el-button size="small" plain :disabled="isAssistantTyping || !canSkipCurrent" @click="skipCurrentStep">跳过此项</el-button>
                <el-button type="primary" class="gradient-btn" :loading="saving || isAssistantTyping" :disabled="isAssistantTyping" @click="handleSendProfileMessage">发送</el-button>
              </div>
            </div>

            <div class="profile-summary-actions">
              <el-button type="primary" class="gradient-btn" :loading="saving" @click="submitProfile">保存画像</el-button>
              <el-button plain @click="$router.push('/path')">生成学习路径</el-button>
              <el-button plain @click="$router.push('/dashboard')">进入学习工作台</el-button>
              <el-button plain @click="continueNotes">继续补充</el-button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="card-panel profile-form-card">
            <div class="panel-head">
              <div>
                <h3>表单生成（备用）</h3>
                <p>使用结构化表单快速补充画像字段</p>
              </div>
              <el-tag type="warning" effect="light">备用入口</el-tag>
            </div>

            <el-form label-position="top" class="profile-form-grid">
              <el-form-item label="年级"><div class="field-control"><el-input v-model="form.grade" placeholder="例如：大二" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('grade', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="专业 / 学科方向"><div class="field-control"><el-input v-model="form.major" placeholder="例如：智能科学与技术" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('major', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="当前课程"><div class="field-control"><el-input v-model="form.course" placeholder="例如：多媒体信息处理" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('course', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="学习目标"><div class="field-control"><el-input v-model="form.goal" placeholder="例如：期末复习" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('goal', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="基础水平"><div class="field-control"><el-input v-model="form.level" placeholder="例如：基础较弱" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('level', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="学习偏好"><div class="field-control"><el-input v-model="form.learning_style" type="textarea" :rows="3" placeholder="例如：喜欢通俗解释和案例化学习" /><SpeechInputButton size="small" :text="false" @result="(text) => applySpeech('learning_style', text)" @error="handleFormSpeechError" /></div></el-form-item>
              <el-form-item label="每周学习时间"><el-input v-model="form.weekly_time" placeholder="例如：6 小时" /></el-form-item>
              <el-form-item label="已掌握知识点"><el-input v-model="form.mastered_points" type="textarea" :rows="2" placeholder="例如：基础概念、简单练习题" /></el-form-item>
              <el-form-item label="薄弱知识点"><el-input v-model="form.weak_points" type="textarea" :rows="2" placeholder="例如：LZW算法、JPEG压缩" /></el-form-item>
            </el-form>

            <div class="profile-actions-row">
              <el-button type="primary" class="gradient-btn" :loading="saving" @click="submitProfile">保存画像</el-button>
              <el-button plain @click="profileMode = 'chat'">返回对话式画像</el-button>
            </div>
          </div>
        </template>
      </div>

      <aside class="profile-summary-panel">
        <div class="card-panel summary-card">
          <div class="summary-head">
            <h3>画像概览</h3>
            <el-tag type="primary" effect="light">实时同步</el-tag>
          </div>
          <div class="summary-progress">
            <div class="progress-row"><span>画像完成度</span><strong>{{ completionPercent }}%</strong></div>
            <el-progress :percentage="completionPercent" :stroke-width="8" :color="'var(--primary)'" />
            <p class="pending-list">待补充：{{ pendingFieldsText }}</p>
          </div>
          <div class="summary-meta">
            <div><span>年级</span><strong>{{ profileSnapshot.grade }}</strong></div>
            <div><span>专业</span><strong>{{ profileSnapshot.major }}</strong></div>
            <div><span>当前课程</span><strong>{{ profileSnapshot.course }}</strong></div>
          </div>
        </div>

        <div class="card-panel summary-card">
          <h3>能力雷达图</h3>
          <div ref="radarRef" class="radar-box"></div>
        </div>

        <div class="card-panel summary-card">
          <h3>学习档案摘要</h3>
          <div class="summary-tags">
            <el-tag effect="light">目标：{{ profileSnapshot.goal }}</el-tag>
            <el-tag effect="light">基础：{{ profileSnapshot.level }}</el-tag>
            <el-tag effect="light">偏好：{{ profileSnapshot.learning_style }}</el-tag>
            <el-tag effect="light">时间：{{ profileSnapshot.weekly_time }}</el-tag>
            <el-tag effect="light" type="warning">薄弱点：{{ profileSnapshot.weak_points }}</el-tag>
            <el-tag effect="light" type="success">已掌握：{{ profileSnapshot.mastered_points }}</el-tag>
            <el-tag effect="light" type="info">补充说明：{{ profileSnapshot.extra_notes }}</el-tag>
          </div>
        </div>

        <div class="card-panel summary-card">
          <h3>下一步行动</h3>
          <div class="action-list">
            <el-button type="primary" class="gradient-btn" @click="$router.push('/path')">生成学习路径</el-button>
            <el-button plain @click="$router.push('/dashboard')">进入学习工作台</el-button>
            <el-button plain @click="$router.push('/resource')">生成学习资源</el-button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { Cpu } from '@element-plus/icons-vue'
import { useStudentStore } from '@/store/student'
import SpeechInputButton from '@/components/SpeechInputButton.vue'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { useSpeechInputField } from '@/composables/useSpeechInputField'

const CHAT_KEY = 'learnloop_profile_chat_messages'
const STEP_KEY = 'learnloop_profile_chat_step'
const COMPLETED_KEY = 'learnloop_profile_chat_completed'
const EXTRA_KEY = 'learnloop_profile_chat_extra_notes'

const store = useStudentStore()
const profileMode = ref('chat')
const saving = ref(false)
const isAssistantTyping = ref(false)
const radarRef = ref(null)
const messageListRef = ref(null)
let radarChart = null

const profileQuestions = [
  { key: 'grade', label: '年级', question: '你好，我是你的 AI 学习画像助手。为了帮你生成更准确的学习路径，请先告诉我你目前所在年级。' },
  { key: 'major', label: '专业 / 学科方向', question: '好的。你目前的专业或学科方向是什么？例如：智能科学与技术、计算机科学、数学、英语等。' },
  { key: 'course', label: '当前课程', question: '你现在主要想围绕哪门课程或哪个学习主题进行提升？' },
  { key: 'goal', label: '学习目标', question: '你希望通过这个学习系统达成什么目标？例如：期末复习、竞赛提升、科研入门、查漏补缺等。' },
  { key: 'level', label: '基础水平', question: '你觉得自己当前基础水平如何？可以说基础薄弱、一般、较好，或者具体描述你的情况。' },
  { key: 'weak_points', label: '薄弱知识点', question: '你目前最薄弱或最困惑的知识点有哪些？可以直接用自然语言描述。' },
  { key: 'mastered_points', label: '已掌握知识点', question: '你已经比较熟悉或掌握的知识点有哪些？' },
  { key: 'learning_style', label: '学习偏好', question: '你更喜欢哪种学习方式？例如：例题讲解、图文总结、视频式说明、先练后讲、项目实践等。' },
  { key: 'weekly_time', label: '每周学习时间', question: '你每周大概能安排多少时间学习这门内容？' }
]

const form = reactive({
  grade: store.student_profile.grade || '',
  major: store.student_profile.major || '',
  course: store.student_profile.course || '',
  level: store.student_profile.level || '',
  goal: store.student_profile.goal || '',
  weak_points: (store.student_profile.weak_points || []).join('、'),
  mastered_points: (store.mastered_points || []).join('、'),
  learning_style: store.student_profile.learning_style || '',
  weekly_time: store.student_profile.weekly_time || '',
  extra_notes: store.student_profile.extra_notes || ''
})

const profileChatMessages = ref([])
const currentProfileStep = ref(0)
const chatInput = ref('')
const speech = useSpeechInput()
const chatSpeechField = useSpeechInputField(speech, { getValue: () => chatInput.value, setValue: (val) => { chatInput.value = val } })
const completed = ref(false)
const waitingForContinue = ref(false)
const progressHoldStep = ref(null)

const currentStep = computed(() => profileQuestions[currentProfileStep.value] || null)
const currentStepLabel = computed(() => currentStep.value?.label || '补充说明')
const currentStepNumber = computed(() => Math.min(currentProfileStep.value + 1, profileQuestions.length))
const progressPercent = computed(() => Math.round((currentProfileStep.value / profileQuestions.length) * 100))
const currentProgressText = computed(() => `${currentStepNumber.value} / ${profileQuestions.length}`)
const chatPlaceholder = computed(() => {
  const step = currentStep.value?.key
  if (waitingForContinue.value) return '请输入补充说明，例如：我还想补充……'
  if (step === 'grade') return '请输入你的年级，例如：大一'
  if (step === 'major') return '请输入你的专业，例如：智能科学与技术'
  if (step === 'course') return '请输入当前课程，例如：多媒体信息处理'
  if (step === 'goal') return '请输入你的学习目标，例如：期末复习'
  if (step === 'level') return '请输入你的基础水平，例如：基础薄弱'
  if (step === 'weak_points') return '请输入薄弱知识点，例如：LZW 算法'
  if (step === 'mastered_points') return '请输入已掌握知识点'
  if (step === 'learning_style') return '请输入你的学习偏好，例如：图文总结'
  if (step === 'weekly_time') return '请输入每周学习时间，例如：6 小时'
  return '请输入你的回答'
})
const canReanswer = computed(() => currentProfileStep.value > 0 && !completed.value)
const canSkipCurrent = computed(() => Boolean(currentStep.value) && !completed.value)
const showQuickReplies = computed(() => !completed.value && ['grade', 'goal', 'level', 'learning_style', 'weekly_time'].includes(currentStep.value?.key))
const quickReplies = computed(() => {
  const step = currentStep.value?.key
  if (step === 'grade') return ['大一', '大二', '大三', '大四', '研一']
  if (step === 'goal') return ['期末复习', '查漏补缺', '竞赛提升', '科研入门', '项目实践']
  if (step === 'level') return ['基础薄弱', '一般', '较好', '较强']
  if (step === 'learning_style') return ['例题讲解', '图文总结', '先练后讲', '项目实践', '综合训练']
  if (step === 'weekly_time') return ['每周 2 小时', '每周 5 小时', '每周 8 小时', '每天 1 小时']
  return []
})

function defaultAssistantMessage() {
  return { role: 'assistant', content: profileQuestions[0].question, step: profileQuestions[0].key, stepLabel: '第 1 轮采集', time: Date.now() }
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function syncStorage() {
  localStorage.setItem(CHAT_KEY, JSON.stringify(profileChatMessages.value))
  localStorage.setItem(STEP_KEY, String(currentProfileStep.value))
  localStorage.setItem(COMPLETED_KEY, completed.value ? '1' : '0')
  localStorage.setItem(EXTRA_KEY, form.extra_notes || '')
}

function loadChatState() {
  try {
    const msgs = JSON.parse(localStorage.getItem(CHAT_KEY) || 'null')
    const step = Number(localStorage.getItem(STEP_KEY) || 0)
    const done = localStorage.getItem(COMPLETED_KEY) === '1'
    const extra = localStorage.getItem(EXTRA_KEY) || ''
    if (Array.isArray(msgs) && msgs.length) profileChatMessages.value = msgs
    else profileChatMessages.value = [defaultAssistantMessage()]
    currentProfileStep.value = Number.isFinite(step) ? step : 0
    completed.value = done
    form.extra_notes = extra || form.extra_notes || ''
  } catch {
    profileChatMessages.value = [defaultAssistantMessage()]
  }
}

function persistProfileFields() {
  const payload = buildProfilePayload()
  store.updateProfile(payload)
  store.mastered_points = payload.mastered_points
  if (payload.extra_notes) store.updateProfileField('extra_notes', payload.extra_notes)
}

function mapAnswerToProfile(stepKey, answer) {
  const text = String(answer || '').trim()
  if (!text) return
  if (stepKey === 'weak_points') {
    form.weak_points = text
    store.updateProfileField('weak_points', text.split(/[、,，\n]/).map(s => s.trim()).filter(Boolean))
    return
  }
  if (stepKey === 'mastered_points') {
    form.mastered_points = text
    store.mastered_points = text.split(/[、,，\n]/).map(s => s.trim()).filter(Boolean)
    return
  }
  if (stepKey === 'weekly_time') {
    form.weekly_time = text
    store.updateProfileField('weekly_time', text)
    return
  }
  if (stepKey === 'level') {
    form.level = text
    store.updateProfileField('level', text)
    return
  }
  if (stepKey === 'goal') form.goal = text
  if (stepKey === 'learning_style') form.learning_style = text
  if (stepKey === 'grade') form.grade = text
  if (stepKey === 'major') form.major = text
  if (stepKey === 'course') form.course = text
  store.updateProfileField(stepKey, text)
}

function buildProfilePayload() {
  return {
    grade: form.grade,
    major: form.major,
    course: form.course,
    goal: form.goal,
    level: form.level,
    learning_style: form.learning_style,
    weekly_time: form.weekly_time,
    extra_notes: form.extra_notes,
    weak_points: String(form.weak_points || '').split(/[、,，\n]/).map(s => s.trim()).filter(Boolean),
    mastered_points: String(form.mastered_points || '').split(/[、,，\n]/).map(s => s.trim()).filter(Boolean)
  }
}

function scrollMessagesToBottom() {
  nextTick(() => {
    const el = messageListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function pushMessage(message) {
  profileChatMessages.value.push(message)
  syncStorage()
  scrollMessagesToBottom()
}

function pushAssistantMessage(content, step = currentStep.value?.key || 'summary', stepLabel = '') {
  pushMessage({ role: 'assistant', content, step, stepLabel, time: Date.now() })
}

function pushUserMessage(content) {
  pushMessage({ role: 'user', content, time: Date.now() })
}

function getStepSummaryLine() {
  const parts = [
    form.grade || '待补充',
    form.major || '待补充',
    form.course || '待补充'
  ]
  return `${parts.join(' / ')}`
}

function buildSummaryMessage() {
  return `我已经根据你的回答生成了初步学习画像：${getStepSummaryLine()}。你的目标是${form.goal || '待补充'}，基础水平为${form.level || '待补充'}。已掌握：${form.mastered_points || '待补充'}；薄弱点：${form.weak_points || '待补充'}；学习偏好：${form.learning_style || '待补充'}；每周学习时间：${form.weekly_time || '待补充'}。你可以点击保存画像，也可以继续补充说明。`
}

function finishConversationIfNeeded() {
  if (currentProfileStep.value >= profileQuestions.length) {
    if (!completed.value) {
      pushAssistantMessage(buildSummaryMessage(), 'summary', '画像总结')
      completed.value = true
      syncStorage()
    }
    return true
  }
  return false
}

function showNextAssistantQuestion() {
  if (currentProfileStep.value >= profileQuestions.length) return finishConversationIfNeeded()
  const q = profileQuestions[currentProfileStep.value]
  pushAssistantMessage(q.question, q.key, `第 ${currentProfileStep.value + 1} 轮采集`)
}

function startTypingThen(callback) {
  isAssistantTyping.value = true
  const delay = 300 + Math.floor(Math.random() * 500)
  window.setTimeout(() => {
    isAssistantTyping.value = false
    callback()
    scrollMessagesToBottom()
  }, delay)
}

function commitCurrentAnswer(rawAnswer) {
  const current = currentStep.value
  if (!current && !waitingForContinue.value) {
    ElMessage.warning('当前采集已完成，如需继续请点击“继续补充”')
    return false
  }

  if (waitingForContinue.value) {
    form.extra_notes = form.extra_notes ? `${form.extra_notes} ${rawAnswer}` : rawAnswer
    store.updateProfileField('extra_notes', form.extra_notes)
    waitingForContinue.value = false
    pushAssistantMessage('已记录补充说明，你还可以继续保存画像或补充更多细节。', 'extra_notes', '补充说明')
    syncStorage()
    return true
  }

  mapAnswerToProfile(current.key, rawAnswer)
  currentProfileStep.value += 1
  syncStorage()
  startTypingThen(() => {
    if (currentProfileStep.value < profileQuestions.length) showNextAssistantQuestion()
    else finishConversationIfNeeded()
  })
  return true
}

function handleSendProfileMessage() {
  const rawAnswer = chatInput.value.trim()
  if (!rawAnswer) {
    ElMessage.warning('请输入你的回答')
    return
  }
  if (isAssistantTyping.value) return

  chatSpeechField.cancelSpeech()
  chatInput.value = ''
  pushUserMessage(rawAnswer)
  commitCurrentAnswer(rawAnswer)
}

function fillQuickReply(text) {
  chatSpeechField.cancelSpeech()
  chatInput.value = text
  chatSpeechField.resetSpeechState()
}

function resetProfileSpeechState() {
  chatSpeechField.resetSpeechState()
}
function cancelProfileSpeech() {
  chatSpeechField.cancelSpeech()
}

function handleSpeechStart() {
  chatSpeechField.handleSpeechStart(chatInput.value)
}
function handleSpeechInterim(text) {
  chatSpeechField.handleSpeechInterim(text)
}
function handleSpeechResult(text) {
  chatSpeechField.handleSpeechResult(text)
}
function handleSpeechStop() {
  chatSpeechField.handleSpeechStop()
}

function handleChatInputUpdate(value) {
  chatInput.value = value
  chatSpeechField.handleManualInput(value)
}

function handleSpeechError(message) { chatSpeechField.handleSpeechError(message); if (message) ElMessage.warning(message) }
function applySpeech(fieldKey, text) {
  const normalized = String(text || '').trim()
  if (!normalized) return
  if (fieldKey === 'grade') form.grade = normalized
  if (fieldKey === 'major') form.major = normalized
  if (fieldKey === 'course') form.course = normalized
  if (fieldKey === 'goal') form.goal = normalized
  if (fieldKey === 'level') form.level = normalized
  if (fieldKey === 'learning_style') form.learning_style = normalized
}
function handleFormSpeechError(message) { if (message) ElMessage.warning(message) }

function skipCurrentStep() {
  if (!currentStep.value || isAssistantTyping.value) return
  chatSpeechField.cancelSpeech()
  chatInput.value = ''
  pushUserMessage('暂时跳过')
  mapAnswerToProfile(currentStep.value.key, '')
  currentProfileStep.value += 1
  syncStorage()
  startTypingThen(() => {
    if (currentProfileStep.value < profileQuestions.length) showNextAssistantQuestion()
    else finishConversationIfNeeded()
  })
}

function reanswerCurrentStep() {
  if (!currentStep.value || isAssistantTyping.value) return
  chatSpeechField.cancelSpeech()
  chatInput.value = ''
  pushAssistantMessage(`好的，我们重新补充一下【${currentStep.value.label}】。请重新告诉我……`, currentStep.value.key, '重新回答')
}

function continueNotes() {
  waitingForContinue.value = true
  chatSpeechField.cancelSpeech()
  chatInput.value = ''
  pushAssistantMessage('你可以继续补充你的学习习惯、近期考试安排或其他需求。', 'extra_notes', '补充说明')
  syncStorage()
}

function submitProfile() {
  saving.value = true
  try {
    const payload = buildProfilePayload()
    store.updateProfile(payload)
    store.mastered_points = payload.mastered_points
    if (payload.extra_notes) store.updateProfileField('extra_notes', payload.extra_notes)
    chatSpeechField.cancelSpeech()
    chatInput.value = ''
    ElMessage.success('学习画像已保存')
    renderRadar()
    if (completed.value) {
      ElMessage.info('你可以继续前往学习路径或学习工作台，继续完成后续学习闭环。')
    }
  } finally {
    saving.value = false
  }
}

async function restartConversation() {
  try {
    await ElMessageBox.confirm('重新开始会清空当前对话记录，但不会删除已保存的学习画像。是否继续？', '重新开始画像构建', { type: 'warning', confirmButtonText: '继续', cancelButtonText: '取消' })
    profileChatMessages.value = [defaultAssistantMessage()]
    currentProfileStep.value = 0
    chatSpeechField.cancelSpeech()
    chatInput.value = ''
    resetProfileSpeechState()
    completed.value = false
    waitingForContinue.value = false
    form.extra_notes = ''
    localStorage.removeItem(CHAT_KEY)
    localStorage.removeItem(STEP_KEY)
    localStorage.removeItem(COMPLETED_KEY)
    localStorage.removeItem(EXTRA_KEY)
    syncStorage()
    scrollMessagesToBottom()
  } catch {}
}

const profileSnapshot = computed(() => ({
  grade: store.student_profile.grade || '待补充',
  major: store.student_profile.major || '待补充',
  course: store.student_profile.course || '待补充',
  goal: store.student_profile.goal || '待补充',
  level: store.student_profile.level || '待补充',
  weak_points: (store.student_profile.weak_points || []).join('、') || '待补充',
  mastered_points: (store.mastered_points || []).join('、') || '待补充',
  learning_style: store.student_profile.learning_style || '待补充',
  weekly_time: store.student_profile.weekly_time || '待补充',
  extra_notes: store.student_profile.extra_notes || '待补充'
}))

const completionPercent = computed(() => {
  const total = profileQuestions.length
  const filled = profileQuestions.filter(item => {
    const val = profileSnapshot.value[item.key]
    return val && val !== '待补充' && String(val).trim()
  }).length
  return Math.round((filled / total) * 100)
})

const pendingFieldsText = computed(() => {
  const pending = profileQuestions.filter(item => {
    const val = profileSnapshot.value[item.key]
    return !val || val === '待补充' || !String(val).trim()
  }).map(item => item.label)
  return pending.length ? pending.join('、') : '无'
})

function renderRadar() {
  if (!radarRef.value) return
  radarChart = radarChart || echarts.init(radarRef.value)
  radarChart.setOption({
    radar: {
      indicator: [
        { name: '基础知识', max: 100 },
        { name: '综合掌握', max: 100 },
        { name: '自主学习', max: 100 },
        { name: '实践能力', max: 100 },
        { name: '学习稳定性', max: 100 }
      ]
    },
    series: [{ type: 'radar', data: [{ value: [78, 66, 72, 68, 74], name: '画像评估', areaStyle: { color: 'rgba(99,102,241,0.18)' } }] }]
  })
}

watch(() => store.student_profile, () => nextTick(renderRadar), { deep: true, immediate: true })
watch(profileMode, (mode) => { if (mode === 'chat') nextTick(scrollMessagesToBottom) })

onMounted(() => {
  loadChatState()
  if (!profileChatMessages.value.length) profileChatMessages.value = [defaultAssistantMessage()]
  if (!profileChatMessages.value.some(item => item.role === 'assistant')) profileChatMessages.value.unshift(defaultAssistantMessage())
  renderRadar()
  scrollMessagesToBottom()
})

onBeforeUnmount(() => {
  chatSpeechField.cancelSpeech()
  syncStorage()
  radarChart?.dispose()
  radarChart = null
})
</script>

<style scoped>
.profile-hero { padding: 32px 32px 28px; background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(59,130,246,0.06)); margin-bottom: 24px; }
.profile-hero-kicker { font-size: 12px; font-weight: 700; letter-spacing: .08em; color: var(--primary); text-transform: uppercase; }
.profile-hero-title { margin-top: 10px; font-size: 32px; font-weight: 800; color: var(--text-primary); line-height: 1.2; }
.profile-hero-desc { margin-top: 10px; color: var(--text-secondary); font-size: 15px; line-height: 1.8; max-width: 860px; }
.profile-mode-tabs { display:flex; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
.profile-mode-tab { border: 0; border-radius: 999px; padding: 12px 18px; background: rgba(255,255,255,0.62); color: var(--primary-dark); font-weight: 700; cursor: pointer; transition: all .2s ease; box-shadow: inset 0 0 0 1px rgba(99,102,241,.12); }
.profile-mode-tab.active { background: #fff; box-shadow: 0 10px 22px rgba(99,102,241,.16); transform: translateY(-1px); }
.profile-layout { display:grid; grid-template-columns:minmax(0,1.6fr) minmax(320px, .9fr); gap: 24px; align-items:start; }
.profile-main-panel { min-width:0; }
.profile-summary-panel { display:flex; flex-direction:column; gap:16px; position: sticky; top: 92px; }
.profile-chat-panel, .profile-form-card { padding: 24px; }
.profile-chat-header { display:flex; justify-content:space-between; gap: 16px; align-items:flex-start; margin-bottom: 14px; }
.header-meta { display:flex; gap: 8px; align-items:center; flex-wrap:wrap; }
.profile-chat-header h3, .panel-head h3 { font-size: 20px; margin-bottom: 6px; }
.profile-chat-header p, .panel-head p { color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.profile-chat-progress { margin-bottom: 16px; }
.progress-row { display:flex; justify-content:space-between; gap: 10px; color: var(--text-secondary); font-size: 13px; margin-bottom: 8px; }
.profile-message-list { height: 500px; overflow-y: auto; padding: 12px 4px 16px; display:flex; flex-direction:column; gap: 14px; border-radius: 18px; background: linear-gradient(180deg, rgba(248,250,252,.72), rgba(241,245,249,.56)); border: 1px solid var(--border); }
.profile-message { display:flex; gap: 10px; align-items:flex-end; }
.profile-message.user { flex-direction: row-reverse; }
.profile-message-avatar { width: 36px; height: 36px; border-radius: 50%; display:flex; align-items:center; justify-content:center; flex-shrink:0; background: rgba(99,102,241,.12); color: var(--primary-dark); font-weight: 700; }
.profile-message.user .profile-message-avatar { background: var(--gradient); color: #fff; }
.profile-message-bubble { max-width: 78%; padding: 12px 14px; border-radius: 16px; background: #fff; border: 1px solid var(--border); box-shadow: 0 6px 16px rgba(15,23,42,.05); line-height: 1.7; }
.profile-message.user .profile-message-bubble { background: var(--gradient); color: #fff; border-color: transparent; max-width: 70%; }
.profile-message-bubble p { white-space: pre-wrap; word-break: break-word; }
.profile-message-bubble small { display:block; margin-top:6px; opacity:.75; font-size:11px; }
.profile-quick-replies { display:flex; flex-wrap:wrap; gap: 8px; margin: 12px 0 14px; }
.quick-reply-tag { cursor:pointer; }
.profile-chat-input-bar { display:flex; gap: 12px; align-items:flex-end; margin-top: 8px; }
.profile-chat-input-bar :deep(.el-textarea) { flex: 1; }
.input-actions { display:flex; gap: 8px; align-items:center; flex-shrink:0; flex-wrap: wrap; }
.profile-summary-actions { display:flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.panel-head { display:flex; justify-content:space-between; gap: 16px; align-items:flex-start; margin-bottom: 16px; }
.profile-form-grid :deep(.el-form-item) { margin-bottom: 16px; }
.field-control { display:flex; gap: 10px; align-items:flex-start; }
.field-control :deep(.el-input), .field-control :deep(.el-textarea) { flex: 1; }
.summary-card { padding: 18px; }
.summary-head { display:flex; justify-content:space-between; gap: 10px; align-items:center; margin-bottom: 10px; }
.summary-head h3 { font-size: 16px; }
.summary-progress { margin-bottom: 12px; }
.pending-list { margin-top: 8px; font-size: 12px; color: var(--text-secondary); line-height: 1.5; }
.summary-meta { display:grid; gap: 10px; }
.summary-meta div { display:flex; justify-content:space-between; gap: 12px; align-items:center; padding: 10px 12px; background: rgba(255,255,255,.72); border:1px solid var(--border); border-radius: 12px; }
.summary-meta span { color: var(--text-secondary); font-size: 13px; }
.summary-meta strong { color: var(--text-primary); font-size: 13px; }
.radar-box { height: 240px; }
.summary-tags { display:flex; flex-wrap:wrap; gap: 8px; }
.action-list { display:flex; flex-direction:column; gap: 10px; }
.typing-bubble { display:flex; align-items:center; gap: 8px; }
.typing-dots { display:inline-flex; gap: 4px; align-items:center; }
.typing-dots i { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); animation: bounce 1.2s infinite ease-in-out; }
.typing-dots i:nth-child(2) { animation-delay: .15s; }
.typing-dots i:nth-child(3) { animation-delay: .3s; }
@keyframes bounce { 0%,80%,100%{transform:scale(.5);opacity:.5} 40%{transform:scale(1);opacity:1} }
@media (max-width: 900px) { .profile-layout { grid-template-columns: 1fr; } .profile-summary-panel { position: static; } .profile-hero-title { font-size: 28px; } .profile-message-list { height: 420px; } }
</style>
