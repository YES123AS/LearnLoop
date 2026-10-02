<template>
  <div class="page-container">
    <PageHeader :title="student?.name || '学生详情'" subtitle="教师仅查看与督导，不进行学生端操作" />
    <el-empty v-if="!student" description="未找到学生" />
    <template v-else>
      <div class="grid-two">
        <SectionCard title="学生画像卡片" desc="基础信息与学习画像摘要">
          <p>班级：{{ student.className }}</p>
          <p>学习进度：{{ student.progress }}%</p>
          <p>正确率：{{ student.accuracy }}%</p>
          <p>画像摘要：{{ student.profileSummary }}</p>
        </SectionCard>
        <SectionCard title="错题统计" desc="最近错题与督导方向">
          <p>错题数量：{{ student.mistakes }}</p>
          <div class="tags"><el-tag v-for="tag in student.weakPoints" :key="tag">{{ tag }}</el-tag></div>
        </SectionCard>
      </div>
      <SectionCard title="最近学习记录" desc="最近两次练习情况" style="margin-top:16px">
        <el-table :data="student.recentRecords" stripe>
          <el-table-column prop="topic" label="知识点" />
          <el-table-column prop="type" label="题型" />
          <el-table-column prop="time" label="时间" />
          <el-table-column label="结果"><template #default="{ row }"><el-tag :type="row.correct ? 'success' : 'danger'">{{ row.correct ? '正确' : '错误' }}</el-tag></template></el-table-column>
        </el-table>
      </SectionCard>
      <SectionCard title="教师督导建议" desc="填写并保存督导建议" style="margin-top:16px">
        <el-input v-model="note" type="textarea" :rows="4" placeholder="填写督导建议" />
        <el-button type="primary" class="gradient-btn" style="margin-top: 12px" @click="save">保存督导建议</el-button>
      </SectionCard>
    </template>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'; import { useRoute } from 'vue-router'; import { ElMessage } from 'element-plus'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockStudents } from '@/mock/roleData'; const route=useRoute(); const note=ref(''); const student=computed(()=>mockStudents.find(s=>s.id===route.params.id)); const save=()=>ElMessage.success('督导建议已保存（mock）')
</script>
<style scoped>.grid-two{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.tags{display:flex;flex-wrap:wrap;gap:8px}@media(max-width:768px){.grid-two{grid-template-columns:1fr}}</style>
