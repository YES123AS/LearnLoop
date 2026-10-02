<template>
  <div class="page-container">
    <PageHeader title="批改与反馈" subtitle="查看学生答案并提交评分和评语" />
    <SectionCard title="待批改列表" desc="提交后状态会同步变化">
      <el-empty v-if="reviews.length===0" description="暂无待批改内容" />
      <el-table v-else :data="reviews" stripe>
        <el-table-column prop="studentName" label="学生" width="110" />
        <el-table-column prop="question" label="题目" />
        <el-table-column prop="answer" label="学生答案" />
        <el-table-column prop="status" label="状态" width="110"><template #default="{ row }"><el-tag :type="row.status==='已批改'?'success':'warning'">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="120"><template #default="{ row }"><el-button link type="primary" @click="active=row">批改</el-button></template></el-table-column>
      </el-table>
    </SectionCard>

    <SectionCard v-if="active" title="批改面板" desc="填写分数和评语" style="margin-top:16px">
      <p><b>{{ active.studentName }}</b> · {{ active.question }}</p>
      <el-input v-model.number="active.score" type="number" min="0" max="100" placeholder="输入分数" style="max-width:200px;margin:12px 0" />
      <el-input v-model="active.teacherComment" type="textarea" :rows="4" placeholder="输入评语" />
      <el-button type="primary" class="gradient-btn" style="margin-top: 12px" @click="submit(active)">提交批改</el-button>
    </SectionCard>
  </div>
</template>
<script setup>
import { ref } from 'vue'; import { ElMessage } from 'element-plus'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockReviews } from '@/mock/roleData'; const reviews = ref(mockReviews.map(i=>({...i}))); const active = ref(reviews.value.find(i=>i.status==='待批改') || null); const submit=(item)=>{ item.status='已批改'; ElMessage.success('批改已提交') }
</script>
