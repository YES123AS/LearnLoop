<template>
  <div class="page-container">
    <PageHeader title="孩子学习概览" subtitle="只读查看学习状态" />
    <div class="grid-two">
      <SectionCard title="学习进度" desc="家长只能查看，不可修改">
        <el-progress :percentage="data.progress" />
        <p class="sub">当前状态：{{ data.warningText }}</p>
      </SectionCard>
      <SectionCard title="错题趋势" desc="最近错题变化">
        <div ref="chartEl" class="chart-box"></div>
      </SectionCard>
    </div>
    <SectionCard title="最近练习记录" desc="查看最近的做题情况" style="margin-top:16px">
      <el-table :data="data.recentRecords" stripe>
        <el-table-column prop="topic" label="知识点" />
        <el-table-column prop="type" label="题型" />
        <el-table-column prop="time" label="时间" />
        <el-table-column label="结果"><template #default="{ row }"><el-tag :type="row.correct ? 'success' : 'danger'">{{ row.correct ? '正确' : '错误' }}</el-tag></template></el-table-column>
      </el-table>
    </SectionCard>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'; import * as echarts from 'echarts'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockParentChildData as data } from '@/mock/roleData'; const chartEl=ref(); onMounted(()=>{ echarts.init(chartEl.value).setOption({ xAxis:{type:'category',data:['第1次','第2次','第3次','第4次']}, yAxis:{type:'value'}, series:[{type:'bar',data:[6,5,4,3]}] }) })
</script>
<style scoped>.grid-two{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.chart-box{height:240px}.sub{color:var(--text-secondary);margin-top:12px}@media(max-width:768px){.grid-two{grid-template-columns:1fr}}</style>
