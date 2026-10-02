<template>
  <div class="page-container path-page">
    <section class="page-hero card-panel">
      <div class="hero-copy">
        <div class="hero-kicker">LearnLoopAI · 路径规划工作台</div>
        <h1 class="hero-title">学习路径规划</h1>
        <p class="hero-desc">结合学习目标、基础水平、薄弱知识点与可用时间，生成阶段化、可执行的个性化学习路线。</p>
        <div class="hero-actions">
          <el-button type="primary" class="gradient-btn" @click="$router.push('/profile')">完善学习画像</el-button>
          <el-button plain @click="$router.push('/resource')">去学习资源</el-button>
          <el-button plain @click="$router.push('/quiz')">去生成题目</el-button>
        </div>
      </div>
      <div class="hero-summary card-panel soft-card">
        <div class="summary-title">当前画像摘要</div>
        <div class="summary-grid">
          <div><span>当前课程</span><strong>{{ profileText.course }}</strong></div>
          <div><span>学习目标</span><strong>{{ profileText.goal }}</strong></div>
          <div><span>基础水平</span><strong>{{ profileText.level }}</strong></div>
          <div><span>每周学习时间</span><strong>{{ profileText.weekly_time }}</strong></div>
          <div class="full"><span>薄弱点</span><strong>{{ profileText.weak_points }}</strong></div>
        </div>
        <el-alert v-if="!hasProfile" title="请先完善学习画像，以获得更精准的路径规划结果。" type="warning" :closable="false" show-icon />
      </div>
    </section>

    <div class="path-layout">
      <div class="path-main">
        <div class="card-panel section-card">
          <div class="panel-head">
            <div>
              <h3>路径配置</h3>
              <p>设置目标、周期、学习时长与规划重点，生成可执行的个性化路径。</p>
            </div>
            <el-tag type="primary" effect="light">支持语音输入</el-tag>
          </div>
          <el-form label-position="top" class="config-form">
            <el-form-item label="学习目标"><div class="inline-input-row"><el-input :model-value="goal" placeholder="输入你的学习目标" @update:model-value="handleGoalInput" @keyup.enter="handleGeneratePath" /><SpeechInputButton size="small" :text="false" :model-value="goal" @start="handlePathSpeechStart" @interim="handlePathSpeechInterim" @result="handlePathSpeechResult" @stop="handlePathSpeechStop" @error="handlePathSpeechError" /></div></el-form-item>
            <el-row :gutter="16"><el-col :span="12"><el-form-item label="计划周期"><el-select v-model="days" class="w100"><el-option v-for="opt in daysOptions" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="每日学习时长"><el-select v-model="dailyTime" class="w100"><el-option v-for="opt in dailyTimeOptions" :key="opt" :label="opt" :value="opt" /></el-select></el-form-item></el-col></el-row>
            <el-form-item label="路径强度"><el-radio-group v-model="intensity"><el-radio-button v-for="opt in intensityOptions" :key="opt" :label="opt" /></el-radio-group></el-form-item>
            <el-form-item label="规划重点"><el-checkbox-group v-model="focus"><el-checkbox v-for="opt in focusOptions" :key="opt" :label="opt" /></el-checkbox-group></el-form-item>
            <div class="form-actions"><el-button type="primary" class="gradient-btn" :loading="loading" @click="handleGeneratePath">生成路径</el-button><el-button plain @click="fillTemplate('画像路径')">根据我的学习画像生成路径</el-button></div>
          </el-form>
        </div>

        <EmptyState
          v-if="!renderedContent && !loading"
          title="你可以这样开始"
          description="例如：期末复习、竞赛提升、系统提升。先输入目标，再选择周期和强度，系统会优先匹配课程和薄弱点。"
          :has-action="false"
        />

        <LoadingState
          v-if="loading"
          title="生成中"
          description="正在读取学习画像并生成个性化路径。"
          loading-text="路径生成中，请稍候..."
          :stage-text="loadingStages[loadingStep] || ''"
        />

        <div v-if="renderedContent" class="card-panel section-card result-card">
          <div class="quality-card">
            <div class="quality-title">本路径已结合：</div>
            <div class="quality-tags"><el-tag v-for="t in qualityTags" :key="t" effect="light">{{ t }}</el-tag></div>
            <p v-if="!hasProfile" class="quality-hint">画像不完整，建议完善后再生成更精准的路径。</p>
          </div>

          <div class="panel-head">
            <div>
              <h3>路径结果</h3>
              <p>已按总览、阶段路线、每日任务、里程碑与复盘建议结构化展示。</p>
            </div>
            <div class="result-actions">
              <el-button size="small" @click="copyFullResult">复制完整路径</el-button>
              <el-button size="small" @click="copyCurrentSection">复制当前模块</el-button>
              <el-button size="small" type="primary" @click="handleGeneratePath">重新生成</el-button>
              <el-button size="small" plain @click="$router.push('/resource')">去学习资源</el-button>
            </div>
          </div>

          <div class="result-layout">
            <aside class="toc-card card-panel soft-card">
              <div class="toc-head">路径目录</div>
              <button v-for="item in sectionList" :key="item.id" class="toc-item" :class="{ active: activeSection === item.id }" @click="scrollToSection(item.id)">{{ item.label }}</button>
            </aside>

            <div class="result-content">
              <div class="summary-panel card-panel soft-card" ref="sectionRefs.overview">
                <div class="block-head"><h4>路径总览</h4><span>总体节奏与目标</span></div>
                <div class="summary-progress"><div class="progress-row"><span>当前完成度</span><strong>{{ completionPercent }}%</strong></div><el-progress :percentage="completionPercent" /></div>
                <div class="overview-grid">
                  <div><span>总周期</span><strong>{{ days }} 天</strong></div>
                  <div><span>每日学习时长</span><strong>{{ dailyTime }}</strong></div>
                  <div><span>路径强度</span><strong>{{ intensity }}</strong></div>
                  <div><span>优先补强点</span><strong>{{ priorityWeakPoint }}</strong></div>
                  <div class="full"><span>下一步任务</span><strong>{{ nextTaskText }}</strong></div>
                </div>
              </div>

              <div class="task-card card-panel soft-card" ref="sectionRefs.today">
                <div class="block-head"><h4>今日建议任务</h4><span>可执行任务清单</span></div>
                <div class="today-grid">
                  <div><span>今日学习内容</span><strong>{{ todayPlan.study }}</strong></div>
                  <div><span>今日练习任务</span><strong>{{ todayPlan.practice }}</strong></div>
                  <div><span>今日复盘任务</span><strong>{{ todayPlan.review }}</strong></div>
                  <div><span>预计用时</span><strong>{{ todayPlan.duration }}</strong></div>
                </div>
                <div class="task-actions"><el-button type="primary" size="small" @click="markTodayDone">完成今日任务</el-button></div>
              </div>

              <div class="stage-card card-panel soft-card" ref="sectionRefs.stages">
                <div class="block-head"><h4>阶段路线</h4><span>支持折叠查看</span></div>
                <el-collapse v-model="openStages">
                  <el-collapse-item v-for="(stage, idx) in stages" :key="stage.title" :name="idx">
                    <template #title>
                      <div class="stage-title-row"><strong>{{ stage.title }}</strong><span>{{ stage.days }} 天 · {{ stage.goal }}</span></div>
                    </template>
                    <div class="stage-body">
                      <p><strong>阶段目标：</strong>{{ stage.goal }}</p>
                      <p><strong>学习重点：</strong>{{ stage.focus }}</p>
                      <p><strong>检测方式：</strong>{{ stage.check }}</p>
                      <ul><li v-for="task in stage.tasks" :key="task">{{ task }}</li></ul>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <div class="task-card card-panel soft-card" ref="sectionRefs.tasks">
                <div class="block-head"><h4>每日任务</h4><span>勾选后实时更新进度</span></div>
                <div class="task-toolbar"><el-button size="small" @click="markAllDone">全部标记完成</el-button><el-button size="small" plain @click="resetProgress">重置进度</el-button></div>
                <div class="task-list">
                  <label v-for="task in dailyTasks" :key="task.id" class="task-item" :class="{ done: task.done }"><el-checkbox v-model="task.done" @change="persistProgress">{{ task.title }}</el-checkbox><small>{{ task.desc }}</small></label>
                </div>
              </div>

              <div class="milestone-card card-panel soft-card" ref="sectionRefs.milestones">
                <div class="block-head"><h4>学习里程碑</h4><span>按进度展示状态</span></div>
                <el-timeline>
                  <el-timeline-item v-for="item in milestoneState" :key="item.title" :type="item.statusType"><strong>{{ item.title }}</strong><p>{{ item.desc }}</p><small>{{ item.status }}</small></el-timeline-item>
                </el-timeline>
              </div>

              <div class="advice-card card-panel soft-card" ref="sectionRefs.advice">
                <div class="block-head"><h4>路径建议</h4><span>执行与复盘建议</span></div>
                <p>{{ suggestionText }}</p>
              </div>

              <div class="markdown-wrapper" ref="sectionRefs.complete" v-if="rawMarkdown">
                <h4>完整内容</h4>
                <MarkdownViewer :content="rawMarkdown" />
              </div>

              <div class="next-actions card-panel soft-card">
                <h4>路径闭环操作</h4>
                <div class="next-actions-row">
                  <el-button type="primary" class="gradient-btn" @click="goNext('/resource', { topic: goal })">生成学习资源</el-button>
                  <el-button type="primary" plain @click="goNext('/quiz')">进入题目练习</el-button>
                  <el-button plain @click="goNext('/mistakes')">查看错题集</el-button>
                  <el-button plain @click="goNext('/analysis')">查看学情分析</el-button>
                </div>
              </div>

              <div class="history-card card-panel soft-card">
                <div class="history-head"><h4>最近学习路径</h4><span>最多保留 5 条</span></div>
                <div class="history-list">
                  <div v-for="item in history" :key="item.time + item.goal" class="history-item">
                    <div class="history-main">
                      <el-tag size="small" type="primary" effect="light">{{ item.intensity }}</el-tag>
                      <strong>{{ item.goal }}</strong>
                      <span>{{ item.days }} · 完成度 {{ item.completion }}% · {{ item.timeText }}</span>
                    </div>
                    <div class="history-actions"><el-button size="small" @click="restoreHistory(item)">查看</el-button><el-button size="small" type="primary" plain @click="continueHistory(item)">继续学习</el-button></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <ErrorState
          v-if="errorState"
          title="生成失败"
          :message="errorState"
          :has-retry="true"
          @retry="handleGeneratePath"
        >
          <template #default>
            <div class="error-actions"><el-button type="primary" @click="handleGeneratePath">重新生成</el-button><el-button plain @click="$router.push('/profile')">检查学习画像</el-button><el-button plain @click="$router.push('/analysis')">查看学情分析</el-button></div>
          </template>
        </ErrorState>
      </div>

      <aside class="path-side">
        <div class="card-panel section-card sticky-card">
          <h3 class="section-heading">规划建议</h3>
          <div class="suggest-box"><p>{{ recommendation }}</p></div>
        </div>
        <SuggestionList
          title="快捷模板"
          description="选择一个模板快速填充学习目标。"
          layout="vertical"
          :items="templates"
          item-label-key="title"
          item-desc-key="desc"
          item-key-key="key"
          @select="handleTemplateSelect"
        />
        <SuggestionList
          title="学习建议"
          description="根据当前画像给出的优先处理建议。"
          layout="vertical"
          :items="learningTips.map((tip, index) => ({ key: index, label: tip }))"
          empty-text="暂无学习建议"
          :disabled="true"
        />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/store/student'
