/** 错题本数据变更版本号，用于跨页面感知刷新 */
let version = 0

try {
  version = Number(sessionStorage.getItem('sc_mistake_book_version') || 0)
} catch {
  /* ignore */
}

export function getMistakeBookVersion() {
  return version
}

export function notifyMistakeBookChanged() {
  version += 1
  try {
    sessionStorage.setItem('sc_mistake_book_version', String(version))
  } catch {
    /* ignore */
  }
}
