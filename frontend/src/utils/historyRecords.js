export function loadHistoryRecords(storageKey) {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return []
    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export function saveHistoryRecord(storageKey, record, limit = 5) {
  try {
    const list = loadHistoryRecords(storageKey)
    const next = [record, ...list].slice(0, limit)
    localStorage.setItem(storageKey, JSON.stringify(next))
    return next
  } catch {
    return loadHistoryRecords(storageKey)
  }
}

export function removeHistoryRecord(storageKey, predicate) {
  try {
    const list = loadHistoryRecords(storageKey)
    const next = typeof predicate === 'function' ? list.filter(item => !predicate(item)) : list
    localStorage.setItem(storageKey, JSON.stringify(next))
    return next
  } catch {
    return []
  }
}

export function clearHistoryRecords(storageKey) {
  try {
    localStorage.removeItem(storageKey)
  } catch {}
}
