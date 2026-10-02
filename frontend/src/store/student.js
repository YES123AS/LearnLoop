import { defineStore } from 'pinia'

const INIT_KEY = 'sc_initialized'
const DEMO_MODE_KEY = 'demo_mode'

/** 项目使用的 canonical keys（Pinia 持久化） */
const CANONICAL_KEYS = [
  'sc_student_profile',
  'sc_records',
  'sc_chat_history',
  'sc_analysis_result',
  'sc_weak_points',
  'sc_mastered_points',
  'sc_recommendation',
  INIT_KEY
]

/** 历史/遗留 localStorage keys，关闭演示模式时一并清理 */
const LEGACY_KEYS = [
  'student_profile',
  'studentProfile',
  'records',
  'weak_points',
  'mastered_points',
  'chat_history',
  'analysis_result',
  'recommendation',
  'learning_path',
  'current_resource',
  'current_quiz'
]

const ALL_STORAGE_KEYS = [...CANONICAL_KEYS, ...LEGACY_KEYS, DEMO_MODE_KEY]

const DEFAULT_PROFILE = {
  grade: '大二',
  major: '智能科学与技术',
  course: '多媒体信息处理',
  level: '基础较弱',
  goal: '期末复习',
  weak_points: ['LZW算法', 'JPEG压缩', '霍夫曼编码'],
  learning_style: '喜欢通俗解释和案例化学习'
}

const EMPTY_PROFILE = {
  grade: '',
  major: '',
  course: '',
  level: '',
  goal: '',
  weak_points: [],
  learning_style: ''
}

const DEFAULT_RECORDS = [
  { knowledge_point: 'LZW算法', question_type: '选择题', correct: false },
  { knowledge_point: 'LZW算法', question_type: '填空题', correct: true },
  { knowledge_point: 'JPEG压缩', question_type: '简答题', correct: false },
  { knowledge_point: '霍夫曼编码', question_type: '选择题', correct: false },
  { knowledge_point: '颜色直方图', question_type: '选择题', correct: true }
]

