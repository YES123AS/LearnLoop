export function stringifySections(sections) {
  if (!sections || typeof sections !== 'object') return ''
  return Object.entries(sections).map(([k, v]) => `## ${k}\n${String(v)}`).join('\n\n')
}

export function parseMarkdownSections(text) {
  const sections = {}
  const lines = String(text || '').split(/\n+/)
  let current = ''
  for (const line of lines) {
    const match = line.match(/^#+\s*(.+)$/)
    if (match) {
      current = match[1].trim().toLowerCase()
      sections[current] = sections[current] || ''
      continue
    }
    if (!current) continue
    sections[current] += (sections[current] ? '\n' : '') + line
  }
  return sections
}
