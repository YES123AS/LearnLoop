/**
 * 从 /ai/generate_resource 各类响应结构中提取 Markdown 内容
 * @param {object|string} response - request() 解包结果或 axios 原始响应
 * @returns {{ content: string, rawResponse: object|string|null }}
 */
export function extractResourceContent(response) {
  if (response == null) {
    return { content: '', rawResponse: null }
  }

  if (typeof response === 'string') {
    return { content: response.trim(), rawResponse: response }
  }

  const candidates = [
    response?.data?.content,
    response?.content,
    response?.data?.data?.content,
    response?.data?.raw,
    response?.raw,
    response?.data?.markdown,
    response?.markdown,
    response?.data?.markdown_content,
    response?.markdown_content
  ]

  for (const item of candidates) {
    if (typeof item === 'string' && item.trim()) {
      return { content: item.trim(), rawResponse: response }
    }
  }

  // generate_learning_resource 返回 { content, output_file } 嵌套在 data 中
  if (response?.data && typeof response.data === 'object') {
    const nested = extractResourceContent(response.data)
    if (nested.content) return { content: nested.content, rawResponse: response }
  }

  return { content: '', rawResponse: response }
}
