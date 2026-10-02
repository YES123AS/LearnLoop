export const APP_ROUTES = {
  dashboard: '/dashboard',
  profile: '/profile',
  chat: '/chat',
  knowledge: '/knowledge',
  resource: '/resource',
  path: '/path',
  quiz: '/quiz',
  mistakes: '/mistakes',
  analysis: '/analysis',
  recommend: '/recommend',
  teacherDashboard: '/teacher/dashboard',
  teacherStudents: '/teacher/students',
  teacherStudentDetail: (id) => `/teacher/student/${id}`,
  teacherTasks: '/teacher/tasks',
  teacherReview: '/teacher/review',
  teacherAnalysis: '/teacher/analysis',
  parentDashboard: '/parent/dashboard',
  parentChild: '/parent/child',
  parentReport: '/parent/report',
  parentFeedback: '/parent/feedback',
  parentSuggestions: '/parent/suggestions',
  login: '/login',
  forbidden: '/403'
}

export const SIDEBAR_NAV_ITEMS = [
  { key: 'dashboard', path: APP_ROUTES.dashboard, title: '首页', icon: 'HomeFilled', roles: ['student'] },
  { key: 'profile', path: APP_ROUTES.profile, title: '学习画像', icon: 'User', roles: ['student'] },
  { key: 'chat', path: APP_ROUTES.chat, title: '智能辅导', icon: 'ChatDotRound', roles: ['student'] },
  { key: 'knowledge', path: APP_ROUTES.knowledge, title: '知识库管理', icon: 'FolderOpened', roles: ['student'] },
  { key: 'resource', path: APP_ROUTES.resource, title: '资源生成', icon: 'Document', roles: ['student'] },
  { key: 'path', path: APP_ROUTES.path, title: '学习路径', icon: 'Guide', roles: ['student'] },
  { key: 'quiz', path: APP_ROUTES.quiz, title: '题目练习', icon: 'EditPen', roles: ['student'] },
  { key: 'mistakes', path: APP_ROUTES.mistakes, title: '错题集', icon: 'Warning', roles: ['student'] },
  { key: 'analysis', path: APP_ROUTES.analysis, title: '学情分析', icon: 'DataAnalysis', roles: ['student'] },
  { key: 'recommend', path: APP_ROUTES.recommend, title: '学习推荐', icon: 'Star', roles: ['student'] }
]

export const ROLE_MENU = {
  student: SIDEBAR_NAV_ITEMS,
  teacher: [
    { key: 'teacherDashboard', path: APP_ROUTES.teacherDashboard, title: '教师工作台', icon: 'HomeFilled', roles: ['teacher'] },
    { key: 'teacherStudents', path: APP_ROUTES.teacherStudents, title: '学生管理', icon: 'User', roles: ['teacher'] },
    { key: 'teacherTasks', path: APP_ROUTES.teacherTasks, title: '任务督导', icon: 'Document', roles: ['teacher'] },
    { key: 'teacherReview', path: APP_ROUTES.teacherReview, title: '批改反馈', icon: 'EditPen', roles: ['teacher'] },
    { key: 'teacherAnalysis', path: APP_ROUTES.teacherAnalysis, title: '班级学情分析', icon: 'DataAnalysis', roles: ['teacher'] }
  ],
  parent: [
    { key: 'parentDashboard', path: APP_ROUTES.parentDashboard, title: '家长工作台', icon: 'HomeFilled', roles: ['parent'] },
    { key: 'parentChild', path: APP_ROUTES.parentChild, title: '学习概览', icon: 'User', roles: ['parent'] },
    { key: 'parentReport', path: APP_ROUTES.parentReport, title: '学习报告', icon: 'Document', roles: ['parent'] },
    { key: 'parentFeedback', path: APP_ROUTES.parentFeedback, title: '教师反馈', icon: 'ChatDotRound', roles: ['parent'] },
    { key: 'parentSuggestions', path: APP_ROUTES.parentSuggestions, title: '家庭辅导建议', icon: 'Star', roles: ['parent'] }
  ]
}
