<template>
  <div class="chat-bubble" :class="role">
    <div class="avatar" :class="role">
      <el-icon v-if="role === 'user'" :size="20"><User /></el-icon>
      <el-icon v-else :size="20"><Cpu /></el-icon>
    </div>
    <div class="bubble-content">
      <div class="bubble-header">
        <span class="name">{{ role === 'user' ? '我' : 'AI 辅导助手' }}</span>
        <span v-if="time" class="time">{{ formatTime(time) }}</span>
      </div>
      <div v-if="role === 'user'" class="bubble-text">{{ content }}</div>
      <div v-else class="bubble-text bubble-markdown">
        <MarkdownViewer :content="content" compact code-theme="light" />
      </div>
    </div>
  </div>
</template>

<script setup>
import MarkdownViewer from '@/components/MarkdownViewer.vue'

defineProps({
  role: { type: String, required: true },
  content: { type: String, required: true },
  time: { type: Number, default: 0 }
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  min-width: 0;
}

.chat-bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar.user {
  background: var(--gradient);
  color: #fff;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.25);
}

.avatar.assistant {
  background: #fff;
  color: var(--primary);
  border: 1px solid var(--border);
}

.bubble-content {
  max-width: 72%;
  min-width: 0;
  overflow: hidden;
}

.assistant .bubble-content {
  max-width: min(78%, 720px);
}

.user .bubble-content {
  text-align: right;
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.user .bubble-header {
  flex-direction: row-reverse;
}

.name {
  font-weight: 600;
  color: var(--text-primary);
}

.bubble-text {
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.75;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: break-word;
}

.user .bubble-text {
  background: var(--gradient);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.2);
}

.assistant .bubble-text {
  background: #fff;
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  box-shadow: var(--shadow);
}

.bubble-markdown {
  padding: 12px 16px;
  white-space: normal;
}

.bubble-markdown :deep(.markdown-body) {
  font-size: 14px;
  line-height: 1.75;
  overflow-wrap: break-word;
  word-break: break-word;
  max-width: 100%;
}

.bubble-markdown :deep(.markdown-body > *:first-child) {
  margin-top: 0;
}

.bubble-markdown :deep(.markdown-body > *:last-child) {
  margin-bottom: 0;
}

.bubble-markdown :deep(.markdown-body h1),
.bubble-markdown :deep(.markdown-body h2),
.bubble-markdown :deep(.markdown-body h3) {
  margin: 14px 0 8px;
  font-weight: 700;
}

.bubble-markdown :deep(.markdown-body h1) { font-size: 18px; }
.bubble-markdown :deep(.markdown-body h2) { font-size: 17px; }
.bubble-markdown :deep(.markdown-body h3) { font-size: 16px; }

.bubble-markdown :deep(.markdown-body p) {
  margin: 8px 0;
}

.bubble-markdown :deep(.markdown-body ul),
.bubble-markdown :deep(.markdown-body ol) {
  padding-left: 22px;
  margin: 8px 0;
}

.bubble-markdown :deep(.markdown-body li) {
  margin: 4px 0;
}

.bubble-markdown :deep(.markdown-body pre) {
  background: #f3f4f6;
  color: #111827;
  border: 1px solid var(--border);
  padding: 12px 14px;
  border-radius: 10px;
  overflow-x: auto;
  max-width: 100%;
  margin: 10px 0;
  font-size: 13px;
}

.bubble-markdown :deep(.markdown-body pre code) {
  background: none;
  color: inherit;
  padding: 0;
}

.bubble-markdown :deep(.markdown-body table) {
  display: block;
  overflow-x: auto;
  max-width: 100%;
}
</style>
