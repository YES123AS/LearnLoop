/**
 * 将技术错误信息转换为用户友好提示
 * @param {unknown} err
 * @returns {string}
 */
export function normalizeErrorMessage(err) {
  const raw = extractRawMessage(err)
  const lower = raw.toLowerCase()

  if (
    raw === 'Network Error' ||
    lower.includes('network error') ||
    lower.includes('err_network') ||
    lower.includes('无法连接后端')
  ) {
    return '服务暂时不可用，请确认后端服务已启动后重试'
  }

  if (
    lower.includes('timeout') ||
    lower.includes('exceeded') ||
    lower.includes('econnaborted') ||
    lower.includes('请求超时')
  ) {
    return '内容生成时间较长，请稍后重试或减少生成内容'
  }

  if (/\b500\b/.test(raw) || lower.includes('internal server error')) {
    return '服务处理异常，请稍后重试'
  }

  if (/\b404\b/.test(raw) || lower.includes('not found')) {
    return '请求的资源不存在，请检查功能入口是否正确'
  }

  if (raw && raw.length <= 120 && !looksLikeStack(raw)) {
    return raw
  }

  return '操作未完成，请稍后重试'
}

function extractRawMessage(err) {
  if (!err) return ''
  if (typeof err === 'string') return err
  if (err instanceof Error) return err.message || ''
  if (typeof err === 'object') {
    const e = /** @type {Record<string, unknown>} */ (err)
    if (e.response && typeof e.response === 'object') {
      const resp = /** @type {Record<string, unknown>} */ (e.response)
      const data = resp.data
      if (data && typeof data === 'object') {
        const d = /** @type {Record<string, unknown>} */ (data)
        if (typeof d.detail === 'string') return d.detail
        if (d.detail && typeof d.detail === 'object' && d.detail !== null) {
          const detail = /** @type {Record<string, unknown>} */ (d.detail)
          if (typeof detail.message === 'string') return detail.message
        }
        if (typeof d.message === 'string') return d.message
      }
      if (typeof resp.status === 'number') return String(resp.status)
    }
    if (typeof e.message === 'string') return e.message
    if (typeof e.code === 'string') return e.code
  }
  return String(err)
}

function looksLikeStack(text) {
  return text.includes(' at ') || text.includes('\n    ')
}

/**
 * 记录原始错误并返回友好提示（供 API 层等使用）
 */
export function logAndNormalizeError(err, context = '') {
  console.error(context ? `[${context}]` : '[error]', err)
  return normalizeErrorMessage(err)
}
