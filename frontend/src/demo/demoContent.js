/** 内置预览内容：纯前端静态展示，不调用后端 */

export const DEMO_CHAT_MESSAGES = [
  {
    role: 'user',
    content: 'LZW算法是什么？请用通俗的方式解释一下。',
    time: Date.now() - 120000
  },
  {
    role: 'assistant',
    content:
      'LZW（Lempel-Ziv-Welch）是一种**无损数据压缩算法**，核心思想是用「字典」把重复出现的字符串替换成更短的编码。\n\n' +
      '通俗理解：就像你和朋友约定暗号——第一次说「多媒体课程」写全称，之后再说「多媒体课程」就只写编号「1」，文件越小。\n\n' +
      '结合你的薄弱点，建议先掌握：① 字典如何动态增长；② 编码/解码对称过程；③ 与霍夫曼编码的对比。',
    time: Date.now() - 110000
  },
  {
    role: 'user',
    content: 'JPEG 压缩的基本流程是什么？',
    time: Date.now() - 60000
  },
  {
    role: 'assistant',
    content:
      'JPEG 压缩大致分五步：\n\n' +
      '1. **颜色空间转换**：RGB → YCbCr，亮度与色度分离\n' +
      '2. **分块与 DCT**：8×8 块做离散余弦变换\n' +
      '3. **量化**：丢弃人眼不敏感的高频信息（有损关键步骤）\n' +
      '4. **熵编码**：对量化系数做霍夫曼或算术编码\n' +
      '5. **重组比特流**：写入文件头与扫描数据\n\n' +
      '你目前 JPEG 正确率偏低，建议配合颜色直方图案例一起复习。',
    time: Date.now() - 50000
  }
]

export const DEMO_RESOURCE_MARKDOWN = `# LZW 算法 · 完整学习资料

> 以下为内置预览内容，点击「开始生成」后将获取 AI 个性化学习资料。

## 第一章 基础概念

**LZW** 是一种基于字典的无损压缩算法，由 Welch 在 Lempel-Ziv 基础上改进。编码时维护动态字典，将已出现过的字符串映射为整数索引。

### 核心术语
- **字典（Dictionary）**：存储已编码字符串的表
- **前缀（Prefix）**：当前正在构建的字符串
- **码字（Code）**：字典中的整数编号

## 第二章 编码流程

1. 初始化字典，包含所有单字符
2. 读取输入字符，与前缀拼接
3. 若拼接串在字典中，继续扩展前缀
4. 若不在字典中，输出前缀对应码字，将新串加入字典
5. 重复直至输入结束

### 编码示意
输入 \`ABABABA\` → 字典逐步增长，重复子串 \`AB\`、\`ABA\` 被替换为更短码字。

## 第三章 案例分析

**案例：GIF 图像压缩**  
GIF 格式采用 LZW 变体，适合重复像素较多的简单图形。

**案例：与霍夫曼编码对比**  
霍夫曼基于频率统计；LZW 基于字符串模式，无需预先统计。

## 第四章 综合练习

1. 手动对字符串 \`TOBEORNOT\` 进行 LZW 编码
2. 说明字典溢出时的处理策略
3. 比较 LZW 在文本与图像压缩中的适用性

---
*点击「开始生成」可获取 AI 个性化学习资料*`

export const DEMO_PATH_DAYS = [
  {
    title: 'Day 1 · LZW 基础概念',
    isDemo: true,
    tasks: ['理解 LZW 算法基本原理与字典思想', '学习字典构建与初始化过程', '完成 3 道基础检测题']
  },
  {
    title: 'Day 2 · 编码流程与实践',
    isDemo: true,
    tasks: ['掌握编码与解码完整步骤', '分析 TOBEORNOT 典型编码案例', '完成 5 道中等难度练习']
  },
  {
    title: 'Day 3 · 综合复习与检测',
    isDemo: true,
    tasks: ['回顾 LZW / JPEG / 霍夫曼薄弱点', '综合案例实战与对比总结', '完成学情自测并查看分析报告']
  }
]

export const DEMO_QUIZ_QUESTIONS = [
  {
    id: 'demo-1',
    type: '选择题',
    question: 'LZW 算法属于哪一类压缩方法？',
    options: ['有损压缩', '无损压缩', '视频专用压缩', '音频专用压缩'],
    answer: '无损压缩',
    explanation: 'LZW 通过字典替换实现无损压缩，解码后可完全还原原始数据。'
  },
  {
    id: 'demo-2',
    type: '填空题',
    question: 'LZW 编码过程中，当遇到字典中不存在的字符串时，应输出____对应码字，并将新字符串加入字典。',
    answer: '前缀',
    explanation: '标准 LZW 流程：输出当前前缀的码字，然后把「前缀+当前字符」作为新条目写入字典。'
  },
  {
    id: 'demo-3',
    type: '简答题',
    question: '简述 LZW 与霍夫曼编码的主要区别。',
    answer:
      '霍夫曼编码基于字符出现频率构建变长码，需预先统计；LZW 基于动态字典匹配重复字符串模式，无需预先统计频率，更适合重复模式明显的数据。',
    explanation: '两者可结合使用，如 GIF 用 LZW，JPEG 熵编码阶段常用霍夫曼。'
  }
]

export const DEMO_ANALYSIS_RESULT = {
  weak_points: ['LZW算法', 'JPEG压缩', '霍夫曼编码'],
  basic_points: ['颜色直方图'],
  mastered_points: [],
  ai_analysis: `## AI 学情分析总结

根据 **5 条**练习记录，系统识别出以下学情特征：

### 整体表现
- 总正确率 **40%**，处于基础巩固阶段
- **LZW算法** 与 **霍夫曼编码** 连续出错，需优先突破
- **颜色直方图** 掌握较好，可作为类比学习的切入点

### 学习建议
1. 先通过 LZW 字典构建案例建立直观理解
2. 结合 JPEG 流程图复习 DCT 与量化步骤
3. 用 3 天学习路径进行阶段性巩固

> 点击「生成学情分析」可获取基于你的练习数据的 AI 分析`,
  statistics: [
    { knowledge_point: 'LZW算法', total: 2, correct: 1, accuracy: 0.5, mastery_level: '基本掌握' },
    { knowledge_point: 'JPEG压缩', total: 1, correct: 0, accuracy: 0, mastery_level: '薄弱' },
    { knowledge_point: '霍夫曼编码', total: 1, correct: 0, accuracy: 0, mastery_level: '薄弱' },
    { knowledge_point: '颜色直方图', total: 1, correct: 1, accuracy: 1, mastery_level: '掌握较好' }
  ]
}

export const DEMO_RECOMMENDATION = `## 个性化学习推荐

基于当前学习画像与学情分析，AI 智能体为你生成以下学习路线：

### 第一优先级：LZW 算法
- **原因**：连续答题错误，为最薄弱知识点
- **行动**：生成 LZW 完整学习资料 → 完成 3 道针对性练习 → 智能辅导答疑

### 第二优先级：JPEG 压缩
- **原因**：简答题未答对，流程理解不足
- **行动**：复习 YCbCr 与 DCT 步骤 → 结合颜色直方图案例理解

### 第三优先级：霍夫曼编码
- **原因**：与 LZW 对比题错误，概念混淆
- **行动**：对比两种编码思想 → 完成 5 道中等难度检测题

### 预计收益
按此路线学习 **3 天**，预计掌握率可提升至 **85%** 以上。

---
*点击「生成学习推荐」可获取 AI 个性化学习建议*`
