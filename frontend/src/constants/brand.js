/** 智学环 LearnLoop 品牌与页面文案常量（仅展示层） */

import { APP_ROUTES } from '@/constants/routes'

export const BRAND_NAME = '智学环 LearnLoop'
export const BRAND_NAME_SHORT = '智学环'
export const BRAND_NAME_EN = 'LearnLoop'
export const BRAND_SLOGAN = 'AI 个性化学习闭环平台'
export const BRAND_DESC =
  '围绕学习画像、资源生成、题目练习、错题诊断与学情分析，构建 AI 个性化学习闭环。'
export const WORKBENCH_TITLE = '智能学习工作台'
export const DOCUMENT_TITLE_SUFFIX = BRAND_NAME

export const PAGE_HEADERS = {
  chat: {
    title: 'AI 智能辅导',
    subtitle: '围绕学习目标与薄弱知识点，提供个性化问答与学习建议。'
  },
  profile: {
    title: '学习画像',
    subtitle: '通过学习目标、基础水平、学习偏好与薄弱点构建个性化学习档案。'
  },
  resource: {
    title: '多智能体协同资源生成',
    subtitle: '四大 AI 智能体协同协作，基于学习画像生成个性化学习资料'
  },
  knowledge: {
    title: '知识库管理',
    subtitle: '上传课程资料并重建向量库，让问答、资源生成与出题使用最新知识。'
  },
  path: {
    title: '个性化学习路径规划',
    subtitle: 'AI 智能体根据学习画像，生成每日个性化学习路径'
  },
  quiz: {
    title: '题目练习',
    subtitle: 'AI 智能体生成个性化检测题，实时记录答题数据驱动学情分析'
  },
  analysis: {
    title: '学习效果评估',
    subtitle: '学习驾驶舱 · AI 智能体驱动的学情分析与画像同步'
  },
  recommend: {
    title: '动态学习推荐',
    subtitle: 'AI 智能体基于学情分析结果，生成个性化学习推荐与学习路线图'
  },
  mistakes: {
    title: '错题集',
    subtitle: '汇总练习中的薄弱题目，结合 AI 诊断进行针对性复习'
  }
}

/** 完整学习闭环流程（Dashboard 引导用） */
export const LEARNING_FLOW_STEPS = [
  {
    key: 'profile',
    title: '学习画像',
    desc: '构建个性化档案，记录基础水平与薄弱点',
    route: APP_ROUTES.profile
  },
  {
    key: 'path',
    title: '学习路径',
    desc: '按目标规划每日学习任务与阶段目标',
    route: APP_ROUTES.path
  },
  {
    key: 'knowledge',
    title: '知识库管理',
    desc: '上传课程资料，构建 RAG 检索知识库',
    route: APP_ROUTES.knowledge
  },
  {
    key: 'resource',
    title: '资源生成',
    desc: '生成结构化讲义、提纲与复习资料',
    route: APP_ROUTES.resource
  },
  {
    key: 'quiz',
    title: '题目练习',
    desc: '智能出题，实时记录答题与掌握情况',
    route: APP_ROUTES.quiz
  },
  {
    key: 'mistakes',
    title: '错题集',
    desc: 'AI 错因诊断，变式题重练修复薄弱点',
    route: APP_ROUTES.mistakes
  },
  {
    key: 'analysis',
    title: '学情分析',
    desc: '统计练习数据，识别薄弱与掌握知识点',
    route: APP_ROUTES.analysis
  },
  {
    key: 'recommend',
    title: '学习推荐',
    desc: '基于学情给出下一步复习与提升方向',
    route: APP_ROUTES.recommend
  }
]
