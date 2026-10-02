<template>
  <div class="page-container">
    <PageHeader title="学习报告" subtitle="展示周学习趋势与建议" />
    <div class="stats-grid">
      <StatCard label="本周学习时长" :value="data.todayStudyMinutes * 5 + ' 分钟'" icon="Clock" />
      <StatCard label="平均正确率" :value="data.accuracy + '%'" icon="TrendCharts" />
      <StatCard label="优势知识点" :value="data.report.strengths.length" icon="Star" />
      <StatCard label="待提升知识点" :value="data.report.needsImprove.length" icon="Warning" />
    </div>

    <div class="grid-two">
      <SectionCard title="学习时长趋势" desc="近 6 天学习时间变化">
        <div ref="timeChart" class="chart-box"></div>
      </SectionCard>
      <SectionCard title="正确率趋势" desc="近 6 天练习正确率变化">
        <div ref="accChart" class="chart-box"></div>
      </SectionCard>
    </div>

    <div class="grid-two mt16">
      <SectionCard title="优势知识点" desc="学习中表现较好的内容">
        <el-tag v-for="item in data.report.strengths" :key="item" style="margin-right:8px;margin-bottom:8px">{{ item }}</el-tag>
      </SectionCard>
      <SectionCard title="待提升知识点" desc="建议继续巩固的内容">
        <el-tag v-for="item in data.report.needsImprove" :key="item" type="warning" style="margin-right:8px;margin-bottom:8px">{{ item }}</el-tag>
      </SectionCard>
    </div>

    <SectionCard title="本周总结" desc="给家长的整体反馈" style="margin-top:16px">
      <el-alert type="success" show-icon :closable="false" :title="data.report.weeklySummary" />
    </SectionCard>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'; import * as echarts from 'echarts'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import StatCard from '@/components/StatCard.vue'; import { mockParentChildData as data } from '@/mock/roleData'; const timeChart=ref(); const accChart=ref(); onMounted(()=>{ echarts.init(timeChart.value).setOption({ xAxis:{type:'category',data:['周一','周二','周三','周四','周五','周六']}, yAxis:{type:'value'}, series:[{type:'bar',data:[40,55,35,60,70,66]}]}); echarts.init(accChart.value).setOption({ xAxis:{type:'category',data:['周一','周二','周三','周四','周五','周六']}, yAxis:{type:'value',max:100}, series:[{type:'line',smooth:true,data:[62,68,72,79,84,86]}]}) })
</script>
<style scoped>.stats-grid,.grid-two{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.grid-two{grid-template-columns:repeat(2,1fr);margin-top:16px}.chart-box{height:260px}.mt16{margin-top:16px}@media(max-width:900px){.stats-grid,.grid-two{grid-template-columns:1fr}}</style>
