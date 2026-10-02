<template>
  <div class="page-container chat-page">
    <PageHeader :title="PAGE_HEADERS.chat.title" :subtitle="PAGE_HEADERS.chat.subtitle" />

    <div class="chat-layout card-panel">
      <div class="chat-sidebar">
        <ProfileCard :profile="store.student_profile" />
        <div v-if="store.hasProfile" class="quick-section glass-panel">
          <h4>快捷提问</h4>
          <el-button
            v-for="q in quickQuestions"
            :key="q"
            size="small"
            round
            class="quick-btn"
            @click="sendQuick(q)"
          >{{ q }}</el-button>
        </div>
        <el-button
          v-if="store.chat_history.length"
          size="small"
          type="primary"
          plain
          class="sidebar-action"
          @click="exportChat"
        >导出对话记录</el-button>
        <el-button type="danger" plain size="small" class="sidebar-action" @click="clearChat">清空对话</el-button>
      </div>

      <div class="chat-main">
        <div ref="messagesRef" class="messages-area">
          <ChatBubble v-for="(msg, i) in displayMessages" :key="i" :role="msg.role" :content="msg.content" :time="msg.time" />
          <div v-if="loading" class="thinking-box glass-panel">
            <div class="thinking-avatar"><el-icon :size="20"><Cpu /></el-icon></div>
            <div>
              <p class="thinking-title">AI 正在分析中…</p>
              <p class="thinking-text">{{ thinkingText }}</p>
              <div class="thinking-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>

        <div class="input-area glass-panel">
          <input
            ref="fileInputRef"
            class="hidden-file-input"
            type="file"
            accept=".pdf,.pptx,.docx,.txt,.png,.jpg,.jpeg,.webp,.bmp"
            @change="onFileChange"
          />
          <div class="composer-row">
            <el-tooltip content="上传图片或知识库文件" placement="top">
              <el-button class="attach-btn" :disabled="loading" @click="openFilePicker">
                <el-icon :size="18"><Upload /></el-icon>
              </el-button>
            </el-tooltip>
            <div class="composer-main">
              <div v-if="attachedFile" class="attachment-chip">
                <el-icon :size="16"><Picture v-if="isAttachedImage" /><Document v-else /></el-icon>
                <span class="attachment-name">{{ attachedFile.name }}</span>
                <span class="attachment-meta">{{ attachmentModeText }}</span>
                <el-button text class="remove-attachment" :disabled="loading" @click="clearAttachment">
                  <el-icon :size="14"><Close /></el-icon>
                </el-button>
              </div>
              <el-input
                :model-value="inputText"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 5 }"
                :placeholder="inputPlaceholder"
                :disabled="loading"
                resize="none"
                @update:model-value="handleManualInput"
                @keydown.ctrl.enter="sendMessage"
              />
            </div>
            <SpeechInputButton
              :text="true"
              :disabled="loading"
              :model-value="inputText"
              @start="handleChatSpeechStart"
              @interim="handleChatSpeechInterim"
              @result="handleChatSpeechResult"
              @stop="handleChatSpeechStop"
              @error="handleChatSpeechError"
            />
            <el-button type="primary" class="gradient-btn send-btn" :loading="loading" @click="sendMessage">
              <el-icon :size="16"><Promotion /></el-icon>
              <span>发送</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { useStudentStore } from '@/store/student'
import { chat, uploadChatAttachment } from '@/api/index'
import { DEMO_CHAT_MESSAGES } from '@/demo/demoContent'
import { downloadTextFile, formatDateFilename } from '@/utils/download'
import ChatBubble from '@/components/ChatBubble.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import PageHeader from '@/components/PageHeader.vue'
import SpeechInputButton from '@/components/SpeechInputButton.vue'
import { PAGE_HEADERS } from '@/constants/brand'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { useSpeechInputField } from '@/composables/useSpeechInputField'

const store = useStudentStore()
const inputText = ref('')
const loading = ref(false)
const thinkingText = ref('正在分析学习画像...')
const messagesRef = ref(null)
const fileInputRef = ref(null)
const attachedFile = ref(null)
let thinkingTimer = null
const speech = useSpeechInput()
const speechField = useSpeechInputField(speech, { getValue: () => inputText.value, setValue: (val) => { inputText.value = val } })

const quickQuestions = [
  'LZW算法是什么？简单解释一下',
  'JPEG压缩的基本流程是什么？',
  '霍夫曼编码怎么理解？',
  '帮我总结一下多媒体信息处理的重点',
  '颜色直方图有什么作用？'
]

