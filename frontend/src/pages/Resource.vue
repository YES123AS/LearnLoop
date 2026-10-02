<template>
  <div class="page-container resource-page">
    <section class="page-hero card-panel">
      <div class="hero-copy">
        <div class="hero-kicker">LearnLoopAI · 资源生成工作台</div>
        <h1 class="hero-title">学习资源生成</h1>
        <p class="hero-desc">基于学习画像、课程主题与薄弱知识点，生成结构化学习资料、重点总结与练习建议。</p>
        <div class="hero-actions">
          <el-button type="primary" class="gradient-btn" @click="$router.push('/profile')">完善学习画像</el-button>
          <el-button plain @click="$router.push('/quiz')">去生成题目</el-button>
          <el-button plain @click="$router.push('/path')">去学习路径</el-button>
        </div>
      </div>
      <div class="hero-summary card-panel soft-card">
        <div class="summary-title">当前画像摘要</div>
        <div class="summary-grid">
          <div><span>当前课程</span><strong>{{ profileText.course }}</strong></div>
          <div><span>学习目标</span><strong>{{ profileText.goal }}</strong></div>
          <div><span>基础水平</span><strong>{{ profileText.level }}</strong></div>
          <div><span>薄弱点</span><strong>{{ profileText.weak_points }}</strong></div>
        </div>
        <el-alert v-if="!hasProfile" title="请先完善学习画像，以获得更精准的资源生成结果。" type="warning" :closable="false" show-icon />
      </div>
    </section>

    <div class="resource-layout">
      <div class="resource-main">
        <div class="card-panel section-card">
          <div class="panel-head">
            <div>
              <h3>生成配置</h3>
              <p>输入主题并选择资源类型、深度与风格，生成更贴合你的学习资料。</p>
            </div>
            <el-tag type="primary" effect="light">支持语音输入</el-tag>
          </div>
          <el-form label-position="top" class="config-form">
            <el-form-item label="学习主题">
              <div class="inline-input-row">
                <el-input :model-value="topic" placeholder="输入需要生成的资源主题" @update:model-value="handleTopicInput" @keyup.enter="handleGenerateResources" />
                <SpeechInputButton size="small" :text="false" :model-value="topic" @start="handleResourceSpeechStart" @interim="handleResourceSpeechInterim" @result="handleResourceSpeechResult" @stop="handleResourceSpeechStop" @error="handleResourceSpeechError" />
              </div>
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="资源类型"><el-select v-model="resourceType" class="w100"><el-option v-for="opt in resourceTypeOptions" :key="opt" :label="opt" :value="opt" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="内容深度"><el-select v-model="depth" class="w100"><el-option v-for="opt in depthOptions" :key="opt" :label="opt" :value="opt" /></el-select></el-form-item></el-col>
            </el-row>
            <el-form-item label="输出风格"><el-radio-group v-model="style"><el-radio-button v-for="opt in styleOptions" :key="opt" :label="opt" /></el-radio-group></el-form-item>
            <div class="switch-row"><el-switch v-model="useWeakPoints" /><span>结合我的薄弱知识点生成</span></div>
            <div class="switch-row"><el-switch v-model="includePractice" /><span>附带练习建议</span></div>
            <div class="form-actions"><el-button type="primary" class="gradient-btn" :loading="loading" @click="handleGenerateResources">生成资源</el-button><el-button plain @click="fillTemplate('薄弱点复习')">使用薄弱点模板</el-button></div>
          </el-form>
        </div>

        <EmptyState
          v-if="!renderedContent && !loading"
          title="你可以这样开始"
          description="例如：LZW 算法、JPEG 压缩、神经网络基础。输入课程主题后，选择资源类型即可生成结构化学习资料。"
          :has-action="false"
        />

        <LoadingState
          v-if="loading"
          title="生成中"
          description="正在结合学习画像生成个性化资源。"
          loading-text="资源生成中，请稍候..."
          :stage-text="loadingStages[loadingStep] || ''"
        />

        <div v-if="renderedContent" class="card-panel section-card result-card">
          <div class="quality-card">
            <div class="quality-title">本资源已结合：</div>
            <div class="quality-tags">
              <el-tag v-for="t in qualityTags" :key="t" effect="light">{{ t }}</el-tag>
            </div>
            <p v-if="!hasProfile" class="quality-hint">当前资源未充分结合画像，建议先完善学习画像。</p>
          </div>

          <div class="panel-head">
            <div>
              <h3>生成结果</h3>
              <p>资源内容已按模块结构化展示，可复制、重生成或继续进入学习闭环。</p>
            </div>
            <div class="result-actions">
              <el-button size="small" @click="copyFullResult">复制完整资源</el-button>
              <el-button size="small" @click="copyCurrentSection">复制当前模块</el-button>
              <el-button size="small" type="primary" @click="handleGenerateResources">重新生成</el-button>
              <el-button size="small" plain @click="$router.push('/quiz')">去生成题目</el-button>
              <el-button size="small" plain @click="$router.push('/path')">去学习路径</el-button>
            </div>
          </div>

          <div class="result-layout">
            <aside class="toc-card card-panel soft-card">
              <div class="toc-head">资源目录</div>
              <button v-for="item in resultSections" :key="item.id" class="toc-item" :class="{ active: activeSection === item.id }" @click="scrollToSection(item.id)">{{ item.label }}</button>
            </aside>

            <div class="result-content">
              <div v-for="section in renderedSections" :key="section.id" :ref="el => setSectionRef(section.id, el)" class="result-block card-panel soft-card" :data-section-id="section.id">
                <div class="block-head"><h4>{{ section.title }}</h4><span>{{ section.desc }}</span></div>
                <div class="block-tags" v-if="section.tags?.length"><el-tag v-for="tag in section.tags" :key="tag" size="small" effect="light">{{ tag }}</el-tag></div>
                <p class="block-content">{{ section.content }}</p>
                <div class="block-actions"><el-button size="small" @click="copySection(section.id)">复制本模块</el-button></div>
              </div>
            </div>
          </div>

          <div class="markdown-wrapper" v-if="rawMarkdown">
            <h4>完整内容</h4>
            <MarkdownViewer :content="rawMarkdown" />
          </div>

          <div class="next-actions card-panel soft-card">
            <h4>下一步学习操作</h4>
            <div class="next-actions-row">
              <el-button type="primary" class="gradient-btn" @click="goNext('/quiz', { topic: topic })">生成配套练习</el-button>
              <el-button type="primary" plain @click="goNext('/path', { goal: topic })">生成学习路径</el-button>
              <el-button plain @click="goNext('/chat')">进入智能辅导</el-button>
              <el-button plain @click="goNext('/analysis')">查看学情分析</el-button>
            </div>
          </div>

          <div class="history-card card-panel soft-card">
            <div class="history-head"><h4>最近生成资源</h4><span>最多保留 5 条</span></div>
            <div class="history-list">
              <div v-for="item in history" :key="item.time + item.topic" class="history-item">
                <div class="history-main">
                  <el-tag size="small" type="primary" effect="light">{{ item.resourceType }}</el-tag>
                  <strong>{{ item.topic }}</strong>
                  <span>{{ item.timeText }}</span>
                  <small>{{ item.summary }}</small>
                </div>
                <div class="history-actions"><el-button size="small" @click="restoreHistory(item)">查看</el-button><el-button size="small" type="primary" plain @click="rerunHistory(item)">再生成</el-button></div>
              </div>
            </div>
          </div>
        </div>

        <ErrorState
          v-if="errorState"
          title="生成失败"
          :message="errorState"
          :has-retry="true"
          @retry="handleGenerateResources"
        >
          <template #default>
            <div class="error-actions"><el-button type="primary" @click="handleGenerateResources">重新生成</el-button><el-button plain @click="$router.push('/profile')">检查学习画像</el-button><el-button plain @click="$router.push('/chat')">检查后端服务提示</el-button></div>
          </template>
        </ErrorState>
      </div>

      <aside class="resource-side">
        <SuggestionList
          title="智能推荐主题"
          description="点击推荐主题可快速回填资源主题。"
          layout="inline"
          :items="recommendationTopics.map((item) => ({ key: item, label: item }))"
          item-label-key="label"
          item-key-key="key"
          @select="(item) => useTopic(item.key)"
        />
        <SuggestionList
          title="快捷模板"
          description="选择模板快速填充资源主题。"
          layout="vertical"
          :items="templates"
          item-label-key="title"
          item-desc-key="desc"
          item-key-key="key"
          @select="(item) => fillTemplate(item.key)"
        />
        <div class="card-panel section-card sticky-card">
          <h3 class="section-heading">建议与提示</h3>
          <ul class="suggestion-list"><li v-for="tip in tips" :key="tip">{{ tip }}</li></ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/store/student'
