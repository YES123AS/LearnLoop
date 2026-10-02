<template>
  <div class="page-container">
    <!-- Hero -->
    <section class="hero dashboard-hero">
      <div class="hero-content">
        <div class="hero-tags">
          <span class="ai-badge">AI 辅导</span>
          <span class="ai-badge">个性化路径</span>
          <span class="ai-badge">学情分析</span>
        </div>
        <h1 class="hero-title">{{ BRAND_NAME }}</h1>
        <p class="hero-subtitle">{{ WORKBENCH_TITLE }}</p>
        <p class="hero-desc">{{ BRAND_DESC }}</p>
        <el-button
          type="primary"
          size="large"
          class="gradient-btn hero-btn"
          @click="$router.push(store.hasProfile ? APP_ROUTES.chat : APP_ROUTES.profile)"
        >
          {{ store.hasProfile ? '开始智能辅导' : '构建学习画像' }}
        </el-button>
      </div>

      <div class="hero-visual">
        <div class="hero-logo-card">
          <LogoIcon :size="96" />
          <div class="hero-logo-title">{{ BRAND_NAME }}</div>
          <div class="hero-logo-subtitle">{{ BRAND_SLOGAN }}</div>
        </div>
        <div class="loop-node node-profile">画像</div>
        <div class="loop-node node-resource">资源</div>
        <div class="loop-node node-practice">练习</div>
        <div class="loop-node node-analysis">分析</div>
      </div>
    </section>

    <!-- 学习状态概览 -->
    <div class="stats-row">
      <StatCard
        label="练习记录"
        :value="store.totalQuestions"
        icon="EditPen"
        icon-bg="linear-gradient(135deg, #6366f1, #8b5cf6)"
      />
      <StatCard
        label="对话消息"
        :value="store.chat_history.length"
        icon="ChatDotRound"
        icon-bg="linear-gradient(135deg, #8b5cf6, #3b82f6)"
      />
      <StatCard
        label="正确率"
        :value="store.totalQuestions ? store.accuracyRate + '%' : '—'"
        icon="TrendCharts"
        icon-bg="linear-gradient(135deg, #6366f1, #3b82f6)"
      />
      <StatCard
        label="薄弱知识点"
        :value="store.weak_points.length"
        icon="Warning"
        icon-bg="linear-gradient(135deg, #a78bfa, #6366f1)"
      />
    </div>

    <!-- 错题概览 -->
    <div class="stats-row mistake-stats-row">
      <StatCard
        label="错题总数"
        :value="mistakeStats.total"
        icon="Document"
        icon-bg="linear-gradient(135deg, #6366f1, #8b5cf6)"
      />
      <StatCard
        label="未修复错题"
        :value="mistakeStats.unresolved"
        icon="Warning"
        icon-bg="linear-gradient(135deg, #a78bfa, #6366f1)"
      />
      <StatCard
        label="已修复错题"
        :value="mistakeStats.resolved"
        icon="CircleCheck"
        icon-bg="linear-gradient(135deg, #6366f1, #3b82f6)"
      />
      <StatCard
        label="错题涉及知识点"
        :value="mistakeStats.knowledgePoints.length"
        icon="Reading"
        icon-bg="linear-gradient(135deg, #8b5cf6, #3b82f6)"
      />
    </div>

    <!-- 错题复习提醒 -->
    <section class="review-reminder card-panel">
      <div class="reminder-content">
        <h3 class="section-heading">错题复习提醒</h3>
        <template v-if="mistakeStats.unresolved > 0">
          <p class="reminder-text">
            你还有 <strong>{{ mistakeStats.unresolved }}</strong> 道待修复错题
          </p>
          <p v-if="mistakeStats.topWeakPoints.length" class="reminder-sub">
            建议优先复习：{{ mistakeStats.topWeakPoints.slice(0, 3).join('、') }}
          </p>
          <el-button type="primary" class="gradient-btn" @click="$router.push(APP_ROUTES.mistakes)">
            进入错题集
          </el-button>
        </template>
        <template v-else>
          <p class="reminder-text">当前暂无待修复错题，继续保持练习节奏</p>
          <el-button type="primary" class="gradient-btn" @click="$router.push(APP_ROUTES.quiz)">
            继续练习
          </el-button>
        </template>
      </div>
    </section>

    <!-- 学习流程引导 -->
    <SectionCard title="学习流程引导" desc="按顺序完成以下环节，构建完整的 AI 个性化学习闭环">
      <div class="flow-guide">
        <div
          v-for="(step, i) in LEARNING_FLOW_STEPS"
          :key="step.key"
          class="flow-guide-item"
          @click="$router.push(step.route)"
        >
          <div class="flow-guide-index">{{ i + 1 }}</div>
          <div class="flow-guide-body">
            <strong>{{ step.title }}</strong>
            <p>{{ step.desc }}</p>
          </div>
          <el-icon class="flow-guide-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </SectionCard>

    <!-- 功能入口 -->
    <section class="feature-section">
      <h2 class="section-heading">核心功能</h2>
      <div class="feature-grid">
        <div
          v-for="item in features"
          :key="item.route"
          class="feature-card card-panel"
          @click="$router.push(item.route)"
        >
          <div class="feature-icon">
            <el-icon :size="26"><component :is="item.icon" /></el-icon>
          </div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
          <span class="feature-link">进入功能 →</span>
        </div>
      </div>
    </section>

    <!-- 学习闭环 -->
    <section class="flow-section card-panel">
      <h2 class="section-heading">学习闭环</h2>
      <p class="flow-desc">从画像构建到错题修复，形成智学环驱动的完整学习闭环</p>
      <div class="flow-pipeline">
        <template v-for="(step, i) in flowSteps" :key="i">
          <div class="flow-node">
            <div class="flow-dot">{{ i + 1 }}</div>
            <span>{{ step }}</span>
          </div>
          <div v-if="i < flowSteps.length - 1" class="flow-connector">
            <div class="connector-line"></div>
            <el-icon class="connector-arrow"><ArrowRight /></el-icon>
          </div>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useStudentStore } from '@/store/student'
