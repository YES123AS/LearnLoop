import { computed, onBeforeUnmount, ref } from 'vue'

function getSpeechEnvironment() {
  if (typeof window === 'undefined') {
    return {
      hostname: '',
      protocol: '',
      isLocalhost: false,
      isHttps: false,
      isSecureSpeechContext: false,
      hasSpeechRecognition: false,
      hasWebkitSpeechRecognition: false,
      hasMediaDevices: false,
      SpeechRecognitionCtor: null
    }
  }

  const hostname = window.location.hostname
  const protocol = window.location.protocol
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1'
  const isHttps = protocol === 'https:'
  const isSecureSpeechContext = Boolean(window.isSecureContext || isLocalhost || isHttps)
  const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition || null

  return {
    hostname,
    protocol,
    isLocalhost,
    isHttps,
    isSecureSpeechContext,
    hasSpeechRecognition: Boolean(window.SpeechRecognition),
    hasWebkitSpeechRecognition: Boolean(window.webkitSpeechRecognition),
    hasMediaDevices: Boolean(navigator.mediaDevices?.getUserMedia),
    SpeechRecognitionCtor
  }
}

function normalizeSpeechText(text = '') {
  return String(text)
    .replace(/\s+/g, ' ')
    .replace(/\s*([，。！？；：,.!?;:])\s*/g, '$1')
    .trim()
}

function mapSpeechError(errorCode, hasRecognitionSupport) {
  if (!hasRecognitionSupport) return '当前浏览器暂不支持语音识别，请使用最新版 Chrome 或 Edge。'
  switch (errorCode) {
    case 'not-allowed':
    case 'permission-denied':
      return '麦克风权限被拒绝，请点击地址栏左侧权限图标，在网站设置中允许麦克风。'
    case 'not-found':
      return '未检测到可用麦克风，请检查设备连接。'
    case 'audio-capture':
      return '麦克风可能被其他应用占用，请关闭占用麦克风的软件后重试。'
    case 'network':
      return '语音识别服务连接失败，请检查网络，或稍后重试。'
    case 'service-not-allowed':
      return '当前浏览器可以使用麦克风，但不支持浏览器语音转文字能力。请使用 Chrome 或 Edge，或后续接入后端语音识别服务。'
    default:
      return '语音识别失败，请稍后重试。'
  }
}

