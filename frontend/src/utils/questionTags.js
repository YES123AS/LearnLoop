const clampScore = (value, fallback = 3) => {
  const num = Number(value)
  if (!Number.isFinite(num)) return fallback
  return Math.min(5, Math.max(1, Math.round(num)))
}

const typeToInnovation = (type = '') => {
  if (/选择|判断/.test(type)) return 1
  if (/填空/.test(type)) return 2
  if (/简答|计算/.test(type)) return 3
  return 3
}

const importanceKeywords = ['核心', '重点', '高频', '必考', '主干', '基础', '常考']
const integrationKeywords = ['综合', '联动', '跨', '应用', '迁移', '分析', '设计']

export function createDefaultTagMetrics(question = {}) {
  const diff = question.difficulty ?? question.level ?? question.difficulty_level
  const knowledgePoint = question.knowledge_point || question.topic || question.knowledgePoint || ''
  const knowledgeCount = Array.isArray(question.knowledge_points)
    ? question.knowledge_points.length
    : String(knowledgePoint).split(/[、,，/]/).filter(Boolean).length || 1

  const importanceText = `${knowledgePoint} ${question.analysis || ''} ${question.explanation || ''}`

  return {
    difficulty: clampScore(typeof diff === 'string' ? ({ 简单: 2, 中等: 3, 困难: 4 }[diff] || 3) : diff, 3),
    innovation: clampScore(question.innovation ?? typeToInnovation(question.type), 3),
    importance: clampScore(
      question.importance ?? (importanceKeywords.some(k => importanceText.includes(k)) ? 4 : 3),
      3
    ),
    integration: clampScore(
      question.integration ?? (integrationKeywords.some(k => importanceText.includes(k)) ? 4 : knowledgeCount >= 3 ? 4 : knowledgeCount === 2 ? 3 : 2),
      3
    )
  }
}

export function normalizeQuestionTags(question = {}) {
  const raw = question.tagMetrics || question.tags || {}
  return {
    difficulty: clampScore(raw.difficulty ?? question.difficulty, 3),
    innovation: clampScore(raw.innovation ?? question.innovation ?? typeToInnovation(question.type), 3),
    importance: clampScore(raw.importance ?? question.importance ?? createDefaultTagMetrics(question).importance, 3),
    integration: clampScore(raw.integration ?? question.integration ?? createDefaultTagMetrics(question).integration, 3)
  }
}

export function getTagLevel(score) {
  if (score <= 2) return '基础'
  if (score === 3) return '中等'
  if (score === 4) return '较高'
  return '高阶'
}

export function getTagColor(score) {
  if (score <= 2) return 'info'
  if (score === 3) return 'warning'
  if (score === 4) return 'primary'
  return 'success'
}

export function getQuestionTagSummary(question = {}) {
  const tags = normalizeQuestionTags(question)
  const difficultyText = ['很简单', '简单', '中等', '较难', '困难'][tags.difficulty - 1] || '中等'
  const innovationText = ['常规基础题', '略有变化', '综合应用', '新颖情境', '创新探究'][tags.innovation - 1] || '综合应用'
  const importanceText = ['了解即可', '一般考点', '常见考点', '重点考点', '核心高频考点'][tags.importance - 1] || '重点考点'
  const integrationText = ['单一知识点', '两个知识点', '多知识点关联', '跨模块综合', '高综合应用'][tags.integration - 1] || '多知识点关联'
  return `${difficultyText}，${importanceText}，${integrationText}，${innovationText}`
}
