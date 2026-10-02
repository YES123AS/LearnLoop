/** 读取错题状态，默认未修复 */
export function getMistakeStatus(item) {
  return item?.status || '未修复'
}

/** 读取知识点 */
export function getKnowledgePoint(item) {
  if (!item) return '未知知识点'
  return item.knowledge_point || item.question?.knowledge_point || '未知知识点'
}

/** 读取题型 */
export function getQuestionType(item) {
  return item?.question_type || item?.question?.type || item?.type || '未知题型'
}

/** 读取题干 */
export function getStem(item) {
  if (!item) return '—'
  if (typeof item.question === 'object' && item.question?.question) return item.question.question
  if (typeof item.question === 'string' && item.question.trim()) return item.question
  return item.question_text || '（题干缺失）'
}

/** 读取标准答案 */
export function getStandardAnswer(item) {
  return item?.standard_answer || item?.answer || item?.question?.answer || '—'
}

/** 读取错因类型 */
export function getErrorTypes(item) {
  const types = item?.error_types
  if (Array.isArray(types)) return types.filter(Boolean)
  if (typeof types === 'string' && types.trim()) return [types.trim()]
  return []
}

/** 读取时间戳用于排序 */
export function getMistakeTimestamp(item) {
  return item?.created_at || item?.create_time || item?.timestamp || ''
}

/** 按时间倒序排序错题 */
export function sortMistakesByTime(mistakes = []) {
  return [...mistakes].sort((a, b) => {
    const ta = getMistakeTimestamp(a)
    const tb = getMistakeTimestamp(b)
    if (ta && tb) return String(tb).localeCompare(String(ta))
    return 0
  })
}

/**
 * 统一统计错题列表
 * @param {Array} mistakes
 * @returns 统计结果
 */
export function buildMistakeStats(mistakes = []) {
  const list = Array.isArray(mistakes) ? mistakes : []
  const knowledgePointStats = {}
  const errorTypeStats = {}

  for (const item of list) {
    const kp = getKnowledgePoint(item)
    if (kp && kp !== '未知知识点') {
      knowledgePointStats[kp] = (knowledgePointStats[kp] || 0) + 1
    }

    const types = getErrorTypes(item)
    if (types.length) {
      for (const t of types) {
        errorTypeStats[t] = (errorTypeStats[t] || 0) + 1
      }
    } else {
      errorTypeStats['待分析'] = (errorTypeStats['待分析'] || 0) + 1
    }
  }

  const knowledgePoints = Object.keys(knowledgePointStats)
  const topWeakPoints = Object.entries(knowledgePointStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name]) => name)

  const sorted = sortMistakesByTime(list)

  return {
    total: list.length,
    unresolved: list.filter(m => getMistakeStatus(m) !== '已修复').length,
    resolved: list.filter(m => getMistakeStatus(m) === '已修复').length,
    knowledgePoints,
    knowledgePointStats,
    topWeakPoints,
    recentMistakes: sorted.slice(0, 5),
    errorTypeStats
  }
}