import { generateResource as generateResourceApi } from '@/api/index'
import MarkdownViewer from '@/components/MarkdownViewer.vue'
import SpeechInputButton from '@/components/SpeechInputButton.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SuggestionList from '@/components/common/SuggestionList.vue'
import { loadHistoryRecords, saveHistoryRecord } from '@/utils/historyRecords'
import { parseMarkdownSections, stringifySections } from '@/utils/resultFormat'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { useSpeechInputField } from '@/composables/useSpeechInputField'

const HISTORY_KEY = 'learnloop_resource_history'
const store = useStudentStore()
const router = useRouter()
const topic = ref('')
const speech = useSpeechInput()
const speechField = useSpeechInputField(speech, { getValue: () => topic.value, setValue: (val) => { topic.value = val } })
const resourceType = ref('知识讲解')
const depth = ref('标准掌握')
const style = ref('结构化笔记')
const useWeakPoints = ref(true)
const includePractice = ref(true)
const loading = ref(false)
const loadingStep = ref(0)
const loadingProgress = ref(0)
const rawMarkdown = ref('')
const history = ref(loadHistoryRecords(HISTORY_KEY))
const resultPayload = ref(null)
const errorState = ref('')
const sectionRefs = ref({})
const activeSection = ref('overview')
const currentSectionId = ref('overview')

