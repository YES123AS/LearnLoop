<template>
  <div class="app-layout">
    <aside class="app-sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <LogoIcon :size="36" />
        </div>
        <div class="brand-text">
          <div class="brand-name">智学环 LearnLoopAI</div>
          <div class="brand-desc">面向学生、教师、家长的 AI 学习协同平台</div>
        </div>
      </div>

      <div class="sidebar-user">
        <el-tag :type="roleTagType" effect="light" round>{{ userStore.roleLabel }}</el-tag>
        <div class="role-user">{{ userStore.userInfo?.name || '未登录' }}</div>
      </div>

      <div class="sidebar-menu-scroll">
        <el-menu
          class="menu"
          :default-active="activePath"
          :router="true"
          background-color="transparent"
          text-color="var(--text-secondary)"
          active-text-color="var(--primary)"
        >
          <el-menu-item
            v-for="item in navItems"
            :key="item.path"
            :index="item.path"
            class="menu-item"
          >
            <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
            <span class="menu-text">{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="sidebar-footer">
        <el-button class="logout-btn" plain @click="handleLogout">退出登录</el-button>
      </div>
    </aside>

    <div class="main-wrapper">
      <header class="topbar">
        <div class="topbar-left">
          <div class="page-title">{{ currentTitle }}</div>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item>智学环</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="topbar-right">
          <el-tag :type="roleTagType" effect="light" round>{{ userStore.roleLabel }}</el-tag>
          <span class="user-name">{{ userStore.userInfo?.name || '未登录' }}</span>
          <el-button size="small" @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <main class="content-shell">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { HomeFilled, User, ChatDotRound, Document, Guide, EditPen, DataAnalysis, Star, Warning, FolderOpened } from '@element-plus/icons-vue'
import LogoIcon from '@/components/LogoIcon.vue'
import { APP_ROUTES, ROLE_MENU } from '@/constants/routes'
import { useUserStore } from '@/store/user'

const iconMap = { HomeFilled, User, ChatDotRound, Document, Guide, EditPen, DataAnalysis, Star, Warning, FolderOpened }
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const navItems = computed(() => (ROLE_MENU[userStore.role] || ROLE_MENU.student).map((item) => ({ ...item, icon: iconMap[item.icon] })))
const activePath = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '首页')
const roleTagType = computed(() => ({ student: 'primary', teacher: 'success', parent: 'warning' }[userStore.role] || 'info'))

function handleLogout() {
  userStore.logout()
  router.replace(APP_ROUTES.login)
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  background: var(--gradient-bg);
  overflow: hidden;
}

.app-sidebar {
  width: 270px;
  height: 100vh;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  border-right: 1px solid var(--border);
  box-shadow: 2px 0 14px rgba(15, 23, 42, 0.04);
}

.sidebar-brand {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border);
}

.brand-logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-soft);
  flex-shrink: 0;
}

.brand-name {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.brand-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.sidebar-user {
  flex-shrink: 0;
  padding: 14px 20px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}

.role-user {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.sidebar-menu-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 10px 8px 12px;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.45) transparent;
}

.sidebar-menu-scroll::-webkit-scrollbar {
  width: 7px;
}

.sidebar-menu-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-menu-scroll::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.26);
  border-radius: 999px;
}

.sidebar-menu-scroll:hover::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.48);
}

.menu {
  border-right: 0;
}

.menu :deep(.el-menu-item) {
  height: 46px;
  border-radius: 12px;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  line-height: 1;
  padding-left: 14px !important;
  padding-right: 14px !important;
}

.menu :deep(.el-menu-item.is-active) {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary) !important;
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--primary);
}

.menu :deep(.el-menu-item.is-active .menu-icon) {
  color: var(--primary);
}

.menu :deep(.el-menu-item.is-active .menu-text) {
  color: var(--primary);
}

.menu-icon {
  margin-right: 0;
  font-size: 16px;
  flex-shrink: 0;
}

.menu-text {
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
  line-height: 1;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--border);
}

.logout-btn {
  width: 100%;
}

.main-wrapper {
  flex: 1;
  min-width: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  height: 68px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.topbar-left {
  min-width: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.breadcrumb {
  margin-top: 6px;
  font-size: 12px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.user-name {
  font-size: 14px;
  color: var(--text-secondary);
}

.content-shell {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
}

@media (max-width: 768px) {
  .app-sidebar {
    width: 88px;
  }

  .sidebar-brand,
  .sidebar-user,
  .sidebar-footer {
    padding-left: 12px;
    padding-right: 12px;
  }

  .brand-text,
  .role-user {
    display: none;
  }

  .sidebar-menu-scroll {
    padding-left: 8px;
    padding-right: 6px;
  }

  .menu-text {
    display: none;
  }

  .topbar {
    padding: 0 16px;
  }

  .page-title {
    font-size: 16px;
  }

  .content-shell {
    padding: 16px;
  }
}
</style>