import { useMistakeSummary } from '@/composables/useMistakeSummary'
import { usePageRefresh } from '@/composables/usePageRefresh'
import StatCard from '@/components/StatCard.vue'
import LogoIcon from '@/components/LogoIcon.vue'
import SectionCard from '@/components/SectionCard.vue'
import {
  BRAND_NAME,
  BRAND_SLOGAN,
  BRAND_DESC,
  WORKBENCH_TITLE,
  LEARNING_FLOW_STEPS
} from '@/constants/brand'
import { APP_ROUTES } from '@/constants/routes'
import {
  User, ChatDotRound, Document, Guide, EditPen, DataAnalysis, Star, ArrowRight, FolderOpened
} from '@element-plus/icons-vue'

const store = useStudentStore()
const { stats: mistakeStats, refresh: refreshMistakeSummary } = useMistakeSummary({ silent: true })
usePageRefresh(refreshMistakeSummary, { smart: true })

const features = [
  { title: '学习画像', desc: '构建个性化学习画像，记录基础信息与薄弱知识点', icon: User, route: APP_ROUTES.profile },
  { title: '智能辅导', desc: '结合画像的 AI 问答辅导，因材施教解答学习疑问', icon: ChatDotRound, route: APP_ROUTES.chat },
  { title: '知识库管理', desc: '上传课件、文档与笔记，重建 RAG 检索知识库', icon: FolderOpened, route: APP_ROUTES.knowledge },
  { title: '资源生成', desc: '根据主题与画像生成结构化学习资料', icon: Document, route: APP_ROUTES.resource },
  { title: '学习路径', desc: '按目标与天数规划每日学习任务', icon: Guide, route: APP_ROUTES.path },
  { title: '题目练习', desc: '智能生成练习题，巩固知识点掌握情况', icon: EditPen, route: APP_ROUTES.quiz },
  { title: '学情分析', desc: '统计练习数据，AI 分析薄弱点并更新画像', icon: DataAnalysis, route: APP_ROUTES.analysis },
  { title: '学习推荐', desc: '基于学情与画像推荐下一步学习内容', icon: Star, route: APP_ROUTES.recommend }
]