const resourceTypeOptions = ['知识讲解', '重点总结', '复习提纲', '案例解析', '练习指导', '考前速记']
const depthOptions = ['入门理解', '标准掌握', '深入拓展']
const styleOptions = ['通俗解释', '结构化笔记', '例题驱动', '对比总结']
const templates = [
  { key: '薄弱点复习', title: '根据我的薄弱点生成复习资料', desc: '快速聚焦薄弱知识点' },
  { key: '当前课程总结', title: '生成当前课程重点总结', desc: '适合课堂复盘' },
  { key: '考试提纲', title: '生成考试复习提纲', desc: '适合考前冲刺' },
  { key: '概念辨析', title: '生成概念辨析资料', desc: '适合理清易混概念' },
  { key: '案例讲解', title: '生成案例讲解资料', desc: '适合理解应用' }
]
const loadingStages = ['读取学习画像', '分析知识薄弱点', '组织内容结构', '生成个性化结果']

const recommendationTopics = computed(() => { const weak = store.student_profile.weak_points || []; const base = [`${store.student_profile.course || '当前课程'}基础概念`, '图像压缩与编码', '特征提取与模式识别', '神经网络基础', '错题高频知识点复习']; return [...new Set([...weak.map(item => `${item}复习`), ...base])].slice(0, 6) })
const tips = computed(() => [`结合薄弱点：${(store.student_profile.weak_points || []).join('、') || '暂无'}`, `当前课程：${store.student_profile.course || '待补充'}`, `学习目标：${store.student_profile.goal || '待补充'}`, `建议优先生成“重点总结 + 练习指导”组合`])
const hasProfile = computed(() => Boolean(store.student_profile.course || store.student_profile.goal || (store.student_profile.weak_points || []).length))
const profileText = computed(() => ({ course: store.student_profile.course || '待补充', goal: store.student_profile.goal || '待补充', level: store.student_profile.level || '待补充', weak_points: (store.student_profile.weak_points || []).join('、') || '待补充' }))
const renderedContent = computed(() => Boolean(resultPayload.value || rawMarkdown.value))
const resultSections = computed(() => [{ id: 'overview', label: '资源概览' }, { id: 'core', label: '核心知识讲解' }, { id: 'keyPoints', label: '重点难点' }, { id: 'examples', label: '示例与案例' }, { id: 'suggestion', label: '学习建议' }, { id: 'practice', label: '练习建议' }, { id: 'complete', label: '完整内容' }])
const parsedSections = computed(() => parseMarkdownSections(rawMarkdown.value || stringifyPayload(resultPayload.value)))
const resultMeta = computed(() => `主题：${topic.value || '未填写'} · 类型：${resourceType.value} · 深度：${depth.value}`)
const qualityTags = computed(() => ['学习画像', '薄弱点', '练习建议', '结构化输出'])
const renderedSections = computed(() => [
  { id: 'overview', title: '资源概览', desc: '面向当前主题的整体说明', content: resultMeta.value, tags: ['概览'] },
  { id: 'core', title: '核心知识讲解', desc: '学习核心概念和原理', content: parsedSections.value.core || parsedSections.value.overview || '暂无结构化内容，以下为原始结果。', tags: [resourceType.value, depth.value] },
  { id: 'keyPoints', title: '重点难点', desc: '理解过程中最需要关注的地方', content: parsedSections.value.keyPoints || parsedSections.value.difficulty || '暂无结构化内容。', tags: ['重点'] },
  { id: 'examples', title: '示例与案例', desc: '通过示例帮助理解和迁移', content: parsedSections.value.examples || parsedSections.value.cases || '暂无结构化内容。', tags: ['案例'] },
  { id: 'suggestion', title: '学习建议', desc: '学习顺序与方法建议', content: parsedSections.value.suggestion || parsedSections.value.studyAdvice || '暂无结构化内容。', tags: ['建议'] },
  { id: 'practice', title: '练习建议', desc: '用于巩固理解的任务建议', content: parsedSections.value.practice || (includePractice.value ? '建议结合错题与主题练习进行巩固。' : '已关闭练习建议。'), tags: ['练习'] },
  { id: 'complete', title: '完整内容', desc: '原始内容与 Markdown 展示', content: rawMarkdown.value || '暂无内容', tags: ['全文'] }
])

