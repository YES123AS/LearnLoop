<template>
  <div class="page-container">
    <PageHeader title="学生管理" subtitle="搜索学生并查看学习概览" />

    <SectionCard title="筛选条件" desc="按姓名、班级与学习状态检索学生">
      <div class="filters">
        <el-input v-model="keyword" placeholder="搜索学生姓名或班级" clearable />
        <el-select v-model="classFilter" placeholder="选择班级" clearable>
          <el-option v-for="item in classOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="学习状态" clearable>
          <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </SectionCard>

    <SectionCard title="学生列表" desc="点击查看学生详情" style="margin-top:16px">
      <el-table v-if="filteredStudents.length" :data="filteredStudents" stripe>
        <el-table-column prop="name" label="姓名" width="110" />
        <el-table-column prop="className" label="班级" width="110" />
        <el-table-column label="学习进度">
          <template #default="{ row }"><el-progress :percentage="row.progress" /></template>
        </el-table-column>
        <el-table-column label="正确率">
          <template #default="{ row }"><el-progress :percentage="row.accuracy" :stroke-width="10" status="success" /></template>
        </el-table-column>
        <el-table-column prop="weakPoints" label="薄弱点">
          <template #default="{ row }">
            <el-tag v-for="tag in row.weakPoints" :key="tag" size="small" effect="light" style="margin-right:6px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastStudyTime" label="最近学习时间" width="160" />
        <el-table-column prop="learningStatus" label="状态" width="110">
          <template #default="{ row }"><el-tag :type="statusType(row.learningStatus)" effect="light">{{ row.learningStatus }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }"><el-button type="primary" link @click="goDetail(row)">查看详情</el-button></template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无符合条件的学生" />
    </SectionCard>
  </div>
</template>
<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import { mockStudents } from '@/mock/roleData'
const keyword = ref(''); const classFilter = ref(''); const statusFilter = ref(''); const router = useRouter(); const classOptions=[...new Set(mockStudents.map(s=>s.className))]; const statusOptions=[...new Set(mockStudents.map(s=>s.learningStatus))]; const filteredStudents = computed(()=>mockStudents.filter(s=>`${s.name}${s.className}`.includes(keyword.value) && (!classFilter.value || s.className===classFilter.value) && (!statusFilter.value || s.learningStatus===statusFilter.value))); const goDetail = row=>router.push(`/teacher/student/${row.id}`); const statusType = s => s==='优秀'?'success':s==='需要督促'?'danger':'warning'
</script>
<style scoped>.filters{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}@media(max-width:768px){.filters{grid-template-columns:1fr}}</style>
