export const mockStudents = [
  {
    id: 's001',
    name: '李明',
    className: '计科2301',
    progress: 78,
    accuracy: 86,
    weakPoints: ['LZW算法', 'JPEG压缩'],
    lastStudyTime: '2026-06-14 19:20',
    learningStatus: '稳定提升',
    recentRecords: [
      { topic: 'LZW算法', type: '选择题', correct: true, time: '2026-06-14 18:30' },
      { topic: 'JPEG压缩', type: '简答题', correct: false, time: '2026-06-13 20:10' }
    ],
    mistakes: 6,
    profileSummary: '基础较好，细节题仍需加强，适合案例化讲解。',
    teacherNotes: '建议继续巩固压缩编码与编码树相关知识。'
  },
  {
    id: 's002',
    name: '王婷',
    className: '计科2302',
    progress: 54,
    accuracy: 68,
    weakPoints: ['霍夫曼编码', '颜色直方图'],
    lastStudyTime: '2026-06-14 17:05',
    learningStatus: '需要督促',
    recentRecords: [
      { topic: '霍夫曼编码', type: '填空题', correct: false, time: '2026-06-14 16:40' },
      { topic: '颜色直方图', type: '选择题', correct: true, time: '2026-06-12 21:30' }
    ],
    mistakes: 11,
    profileSummary: '学习节奏偏慢，适合分步骤复习与及时反馈。',
    teacherNotes: '近期作业完成度一般，建议加强课后提醒。'
  },
  {
    id: 's003',
    name: '张浩',
    className: '计科2301',
    progress: 91,
    accuracy: 94,
    weakPoints: ['视频编码基础'],
    lastStudyTime: '2026-06-14 20:15',
    learningStatus: '优秀',
    recentRecords: [
      { topic: 'DCT变换', type: '选择题', correct: true, time: '2026-06-14 19:10' },
      { topic: '视频编码基础', type: '简答题', correct: false, time: '2026-06-13 19:30' }
    ],
    mistakes: 3,
    profileSummary: '掌握度高，可适当增加拓展题与迁移题。',
    teacherNotes: '可担任学习小组示范成员。'
  }
]

export const mockTeacherTasks = [
  { id: 't001', title: '第 8 章课后练习', target: '计科2301', assignee: '全班', deadline: '2026-06-15 23:59', status: '进行中', count: 38, progress: 65 },
  { id: 't002', title: 'JPEG 压缩专题复习', target: '计科2302', assignee: '王婷', deadline: '2026-06-16 21:00', status: '需督促', count: 1, progress: 45 },
  { id: 't003', title: '期末错题巩固单', target: '计科2301', assignee: '全班', deadline: '2026-06-20 20:00', status: '未开始', count: 38, progress: 0 }
]

export const mockReviews = [
  {
    id: 'r001',
    studentId: 's001',
    studentName: '李明',
    question: '请简述霍夫曼编码的基本思想。',
    answer: '通过构建最优二叉树减少平均编码长度。',
    score: 88,
    teacherComment: '',
    status: '待批改',
    category: '简答题'
  },
  {
    id: 'r002',
    studentId: 's002',
    studentName: '王婷',
    question: 'JPEG 压缩为什么要进行量化？',
    answer: '为了减少冗余并压缩数据。',
    score: 0,
    teacherComment: '思路正确，但需补充有损压缩的目的。',
    status: '已批改',
    category: '简答题'
  }
]

export const mockParentChildData = {
  childName: '李明',
  className: '计科2301',
  todayStudyMinutes: 126,
  weeklyFinishedTasks: 5,
  accuracy: 86,
  progress: 78,
  weakPoints: ['LZW算法', 'JPEG压缩'],
  warningText: '本周练习节奏不错，但在压缩编码类知识点上仍需重点陪伴。',
  recentRecords: [
    { topic: 'LZW算法', type: '选择题', correct: true, time: '2026-06-14 18:30' },
    { topic: 'JPEG压缩', type: '简答题', correct: false, time: '2026-06-13 20:10' },
    { topic: '颜色直方图', type: '选择题', correct: true, time: '2026-06-12 20:40' }
  ],
  report: {
    strengths: ['颜色直方图', '基础概念掌握较稳'],
    needsImprove: ['LZW算法', 'JPEG压缩'],
    trend: [62, 68, 72, 79, 84, 86],
    weeklySummary: '本周整体学习状态稳定，周中出现一次错题波动，周末已回升。',
    studyMinutesTrend: [40, 55, 35, 60, 70, 66],
    accuracyTrend: [62, 68, 72, 79, 84, 86]
  },
  suggestions: [
    {
      title: '建议陪伴方式',
      content: '每天固定 20~30 分钟陪孩子做一次回顾，重点听他讲“为什么这么做”，帮助理清思路。'
    },
    {
      title: '复习重点',
      content: '优先复习 LZW 与 JPEG 压缩相关知识点，建议先看例题，再做 1~2 道基础题。'
    },
    {
      title: '沟通建议',
      content: '多肯定学习进步，少直接否定；当孩子卡住时，用提问引导他自己说出解题步骤。'
    }
  ]
}

export const mockTeacherFeedback = [
  {
    id: 'f001',
    studentName: '李明',
    time: '2026-06-14 21:10',
    category: '督导建议',
    content: '建议继续巩固压缩编码题目，明天先完成 3 道基础练习。',
    type: '督导建议'
  },
  {
    id: 'f002',
    studentName: '王婷',
    time: '2026-06-13 22:05',
    category: '批改意见',
    content: '答案思路正确，但表达不够完整，后续注意答题结构。',
    type: '批改意见'
  }
]

export const mockClassStats = {
  totalStudents: mockStudents.length,
  pendingReviews: 7,
  weakKnowledgePoints: [
    { name: 'LZW算法', value: 18 },
    { name: 'JPEG压缩', value: 15 },
    { name: '霍夫曼编码', value: 12 },
    { name: '颜色直方图', value: 8 }
  ],
  accuracyTrend: [72, 74, 75, 78, 80, 83],
  masteryRanking: mockStudents.map((s) => ({ name: s.name, value: s.accuracy })).sort((a, b) => b.value - a.value),
  abnormalStudents: [
    { id: 's002', name: '王婷', reason: '连续两次正确率低于 70%' }
  ]
}
