<template>
  <div class="page-container">
    <PageHeader title="教师反馈" subtitle="查看来自老师的批改与督导建议" />
    <SectionCard title="反馈列表" desc="按时间查看反馈记录">
      <el-empty v-if="feedback.length===0" description="暂无反馈" />
      <el-timeline v-else>
        <el-timeline-item v-for="item in feedback" :key="item.id" :timestamp="item.time">
          <el-tag size="small" effect="light" style="margin-right:8px">{{ item.category }}</el-tag>
          {{ item.content }}
        </el-timeline-item>
      </el-timeline>
    </SectionCard>
  </div>
</template>
<script setup>
import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockTeacherFeedback as feedback } from '@/mock/roleData'
</script>