export function useSpeechInput(initialLanguage = 'zh-CN') {
  const env = getSpeechEnvironment()
  const isSupported = computed(() => Boolean(env.SpeechRecognitionCtor))
  const isListening = ref(false)
  const interimTranscript = ref('')
  const finalTranscript = ref('')
  const error = ref('')
  const language = ref(initialLanguage)

  let recognition = null
  let sessionCounter = 0
  let activeSessionId = 0
  let finalCommittedSessionId = 0
  let cancelledSessionId = 0
  let pendingFinalText = ''

  if (import.meta.env.DEV) {
    console.log('[SpeechInput][env]', {
      hostname: env.hostname,
      protocol: env.protocol,
      isSecureContext: typeof window !== 'undefined' ? window.isSecureContext : false,
      isLocalhost: env.isLocalhost,
      isHttps: env.isHttps,
      isSecureSpeechContext: env.isSecureSpeechContext,
      hasSpeechRecognition: env.hasSpeechRecognition,
      hasWebkitSpeechRecognition: env.hasWebkitSpeechRecognition,
      hasMediaDevices: env.hasMediaDevices,
      buttonDisabledReason: env.SpeechRecognitionCtor ? '' : 'browser-no-speech-recognition'
    })
  }

  function isSessionActive(sessionId) {
    return sessionId > 0 && sessionId === activeSessionId && sessionId !== cancelledSessionId
  }

  function clearSpeechState() {
    interimTranscript.value = ''
    finalTranscript.value = ''
    error.value = ''
    pendingFinalText = ''
  }

  function teardownRecognition() {
    if (!recognition) return
    recognition.onstart = null
    recognition.onresult = null
    recognition.onerror = null
    recognition.onend = null
    recognition = null
  }

  function createRecognition(sessionId) {
    if (!env.SpeechRecognitionCtor) return null
    const inst = new env.SpeechRecognitionCtor()
    inst.lang = language.value
    inst.continuous = false
    inst.interimResults = true
    inst.maxAlternatives = 1

    inst.onstart = () => {
      if (!isSessionActive(sessionId)) {
        try { inst.stop?.() } catch {}
        return
      }
      isListening.value = true
      error.value = ''
      pendingFinalText = ''
      clearSpeechState()
    }

    inst.onresult = (event) => {
      if (!isSessionActive(sessionId)) return
      let currentInterim = ''
      let currentFinal = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const text = normalizeSpeechText(result[0]?.transcript || '')
        if (!text) continue
        if (import.meta.env.DEV) console.log('[speech result]', { sessionId, isFinal: result.isFinal, text })
        if (result.isFinal) currentFinal += (currentFinal ? ' ' : '') + text
        else currentInterim += (currentInterim ? ' ' : '') + text
      }
      if (currentInterim) interimTranscript.value = normalizeSpeechText(currentInterim)
      if (currentFinal) {
        pendingFinalText = normalizeSpeechText([pendingFinalText, currentFinal].filter(Boolean).join(' '))
        finalTranscript.value = pendingFinalText
      }
    }

    inst.onerror = (event) => {
      if (!isSessionActive(sessionId)) return
      error.value = mapSpeechError(event?.error, true)
      isListening.value = false
    }

    inst.onend = () => {
      if (sessionId === activeSessionId) isListening.value = false
      teardownRecognition()
    }

    return inst
  }

  function commitFinalTranscript(sessionId) {
    if (!isSessionActive(sessionId)) return ''
    if (finalCommittedSessionId === sessionId) return ''
    const text = normalizeSpeechText(finalTranscript.value || pendingFinalText || interimTranscript.value)
    if (!text) return ''
    finalCommittedSessionId = sessionId
    return text
  }

  async function startListening() {
    if (!env.SpeechRecognitionCtor) {
      error.value = '当前浏览器暂不支持语音识别，请使用最新版 Chrome 或 Edge。'
      return false
    }
    if (!env.isSecureSpeechContext) {
      error.value = '当前通过局域网 IP 访问，浏览器可能禁止麦克风。请使用 localhost、127.0.0.1 或 HTTPS。'
      return false
    }
    if (!env.hasMediaDevices) {
      error.value = '当前浏览器暂不支持麦克风访问，请使用最新版 Chrome 或 Edge。'
      return false
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())

      cancelSpeech(true)
      const sessionId = ++sessionCounter
      activeSessionId = sessionId
      cancelledSessionId = 0
      finalCommittedSessionId = 0
      clearSpeechState()
      isListening.value = false
      recognition = createRecognition(sessionId)
      if (!recognition) return false
      recognition.lang = language.value
      recognition.start()
      return true
    } catch (e) {
      const name = e?.name || e?.error
      error.value = mapSpeechError(name, Boolean(env.SpeechRecognitionCtor))
      isListening.value = false
      return false
    }
  }

  function stopListening() {
    const currentSessionId = activeSessionId
    try {
      recognition?.stop?.()
    } catch {
      try { recognition?.abort?.() } catch {}
    }
    if (currentSessionId && finalCommittedSessionId !== currentSessionId) {
      finalCommittedSessionId = currentSessionId
    }
    isListening.value = false
  }

  function cancelSpeech(silent = false) {
    cancelledSessionId = activeSessionId || (sessionCounter + 1)
    activeSessionId = 0
    finalCommittedSessionId = 0
    pendingFinalText = ''
    clearSpeechState()
    try {
      recognition?.abort?.()
    } catch {
      try { recognition?.stop?.() } catch {}
    }
    if (!silent) isListening.value = false
    else isListening.value = false
    teardownRecognition()
  }

  function resetTranscript() {
    clearSpeechState()
  }

  function setLanguage(nextLanguage) {
    language.value = nextLanguage || 'zh-CN'
    if (recognition) recognition.lang = language.value
  }

  function consumeFinalTranscript() {
    return commitFinalTranscript(activeSessionId)
  }

  onBeforeUnmount(() => {
    cancelSpeech(true)
  })

  function getSessionId() {
    return activeSessionId
  }

  function hasFinalCommitted(sessionId = activeSessionId) {
    return finalCommittedSessionId === sessionId && sessionId > 0
  }

  return {
    isSupported,
    isListening,
    interimTranscript,
    finalTranscript,
    error,
    startListening,
    stopListening,
    cancelSpeech,
    resetTranscript,
    setLanguage,
    consumeFinalTranscript,
    getSessionId,
    hasFinalCommitted,
    env
  }
}
