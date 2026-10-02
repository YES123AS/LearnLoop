<template>
  <div class="ai-loading">
    <div class="loading-ring"></div>
    <div class="loading-dots">
      <span></span><span></span><span></span>
    </div>
    <p class="loading-text">{{ text }}</p>
    <p class="loading-hint">正在生成个性化内容，请稍候…</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: 'AI 正在分析中…' }
})
</script>

<style scoped>
.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  gap: 12px;
}

.loading-ring {
  width: 44px;
  height: 44px;
  border: 3px solid rgba(99, 102, 241, 0.12);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.loading-dots {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gradient);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

.loading-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 8px;
}

.loading-hint {
  font-size: 13px;
  color: var(--text-secondary);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
