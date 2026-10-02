<template>
  <div class="page-container">
    <PageHeader title="班级学情分析" subtitle="正确率、薄弱知识点与掌握度排行" />
    <div class="stats-grid">
      <StatCard label="班级平均正确率" :value="'83%'" icon="TrendCharts" />
      <StatCard label="薄弱知识点数" :value="mockClassStats.weakKnowledgePoints.length" icon="Warning" />
      <StatCard label="高掌握学生数" :value="2" icon="User" />
      <StatCard label="分析结论" value="稳定" icon="DataAnalysis" />
    </div>
    <div class="grid-two">
      <SectionCard title="知识点薄弱排行" desc="班级共性问题">
        <div ref="weakChart" class="chart-box"></div>
      </SectionCard>
      <SectionCard title="学生掌握度排行" desc="按正确率排序">
        <div ref="masterChart" class="chart-box"></div>
      </SectionCard>
    </div>
    <SectionCard title="分析结论" desc="基于当前 mock 数据生成的教师建议" style="margin-top:16px">
      <el-alert type="info" show-icon :closable="false" title="班级整体处于稳步上升阶段，建议继续围绕 LZW、JPEG 压缩开展分层练习，并对学习节奏偏慢的学生进行周内提醒。" />
    </SectionCard>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'; import * as echarts from 'echarts'; import PageHeader from '@/components/PageHeader.vue'; import StatCard from '@/components/StatCard.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockClassStats, mockStudents } from '@/mock/roleData'; const weakChart=ref(); const masterChart=ref(); onMounted(()=>{ echarts.init(weakChart.value).setOption({ xAxis:{type:'category',data:mockClassStats.weakKnowledgePoints.map(i=>i.name)}, yAxis:{type:'value'}, series:[{type:'bar',data:mockClassStats.weakKnowledgePoints.map(i=>i.value)}]}); echarts.init(masterChart.value).setOption({ xAxis:{type:'category',data:mockStudents.map(i=>i.name)}, yAxis:{type:'value',max:100}, series:[{type:'bar',data:mockStudents.map(i=>i.accuracy)}]}) })
</script>
<style scoped>.stats-grid,.grid-two{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.grid-two{grid-template-columns:repeat(2,1fr);margin-top:16px}.chart-box{height:280px}@media(max-width:900px){.stats-grid,.grid-two{grid-template-columns:1fr}}</style>
