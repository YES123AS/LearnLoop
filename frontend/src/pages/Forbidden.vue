<template>
  <div class="forbidden-wrap">
    <el-result icon="warning" title="当前身份无权访问该页面" sub-title="请返回你的工作台继续操作">
      <template #extra>
        <el-button type="primary" class="gradient-btn" @click="goHome">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

function goHome() {
  router.replace(userStore.getHomeByRole())
}
</script>

<style scoped>
.forbidden-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--gradient-bg); }
</style>
