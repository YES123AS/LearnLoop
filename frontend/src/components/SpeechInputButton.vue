<template>
  <el-tooltip :content="tooltipText" placement="top">
    <el-button
      class="speech-btn"
      :size="size"
      :disabled="buttonDisabled"
      :loading="isListening"
      :type="isListening ? 'danger' : 'primary'"
      plain
      @click="toggleListening"
    >
      <el-icon :size="iconSize" class="speech-icon"><Microphone /></el-icon>
      <span v-if="text" class="speech-text">{{ isListening ? '识别中' : '语音输入' }}</span>
      <span v-if="isListening && previewText" class="speech-preview">：{{ previewText }}</span>
      <span v-if="isListening" class="speech-dot"></span>
    </el-button>
  </el-tooltip>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone } from '@element-plus/icons-vue'
import { useSpeechInput } from '@/composables/useSpeechInput'

const props = defineProps({
  modelValue: { type: String, default: '' },
  append: { type: Boolean, default: true },
  language: { type: String, default: 'zh-CN' },
  size: { type: String, default: 'default' },
  text: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['start', 'result', 'interim', 'stop', 'error'])
const speech = useSpeechInput(props.language)
const iconSize = computed(() => (props.size === 'small' ? 14 : 16))
const buttonDisabled = computed(() => props.disabled || !speech.isSupported.value)
const previewText = ref('')
const hasEmittedFinal = ref(false)

const tooltipText = computed(() => {
  if (!speech.isSupported.value) return '当前浏览器暂不支持语音识别，请使用最新版 Chrome 或 Edge。'
  if (!speech.env.isSecureSpeechContext) return '当前通过局域网 IP 访问，浏览器可能禁止麦克风。请使用 localhost、127.0.0.1 或 HTTPS。'
  return speech.isListening.value ? '正在实时转写，点击可停止' : '点击开始语音输入（请允许麦克风权限）'
})

async function toggleListening() {
  if (!speech.isSupported.value) { const msg = '当前浏览器暂不支持语音识别，请使用最新版 Chrome 或 Edge。'; emit('error', msg); ElMessage.warning(msg); return }
  if (!speech.env.isSecureSpeechContext) { const msg = '当前通过局域网 IP 访问，浏览器可能禁止麦克风。请使用 localhost、127.0.0.1 或 HTTPS。'; emit('error', msg); ElMessage.warning(msg); return }
  if (speech.isListening.value) {
    speech.stopListening()
    emit('stop')
    previewText.value = ''
    return
  }
  previewText.value = ''
  hasEmittedFinal.value = false
  ElMessage.info('正在请求麦克风权限，请在浏览器弹窗中允许访问')
  const started = await speech.startListening()
  if (started) emit('start')
  if (!started && speech.error.value) { emit('error', speech.error.value); ElMessage.warning(speech.error.value) }
}

watch(() => speech.interimTranscript.value, (val) => { previewText.value = val; emit('interim', val) })
watch(() => speech.finalTranscript.value, (val) => {
  if (!val || hasEmittedFinal.value) return
  const sessionId = typeof speech.getSessionId === 'function' ? speech.getSessionId() : 0
  if (!sessionId || (typeof speech.hasFinalCommitted === 'function' && speech.hasFinalCommitted(sessionId))) return
  if (!speech.isListening.value) return
  const committed = typeof speech.consumeFinalTranscript === 'function' ? speech.consumeFinalTranscript() : ''
  if (committed && !hasEmittedFinal.value) {
    hasEmittedFinal.value = true
    emit('result', committed)
  }
})
watch(() => speech.error.value, (val) => { if (val) emit('error', val) })
watch(() => props.language, (lang) => speech.setLanguage(lang), { immediate: true })
onBeforeUnmount(() => speech.cancelSpeech(true))
</script>

<style scoped>
.speech-btn {
  position: relative;
  min-width: 92px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.speech-btn:hover {
  transform: translateY(-1px);
}

.speech-icon {
  flex-shrink: 0;
}

.speech-text {
  white-space: nowrap;
}

.speech-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.35); }
  70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
</style>