import { generatePath as generatePathApi } from '@/api/index'
import MarkdownViewer from '@/components/MarkdownViewer.vue'
import SpeechInputButton from '@/components/SpeechInputButton.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SuggestionList from '@/components/common/SuggestionList.vue'
import { loadHistoryRecords, saveHistoryRecord } from '@/utils/historyRecords'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { useSpeechInputField } from '@/composables/useSpeechInputField'

const HISTORY_KEY = 'learnloop_path_history'
const PROGRESS_KEY = 'learnloop_path_progress'
const store = useStudentStore()
const route = useRoute()
const router = useRouter()
const goal = ref(store.student_profile.goal || '')
const speech = useSpeechInput()
const speechField = useSpeechInputField(speech, { getValue: () => goal.value, setValue: (val) => { goal.value = val } })
const days = ref(14)
const dailyTime = ref('1 小时')
const intensity = ref('标准提升')
const focus = ref(['基础概念', '重点难点', '错题修复'])
const loading = ref(false)
const loadingStep = ref(0)
const loadingProgress = ref(0)
const rawMarkdown = ref('')
const history = ref(loadHistoryRecords(HISTORY_KEY))
const dailyTasks = ref([])
const errorState = ref('')
const openStages = ref([0])
const sectionRefs = reactive({})