const welcomeMessage = computed(() => {
  const weak = (store.student_profile.weak_points || []).join('\n')
  return `你好，我已经根据你的学习画像完成分析。\n\n当前薄弱知识点：\n${weak || '暂无'}\n\n你可以随时向我提问，我会结合你的基础水平和学习风格个性化回答。`
})

const noProfileHint = '请先构建学习画像，以获得个性化辅导'
const imageSuffixes = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']

const isAttachedImage = computed(() => {
  if (!attachedFile.value) return false
  const name = attachedFile.value.name.toLowerCase()
  return imageSuffixes.some(suffix => name.endsWith(suffix))
})

const attachmentModeText = computed(() => {
  if (!attachedFile.value) return ''
  return isAttachedImage.value ? '图片识别' : '加入知识库'
})

const inputPlaceholder = computed(() => {
  if (!attachedFile.value) return '输入你的学习问题，按 Ctrl+Enter 发送...'
  return isAttachedImage.value
    ? '可以补充你想问图片里的哪一处...'
    : '可以补充你想基于该文件检索的问题...'
})

const displayMessages = computed(() => {
  if (store.chat_history.length) return store.chat_history
  if (!store.hasProfile) {
    return [{ role: 'assistant', content: noProfileHint, time: Date.now() }]
  }
  if (store.demo_mode) return DEMO_CHAT_MESSAGES
  return [{ role: 'assistant', content: welcomeMessage.value, time: Date.now() }]
})

function scrollToBottom() {
  nextTick(() => {
    requestAnimationFrame(() => {
      const el = messagesRef.value
      if (el) el.scrollTop = el.scrollHeight
    })
  })
}

function startThinkingAnimation() {
  const steps = ['正在分析学习画像...', '正在检索知识库...', '正在生成个性化回答...']
  let i = 0
  thinkingText.value = steps[0]
  thinkingTimer = setInterval(() => {
    i = (i + 1) % steps.length
    thinkingText.value = steps[i]
  }, 2500)
}

function stopThinkingAnimation() {
  if (thinkingTimer) { clearInterval(thinkingTimer); thinkingTimer = null }
}

function openFilePicker() {
  if (loading.value) return
  fileInputRef.value?.click()
}

function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning('请上传 20MB 以内的文件')
    return
  }
  attachedFile.value = file
  ElMessage.success(isAttachedImage.value ? '图片已选择，发送后将识别内容' : '文件已选择，发送后将加入知识库检索')
}

function clearAttachment() {
  attachedFile.value = null
}

function buildUserMessage(text, file) {
  if (!file) return text
  const mode = isAttachedImage.value ? '图片' : '文件'
  const question = text || (isAttachedImage.value ? '请识别这张图片并讲解' : '请基于这个文件进行学习辅导')
  return `上传${mode}：${file.name}\n\n${question}`
}

function formatTrustLabel(data) {
  const level = data?.trust_level
  if (level === 'high') return '【知识库可信回答】'
  if (level === 'medium') return '【部分可信，建议核对课程资料】'
  if (level === 'low') return '【AI 生成，可信度较低】'
  return ''
}

function buildAssistantMessage(data, file) {
  const uploadPrefix = data.mode === 'file_rag'
    ? `已将「${data.attachment?.name || file?.name || '文件'}」加入知识库并完成检索。\n\n`
    : ''
  const trustLabel = formatTrustLabel(data)
  const trustPrefix = trustLabel ? `${trustLabel}\n\n` : ''
  return `${uploadPrefix}${trustPrefix}${data.answer || '暂无回答'}`
}

function handleChatSpeechStart() {
  speechField.handleSpeechStart(inputText.value)
}

function handleChatSpeechInterim(text) {
  speechField.handleSpeechInterim(text)
}

function handleChatSpeechResult(text) {
  speechField.handleSpeechResult(text)
}

function handleChatSpeechStop() {
  speechField.handleSpeechStop()
}

function handleChatSpeechError(message) {
  speechField.handleSpeechError(message)
  if (message) ElMessage.warning(message)
}

function cancelChatSpeech() {
  speechField.cancelSpeech()
}

function handleManualInput(value) {
  inputText.value = value
  speechField.handleManualInput(value)
}

