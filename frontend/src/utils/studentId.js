const STORAGE_KEY = 'sc_student_id'

function generateId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `S_${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`
  }
  return `S_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
}

/** 获取或创建稳定的本地 student_id，供错题本等后端接口使用 */
export function getStudentId() {
  try {
    const existing = localStorage.getItem(STORAGE_KEY)
    if (existing && String(existing).trim()) {
      return String(existing).trim()
    }
    const id = generateId()
    localStorage.setItem(STORAGE_KEY, id)
    return id
  } catch {
    return generateId()
  }
}
