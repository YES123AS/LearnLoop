<template>
  <div
    v-if="hasContent"
    class="markdown-body"
    :class="{ 'code-theme-light': codeTheme === 'light' }"
    v-html="rendered"
  />
  <div v-else-if="!compact" class="markdown-empty">
    <el-icon :size="40" color="#cbd5e1"><Document /></el-icon>
    <p>{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import multimdTable from 'markdown-it-multimd-table'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, default: '' },
  emptyText: { type: String, default: '暂无内容，请先生成或等待 AI 返回结果' },
  /** 紧凑模式：不显示空状态占位（用于聊天气泡等） */
  compact: { type: Boolean, default: false },
  /** 代码块主题：dark 用于资源页，light 用于聊天气泡 */
  codeTheme: { type: String, default: 'dark' }
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})
md.use(multimdTable, { multiline: true, rowspan: true, headerless: true })

const hasContent = computed(() => Boolean(props.content && props.content.trim()))

const rendered = computed(() => {
  if (!hasContent.value) return ''
  const html = md.render(props.content)
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['target', 'rel']
  })
})
</script>

<style scoped>
.markdown-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  color: var(--text-secondary);
  gap: 12px;
}

.markdown-empty p {
  font-size: 14px;
}
</style>