async function sendMessage() {
  const text = inputText.value.trim()
  const file = attachedFile.value
  if ((!text && !file) || loading.value) return

  cancelChatSpeech()

  if (!store.chat_history.length) store.clearChatHistory()

  const rawQuestion = text
  store.addChatMessage('user', buildUserMessage(rawQuestion, file))
  inputText.value = ''
  attachedFile.value = null
  speechField.resetSpeechState()
  scrollToBottom()

  loading.value = true
  startThinkingAnimation()
  try {
    const data = file
      ? await uploadChatAttachment(file, text, store.student_profile)
      : await chat(text, store.student_profile)
    store.addChatMessage('assistant', buildAssistantMessage(data, file))
  } catch (err) {
    store.addChatMessage('assistant', `请求未成功：${err.message || '无法连接后端服务，请确认后端已启动'}`)
  } finally {
    stopThinkingAnimation()
    loading.value = false
    scrollToBottom()
  }
}

function sendQuick(q) { handleManualInput(q); sendMessage() }
function clearChat() { cancelChatSpeech(); store.clearChatHistory() }

function exportChat() {
  if (!store.chat_history.length) return
  const lines = ['# 智能辅导对话记录', '']
  for (const msg of store.chat_history) {
    const role = msg.role === 'user' ? '学生' : 'AI 辅导助手'
    lines.push(`## ${role}`, '', msg.content || '', '')
  }
  downloadTextFile(lines.join('\n'), formatDateFilename('对话记录', 'md'))
  ElMessage.success('对话记录已开始下载，请在浏览器下载记录中查看')
}


watch(() => store.demo_mode, () => nextTick(scrollToBottom))
watch(displayMessages, () => nextTick(scrollToBottom), { deep: true })

onMounted(scrollToBottom)
onBeforeUnmount(() => { cancelChatSpeech(); stopThinkingAnimation() })
</script>

<style scoped>
.chat-page .page-title {
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.chat-layout {
  display: flex;
  height: calc(100vh - 180px);
  min-height: 600px;
  padding: 0;
  overflow: hidden;
}

.chat-sidebar {
  width: 280px;
  padding: 20px;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  flex-shrink: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f3f6ff 100%);
}

.quick-section {
  padding: 14px;
  margin-top: 16px;
}

.quick-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.quick-btn {
  display: block;
  width: 100%;
  margin-bottom: 6px !important;
  margin-left: 0 !important;
  text-align: left;
  white-space: normal;
  height: auto;
  padding: 8px 12px;
  background: var(--gradient-soft);
  border-color: var(--border-soft);
  color: var(--primary-dark);
}

.quick-btn:hover {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.25);
  color: var(--primary-dark);
}

.sidebar-action {
  width: 100%;
  margin-top: 10px;
  margin-left: 0 !important;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.88), rgba(241, 245, 249, 0.96));
}

.messages-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 28px 28px 18px;
}

.thinking-box {
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  margin-bottom: 16px;
  max-width: 400px;
}

.thinking-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--gradient);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.thinking-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.thinking-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.thinking-dots {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(2) { animation-delay: 0.16s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.32s; }

.input-area {
  padding: 14px;
  margin: 12px 16px 16px;
  border-radius: 14px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
}

.hidden-file-input { display: none; }

.composer-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto auto;
  align-items: end;
  gap: 12px;
}

.attach-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 10px;
  color: var(--primary);
  border-color: rgba(99, 102, 241, 0.22);
  background: rgba(99, 102, 241, 0.06);
}

.attach-btn:hover {
  color: #fff;
  background: var(--gradient);
  border-color: transparent;
}

.composer-main { min-width: 0; }

.composer-main :deep(.el-textarea__inner) {
  min-height: 62px !important;
  border-radius: 10px;
  box-shadow: none;
  border-color: rgba(99, 102, 241, 0.28);
  line-height: 1.6;
  padding: 11px 13px;
}

.composer-main :deep(.el-textarea__inner:focus) {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.attachment-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  max-width: 100%;
  margin-bottom: 8px;
  padding: 7px 8px 7px 10px;
  border-radius: 10px;
  color: var(--primary-dark);
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.18);
  font-size: 12px;
}

.attachment-name {
  max-width: min(360px, 46vw);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.attachment-meta {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.remove-attachment {
  width: 22px;
  height: 22px;
  padding: 0;
  color: var(--text-secondary);
}

.send-btn {
  height: 44px;
  min-width: 92px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 980px) {
  .chat-layout { height: auto; min-height: 0; flex-direction: column; }
  .chat-sidebar { width: 100%; border-right: 0; border-bottom: 1px solid var(--border); }
  .chat-main { min-height: 620px; }
}

@media (max-width: 640px) {
  .composer-row { grid-template-columns: 42px minmax(0, 1fr); }
  .send-btn { grid-column: 1 / -1; width: 100%; }
  .messages-area { padding: 18px 14px; }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