function resetSpeechState() { speechField.resetSpeechState() }
function handleResourceSpeechStart() { speechField.handleSpeechStart(topic.value) }
function handleResourceSpeechInterim(text) { speechField.handleSpeechInterim(text) }
function handleResourceSpeechResult(text) { speechField.handleSpeechResult(text) }
function handleResourceSpeechStop() { speechField.handleSpeechStop() }
function handleResourceSpeechError(message) { speechField.handleSpeechError(message); if (message) ElMessage.warning(message) }
function handleTopicInput(value) { topic.value = value; speechField.handleManualInput(value) }
function handleTopicSelect(item) { useTopic(item.key) }
function handleTemplateSelect(item) { fillTemplate(item.key) }
function useTopic(value) { speechField.cancelSpeech(); topic.value = value; speechField.resetSpeechState() }
function fillTemplate(key) { speechField.cancelSpeech(); if (key === '薄弱点复习') { topic.value = `基于${profileText.value.weak_points}生成复习资料`; resourceType.value = '重点总结'; style.value = '结构化笔记' } if (key === '当前课程总结') { topic.value = `${profileText.value.course}重点总结`; resourceType.value = '重点总结'; style.value = '结构化笔记' } if (key === '考试提纲') { topic.value = `${profileText.value.course}考试复习提纲`; resourceType.value = '复习提纲'; style.value = '通俗解释' } if (key === '概念辨析') { topic.value = `${profileText.value.course}概念辨析`; resourceType.value = '知识讲解'; style.value = '对比总结' } if (key === '案例讲解') { topic.value = `${profileText.value.course}案例讲解`; resourceType.value = '案例解析'; style.value = '例题驱动' }; speechField.resetSpeechState() }
function stringifyPayload(payload) { if (!payload) return ''; return [payload.overview, payload.core, payload.keyPoints, payload.examples, payload.suggestion, payload.practice].filter(Boolean).join('\n\n') }
function setSectionRef(id, el) { if (el) sectionRefs.value[id] = el }
function scrollToSection(id) { activeSection.value = id; currentSectionId.value = id; sectionRefs.value[id]?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
function getClipboardText(sectionId) { if (sectionId === 'complete') return rawMarkdown.value || stringifyPayload(resultPayload.value); const s = renderedSections.value.find(x => x.id === sectionId); return s ? `${s.title}\n\n${s.content}` : '' }
function copyText(text, ok = '已复制到剪贴板', fail = '复制失败，请手动选择内容复制') { navigator.clipboard.writeText(text).then(() => ElMessage.success(ok)).catch(() => ElMessage.warning(fail)) }
function copyFullResult() { copyText(getClipboardText('complete')) }
function copyCurrentSection() { copyText(getClipboardText(currentSectionId.value)) }
function copySection(id) { copyText(getClipboardText(id)); currentSectionId.value = id }
function syncHistory(item) { history.value = saveHistoryRecord(HISTORY_KEY, item, 5) }
function restoreHistory(item) { speechField.cancelSpeech(); topic.value = item.topic || topic.value; resourceType.value = item.resourceType || resourceType.value; depth.value = item.depth || depth.value; style.value = item.style || style.value; rawMarkdown.value = item.content || ''; resultPayload.value = item.payload || null; currentSectionId.value = 'overview'; speechField.resetSpeechState(); nextTick(() => scrollToSection('overview')) }
function rerunHistory(item) { restoreHistory(item); handleGenerateResources() }
function goNext(path, query = {}) { router.push({ path, query }) }
function startLoadingSequence() { loading.value = true; loadingStep.value = 0; loadingProgress.value = 10; const timers = [500, 900, 1300, 1700, 2100]; timers.forEach((delay, index) => window.setTimeout(() => { loadingStep.value = Math.min(index, 4); loadingProgress.value = [18, 38, 58, 78, 96][index] }, delay)); return () => { loading.value = false; loadingStep.value = 0; loadingProgress.value = 0 } }
async function handleGenerateResources() { if (!topic.value.trim()) { ElMessage.warning('请输入资源主题'); return } errorState.value = ''; speechField.cancelSpeech(); const stop = startLoadingSequence(); try { const data = await generateResourceApi(topic.value, resourceType.value, store.student_profile); const normalized = normalizeResourceResponse(data); resultPayload.value = normalized; rawMarkdown.value = normalized.content; store.setCurrentResource(normalized.content); syncHistory({ topic: topic.value, resourceType: resourceType.value, depth: depth.value, style: style.value, time: Date.now(), timeText: new Date().toLocaleString(), summary: normalized.summary, content: normalized.content, payload: normalized }); ElMessage.success('资源生成成功'); nextTick(() => scrollToSection('overview')) } catch { errorState.value = '资源生成失败，请检查后端服务是否可用后重试。'; ElMessage.error('资源生成失败') } finally { stop() } }
onMounted(() => { topic.value = store.student_profile.goal || '' })
onBeforeUnmount(() => speechField.cancelSpeech())
function normalizeResourceResponse(data) { const content = typeof data === 'string' ? data : data?.content || data?.resource || stringifySections(data?.sections) || data?.markdown || ''; return { topic: topic.value, resourceType: resourceType.value, depth: depth.value, style: style.value, content, summary: data?.summary || content.slice(0, 120) || '资源已生成', sections: data?.sections || null, raw: data } }
watch(() => store.student_profile, () => {}, { deep: true })
watch(history, (val) => { localStorage.setItem('learnloop_resource_history', JSON.stringify(val)) }, { deep: true })
onMounted(() => { history.value = getHistory(HISTORY_KEY) })
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
.summary-grid div { background: rgba(255,255,255,.7); border:1px solid var(--border); border-radius: 12px; padding: 10px; }
.summary-grid span { display:block; font-size:12px; color: var(--text-secondary); margin-bottom: 4px; }
.summary-grid strong { font-size:13px; color: var(--text-primary); }
.resource-layout { display:grid; grid-template-columns:minmax(0,1.8fr) minmax(290px,.9fr); gap: 20px; align-items:start; }
.section-card { margin-bottom: 16px; }
.panel-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom: 14px; }
.panel-head h3 { font-size: 18px; margin-bottom: 6px; }
.panel-head p { color: var(--text-secondary); line-height:1.6; font-size:13px; }
.inline-input-row { display:flex; align-items:center; gap:10px; }
.inline-input-row :deep(.el-input) { flex:1; }
.w100 { width: 100%; }
.switch-row { display:flex; align-items:center; gap: 10px; margin-bottom: 10px; color: var(--text-secondary); }
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
.result-block { padding: 14px; scroll-margin-top: 100px; }
.block-head { display:flex; justify-content:space-between; gap: 10px; align-items:flex-start; margin-bottom: 8px; }
.block-head span { font-size:12px; color: var(--text-secondary); }
.block-tags { display:flex; flex-wrap:wrap; gap: 8px; margin-bottom: 8px; }
.block-content { color: var(--text-secondary); line-height:1.7; white-space: pre-wrap; }
.block-actions { margin-top: 10px; }
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
.resource-side { display:flex; flex-direction:column; gap: 14px; position: sticky; top: 92px; }
.template-list { display:flex; flex-direction:column; gap: 10px; }
.template-card { text-align:left; border:1px solid var(--border); background: rgba(255,255,255,.84); border-radius: 14px; padding: 12px; cursor:pointer; }
.template-card strong { display:block; margin-bottom: 6px; }
.template-card p, .suggestion-list { color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.suggestion-list { padding-left: 18px; display:flex; flex-direction:column; gap: 8px; }
.clickable-tag { cursor:pointer; }
.soft-card { background: rgba(255,255,255,.84); }
.result-actions { display:flex; gap: 8px; flex-wrap:wrap; justify-content:flex-end; }
.error-card { border-color: rgba(239,68,68,.2); }
.error-actions { display:flex; gap: 10px; flex-wrap:wrap; margin-top: 12px; }
@media (max-width: 900px) { .page-hero, .resource-layout, .result-grid, .result-layout, .starter-grid { grid-template-columns: 1fr; } .resource-side, .toc-card { position: static; } }
</style>
