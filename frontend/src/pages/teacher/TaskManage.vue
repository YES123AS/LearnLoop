<template>
  <div class="page-container">
    <PageHeader title="任务/作业督导" subtitle="发布任务、跟踪进度、提醒学生完成" />
    <SectionCard title="发布学习任务" desc="新增任务后会立即出现在任务列表中">
      <el-form inline class="task-form">
        <el-form-item label="任务名称"><el-input v-model="form.title" placeholder="请输入任务名称" /></el-form-item>
        <el-form-item label="对象"><el-select v-model="form.target"><el-option label="全班" value="全班"/><el-option label="计科2301" value="计科2301"/><el-option label="计科2302" value="计科2302"/></el-select></el-form-item>
        <el-form-item label="截止时间"><el-date-picker v-model="form.deadline" type="datetime" placeholder="选择截止时间" /></el-form-item>
        <el-button type="primary" class="gradient-btn" @click="addTask">发布任务</el-button>
      </el-form>
    </SectionCard>
    <SectionCard title="任务列表" desc="任务状态与完成进度一目了然" style="margin-top:16px">
      <el-table :data="tasks" stripe>
        <el-table-column prop="title" label="任务" />
        <el-table-column prop="target" label="班级/学生" />
        <el-table-column prop="deadline" label="截止时间" />
        <el-table-column label="状态"><template #default="{ row }"><el-tag :type="statusType(row.status)">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column label="完成进度"><template #default="{ row }"><el-progress :percentage="row.progress" /></template></el-table-column>
        <el-table-column label="操作" width="120"><template #default="{ row }"><el-button link type="warning" @click="urge(row)">督促</el-button></template></el-table-column>
      </el-table>
    </SectionCard>
  </div>
</template>
<script setup>
import { reactive, ref } from 'vue'; import { ElMessage } from 'element-plus'; import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockTeacherTasks } from '@/mock/roleData'; const tasks = ref(mockTeacherTasks.map(t=>({...t, progress: t.status==='已完成'?100:t.status==='进行中'?65:t.status==='需督促'?45:0}))); const form = reactive({ title:'', target:'全班', deadline:'' }); const addTask = () => { if (!form.title) return ElMessage.warning('请先填写任务名称'); tasks.value.unshift({ id: Date.now(), title: form.title, target: form.target, assignee: form.target, deadline: form.deadline || '未设置', status: '未开始', count: 0, progress: 0 }); form.title=''; form.target='全班'; form.deadline=''; ElMessage.success('任务已发布（mock）') }; const urge=(row)=>ElMessage.success(`已发送督促：${row.title}`); const statusType=s=>s==='已完成'?'success':s==='需督促'?'danger':s==='进行中'?'warning':'info'
</script>
<style scoped>.task-form{display:flex;flex-wrap:wrap;gap:12px}.task-form :deep(.el-form-item){margin-bottom:0}</style>
