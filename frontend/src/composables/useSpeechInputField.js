import { ref } from 'vue'

function normalizeSpeechText(text = '') {
  return String(text || '').replace(/\s+/g, ' ').trim()
}

export function useSpeechInputField(speech, options = {}) {
  const currentText = ref('')
  const speechBaseText = ref('')
  const speechLiveText = ref('')
  const speechFinalText = ref('')
  const lastSpeechFinalText = ref('')
  const isSpeechActive = ref(false)
  const speechError = ref('')
  const activeSessionId = ref(0)

  const mode = options.mode || 'replace'
  const getValue = typeof options.getValue === 'function' ? options.getValue : () => currentText.value
  const setValue = typeof options.setValue === 'function' ? options.setValue : (val) => { currentText.value = val }

  function mergeSpeechText(base, speechText) {
    const cleanBase = normalizeSpeechText(base)
    const cleanSpeech = normalizeSpeechText(speechText)
    if (!cleanSpeech) return cleanBase
    if (!cleanBase) return cleanSpeech
    return `${cleanBase} ${cleanSpeech}`
  }

  function syncText(value) {
    setValue(value)
    currentText.value = value
  }

  function isSessionValid(sessionId) {
    if (!sessionId) return false
    return activeSessionId.value === sessionId
  }

  function cancelSpeech() {
    if (speech?.cancelSpeech) speech.cancelSpeech(true)
    speechBaseText.value = ''
    speechLiveText.value = ''
    speechFinalText.value = ''
    lastSpeechFinalText.value = ''
    isSpeechActive.value = false
    speechError.value = ''
    activeSessionId.value += 1
  }

  function resetSpeechState() {
    if (speech?.resetTranscript) speech.resetTranscript()
    speechBaseText.value = ''
    speechLiveText.value = ''
    speechFinalText.value = ''
    lastSpeechFinalText.value = ''
    isSpeechActive.value = false
    speechError.value = ''
    activeSessionId.value = 0
  }

  function handleSpeechStart(currentText) {
    const text = normalizeSpeechText(currentText ?? getValue())
    speechBaseText.value = text
    speechLiveText.value = ''
    speechFinalText.value = ''
    lastSpeechFinalText.value = ''
    speechError.value = ''
    isSpeechActive.value = true
    activeSessionId.value += 1
  }

  function handleSpeechInterim(text) {
    if (!isSpeechActive.value) return
    const sessionId = activeSessionId.value
    if (!isSessionValid(sessionId)) return
    speechLiveText.value = normalizeSpeechText(text)
    syncText(mergeSpeechText(speechBaseText.value, speechLiveText.value))
  }

  function handleSpeechResult(text) {
    const sessionId = activeSessionId.value
    const finalText = normalizeSpeechText(text)
    if (!finalText) {
      handleSpeechStop()
      return
    }
    if (!isSessionValid(sessionId)) return
    if (lastSpeechFinalText.value === finalText) return
    speechFinalText.value = finalText
    lastSpeechFinalText.value = finalText
    syncText(mergeSpeechText(speechBaseText.value, finalText))
    speechBaseText.value = ''
    speechLiveText.value = ''
    isSpeechActive.value = false
    if (speech?.resetTranscript) speech.resetTranscript()
  }

  function handleSpeechStop() {
    speechBaseText.value = ''
    speechLiveText.value = ''
    speechFinalText.value = ''
    isSpeechActive.value = false
    activeSessionId.value = 0
  }

  function handleSpeechError(message) {
    speechError.value = message || ''
  }

  function handleManualInput(value) {
    syncText(value)
    if (isSpeechActive.value) cancelSpeech()
  }

  function bindInput(value) {
    syncText(value)
  }

  return {
    currentText,
    speechBaseText,
    speechLiveText,
    speechFinalText,
    lastSpeechFinalText,
    isSpeechActive,
    speechError,
    mergeSpeechText,
    handleSpeechStart,
    handleSpeechInterim,
    handleSpeechResult,
    handleSpeechStop,
    handleSpeechError,
    cancelSpeech,
    resetSpeechState,
    handleManualInput,
    bindInput,
    mode
  }
}
