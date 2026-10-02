import { normalizeQuestionTags } from '@/utils/questionTags'

export function analyzeQuestionTagPerformance(records = []) {
  const base = {
    difficulty: { total: 0, correct: 0, wrong: 0, sum: 0 },
    innovation: { total: 0, correct: 0, wrong: 0, sum: 0 },
    importance: { total: 0, correct: 0, wrong: 0, sum: 0 },
    integration: { total: 0, correct: 0, wrong: 0, sum: 0 }
  }

  const list = Array.isArray(records) ? records : []
  for (const record of list) {
    const tags = normalizeQuestionTags(record)
    const correct = Boolean(record.correct)
    for (const [key, score] of Object.entries(tags)) {
      const bucket = base[key]
      if (!bucket) continue
      bucket.total += 1
      bucket.sum += score
      if (correct) bucket.correct += 1
      else bucket.wrong += 1
    }
  }

  const result = {}
  for (const [key, bucket] of Object.entries(base)) {
    result[key] = {
      ...bucket,
      average: bucket.total ? Number((bucket.sum / bucket.total).toFixed(2)) : 0,
      accuracy: bucket.total ? Number(((bucket.correct / bucket.total) * 100).toFixed(1)) : 0,
      wrongRate: bucket.total ? Number(((bucket.wrong / bucket.total) * 100).toFixed(1)) : 0
    }
  }

  const weakest = Object.entries(result)
    .sort((a, b) => a[1].accuracy - b[1].accuracy)
    .map(([name]) => name)[0] || 'difficulty'

  return { ...result, weakest }
}

export function generateTagBasedSuggestions(analysis = {}) {
  const suggestions = []
  const pushIfWeak = (key, title, content) => {
    if (!analysis[key]) return
    if (analysis[key].accuracy <= 70 || analysis[key].average >= 4) {
      suggestions.push({ key, title, content })
    }
  }

  pushIfWeak('difficulty', '基础巩固 + 分层训练', '你的高难度题正确率偏低，建议先从基础题和分层练习入手，再逐步提升难题训练。')
  pushIfWeak('innovation', '情境应用题训练', '你在创新题上容易出错，建议多练“题目情境变化”的应用题，提升迁移理解能力。')
  pushIfWeak('importance', '核心考点复习', '重点考点正确率不足，建议优先回到核心知识点做系统梳理。')
  pushIfWeak('integration', '知识网络梳理与综合题训练', '高综合度题目表现偏弱，建议先理清知识点关系，再做综合题巩固。')

  if (!suggestions.length) {
    suggestions.push({
      key: 'maintain',
      title: '保持节奏，继续提升',
      content: '当前各维度表现较均衡，建议继续保持练习频率，并适当增加综合题训练。'
    })
  }

  return suggestions
}
