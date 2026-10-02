<template>
  <div class="page-container teacher-page">
    <PageHeader title="教师工作台" subtitle="班级学情、督导任务与批改反馈一体化管理" />

    <div class="stats-grid">
      <StatCard label="班级学生总数" :value="mockClassStats.totalStudents" icon="User" />
      <StatCard label="今日待批改任务" :value="mockClassStats.pendingReviews" icon="EditPen" />
      <StatCard label="薄弱知识点" :value="mockClassStats.weakKnowledgePoints.length" icon="Warning" />
      <StatCard label="近期异常学生" :value="mockClassStats.abnormalStudents.length" icon="TrendCharts" />
    </div>

    <div class="grid-two">
      <SectionCard title="班级学习趋势图" desc="近 6 次测验正确率变化">
        <div ref="trendChartEl" class="chart-box"></div>
      </SectionCard>
      <SectionCard title="待处理事项" desc="教师近期需要关注的任务">
        <el-empty v-if="pendingTasks.length === 0" description="暂无待处理事项" />
        <div v-else class="todo-list">
          <div v-for="task in pendingTasks" :key="task.label" class="todo-item">
            <strong>{{ task.label }}</strong>
            <span>{{ task.desc }}</span>
          </div>
        </div>
      </SectionCard>
    </div>

    <div class="grid-two mt16">
      <SectionCard title="异常学生提醒" desc="需要优先督导的学生">
        <div class="student-tags">
          <el-tag v-for="item in mockClassStats.abnormalStudents" :key="item.id" effect="light" type="warning">{{ item.name }} · {{ item.reason }}</el-tag>
        </div>
      </SectionCard>
      <SectionCard title="高频薄弱知识点" desc="班级共性问题聚焦">
        <el-table :data="mockClassStats.weakKnowledgePoints" size="small" border>
          <el-table-column prop="name" label="知识点" />
          <el-table-column prop="value" label="出现次数" width="100" />
        </el-table>
      </SectionCard>
    </div>

    <SectionCard title="快捷操作入口" desc="快速进入核心管理页面">
      <div class="quick-grid">
        <router-link v-for="item in quickLinks" :key="item.path" :to="item.path" class="quick-card">
          <strong>{{ item.label }}</strong>
          <span>{{ item.desc }}</span>
        </router-link>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import PageHeader from '@/components/PageHeader.vue'
import StatCard from '@/components/StatCard.vue'
import SectionCard from '@/components/SectionCard.vue'
import { mockClassStats } from '@/mock/roleData'
import { APP_ROUTES } from '@/constants/routes'

const trendChartEl = ref()
const pendingTasks = [
  { label: '批改 7 份课后题', desc: '今晚 22:00 前完成' },
  { label: '跟进 2 名异常学生', desc: '学习节奏波动明显' },
  { label: '发布周末复习任务', desc: '覆盖 LZW 与 JPEG 压缩' }
]
const quickLinks = [
  { path: APP_ROUTES.teacherStudents, label: '学生管理', desc: '查看班级学生状态' },
  { path: APP_ROUTES.teacherTasks, label: '任务督导', desc: '发布并跟踪作业任务' },
  { path: APP_ROUTES.teacherReview, label: '批改反馈', desc: '提交评分与评语' },
  { path: APP_ROUTES.teacherAnalysis, label: '班级分析', desc: '查看班级学情趋势' }
]

onMounted(() => {
  const chart = echarts.init(trendChartEl.value)
  chart.setOption({
    grid: { left: 30, right: 18, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: ['第1次', '第2次', '第3次', '第4次', '第5次', '第6次'] },
    yAxis: { type: 'value', max: 100 },
    series: [{ type: 'line', smooth: true, data: mockClassStats.accuracyTrend, areaStyle: {} }]
  })
})
</script>

<style scoped>
.stats-grid,.grid-two{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.grid-two{grid-template-columns:repeat(2,1fr)}.mt16{margin-top:16px}.chart-box{height:280px}.todo-list{display:grid;gap:12px}.todo-item{padding:14px;border:1px solid var(--border);border-radius:14px;background:var(--bg-light);display:flex;flex-direction:column;gap:4px}.todo-item span{color:var(--text-secondary);font-size:13px}.student-tags{display:flex;flex-wrap:wrap;gap:10px}.quick-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.quick-card{padding:16px;border:1px solid var(--border);border-radius:14px;background:var(--bg-light);display:flex;flex-direction:column;gap:6px}.quick-card span{color:var(--text-secondary);font-size:13px}.teacher-page{padding-bottom:16px}@media(max-width:1200px){.stats-grid,.grid-two,.quick-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:768px){.stats-grid,.grid-two,.quick-grid{grid-template-columns:1fr}}</style>
