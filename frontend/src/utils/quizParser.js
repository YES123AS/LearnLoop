const STANDARD_TYPES = ['选择题', '填空题', '简答题']

/** 去掉 Markdown 代码块包裹 */
function stripCodeFence(text) {
  if (typeof text !== 'string') return ''
  return text
    .replace(/```(?:json)?\s*/gi, '')
    .replace(/```/g, '')
    .trim()
}

/** 尝试 JSON.parse，失败则截取 { } 或 [ ] 再 parse */
function tryParseJson(text) {
  if (typeof text !== 'string' || !text.trim()) return null

  const cleaned = stripCodeFence(text)

  const attempts = [
    cleaned,
    extractJsonObject(cleaned),
    extractJsonArray(cleaned)
  ].filter(Boolean)

  for (const candidate of attempts) {
    try {
      return JSON.parse(candidate)
    } catch {
      /* 继续尝试 */
    }
  }
  return null
}

function extractJsonObject(text) {
  const start = text.indexOf('{')
  const end = text.lastIndexOf('}')
  if (start >= 0 && end > start) return text.slice(start, end + 1)
  return null
}

function extractJsonArray(text) {
  const start = text.indexOf('[')
  const end = text.lastIndexOf(']')
  if (start >= 0 && end > start) return text.slice(start, end + 1)
  return null
}

function looksLikeQuestion(item) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) return false
  return Boolean(
    item.question ??
    item.stem ??
    item.title ??
    item.content ??
    item.text ??
    item.options ??
    item.choices ??
    item.answer ??
    item.correct_answer
  )
}

/** 从对象 / 数组中提取 questions 列表 */
function extractQuestionList(payload, seen = new Set()) {
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (typeof payload !== 'object') return []
  if (seen.has(payload)) return []
  seen.add(payload)

  const keys = [
    'questions',
    'question_list',
    'questionList',
    'items',
    'quiz_list',
    'quizList',
    'exercise_list',
    'exercises',
    'problems',
    'list'
  ]
  for (const key of keys) {
    if (Array.isArray(payload[key])) return payload[key]
  }

  const grouped = []
  for (const value of Object.values(payload)) {
    if (Array.isArray(value) && value.some(looksLikeQuestion)) {
      grouped.push(...value)
    }
  }
  if (grouped.length) return grouped

  const nestedKeys = ['data', 'quiz', 'result', 'payload', 'content']
  for (const key of nestedKeys) {
    if (payload[key] && typeof payload[key] === 'object') {
      const nested = extractQuestionList(payload[key], seen)
      if (nested.length) return nested
    }
  }

  return []
}

function normalizeOptions(options) {
  if (options == null) return []

  if (Array.isArray(options)) {
    return options
      .map((opt) => {
        if (typeof opt === 'string') return opt.trim()
        if (opt && typeof opt === 'object') {
          const label = opt.label || opt.text || opt.content || opt.value || ''
          const key = opt.key || opt.id || ''
          if (key && label) return `${key}. ${label}`.replace(/^([A-D])\.\s*\1\./, '$1.')
          return String(label || key || '').trim()
        }
        return String(opt ?? '').trim()
      })
      .filter(Boolean)
  }

  if (typeof options === 'object') {
    return Object.entries(options)
      .map(([key, val]) => {
        const label = typeof val === 'string' ? val : (val?.text || val?.label || String(val))
        if (/^[A-Da-d]$/.test(key)) return `${key.toUpperCase()}. ${label}`
        return String(label).trim()
      })
      .filter(Boolean)
  }

  if (typeof options === 'string' && options.trim()) {
    return options.split(/[,，;；|]/).map(s => s.trim()).filter(Boolean)
  }

  return []
}

function normalizeType(rawType, options = []) {
  const t = String(rawType || '').trim()

  if (STANDARD_TYPES.includes(t)) return t
  if (/计算/.test(t)) return '简答题'
  if (/选择|单选|多选/.test(t)) return '选择题'
  if (/填空/.test(t)) return '填空题'
  if (/简答|问答|论述|说明/.test(t)) return '简答题'

  if (options.length >= 2) return '选择题'
  return '简答题'
}

/** 单题标准化，字段缺失时不抛错，返回 null 表示整题无效 */
export function normalizeQuestion(raw, index = 0) {
  if (raw == null) return null

  if (typeof raw === 'string') {
    const text = raw.trim()
    if (!text) return null
    return {
      id: index + 1,
      type: '简答题',
      question: text,
      options: [],
      answer: '',
      analysis: ''
    }
  }

  if (typeof raw !== 'object') return null

  const questionText = String(
    raw.question ?? raw.stem ?? raw.title ?? raw.content ?? raw.text ?? ''
  ).trim()

  const options = normalizeOptions(raw.options ?? raw.choices)
  const answer = String(
    raw.answer ?? raw.correct_answer ?? raw.reference_answer ?? raw.ref_answer ?? ''
  ).trim()
  const analysis = String(
    raw.analysis ?? raw.explanation ?? raw.reason ?? raw.parse ?? ''
  ).trim()

  let type = normalizeType(raw.type ?? raw.question_type ?? raw.qtype, options)

  // 选择题无选项时按简答题展示
  if (type === '选择题' && options.length === 0) {
    type = '简答题'
  }

  if (!questionText) return null

  return {
    id: raw.id ?? index + 1,
    type,
    question: questionText,
    options,
    answer,
    analysis
  }
}

