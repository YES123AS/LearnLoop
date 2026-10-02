<template>
  <div class="page-container">
    <PageHeader title="家庭辅导建议" subtitle="更适合家长的陪伴与沟通建议" />
    <div class="grid-three">
      <SectionCard v-for="item in data.suggestions" :key="item.title" :title="item.title" :desc="item.content" />
    </div>
    <SectionCard title="学习习惯建议" desc="帮助孩子逐步形成稳定节奏" style="margin-top:16px">
      <el-alert type="info" show-icon :closable="false" title="建议每天固定一个小段时间复习，优先完成当天薄弱知识点，再进行适量练习，避免临时突击。" />
    </SectionCard>
  </div>
</template>
<script setup>
import PageHeader from '@/components/PageHeader.vue'; import SectionCard from '@/components/SectionCard.vue'; import { mockParentChildData as data } from '@/mock/roleData'
</script>
<style scoped>.grid-three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:900px){.grid-three{grid-template-columns:1fr}}</style>