function loadJSON(key) {
  try {
    const raw = localStorage.getItem(key)
    if (raw == null) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function saveJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

function removeStorageKeys(exceptDemoMode = false) {
  for (const key of ALL_STORAGE_KEYS) {
    if (exceptDemoMode && key === DEMO_MODE_KEY) continue
    localStorage.removeItem(key)
  }
}

function isDemoProfile(profile) {
  if (!profile || typeof profile !== 'object') return false
  return (
    profile.grade === DEFAULT_PROFILE.grade &&
    profile.major === DEFAULT_PROFILE.major &&
    profile.course === DEFAULT_PROFILE.course &&
    profile.level === DEFAULT_PROFILE.level &&
    profile.goal === DEFAULT_PROFILE.goal &&
    profile.learning_style === DEFAULT_PROFILE.learning_style &&
    JSON.stringify(profile.weak_points || []) === JSON.stringify(DEFAULT_PROFILE.weak_points)
  )
}

function isDemoRecords(records) {
  if (!Array.isArray(records) || records.length !== DEFAULT_RECORDS.length) return false
  return records.every((r, i) => (
    r.knowledge_point === DEFAULT_RECORDS[i].knowledge_point &&
    r.question_type === DEFAULT_RECORDS[i].question_type &&
    Boolean(r.correct) === DEFAULT_RECORDS[i].correct
  ))
}

function isDemoWeakPoints(points) {
  return Array.isArray(points) &&
    JSON.stringify(points) === JSON.stringify(DEFAULT_PROFILE.weak_points)
}

function isEmptyProfile(profile) {
  if (!profile || typeof profile !== 'object') return true
  const p = normalizeProfile(profile, false)
  return !(
    p.grade.trim() ||
    p.major.trim() ||
    p.course.trim() ||
    p.level.trim() ||
    p.goal.trim() ||
    p.learning_style.trim() ||
    p.weak_points.length > 0
  )
}

/** 与默认演示画像高度相似（常见残留：大二 + 智能科学与技术 + 基础较弱） */
function isDemoProfileLike(profile) {
  if (!profile || typeof profile !== 'object') return false
  if (isDemoProfile(profile)) return true
  return (
    profile.grade === DEFAULT_PROFILE.grade &&
    profile.major === DEFAULT_PROFILE.major &&
    profile.level === DEFAULT_PROFILE.level
  )
}

function purgeLegacyStorageKeys() {
  for (const key of LEGACY_KEYS) {
    localStorage.removeItem(key)
  }
}

function normalizeProfile(profile, useDemoDefaults = false) {
  if (useDemoDefaults) {
    return { ...DEFAULT_PROFILE, weak_points: [...DEFAULT_PROFILE.weak_points] }
  }
  const src = profile || {}
  return {
    grade: src.grade != null ? String(src.grade) : '',
    major: src.major != null ? String(src.major) : '',
    course: src.course != null ? String(src.course) : '',
    level: src.level != null ? String(src.level) : '',
    goal: src.goal != null ? String(src.goal) : '',
    learning_style: src.learning_style != null ? String(src.learning_style) : '',
    weak_points: Array.isArray(src.weak_points) ? [...src.weak_points] : []
  }
}

function emptyState() {
  return {
    student_profile: { ...EMPTY_PROFILE },
    records: [],
    chat_history: [],
    analysis_result: null,
    weak_points: [],
    mastered_points: [],
    recommendation: '',
    current_resource: ''
  }
}

function seedDemoData() {
  saveJSON('sc_student_profile', DEFAULT_PROFILE)
  saveJSON('sc_records', DEFAULT_RECORDS)
  saveJSON('sc_chat_history', [])
  saveJSON('sc_analysis_result', null)
  saveJSON('sc_weak_points', DEFAULT_PROFILE.weak_points)
  saveJSON('sc_mastered_points', [])
  saveJSON('sc_recommendation', '')
  localStorage.setItem(INIT_KEY, '1')
}

function seedEmptyData() {
  saveJSON('sc_student_profile', EMPTY_PROFILE)
  saveJSON('sc_records', [])
  saveJSON('sc_chat_history', [])
  saveJSON('sc_analysis_result', null)
  saveJSON('sc_weak_points', [])
  saveJSON('sc_mastered_points', [])
  saveJSON('sc_recommendation', '')
  localStorage.setItem(INIT_KEY, '1')
}

function loadDemoMode() {
  try {
    const raw = localStorage.getItem(DEMO_MODE_KEY)
    if (raw === null) return false
    return raw === '1'
  } catch {
    return false
  }
}

function loadInitialState(demoMode) {
  purgeLegacyStorageKeys()

  if (demoMode) {
    if (!localStorage.getItem(INIT_KEY)) {
      seedDemoData()
    }
    const profile = normalizeProfile(loadJSON('sc_student_profile') || DEFAULT_PROFILE, true)
    const records = (loadJSON('sc_records') || DEFAULT_RECORDS).map(r => ({
      ...r,
      correct: Boolean(r.correct)
    }))
    return {
      student_profile: profile,
      records,
      chat_history: loadJSON('sc_chat_history') || [],
      analysis_result: loadJSON('sc_analysis_result'),
      weak_points: [...(profile.weak_points || [])],
      mastered_points: loadJSON('sc_mastered_points') || [],
      recommendation: loadJSON('sc_recommendation') || ''
    }
  }

  // 演示模式关闭：只读 canonical keys；检测到演示残留或空画像则彻底清空
  const profileRaw = loadJSON('sc_student_profile')
  const recordsRaw = loadJSON('sc_records') || []
  const weakPointsRaw = loadJSON('sc_weak_points')

  const shouldClear =
    isDemoProfile(profileRaw) ||
    isDemoProfileLike(profileRaw) ||
    isDemoRecords(recordsRaw) ||
    isDemoWeakPoints(weakPointsRaw) ||
    isEmptyProfile(profileRaw)

  if (shouldClear) {
    removeStorageKeys(true)
    seedEmptyData()
    return emptyState()
  }

  const profile = normalizeProfile(profileRaw, false)
  return {
    student_profile: profile,
    records: recordsRaw.map(r => ({ ...r, correct: Boolean(r.correct) })),
    chat_history: loadJSON('sc_chat_history') || [],
    analysis_result: loadJSON('sc_analysis_result'),
    weak_points: [...(profile.weak_points || [])],
    mastered_points: loadJSON('sc_mastered_points') || [],
    recommendation: loadJSON('sc_recommendation') || ''
  }
}

const initialDemoMode = loadDemoMode()
const initialState = loadInitialState(initialDemoMode)

export const useStudentStore = defineStore('student', {
  state: () => ({
    ...initialState,
    demo_mode: initialDemoMode,
    reset_version: 0,
    current_resource: ''
  }),

  getters: {
    hasProfile(state) {
      const p = state.student_profile
      return Boolean(
        (p.grade && String(p.grade).trim()) ||
        (p.major && String(p.major).trim()) ||
        (p.course && String(p.course).trim()) ||
        (p.level && String(p.level).trim()) ||
        (p.goal && String(p.goal).trim()) ||
        (p.learning_style && String(p.learning_style).trim()) ||
        (p.weak_points && p.weak_points.length > 0)
      )
    },
    profileSummary(state) {
      const p = state.student_profile
      return {
        grade: p.grade,
        course: p.course,
        level: p.level,
        goal: p.goal,
        weakCount: (p.weak_points || []).length
      }
    },
    totalQuestions(state) {
      return state.records.length
    },
    correctCount(state) {
      return state.records.filter(r => r.correct).length
    },
    accuracyRate(state) {
      if (!state.records.length) return 0
      return Math.round((state.correctCount / state.records.length) * 100)
    }
  },

  actions: {
    persistProfile() {
      saveJSON('sc_student_profile', this.student_profile)
      saveJSON('sc_weak_points', this.weak_points)
    },
    persistRecords() {
      saveJSON('sc_records', this.records)
    },
    persistChat() {
      saveJSON('sc_chat_history', this.chat_history)
    },
    persistAnalysis() {
      saveJSON('sc_analysis_result', this.analysis_result)
    },
    persistRecommendation() {
      saveJSON('sc_recommendation', this.recommendation)
    },

    updateProfile(profile) {
      this.student_profile = normalizeProfile(profile, false)
      this.weak_points = [...this.student_profile.weak_points]
      this.persistProfile()
    },

    updateProfileField(field, value) {
      this.student_profile = { ...this.student_profile, [field]: value }
      if (field === 'weak_points') {
        this.weak_points = [...value]
      }
      this.persistProfile()
    },

    addRecord(record) {
      this.records.push({
        knowledge_point: record.knowledge_point,
        question_type: record.question_type,
        correct: Boolean(record.correct)
      })
      this.persistRecords()
    },

    addRecords(records) {
      this.records.push(...records.map(r => ({
        knowledge_point: r.knowledge_point,
        question_type: r.question_type,
        correct: Boolean(r.correct)
      })))
      this.persistRecords()
    },

    clearRecords() {
      this.records = []
      this.persistRecords()
    },

    resetRecordsToDemo() {
      if (!this.demo_mode) return
      this.records = DEFAULT_RECORDS.map(r => ({ ...r }))
      this.persistRecords()
    },

    addChatMessage(role, content) {
      this.chat_history.push({ role, content, time: Date.now() })
      this.persistChat()
    },

    clearChatHistory() {
      this.chat_history = []
      this.persistChat()
    },

    setAnalysisResult(result) {
      this.analysis_result = result
      if (result?.weak_points) {
        this.weak_points = [...result.weak_points]
        this.student_profile = normalizeProfile({
          ...this.student_profile,
          weak_points: [...result.weak_points]
        }, false)
        this.persistProfile()
      }
      if (result?.mastered_points) {
        this.mastered_points = [...result.mastered_points]
        saveJSON('sc_mastered_points', this.mastered_points)
      }
      this.persistAnalysis()
    },

    setRecommendation(text) {
      this.recommendation = text || ''
      this.persistRecommendation()
    },

    setCurrentResource(content) {
      this.current_resource = content || ''
    },

    resetProfileToDemo() {
      if (!this.demo_mode) return
      this.updateProfile({ ...DEFAULT_PROFILE })
    },

    /** 彻底清空用户数据：Pinia 状态 + 全部 localStorage（保留 demo_mode 开关状态） */
    clearAllUserData() {
      const demoMode = this.demo_mode
      removeStorageKeys(true)

      Object.assign(this, emptyState())
      this.demo_mode = demoMode

      seedEmptyData()
      localStorage.setItem(DEMO_MODE_KEY, demoMode ? '1' : '0')
      this.reset_version++
    },

    setDemoMode(enabled) {
      const next = Boolean(enabled)
      this.demo_mode = next
      localStorage.setItem(DEMO_MODE_KEY, next ? '1' : '0')
      if (next) {
        this.resetAllDemoData()
      } else {
        this.clearAllUserData()
      }
    },

    resetAllDemoData() {
      removeStorageKeys(true)

      this.student_profile = normalizeProfile({ ...DEFAULT_PROFILE }, true)
      this.records = DEFAULT_RECORDS.map(r => ({ ...r }))
      this.chat_history = []
      this.analysis_result = null
      this.weak_points = [...DEFAULT_PROFILE.weak_points]
      this.mastered_points = []
      this.recommendation = ''
      this.demo_mode = true

      seedDemoData()
      localStorage.setItem(DEMO_MODE_KEY, '1')
      this.reset_version++
    }
  }
})