const daysOptions = [{ value: 3, label: '3 天冲刺' }, { value: 7, label: '7 天巩固' }, { value: 14, label: '14 天系统提升' }, { value: 30, label: '30 天长期规划' }]
const dailyTimeOptions = ['30 分钟', '1 小时', '2 小时', '自定义']
const intensityOptions = ['轻量复习', '标准提升', '强化训练']
const focusOptions = ['基础概念', '重点难点', '错题修复', '综合应用', '考前复习', '项目实践']
const templates = [ { key: '画像路径', title: '根据我的学习画像生成路径', desc: '使用当前画像自动推荐路径' }, { key: '补强路径', title: '根据薄弱点生成补强路径', desc: '聚焦薄弱知识点' }, { key: '7天', title: '7 天期末复习路径', desc: '适合短期冲刺' }, { key: '14天', title: '14 天系统提升路径', desc: '适合整体提升' }, { key: '错题路径', title: '错题修复专项路径', desc: '围绕错题闭环' }, { key: '项目实践', title: '项目实践入门路径', desc: '适合任务导向' } ]
const learningTips = computed(() => [ `建议先完成：${focus.value.slice(0, 3).join('、') || '基础概念'}`, `参考当前课程：${store.student_profile.course || '待补充'}`, `每周学习时间：${profileText.value.weekly_time}`, `薄弱点：${profileText.value.weak_points}` ])
const loadingStages = ['读取学习画像', '分析学习目标', '匹配薄弱知识点', '拆分阶段任务', '生成学习路径']