/** 纯文本按题号拆分（最后兜底） */
function parseTextQuestions(text) {
  if (typeof text !== 'string' || !text.trim()) return []

  const parts = text.split(/(?=\n\s*(?:第\s*\d+\s*题|\d+\s*[.、)]))/).filter(p => p.trim())
  if (parts.length <= 1 && !/^\s*\d+\s*[.、)]/.test(text)) return []

  const blocks = parts.length > 1 ? parts : text.split(/(?=\n\s*\d+\s*[.、)])/).filter(p => p.trim())
  if (blocks.length <= 1) return []

  const questions = []

  blocks.forEach((block, index) => {
    const lines = block.trim().split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length) return

    const header = lines[0].replace(/^(?:第\s*\d+\s*题[:：.]?\s*|\d+\s*[.、)]\s*)/, '')
    const options = []
    const bodyLines = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (i === 0) {
        if (header) bodyLines.push(header)
        continue
      }
      const optMatch = line.match(/^([A-Da-d])[.、)．]\s*(.+)$/)
      if (optMatch) {
        options.push(`${optMatch[1].toUpperCase()}. ${optMatch[2]}`)
        continue
      }
      if (/^(答案|参考答案|解析)[:：]/i.test(line)) continue
      bodyLines.push(line)
    }

    const question = bodyLines.join('\n').trim()
    if (!question) return

    let answer = ''
    let analysis = ''
    const answerMatch = block.match(/(?:答案|参考答案)[:：]\s*([^\n]+)/i)
    const analysisMatch = block.match(/(?:解析|分析)[:：]\s*([\s\S]+)/i)
    if (answerMatch) answer = answerMatch[1].trim()
    if (analysisMatch) analysis = analysisMatch[1].trim()

    const normalized = normalizeQuestion({
      id: index + 1,
      type: options.length >= 2 ? '选择题' : '简答题',
      question,
      options,
      answer,
      analysis
    }, index)

    if (normalized) questions.push(normalized)
  })

  return questions
}

function collectRawContent(payload) {
  if (!payload || typeof payload !== 'object') return ''
  if (typeof payload.raw === 'string' && payload.raw.trim()) return payload.raw
  if (typeof payload.quiz === 'string' && payload.quiz.trim()) return payload.quiz
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return String(payload)
  }
}

function extractResponseMessage(payload) {
  if (!payload || typeof payload !== 'object') return ''

  const directFields = ['message', 'error', 'detail', 'parse_error', 'fallback_reason']
  for (const field of directFields) {
    if (typeof payload[field] === 'string' && payload[field].trim()) {
      return payload[field].trim()
    }
  }

  const nestedFields = ['quiz', 'data', 'result', 'payload']
  for (const field of nestedFields) {
    if (payload[field] && typeof payload[field] === 'object') {
      const message = extractResponseMessage(payload[field])
      if (message) return message
    }
  }

  return ''
}

function parsePayloadValue(value) {
  if (value == null) return []

  if (Array.isArray(value)) {
    return value.map((q, i) => normalizeQuestion(q, i)).filter(Boolean)
  }

  if (typeof value === 'object') {
    return extractQuestionList(value)
      .map((q, i) => normalizeQuestion(q, i))
      .filter(Boolean)
  }

  if (typeof value === 'string') {
    const parsed = tryParseJson(value)
    if (parsed) {
      const fromJson = extractQuestionList(parsed)
      if (fromJson.length) return fromJson.map((q, i) => normalizeQuestion(q, i)).filter(Boolean)
      if (Array.isArray(parsed)) {
        return parsed.map((q, i) => normalizeQuestion(q, i)).filter(Boolean)
      }
    }
    return parseTextQuestions(value)
  }

  return []
}

/**
 * 统一解析 /ai/generate_quiz 响应
 * @param {object} response - axios 完整响应、{ success, data } 或 request() 解包后的 { quiz, raw }
 * @returns {{ questions: object[], rawContent: string, error: string|null, source: string }}
 */
export function parseQuizResponse(response) {
  const result = {
    questions: [],
    rawContent: '',
    error: null,
    source: ''
  }

  if (!response || typeof response !== 'object') {
    result.error = '响应为空'
    return result
  }

  let payload = response
  if (response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
    payload = response.data
  }

  result.rawContent = collectRawContent(payload)

  const candidates = []

  if (payload.quiz != null) candidates.push({ source: 'data.quiz', value: payload.quiz })
  if (Array.isArray(payload.questions)) candidates.push({ source: 'data.questions', value: payload.questions })
  if (payload.raw != null) candidates.push({ source: 'data.raw', value: payload.raw })
  if (Array.isArray(response.questions)) candidates.push({ source: 'questions', value: response.questions })

  for (const { source, value } of candidates) {
    const questions = parsePayloadValue(value)
    if (questions.length) {
      result.questions = questions
      result.source = source
      return result
    }
  }

  // 顶层 payload 本身可能是题目数组或含 questions 的对象
  const fallback = parsePayloadValue(payload)
  if (fallback.length) {
    result.questions = fallback
    result.source = 'payload'
    return result
  }

  const responseMessage = extractResponseMessage(payload)
  result.error = responseMessage || '无法从响应中解析题目，请查看下方原始返回内容'
  return result
}
