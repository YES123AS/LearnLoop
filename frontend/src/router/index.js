import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { DOCUMENT_TITLE_SUFFIX } from '@/constants/brand'
import { APP_ROUTES } from '@/constants/routes'
import { useUserStore } from '@/store/user'

const studentRoles = ['student']
const teacherRoles = ['teacher']
const parentRoles = ['parent']
const authRoutes = ['/login', '/403']

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { title: '登录' } },
  { path: '/403', name: 'Forbidden', component: () => import('@/pages/Forbidden.vue'), meta: { title: '403' } },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/pages/Dashboard.vue'), meta: { title: '智能学习工作台', roles: studentRoles } },
      { path: 'profile', name: 'Profile', component: () => import('@/pages/Profile.vue'), meta: { title: '学习画像', roles: studentRoles } },
      { path: 'chat', name: 'Chat', component: () => import('@/pages/Chat.vue'), meta: { title: '智能辅导', roles: studentRoles } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('@/pages/Knowledge.vue'), meta: { title: '知识库管理', roles: studentRoles } },
      { path: 'resource', name: 'Resource', component: () => import('@/pages/Resource.vue'), meta: { title: '资源生成', roles: studentRoles } },
      { path: 'path', name: 'Path', component: () => import('@/pages/Path.vue'), meta: { title: '学习路径', roles: studentRoles } },
      { path: 'quiz', name: 'Quiz', component: () => import('@/pages/Quiz.vue'), meta: { title: '题目练习', roles: studentRoles } },
      { path: 'mistakes', name: 'Mistakes', component: () => import('@/pages/Mistake.vue'), meta: { title: '错题集', roles: studentRoles } },
      { path: 'analysis', name: 'Analysis', component: () => import('@/pages/Analysis.vue'), meta: { title: '学情分析', roles: studentRoles } },
      { path: 'recommend', name: 'Recommend', component: () => import('@/pages/Recommend.vue'), meta: { title: '学习推荐', roles: studentRoles } },
      { path: '/teacher/dashboard', name: 'TeacherDashboard', component: () => import('@/pages/teacher/TeacherDashboard.vue'), meta: { title: '教师工作台', roles: teacherRoles } },
      { path: '/teacher/students', name: 'StudentManage', component: () => import('@/pages/teacher/StudentManage.vue'), meta: { title: '学生管理', roles: teacherRoles } },
      { path: '/teacher/student/:id', name: 'StudentDetail', component: () => import('@/pages/teacher/StudentDetail.vue'), meta: { title: '学生详情', roles: teacherRoles } },
      { path: '/teacher/tasks', name: 'TaskManage', component: () => import('@/pages/teacher/TaskManage.vue'), meta: { title: '任务督导', roles: teacherRoles } },
      { path: '/teacher/review', name: 'Review', component: () => import('@/pages/teacher/Review.vue'), meta: { title: '批改反馈', roles: teacherRoles } },
      { path: '/teacher/analysis', name: 'ClassAnalysis', component: () => import('@/pages/teacher/ClassAnalysis.vue'), meta: { title: '班级学情分析', roles: teacherRoles } },
      { path: '/parent/dashboard', name: 'ParentDashboard', component: () => import('@/pages/parent/ParentDashboard.vue'), meta: { title: '家长工作台', roles: parentRoles } },
      { path: '/parent/child', name: 'ChildOverview', component: () => import('@/pages/parent/ChildOverview.vue'), meta: { title: '学习概览', roles: parentRoles } },
      { path: '/parent/report', name: 'LearningReport', component: () => import('@/pages/parent/LearningReport.vue'), meta: { title: '学习报告', roles: parentRoles } },
      { path: '/parent/feedback', name: 'TeacherFeedback', component: () => import('@/pages/parent/TeacherFeedback.vue'), meta: { title: '教师反馈', roles: parentRoles } },
      { path: '/parent/suggestions', name: 'ParentSuggestions', component: () => import('@/pages/parent/ParentSuggestions.vue'), meta: { title: '家庭辅导建议', roles: parentRoles } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (!userStore.isLoggedIn) userStore.restoreLogin()

  if (to.path === '/login' && userStore.isLoggedIn) return next(userStore.getHomeByRole())
  if (to.path === '/403') return next()

  const requiresAuth = Array.isArray(to.meta.roles)
  if (requiresAuth && !userStore.isLoggedIn) return next('/login')

  if (requiresAuth && !userStore.canAccessRoute(to)) {
    return next('/403')
  }

  if (to.path === '/' && userStore.isLoggedIn) return next(userStore.getHomeByRole())
  next()
})

router.afterEach((to) => { document.title = `${to.meta.title || '首页'} - ${DOCUMENT_TITLE_SUFFIX}` })

export default router