const hasProfile = computed(() => Boolean(store.student_profile.course || store.student_profile.goal || store.student_profile.level || (store.student_profile.weak_points || []).length))
const profileText = computed(() => ({ course: store.student_profile.course || '待补充', goal: store.student_profile.goal || '待补充', level: store.student_profile.level || '待补充', weekly_time: store.student_profile.weekly_time || '待补充', weak_points: (store.student_profile.weak_points || []).join('、') || '待补充' }))
const renderedContent = computed(() => Boolean(rawMarkdown.value))
const completionPercent = computed(() => dailyTasks.value.length ? Math.round((dailyTasks.value.filter(t => t.done).length / dailyTasks.value.length) * 100) : 0)
const priorityWeakPoint = computed(() => (store.student_profile.weak_points || [])[0] || '当前课程重点')
const nextTaskText = computed(() => dailyTasks.value.find(t => !t.done)?.title || '今日任务已完成')
const overviewText = computed(() => `总周期 ${days.value} 天 · 每日 ${dailyTime.value} · 强度 ${intensity.value} · 重点 ${focus.value.join('、') || '基础巩固'}`)
const recommendation = computed(() => { const level = store.student_profile.level || '一般'; const weak = (store.student_profile.weak_points || [])[0] || '当前课程重点'; return `当前基础水平为${level}，建议选择 ${days.value} 天${intensity.value}路径，优先补强 ${weak} 等知识点，并保持每日任务和错题复盘闭环。` })
const tips = computed(() => [ `建议先完成：${focus.value.slice(0, 3).join('、') || '基础概念'}`, `参考当前课程：${store.student_profile.course || '待补充'}`, `每周学习时间：${profileText.value.weekly_time}`, `薄弱点：${profileText.value.weak_points}` ])
const stages = computed(() => [ { title: '第 1 阶段：基础回顾', days: 3, goal: '梳理基础概念', focus: '基础概念与高频知识点', check: '小测与概念复述', tasks: ['阅读基础知识', '完成示例题', '整理知识卡片'] }, { title: '第 2 阶段：重点突破', days: 4, goal: '攻克薄弱点', focus: '薄弱知识点与错题', check: '专项练习', tasks: ['专题训练', '错题修复', '记录易错点'] }, { title: '第 3 阶段：综合训练', days: 4, goal: '提高迁移能力', focus: '综合应用与题型迁移', check: '综合测验', tasks: ['综合题训练', '限时练习', '回顾错题'] }, { title: '第 4 阶段：检测复盘', days: 3, goal: '完成自测复盘', focus: '检测与查漏补缺', check: '模拟测验', tasks: ['模拟测验', '复盘总结', '调整下一步计划'] } ])
const milestones = computed(() => [ { title: '完成基础概念复习', desc: '建立知识框架。' }, { title: '完成核心题型训练', desc: '强化解题能力。' }, { title: '完成综合测验', desc: '检验阶段成果。' } ])
const suggestionText = computed(() => `建议采用${intensity.value}策略，保持 ${dailyTime.value} / 天 的学习强度，优先处理 ${focus.value.join('、') || '基础概念'}。`)
const milestoneState = computed(() => milestones.value.map((item, idx) => {
  const progress = completionPercent.value
  const status = progress >= (idx + 1) * 30 ? '已完成' : progress >= idx * 30 ? '进行中' : '未开始'
  return { ...item, status, statusType: status === '已完成' ? 'success' : status === '进行中' ? 'primary' : 'info' }
}))
const todayPlan = computed(() => ({ study: dailyTasks.value[0]?.title || '完成基础概念复习', practice: dailyTasks.value[1]?.title || '完成主题练习', review: dailyTasks.value[2]?.title || '整理错题与复盘记录', duration: dailyTime.value }))
const sectionList = computed(() => [{ id: 'overview', label: '路径总览' }, { id: 'today', label: '今日任务' }, { id: 'stages', label: '阶段路线' }, { id: 'tasks', label: '每日任务' }, { id: 'milestones', label: '里程碑' }, { id: 'advice', label: '路径建议' }, { id: 'complete', label: '完整内容' }])
const activeSection = ref('overview')
const currentSectionId = ref('overview')
const qualityTags = computed(() => ['学习画像', '薄弱点', '任务推进', '执行闭环'])