const flowSteps = ['画像构建', '知识库上传', '路径规划', '资源生成', '智能辅导', '练习测试', '学情评估', '动态推荐']
</script>

<style scoped>
.hero {
  background: var(--gradient);
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  margin-bottom: 28px;
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.16);
}

.dashboard-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 32px;
  align-items: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 640px;
}

.hero-visual {
  position: relative;
  z-index: 2;
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-logo-card {
  width: 240px;
  min-height: 220px;
  padding: 28px 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  box-shadow: 0 12px 28px rgba(30, 41, 59, 0.14);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.2s ease;
}

.hero-logo-card:hover {
  box-shadow: 0 14px 32px rgba(30, 41, 59, 0.16);
}

.hero-logo-title {
  margin-top: 16px;
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
  text-align: center;
  line-height: 1.3;
}

.hero-logo-subtitle {
  margin-top: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.78);
  text-align: center;
  line-height: 1.5;
}

.loop-node {
  position: absolute;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.24);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.node-profile {
  top: 20px;
  left: 8px;
}

.node-resource {
  top: 38px;
  right: 4px;
}

.node-practice {
  bottom: 34px;
  left: 18px;
}

.node-analysis {
  bottom: 18px;
  right: 24px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.hero-tags .ai-badge {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.28);
  color: #fff;
}

.hero-title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
  letter-spacing: -0.02em;
  line-height: 1.25;
}

.hero-subtitle {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  margin-bottom: 12px;
  letter-spacing: 0.02em;
}

.hero-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.88);
  line-height: 1.7;
  margin-bottom: 28px;
}

.hero-btn {
  padding: 12px 32px;
  font-size: 15px;
  border-radius: 12px;
  background: #fff !important;
  color: var(--primary-dark) !important;
  box-shadow: 0 4px 16px rgba(17, 24, 39, 0.12) !important;
}

.hero-btn:hover {
  background: #f9fafb !important;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.16) !important;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.mistake-stats-row {
  margin-bottom: 20px;
}

.review-reminder {
  padding: 22px 24px;
  margin-bottom: 28px;
}

.reminder-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
}

.reminder-text {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.6;
}

.reminder-sub {
  font-size: 13px;
  color: var(--text-secondary);
}

.feature-section {
  margin-bottom: 28px;
}

.flow-guide {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.flow-guide-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--bg-light);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.flow-guide-item:hover {
  border-color: rgba(99, 102, 241, 0.35);
  box-shadow: 0 3px 10px rgba(99, 102, 241, 0.08);
}

.flow-guide-index {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--gradient);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.flow-guide-body {
  flex: 1;
  min-width: 0;
}

.flow-guide-body strong {
  display: block;
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.flow-guide-body p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.flow-guide-arrow {
  color: var(--primary);
  flex-shrink: 0;
}

:deep(.section-card) {
  margin-bottom: 28px;
}

.feature-section {
  margin-bottom: 28px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.feature-card {
  cursor: pointer;
  padding: 22px 20px;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 14px;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.22);
}

.feature-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
  min-height: 42px;
}

.feature-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
}

.flow-section {
  margin-bottom: 8px;
}

.flow-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: -8px 0 20px;
}

.flow-pipeline {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px 0;
}

.flow-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.flow-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--gradient);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.flow-node span {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.flow-connector {
  display: flex;
  align-items: center;
  padding: 0 2px;
}

.connector-line {
  width: 20px;
  height: 2px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 1px;
}

.connector-arrow {
  color: var(--primary);
  font-size: 12px;
}

@media (max-width: 1024px) {
  .dashboard-hero {
    grid-template-columns: 1fr;
    gap: 28px;
  }

  .hero-visual {
    min-height: 180px;
  }

  .hero-logo-card {
    width: 220px;
    min-height: 180px;
    padding: 24px 20px;
  }
}

@media (max-width: 768px) {
  .hero-visual {
    display: none;
  }
}

@media (max-width: 1200px) {
  .feature-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 900px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
  .hero { padding: 36px 28px; }
  .hero-title { font-size: 26px; }
}
</style>
