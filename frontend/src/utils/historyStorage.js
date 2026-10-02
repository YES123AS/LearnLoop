export function getHistory(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export function addHistory(key, item, limit = 5) {
  const list = getHistory(key)
  const next = [item, ...list].slice(0, limit)
  localStorage.setItem(key, JSON.stringify(next))
  return next
}

export function clearHistory(key) {
  localStorage.removeItem(key)
}
