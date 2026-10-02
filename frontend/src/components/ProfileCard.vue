<template>
  <div class="profile-card card-panel">
    <h3 class="card-title">
      <span class="title-icon"><el-icon :size="16"><User /></el-icon></span>
      学习档案摘要
    </h3>

    <div v-if="!hasProfile" class="empty-state">
      <div class="empty-icon">
        <el-icon :size="28"><User /></el-icon>
      </div>
      <p class="empty-text">画像信息待完善</p>
      <p class="empty-hint">完善画像后可获得更精准的辅导</p>
      <el-button type="primary" class="gradient-btn" size="small" @click="$router.push('/profile')">
        前往完善画像
      </el-button>
    </div>

    <div v-else class="info-grid">
      <div class="info-item">
        <span class="label">年级</span>
        <span class="value">{{ profile.grade || '待完善' }}</span>
      </div>
      <div class="info-item">
        <span class="label">专业</span>
        <span class="value">{{ profile.major || '待完善' }}</span>
      </div>
      <div class="info-item">
        <span class="label">课程</span>
        <span class="value">{{ profile.course || '待完善' }}</span>
      </div>
      <div class="info-item">
        <span class="label">基础水平</span>
        <el-tag size="small" :type="levelTagType" effect="light">{{ profile.level || '待完善' }}</el-tag>
      </div>
      <div class="info-item full">
        <span class="label">学习目标</span>
        <span class="value">{{ profile.goal || '待完善' }}</span>
      </div>
      <div class="info-item full">
        <span class="label">学习风格</span>
        <span class="value">{{ profile.learning_style || '待完善' }}</span>
      </div>
      <div class="info-item full" v-if="profile.weak_points?.length">
        <span class="label">薄弱知识点</span>
        <div class="tags">
          <el-tag v-for="p in profile.weak_points" :key="p" type="danger" size="small" effect="light">{{ p }}</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: { type: Object, default: () => ({}) }
})

const hasProfile = computed(() => {
  const p = props.profile || {}
  return Boolean(
    (p.grade && String(p.grade).trim()) ||
    (p.major && String(p.major).trim()) ||
    (p.course && String(p.course).trim()) ||
    (p.level && String(p.level).trim()) ||
    (p.goal && String(p.goal).trim()) ||
    (p.learning_style && String(p.learning_style).trim()) ||
    (p.weak_points && p.weak_points.length > 0)
  )
})

const levelTagType = computed(() => {
  const level = props.profile.level || ''
  if (level.includes('较弱') || level.includes('零基础')) return 'danger'
  if (level.includes('一般') || level.includes('中等')) return 'warning'
  return 'success'
})
</script>

<style scoped>
.profile-card {
  padding: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.title-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--gradient-soft);
  border: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 28px 16px;
  text-align: center;
}

.empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--gradient-soft);
  border: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  margin-bottom: 4px;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.empty-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full {
  grid-column: 1 / -1;
}

.label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}
</style>