function resetSpeechState() { speechField.resetSpeechState() }
function handlePathSpeechStart() { speechField.handleSpeechStart(goal.value) }
function handlePathSpeechInterim(text) { speechField.handleSpeechInterim(text) }
function handlePathSpeechResult(text) { speechField.handleSpeechResult(text) }
function handlePathSpeechStop() { speechField.handleSpeechStop() }
function handlePathSpeechError(message) { speechField.handleSpeechError(message); if (message) ElMessage.warning(message) }
function handleGoalInput(value) { goal.value = value; speechField.handleManualInput(value) }
function fillTemplate(key) { speechField.cancelSpeech(); if (key === '画像路径') { goal.value = store.student_profile.goal || '根据我的学习画像生成路径'; days.value = 14; intensity.value = '标准提升'; focus.value = ['基础概念', '重点难点', '错题修复'] } if (key === '补强路径') { goal.value = `补强${(store.student_profile.weak_points || []).join('、') || '薄弱点'}`; days.value = 14; intensity.value = '强化训练'; focus.value = ['基础概念', '错题修复', '综合应用'] } if (key === '7天') { goal.value = '期末复习'; days.value = 7; intensity.value = '轻量复习'; focus.value = ['重点难点', '错题修复', '考前复习'] } if (key === '14天') { goal.value = '系统提升'; days.value = 14; intensity.value = '标准提升'; focus.value = ['基础概念', '重点难点', '综合应用'] } if (key === '错题路径') { goal.value = '错题修复'; days.value = 7; intensity.value = '强化训练'; focus.value = ['错题修复', '基础概念', '综合应用'] } if (key === '项目实践') { goal.value = '项目实践入门'; days.value = 30; intensity.value = '标准提升'; focus.value = ['项目实践', '综合应用', '基础概念'] }; speechField.resetSpeechState() }
function handleTemplateSelect(item) { fillTemplate(item.key) }
function persistProgress() { localStorage.setItem(PROGRESS_KEY, JSON.stringify(dailyTasks.value)) }
function restoreProgress() { try { const raw = localStorage.getItem(PROGRESS_KEY); if (!raw) return; const list = JSON.parse(raw); if (Array.isArray(list)) dailyTasks.value = list } catch {} }
function copyText(text) { navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制到剪贴板')).catch(() => ElMessage.warning('复制失败，请手动选择内容复制')) }
function copyFullResult() { copyText(rawMarkdown.value) }
function copyCurrentSection() { const current = document.querySelector(`[data-section-id="${currentSectionId.value}"]`); copyText(current?.innerText || rawMarkdown.value) }
function startLoadingSequence() { loading.value = true; loadingStep.value = 0; loadingProgress.value = 10; const timers = [500, 900, 1300, 1700, 2100]; timers.forEach((delay, index) => window.setTimeout(() => { loadingStep.value = Math.min(index, 4); loadingProgress.value = [18, 38, 58, 78, 96][index] }, delay)); return () => { loading.value = false; loadingStep.value = 0; loadingProgress.value = 0 } }
function buildMockPath() { return [ { id: 1, title: '学习基础概念 30 分钟', desc: '梳理核心定义与知识图谱', done: false }, { id: 2, title: '完成主题练习 3 题', desc: '关注薄弱点相关题目', done: false }, { id: 3, title: '错题复盘并记录', desc: '总结错误原因与改进方法', done: false }, { id: 4, title: '综合自测 1 次', desc: '检查阶段学习效果', done: false } ] }
async function handleGeneratePath() { if (!goal.value.trim()) { ElMessage.warning('请输入学习目标'); return } errorState.value = ''; speechField.cancelSpeech(); const stop = startLoadingSequence(); try { const data = await generatePathApi(goal.value, days.value, store.student_profile); const normalized = normalizePathResponse(data); rawMarkdown.value = normalized.content; dailyTasks.value = normalized.tasks.length ? normalized.tasks.map((t, idx) => ({ id: idx + 1, title: t.title, desc: t.desc, done: false })) : buildMockPath(); persistProgress(); history.value = saveHistoryRecord(HISTORY_KEY, { goal: goal.value, days: `${days.value} 天`, intensity: intensity.value, time: Date.now(), timeText: new Date().toLocaleString(), completion: completionPercent.value, content: normalized.content, payload: normalized }, 5); ElMessage.success('路径生成成功'); nextTick(() => scrollToSection('overview')) } catch { errorState.value = '学习路径生成失败，请检查后端服务是否可用后重试。'; ElMessage.error('学习路径生成失败') } finally { stop() } }
function normalizePathResponse(data) { const content = typeof data === 'string' ? data : data?.content || data?.path || data?.plan || stringifyStages(data?.stages) || ''; const tasks = Array.isArray(data?.tasks) ? data.tasks : []; return { content, tasks, raw: data } }
function stringifyStages(stages) { if (!Array.isArray(stages)) return ''; return stages.map(stage => `## ${stage.title || '阶段'}\n${stage.desc || ''}`).join('\n\n') }
function setSectionRef(id, el) { if (el) sectionRefs[id] = el }
function scrollToSection(id) { activeSection.value = id; currentSectionId.value = id; sectionRefs[id]?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
function markTodayDone() { dailyTasks.value.slice(0, 1).forEach(task => (task.done = true)); persistProgress(); ElMessage.success('今日任务已完成') }
function markAllDone() { dailyTasks.value.forEach(task => (task.done = true)); persistProgress() }
function resetProgress() { dailyTasks.value.forEach(task => (task.done = false)); persistProgress(); ElMessage.success('进度已重置') }
function restoreHistory(item) { speechField.cancelSpeech(); goal.value = item.goal || goal.value; days.value = Number(String(item.days).replace(/\D/g, '')) || days.value; intensity.value = item.intensity || intensity.value; rawMarkdown.value = item.content || ''; currentSectionId.value = 'overview'; speechField.resetSpeechState(); nextTick(() => scrollToSection('overview')) }
function continueHistory(item) { restoreHistory(item); nextTick(() => scrollToSection('tasks')) }
function goNext(path, query = {}) { speechField.cancelSpeech(); router.push({ path, query }) }
watch(dailyTasks, persistProgress, { deep: true })
watch(() => store.student_profile, () => {}, { deep: true })
watch(() => route.query.goal, (val) => { if (typeof val === 'string' && val.trim()) { speechField.cancelSpeech(); goal.value = val; speechField.resetSpeechState() } }, { immediate: true })
onMounted(() => restoreProgress())
onBeforeUnmount(() => speechField.cancelSpeech())
</script>

<style scoped>
.page-hero { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(320px, .9fr); gap: 20px; padding: 28px; margin-bottom: 20px; background: linear-gradient(135deg, rgba(99,102,241,.10), rgba(59,130,246,.05)); }
.hero-kicker { font-size:12px; font-weight:700; color: var(--primary); letter-spacing:.08em; text-transform:uppercase; }
.hero-title { font-size: 30px; margin-top: 8px; color: var(--text-primary); }
.hero-desc { margin-top: 10px; color: var(--text-secondary); line-height:1.8; }
.hero-actions { display:flex; gap: 10px; flex-wrap:wrap; margin-top: 16px; }
.hero-summary { padding: 18px; }
.summary-title { font-weight:700; margin-bottom: 12px; }
.summary-grid { display:grid; grid-template-columns:1fr 1fr; gap: 10px; }
.summary-grid .full { grid-column: 1 / -1; }
.summary-grid div { background: rgba(255,255,255,.7); border:1px solid var(--border); border-radius: 12px; padding: 10px; }
.summary-grid span { display:block; font-size:12px; color: var(--text-secondary); margin-bottom: 4px; }
.summary-grid strong { font-size:13px; color: var(--text-primary); }
.path-layout { display:grid; grid-template-columns:minmax(0,1.8fr) minmax(290px,.9fr); gap: 20px; align-items:start; }
.section-card { margin-bottom: 16px; }
.panel-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom: 14px; }
.panel-head h3 { font-size: 18px; margin-bottom: 6px; }
.panel-head p { color: var(--text-secondary); line-height:1.6; font-size:13px; }
.inline-input-row { display:flex; align-items:center; gap:10px; }
.inline-input-row :deep(.el-input) { flex:1; }
.w100 { width: 100%; }
.form-actions { display:flex; gap: 10px; flex-wrap:wrap; margin-top: 12px; }
.loading-panel { min-height: 220px; }
.mt16 { margin-top: 16px; }
.help-card { padding-bottom: 18px; }
.starter-grid { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap: 12px; }
.starter-item { padding: 12px; border:1px solid var(--border); border-radius: 14px; background: rgba(255,255,255,.76); }
.starter-item strong { display:block; margin-bottom: 6px; }
.starter-item p { font-size: 13px; color: var(--text-secondary); line-height:1.6; }
.quality-card { padding: 14px; border-radius: 14px; background: rgba(99,102,241,.06); border:1px solid rgba(99,102,241,.12); margin-bottom: 14px; }
.quality-title { font-weight:700; margin-bottom: 8px; }
.quality-tags { display:flex; flex-wrap:wrap; gap: 8px; }
.quality-hint { margin-top: 10px; color: #b45309; font-size: 13px; }
.result-layout { display:grid; grid-template-columns: 180px minmax(0,1fr); gap: 14px; align-items:start; }
.toc-card { position: sticky; top: 90px; padding: 14px; }
.toc-head { font-weight:700; margin-bottom: 10px; }
.toc-item { width:100%; text-align:left; border:none; background: transparent; padding: 8px 10px; border-radius: 10px; cursor:pointer; color: var(--text-secondary); }
.toc-item.active, .toc-item:hover { background: rgba(99,102,241,.10); color: var(--primary-dark); }
.result-content { display:flex; flex-direction:column; gap: 12px; }
.result-block, .summary-panel, .task-card, .stage-card, .milestone-card, .advice-card { padding: 14px; scroll-margin-top: 100px; }
.block-head { display:flex; justify-content:space-between; gap: 10px; align-items:flex-start; margin-bottom: 8px; }
.block-head span { font-size:12px; color: var(--text-secondary); }
.summary-progress, .task-toolbar { margin-bottom: 10px; }
.progress-row { display:flex; justify-content:space-between; gap: 10px; color: var(--text-secondary); font-size: 13px; margin-bottom: 8px; }
.overview-grid, .today-grid { display:grid; grid-template-columns:1fr 1fr; gap: 10px; }
.overview-grid .full { grid-column: 1 / -1; }
.overview-grid div, .today-grid div { padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: #fff; }
.overview-grid span, .today-grid span { display:block; font-size:12px; color: var(--text-secondary); margin-bottom: 4px; }
.stage-title-row { display:flex; justify-content:space-between; gap: 12px; width:100%; }
.stage-body { color: var(--text-secondary); line-height:1.7; }
.stage-body ul { padding-left: 18px; }
.task-list { display:flex; flex-direction:column; gap: 10px; }
.task-item { display:block; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: #fff; }
.task-item.done { border-color: rgba(99,102,241,.25); background: rgba(99,102,241,.05); }
.task-item small { display:block; margin-top: 6px; color: var(--text-secondary); }
.bullet-list { padding-left: 18px; color: var(--text-secondary); line-height: 1.8; }
.markdown-wrapper { margin-top: 14px; }
.next-actions { margin-top: 14px; padding: 14px; }
.next-actions-row { display:flex; flex-wrap:wrap; gap: 10px; }
.history-card { margin-top: 14px; }
.history-head { display:flex; justify-content:space-between; margin-bottom: 10px; color: var(--text-secondary); }
.history-list { display:flex; flex-direction:column; gap: 10px; }
.history-item { display:flex; justify-content:space-between; gap: 12px; border:1px solid var(--border); background:#fff; border-radius: 12px; padding: 12px; }
.history-main { min-width: 0; display:flex; flex-direction:column; gap: 4px; }
.history-item strong { font-size: 14px; }
.history-item span, .history-item small { color: var(--text-secondary); }
.history-actions { display:flex; gap: 8px; flex-shrink:0; align-items:flex-start; }
.path-side { display:flex; flex-direction:column; gap: 14px; position: sticky; top: 92px; }
.template-list { display:flex; flex-direction:column; gap: 10px; }
.template-card { text-align:left; border:1px solid var(--border); background: rgba(255,255,255,.84); border-radius: 14px; padding: 12px; cursor:pointer; }
.template-card strong { display:block; margin-bottom: 6px; }
.template-card p, .suggestion-list { color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.suggestion-list { padding-left: 18px; display:flex; flex-direction:column; gap: 8px; }
.suggest-box { padding: 12px; border-radius: 12px; background: rgba(99,102,241,.06); color: var(--text-primary); line-height: 1.7; }
.soft-card { background: rgba(255,255,255,.84); }
.result-actions { display:flex; gap: 8px; flex-wrap:wrap; justify-content:flex-end; }
.error-card { border-color: rgba(239,68,68,.2); }
.error-actions { display:flex; gap: 10px; flex-wrap:wrap; margin-top: 12px; }
@media (max-width: 900px) { .page-hero, .path-layout, .result-grid, .result-layout, .starter-grid, .overview-grid, .today-grid { grid-template-columns: 1fr; } .path-side, .toc-card { position: static; } }
</style>
