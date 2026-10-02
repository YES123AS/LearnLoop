/**
 * 浏览器端文件下载（Blob），由用户自行选择保存位置。
 */
export function downloadTextFile(content, filename, mimeType = 'text/markdown;charset=utf-8') {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function downloadJsonFile(data, filename) {
  const content = JSON.stringify(data, null, 2)
  downloadTextFile(content, filename, 'application/json;charset=utf-8')
}

export function sanitizeFilename(name) {
  return (name || '学习资料').replace(/[\\/:*?"<>|]/g, '_').trim() || '学习资料'
}

export function formatDateFilename(prefix, ext) {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${prefix}_${y}${m}${day}.${ext}`
}
