import axios from 'axios'
import { ElMessage } from 'element-plus'
import { logAndNormalizeError } from '@/utils/errorMessage'

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/** 与后端 Pydantic 模型字段对齐 */
export function normalizeProfile(profile = {}) {
  return {
    grade: profile.grade || '',
    major: profile.major || '',
    course: profile.course || '',
    level: profile.level || '',
    goal: profile.goal || '',
    learning_style: profile.learning_style || '',
    weak_points: Array.isArray(profile.weak_points) ? [...profile.weak_points] : []
  }
}

/** 学情分析接口要求的 records 格式 */
export function normalizeRecords(records = []) {
  return records.map((r) => ({
    knowledge_point: r.knowledge_point || '未知知识点',
    question_type: r.question_type || '未知题型',
    correct: Boolean(r.correct)
  }))
}

async function request(fn) {
  try {
    const response = await fn()
    const data = response?.data
    if (!data || typeof data !== 'object') {
      throw new Error('接口返回格式异常')
    }
    if (data.success === false) {
      throw new Error(data.message || '接口返回失败')
    }
    return data.data ?? {}
  } catch (error) {
    const message = logAndNormalizeError(error, 'api')
    ElMessage.error(message)
    throw new Error(message)
  }
}

export async function checkBackendHealth() {
  try {
    const res = await api.get('/health', { timeout: 5000 })
    return res.data?.success === true
  } catch {
    return false
  }
}

export function chat(question, studentProfile) {
  return request(() =>
    api.post('/ai/chat', {
      question,
      student_profile: normalizeProfile(studentProfile)
    })
  )
}

export function uploadChatAttachment(file, question, studentProfile) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('question', question || '')
  formData.append('student_profile', JSON.stringify(normalizeProfile(studentProfile)))
  return request(() =>
    axios.post(`${BASE_URL}/ai/chat/upload`, formData, {
      timeout: 900000
    })
  )
}

export function generateResource(topic, resourceType, studentProfile) {
  return request(() =>
    api.post('/ai/generate_resource', {
      topic,
      resource_type: resourceType,
      student_profile: normalizeProfile(studentProfile)
    }, { timeout: 600000 })
  )
}

export function generateQuiz(topic, questionTypes, count, difficulty, studentProfile) {
  return request(() =>
    api.post('/ai/generate_quiz', {
      topic,
      question_types: questionTypes,
      count,
      difficulty,
      student_profile: normalizeProfile(studentProfile)
    })
  )
}

export function generatePath(goal, days, studentProfile) {
  return request(() =>
    api.post('/ai/generate_path', {
      goal,
      days,
      student_profile: normalizeProfile(studentProfile)
    })
  )
}

export function analyzeStatus(records, studentProfile) {
  return request(() =>
    api.post('/ai/analyze_status', {
      records: normalizeRecords(records),
      student_profile: normalizeProfile(studentProfile)
    })
  )
}

export function recommendNext(studentProfile, weakPoints, masteredPoints) {
  return request(() =>
    api.post('/ai/recommend_next', {
      student_profile: normalizeProfile(studentProfile),
      weak_points: weakPoints ?? normalizeProfile(studentProfile).weak_points,
      mastered_points: masteredPoints ?? []
    })
  )
}

/** 启动或恢复 LangGraph 多 Agent 学习闭环 */
export function runLearningLoop(userInput, studentProfile, extraData = {}, studentId = null) {
  return request(() =>
    api.post('/ai/multi_agent_learning_loop', {
      user_input: userInput,
      student_profile: normalizeProfile(studentProfile),
      student_id: studentId,
      extra_data: extraData
    }, { timeout: 900000 })
  )
}

export function getKnowledgeBaseStatus() {
  return request(() => api.get('/ai/knowledge_base/status'))
}

export function uploadKnowledgeBaseFiles(files) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  return request(() =>
    axios.post(`${BASE_URL}/ai/knowledge_base/upload`, formData, {
      timeout: 900000
    })
  )
}

export function rebuildKnowledgeBase() {
  return request(() => api.post('/ai/knowledge_base/rebuild', {}, { timeout: 900000 }))
}

async function requestSilent(fn) {
  try {
    const response = await fn()
    const data = response?.data
    if (!data || typeof data !== 'object') {
      throw new Error('接口返回格式异常')
    }
    if (data.success === false) {
      throw new Error(data.message || '接口返回失败')
    }
    return data.data ?? {}
  } catch (error) {
    const message = logAndNormalizeError(error, 'api/silent')
    throw new Error(message)
  }
}

/** 答错后生成错因诊断并写入错题本 */
export function diagnoseMistake(payload, options = {}) {
  const run = options.silent ? requestSilent : request
  return run(() =>
    api.post('/ai/mistake/diagnose', {
      student_id: payload.student_id,
      question: payload.question,
      user_answer: payload.user_answer,
      difficulty: payload.difficulty || '简单',
      judge_reason: payload.judge_reason || '与标准答案不一致',
      student_profile: normalizeProfile(payload.student_profile || {})
    }, { timeout: 600000 })
  )
}

/** 获取学生错题本，status 可选：未修复 / 已修复 */
export function getMistakeBook(studentId, status, options = {}) {
  const params = status ? { status } : undefined
  const run = options.silent ? requestSilent : request
  return run(() => api.get(`/ai/mistake_book/${encodeURIComponent(studentId)}`, { params }))
}

/** 获取单道错题详情 */
export function getMistakeDetail(mistakeId) {
  return request(() => api.get(`/ai/mistake/${encodeURIComponent(mistakeId)}`))
}

/** 提交变式题答案并更新修复状态 */
export function retryMistake(payload) {
  return request(() =>
    api.post('/ai/mistake/retry', {
      mistake_id: payload.mistake_id,
      variant_index: payload.variant_index ?? 1,
      user_answer: payload.user_answer
    })
  )
}

export default api
