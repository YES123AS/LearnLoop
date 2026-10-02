<template>
  <div class="page-container">
    <PageHeader title="家长工作台" subtitle="查看孩子学习概况与老师反馈" />
    <div class="stats-grid">
      <StatCard label="今日学习时长" :value="data.todayStudyMinutes + ' 分钟'" icon="Clock" />
      <StatCard label="本周任务完成" :value="data.weeklyFinishedTasks" icon="Document" />
      <StatCard label="当前正确率" :value="data.accuracy + '%'" icon="TrendCharts" />
      <StatCard label="薄弱知识点" :value="data.weakPoints.length" icon="Warning" />
    </div>

    <div class="grid-two">
      <SectionCard title="正确率变化" desc="近一周学习表现趋势">
        <div ref="trendChart" class="chart-box"></div>
      </SectionCard>
      <SectionCard title="教师最新反馈" desc="最近来自老师的提醒与建议">
        <el-empty v-if="feedback.length===0" description="暂无反馈" />
        <el-timeline v-else>
          <el-timeline-item v-for="item in feedback" :key="item.id" :timestamp="item.time">{{ item.content }}</el-timeline-item>
        </el-timeline>
      </SectionCard>
    </div>

    <SectionCard title="家长待关注事项" desc="建议优先关注的内容" style="margin-top:16px">
      <el-alert type="warning" show-icon :closable="false" :title="data.warningText" />
    </SectionCard>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'; import * as echarts from 'echarts'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import StatCard from '@/components/StatCard.vue'; import { mockParentChildData as data, mockTeacherFeedback as feedback } from '@/mock/roleData'; const trendChart=ref(); onMounted(()=>{ echarts.init(trendChart.value).setOption({ xAxis:{type:'category',data:['周一','周二','周三','周四','周五','周六']}, yAxis:{type:'value',max:100}, series:[{type:'line',smooth:true,data:data.report.trend}] }) })
</script>
<style scoped>.stats-grid,.grid-two{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.grid-two{grid-template-columns:repeat(2,1fr);margin-top:16px}.chart-box{height:280px}@media(max-width:900px){.stats-grid,.grid-two{grid-template-columns:1fr}}</style>
