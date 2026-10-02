# SoftwareCup 个性化学习 AI 后端

本项目是一个面向前端调用的个性化学习 AI 能力后端，主要基于讯飞星火 X2 大模型完成学习问答、学习资料生成、题目生成、学习路径规划、学情分析、错因诊断、智能错题本和下一步学习推荐。

当前版本已扩展为“课程知识库 RAG + 学生画像记忆 + 多 Agent 工作流 + 智能错题诊断”的学习系统：普通问题可以直接调用单 Agent，复杂学习任务会自动进入多 Agent 协作流程，问答、资料生成、题目生成和错因诊断都可以优先基于本地课程资料检索结果生成。

后端使用 `FastAPI` 对模型能力进行接口封装，前端可以通过 HTTP 请求直接调用 `/ai/...` 系列接口。

## 使用 Docker 启动

项目根目录提供了 `compose.yaml`，会同时启动 FastAPI 后端和由 Nginx 托管的 Vue 前端。首次启动需要联网拉取基础镜像、安装依赖并下载嵌入模型：

```powershell
New-Item -ItemType Directory -Force .local-data/config | Out-Null
Copy-Item spark/.env.example .local-data/config/spark.env
# 编辑 .local-data/config/spark.env，填写真实的 SPARK_API_PASSWORD
docker compose up -d --build
```

启动完成后访问：

- 前端：`http://localhost:5173`
- 后端接口文档：`http://localhost:8000/docs`
- 后端健康检查：`http://localhost:8000/health`

常用管理命令：

```powershell
# 查看服务状态
docker compose ps

# 持续查看日志
docker compose logs -f

# 停止并删除容器，保留学习数据
docker compose down

# 重新构建并启动
docker compose up -d --build
```

学生学习记录、LangGraph 检查点和生成结果保存在 Docker 命名卷 `learnloop-data` 中。课程文档挂载自 `spark/docs`，向量索引保存在被 Git 忽略的 `.local-data/vector_db`。只有明确要重置所有持久化学习数据时才执行 `docker compose down -v`。

前端容器统一通过 `/api` 反向代理后端，因此浏览器不会依赖 Docker 内部服务名，也不需要写死本机后端地址。`.local-data` 已同时被 Git 和 Docker 构建上下文排除，其中的密钥、数据库、向量索引和日志不会提交或复制进镜像。

## LangChain / LangGraph 架构状态

项目已开始渐进迁移到 LangChain 1.x 与 LangGraph 1.x：

- 普通文本模型调用已通过 `langchain-openai` 的 `ChatOpenAI` 执行。
- 课程检索已提供标准 LangChain `BaseRetriever` 接口，同时兼容原向量文件。
- `/ai/multi_agent_learning_loop` 已由 LangGraph `StateGraph` 编排。
- 生成题目后使用 `interrupt()` 暂停；提交答案时复用 `workflow_id` 从 SQLite 检查点恢复。
- 旧的业务函数继续作为图节点服务使用，确保 API 与前端可以逐步迁移。

完整迁移设计、图结构和后续阶段参见：

```text
docs/LANGCHAIN_LANGGRAPH_MIGRATION.md
```

## 项目结构

```text
SoftwareCup/
├── README.md
├── requirements.txt
├── .local-data/            # 本地私有目录，不提交到 Git
│   ├── config/spark.env
│   ├── data/
│   ├── logs/
│   └── vector_db/
└── spark/
    ├── __init__.py
    ├── .env.example
    ├── ai_api.py
    ├── agent_manager.py
    ├── workflow_manager.py
    ├── multi_agent_learning_loop.py
    ├── spark_llm.py
    ├── trusted_course_generator.py
    ├── personalized_chat.py
    ├── resource_generator.py
    ├── quiz_generator.py
    ├── learning_path_generator.py
    ├── dynamic_learning_path.py
    ├── learning_analysis.py
    ├── knowledge_tracing.py
    ├── student_memory.py
    ├── mistake_diagnosis.py
    ├── practice_engine.py
    ├── build_knowledge_base.py
    ├── test_rag.py
    ├── test_trusted_rag.py
    ├── test_student_memory.py
    ├── docs/
    ├── knowledge_base/
    │   ├── document_loader.py
    │   ├── text_splitter.py
    │   ├── vector_store.py
    │   ├── retriever.py
    │   ├── rag_answer.py
    │   └── rag_resource.py
    └── learning_resource.md
```

## 文件作用说明

### `requirements.txt`

项目依赖文件，包含后端服务和大模型调用需要的基础 Python 包：

```text
fastapi
uvicorn
openai
python-dotenv
```

安装依赖时使用：

```powershell
pip install -r requirements.txt
```

如果启用课程知识库 RAG、PPT/PDF/Word 文档解析和向量检索，还需要安装：

```powershell
pip install sentence-transformers numpy python-pptx pypdf python-docx
```

如果访问 PyPI 出现 SSL 或连接问题，可以临时使用国内镜像：

```powershell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple sentence-transformers numpy python-pptx pypdf python-docx
```

### `.local-data/config/spark.env`

本地环境变量配置文件，用于保存讯飞星火 X2 的 API 配置。

需要配置这些变量：

```env
SPARK_API_PASSWORD=你的讯飞星火API密码
SPARK_BASE_URL=https://spark-api-open.xf-yun.com/agent/v1
SPARK_MODEL=spark-x
SPARK_MODEL_CANDIDATES=spark-x
SPARK_USER=softwarecup
SPARK_ENABLE_THINKING=false
```

注意：该文件包含真实密钥，整个 `.local-data` 目录已被 `.gitignore` 排除，不要强制添加到 Git。

### `spark/__init__.py`

Python 包标识文件。

它的作用是让 `spark` 目录可以被 Python 当作一个包导入，例如：

```powershell
python -m uvicorn spark.ai_api:app --host 127.0.0.1 --port 8000
```

### `spark/spark_llm.py`

大模型调用封装模块。

主要功能：

- 从 `.local-data/config/spark.env` 读取 `SPARK_API_PASSWORD`、`SPARK_BASE_URL`、`SPARK_MODEL`
- 使用 OpenAI SDK 兼容方式调用讯飞星火 X2
- 提供普通非流式调用 `chat`
- 提供流式调用 `chat_stream`
- 支持多轮对话历史 `history`
- 支持设置 `temperature`、`max_tokens`、`thinking`

核心类：

```python
SparkX2Client
```

简单使用：

```python
from spark.spark_llm import SparkX2Client

client = SparkX2Client()
answer = client.chat("请解释一下 LZW 算法")
print(answer)
```

### `spark/trusted_course_generator.py`

可信课程生成模块，用于实现 Self-RAG 式课程问答、学习资料生成和题目生成。

主要功能：

- 判断课程相关任务是否需要检索
- 检索本地课程知识库
- 检查检索资料是否足以支撑当前任务
- 严格基于课程资料生成回答、讲义和题目
- 检查生成内容是否依据课程资料
- 返回 `sources`、`retrieval_check`、`grounding_check`，方便前端展示和答辩说明

主要函数：

```python
generate_trusted_answer(question, student_profile=None, top_k=6)
generate_trusted_resource(topic, output_file, student_profile=None, resource_type="学习资料", top_k=5, fast_checks=True)
generate_trusted_quiz(topic, student_profile, question_types, count=5, difficulty="简单", top_k=8)
```

资源生成默认开启快速检查：用本地检索相似度和生成结果完整性替代两次额外的大模型检查，从而把“检索检查 + 内容生成 + 依据性检查”缩短为主要一次内容生成。需要完整 Self-RAG 严格审核时，可以在接口中传 `fast_mode=false`，或在代码中传 `fast_checks=False`。

### `spark/personalized_chat.py`

个性化学习问答模块。

主要功能：

- 根据学生画像构造个性化 Prompt
- 回答学生提出的学习问题
- 针对学生的基础、目标、薄弱点和学习风格调整回答方式

主要函数：

```python
personalized_answer(question, student_profile)
```

学生画像示例：

```python
student_profile = {
    "grade": "大二",
    "major": "智能科学与技术",
    "course": "多媒体信息处理",
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
}
```

### `spark/resource_generator.py`

学习资料生成模块。

主要功能：

- 默认调用可信课程资料生成，强制基于课程知识库生成资料
- 根据主题生成学习资料
- 返回检索来源和可信性检查信息
- 保留普通分段生成能力作为备用入口
- 每生成一段就写入 Markdown 文件，避免中途失败导致内容全部丢失
- 支持根据学生画像生成更个性化的学习资料

主要函数：

```python
generate_learning_resource(
    topic,
    output_file="learning_resource.md",
    student_profile=None,
    resource_type="学习资源",
    fast_checks=True
)
```

备用普通生成函数：

```python
generate_plain_learning_resource(...)
```

输出文件默认是 Markdown 格式，例如：

```text
spark/learning_resource.md
```

### `spark/quiz_generator.py`

题目生成模块。

主要功能：

- 根据知识点生成学习检测题
- 默认调用可信课程题目生成，强制基于课程知识库出题
- 支持选择题、填空题、简答题、计算题等类型
- 根据学生基础和薄弱点控制题目难度
- 每道题输出 `knowledge_point` 字段，用于追踪细分知识点掌握情况
- 每道题可带 `source_basis` 字段，说明依据的课程资料编号
- 要求模型输出 JSON 格式，方便前端解析和展示

主要函数：

```python
generate_quiz(
    topic,
    student_profile,
    question_types,
    count=5,
    difficulty="简单"
)
```

RAG 版本题目生成函数：

```python
generate_rag_quiz(
    topic,
    student_profile,
    question_types,
    count=5,
    difficulty="简单",
    top_k=5
)
```

`generate_rag_quiz` 会先检索课程知识库，再基于检索到的课程资料生成题目，题目更贴近老师课件。

普通大模型出题保留为备用函数：

```python
generate_plain_quiz(...)
```

### `spark/learning_path_generator.py`

学习路径生成模块。

主要功能：

- 根据学习目标和学生画像生成学习计划
- 支持指定学习天数
- 每天包含学习主题、学习任务、练习任务和完成标准
- 适合前端直接展示为学习计划页面

主要函数：

```python
generate_learning_path(goal, student_profile, days=7)
```

### `spark/dynamic_learning_path.py`

动态学习路径模块。

主要功能：

- 不一次性生成完整多天计划，只生成当前阶段任务
- 根据学生画像、做题记录和知识点掌握度判断下一步状态
- 支持三种路径状态：`remediate` 补救、`consolidate` 巩固、`advance` 推进
- 如果学生连续答错或掌握度较低，优先生成补救任务
- 每轮练习后动态生成下一步学习任务和练习要求

主要函数：

```python
generate_dynamic_initial_path_by_student(student_id, goal)
generate_next_learning_step(student_id, goal, current_topic=None)
```

### `spark/learning_analysis.py`

学情分析模块。

主要功能：

- 调用 `knowledge_tracing.py` 对历史答题序列进行轻量知识追踪
- 综合总体正确率、近期正确率、题目难度、作答速度和稳定性计算 `mastery_score`
- 判断知识点掌握情况：薄弱、待强化、基本掌握、掌握较好
- 给出下一次推荐题目难度 `next_difficulty`
- 调用大模型生成个性化学情分析和后续学习建议

主要函数：

```python
analyze_learning_status(records, student_profile)
```

做题记录示例：

```python
records = [
    {
        "knowledge_point": "LZW算法",
        "question_type": "选择题",
        "correct": False,
        "answer_time": 35,
        "difficulty": "简单",
        "submit_time": "2026-06-01 10:00:00"
    },
    {
        "knowledge_point": "LZW算法",
        "question_type": "填空题",
        "correct": True,
        "answer_time": 50,
        "difficulty": "中等",
        "submit_time": "2026-06-01 10:05:00"
    }
]
```

返回内容包含：

- `statistics`：各知识点知识追踪结果，包含 `mastery_score`、`recent_accuracy`、`next_difficulty` 等
- `weak_points`：薄弱或待强化知识点
- `basic_points`：基本掌握知识点
- `mastered_points`：掌握较好知识点
- `ai_analysis`：大模型生成的学情分析文本

### `spark/knowledge_tracing.py`

轻量知识追踪模块。

主要功能：

- 按知识点聚合学生历史答题记录
- 计算总体正确率、近期正确率、难度得分、速度得分和稳定性得分
- 输出综合掌握度 `mastery_score`
- 根据掌握度输出 `mastery_level` 和 `next_difficulty`

主要函数：

```python
analyze_knowledge_tracing(records)
```

### `spark/agent_manager.py`

多智能体调度模块。

主要功能：

- 先判断是否需要多 Agent 工作流
- 普通任务自动分发到单 Agent
- 复杂任务交给 `workflow_manager.py`
- “学习闭环/多 Agent 协同学习”请求交给 `multi_agent_learning_loop.py`
- 问答优先调用 RAG 知识库问答
- 学习资料优先调用 RAG 课程资料生成
- 支持根据 `student_id` 自动读取学生画像

意图类型：

```text
qa          学习问答
resource    生成学习资料
plan        生成学习路径
evaluate    学情分析
recommend   推荐下一步学习内容
learning_loop 一键多 Agent 学习闭环
```

主要函数：

```python
agent_dispatcher(user_input, student_profile, extra_data=None)
```

根据学生 ID 自动调度：

```python
agent_dispatcher_by_student(user_input, student_id, extra_data=None)
```

也包含推荐函数：

```python
recommend_next_content(student_profile, weak_points, mastered_points=None)
```

### `spark/workflow_manager.py`

多 Agent 工作流模块。

主要功能：

- 判断复杂学习任务是否需要多 Agent 协作
- 支持完整学习闭环、复习闭环和学情诊断闭环
- 自动调用规划 Agent、资料 Agent、题目 Agent、评估 Agent、推荐 Agent
- 最后由总结 Agent 整合多个步骤结果

工作流类型：

```text
full_learning_workflow   完整学习闭环
review_workflow          复习闭环
diagnosis_workflow       学情诊断闭环
single_agent             普通单 Agent 任务
```

主要函数：

```python
detect_workflow_intent(user_input)
workflow_dispatcher(user_input, student_profile, extra_data=None)
```

示例：

```python
from spark.agent_manager import agent_dispatcher

student_profile = {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "weak_points": ["LZW算法"],
    "learning_style": "喜欢通俗解释和例子"
}

result = agent_dispatcher(
    user_input="帮我3天掌握LZW算法，生成学习计划、学习资料和练习题",
    student_profile=student_profile,
    extra_data={"topic": "LZW算法", "days": 3}
)
```

### `spark/multi_agent_learning_loop.py`

一键多 Agent 学习闭环模块。

主要功能：

- 规划 Agent 生成学习路径
- 审核 Agent 检查学习路径、资料和题目质量
- 资源 Agent 优先基于 RAG / Self-RAG 生成可信课程资料
- 题目 Agent 优先基于 RAG / Self-RAG 生成练习题
- 学生提交答案后自动判分，并写入 `student_memory.py`
- 评估 Agent 调用 `learning_analysis.py` 生成学情分析
- 推荐 Agent 根据薄弱点推荐下一步内容
- 补救规划 Agent 为薄弱知识点生成补救路径
- 总结 Agent 整合所有 Agent 输出

主要状态：

```text
waiting_for_answers       已生成计划、资料和题目，等待学生提交答案
closed_loop_completed     已完成答题评估、推荐和补救规划
```

主要函数：

```python
multi_agent_learning_loop(user_input, student_profile, student_id=None, extra_data=None)
multi_agent_learning_loop_by_student(user_input, student_id, extra_data=None)
```

### `spark/mistake_diagnosis.py`

智能错题诊断与错题本模块。

主要功能：

- 在学生答错后读取题目、标准答案、学生答案和判分理由
- 检索课程知识库，为错因诊断提供课程依据
- 判断错误类型，例如概念不清、步骤遗漏、公式误用、计算错误、审题错误、知识迁移弱
- 生成个性化错因诊断、缺失知识点、补救微课和推荐练习
- 生成同类变式题，用于检查学生是否已经修复该错题
- 将错题诊断结果保存到 SQLite 错题本表 `wrong_question_book`
- 支持查询错题本、查看单道错题详情、提交变式题答案并更新修复状态

主要函数：

```python
create_mistake_diagnosis_from_wrong_answer(...)
get_mistake_book(student_id, status=None)
get_mistake_detail(mistake_id)
evaluate_mistake_retry(mistake_id, variant_index, user_answer)
```

说明：`multi_agent_learning_loop.py` 在自动判分发现学生答错时，也会调用该模块生成错因诊断。

### `spark/student_memory.py`

学生画像与学习记忆模块。

主要功能：

- 使用 SQLite 保存学生画像
- 保存每次做题记录
- 每次新增做题记录后，自动使用知识追踪结果更新 `knowledge_mastery`
- 自动生成 `weak_points`、`weak_point_details` 和 `mastered_points`
- 在 `knowledge_mastery` 中保存 `recent_accuracy`、`difficulty_score`、`speed_score`、`stability_score`、`mastery_score`、`next_difficulty`
- 可直接为问答、路径规划、题目生成、学情分析提供学生画像

主要函数：

```python
init_db()
create_or_update_student_profile(...)
add_learning_record(...)
get_student_profile(student_id)
get_learning_records(student_id)
get_knowledge_mastery(student_id)
get_student_report(student_id)
```

示例：

```python
from spark.student_memory import get_student_profile

student_profile = get_student_profile("S001")
```

### `spark/build_knowledge_base.py`

课程知识库构建脚本。

主要功能：

- 读取 `spark/docs/` 下的课程文档
- 抽取 PPT、PDF、Word 等文件中的文本
- 切分课程内容
- 使用 `sentence-transformers` 生成向量
- 保存到 `.local-data/vector_db/`

运行：

```powershell
python spark\build_knowledge_base.py
```

### `spark/knowledge_base/`

课程知识库 RAG 模块。

文件说明：

```text
document_loader.py   课程文档读取
text_splitter.py     文本切分
vector_store.py      向量库保存与加载
retriever.py         相似内容检索
rag_answer.py        基于课程资料的问答
rag_resource.py      基于课程资料的学习资料生成
```

RAG 问答示例：

```python
from spark.knowledge_base.rag_answer import rag_answer

result = rag_answer(
    question="JPEG压缩的基本流程是什么？",
    student_profile=student_profile,
    top_k=5
)

print(result["answer"])
print(result["sources"])
```

### `spark/ai_api.py`

前端接口封装模块，也是本项目推荐的启动入口。

主要功能：

- 使用 FastAPI 封装 AI 能力
- 提供 HTTP 接口给前端调用
- 开启 CORS，方便前端本地联调
- 提供 Swagger 在线接口文档
- 统一返回 JSON 格式

启动后可访问：

```text
http://127.0.0.1:8000/docs
```

### `spark/learning_resource.md`

学习资料生成结果文件。

调用 `/ai/generate_resource` 或 `generate_learning_resource` 后，会把生成的学习资料保存到这个 Markdown 文件中。

## 环境准备

### 1. 进入项目目录

```powershell
cd D:\桌面\SoftwareCup
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 配置本地私有环境变量

先从安全模板创建本地配置：

```powershell
New-Item -ItemType Directory -Force .local-data/config | Out-Null
Copy-Item spark/.env.example .local-data/config/spark.env
```

然后在 `.local-data/config/spark.env` 中填写讯飞星火 X2 配置：

```env
SPARK_API_PASSWORD=你的讯飞星火API密码
SPARK_BASE_URL=https://spark-api-open.xf-yun.com/agent/v1
SPARK_MODEL=spark-x
SPARK_MODEL_CANDIDATES=spark-x
SPARK_USER=softwarecup
SPARK_ENABLE_THINKING=false
```

如果没有配置 `SPARK_API_PASSWORD`，运行时会报错：

```text
未找到 SPARK_API_PASSWORD，请检查 .local-data/config/spark.env 是否配置正确
```

### 4. 构建课程知识库

如果需要使用 RAG 问答、RAG 学习资料生成或 RAG 题目生成，需要先把课程资料放入：

```text
spark/docs/
```

然后执行：

```powershell
python spark\build_knowledge_base.py
```

构建成功后会生成或更新：

```text
.local-data/vector_db/chunks.json
.local-data/vector_db/embeddings.npy
```

### 5. 初始化学生画像数据库

学生画像和做题记录保存在 SQLite 数据库中，默认文件为：

```text
student_learning.db
```

可以运行测试脚本初始化并查看效果：

```powershell
python spark\test_student_memory.py
```

真实业务中推荐先创建学生画像，再通过 `agent_dispatcher_by_student` 自动读取：

```python
from spark.student_memory import create_or_update_student_profile, init_db
from spark.agent_manager import agent_dispatcher_by_student

init_db()

create_or_update_student_profile(
    student_id="S001",
    grade="大二",
    major="智能科学与技术",
    course="多媒体信息处理",
    level="基础较弱",
    goal="期末复习",
    learning_style="喜欢通俗解释和例子"
)

result = agent_dispatcher_by_student(
    user_input="帮我分析一下我的薄弱点",
    student_id="S001"
)
```

## 启动本地接口服务

在项目根目录执行：

```powershell
python -m uvicorn spark.ai_api:app --host 127.0.0.1 --port 8000
```

启动成功后访问：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 关闭本地接口服务

如果服务运行在当前 PowerShell 窗口中，按：

```text
Ctrl + C
```

如果服务在后台运行，可以关闭占用 `8000` 端口的进程：

```powershell
$processId = (Get-NetTCPConnection -LocalPort 8000).OwningProcess
Stop-Process -Id $processId
```

## 接口说明

所有接口默认地址前缀：

```text
http://127.0.0.1:8000
```

统一返回格式：

```json
{
  "success": true,
  "data": {}
}
```

如果调用失败，会返回错误信息：

```json
{
  "detail": {
    "success": false,
    "message": "错误原因"
  }
}
```

### 1. 学习问答

接口：

```text
POST /ai/chat
```

功能：

根据学生画像和课程知识库回答学习问题，并返回来源依据和可信性检查信息。

请求示例：

```json
{
  "question": "LZW算法是什么？能不能简单解释一下？",
  "student_profile": {
    "grade": "大二",
    "major": "智能科学与技术",
    "course": "多媒体信息处理",
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "answer": "严格依据课程资料生成的回答",
    "sources": [],
    "retrieval_check": {
      "status": "passed",
      "relevant": true,
      "confidence": 0.95,
      "reason": "检索资料与问题相关",
      "usable_points": []
    },
    "grounding_check": {
      "status": "passed",
      "grounded": true,
      "confidence": 0.95,
      "unsupported_claims": [],
      "revision_advice": "无需修改。"
    },
    "mode": "self_rag"
  }
}
```

### 2. 生成学习资料

接口：

```text
POST /ai/generate_resource
```

功能：

根据主题检索课程知识库，生成可信学习资料，并保存为 Markdown 文件。

请求示例：

```json
{
  "topic": "LZW算法",
  "resource_type": "完整学习资料",
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "weak_points": ["LZW算法"],
    "learning_style": "喜欢通俗解释和例子"
  }
}
```

可选字段：

```json
{
  "output_file": "spark/learning_resource.md"
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "topic": "LZW算法",
    "resource_type": "完整学习资料",
    "output_file": "生成文件的绝对路径",
    "content": "Markdown学习资料内容",
    "sources": [],
    "retrieval_check": {
      "status": "passed",
      "relevant": true,
      "confidence": 0.95,
      "reason": "检索资料与主题相关",
      "usable_points": []
    },
    "grounding_check": {
      "status": "passed",
      "grounded": true,
      "confidence": 0.95,
      "unsupported_claims": [],
      "revision_advice": "无需修改。"
    },
    "mode": "self_rag"
  }
}
```

### 3. 生成题目

接口：

```text
POST /ai/generate_quiz
```

功能：

根据知识点检索课程知识库，生成可信题目、答案和解析。

请求示例：

```json
{
  "topic": "LZW算法",
  "question_types": ["选择题", "填空题", "简答题"],
  "count": 5,
  "difficulty": "简单",
  "student_profile": {
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法"],
    "learning_style": "喜欢通俗解释和例子"
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "quiz": {
      "topic": "LZW算法",
      "difficulty": "简单",
      "questions": [
        {
          "id": 1,
          "knowledge_point": "LZW编码字典更新",
          "type": "选择题",
          "question": "题目内容",
          "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
          "answer": "A",
          "analysis": "答案解析",
          "source_basis": ["[1]"]
        }
      ],
      "sources": [],
      "retrieval_check": {
        "status": "passed",
        "relevant": true,
        "confidence": 0.95,
        "reason": "检索资料可支撑出题",
        "usable_points": []
      },
      "grounding_check": {
        "status": "passed",
        "grounded": true,
        "confidence": 0.95,
        "unsupported_claims": [],
        "revision_advice": "无需修改。"
      }
    },
    "raw": "模型原始输出"
  }
}
```

说明：如果模型输出是合法 JSON，`quiz` 会自动解析为对象；如果模型输出不是合法 JSON，`quiz` 会保留为字符串。

### 4. 生成学习路径

接口：

```text
POST /ai/generate_path
```

功能：

根据学习目标生成指定天数的学习计划。

请求示例：

```json
{
  "goal": "3天掌握LZW算法",
  "days": 3,
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "path": "模型生成的学习路径"
  }
}
```

### 5. 动态学习路径

动态学习路径分为两个接口：开始学习时生成初始阶段任务，练习结束后根据最新掌握度生成下一步任务。

#### 5.1 生成初始动态路径

接口：

```text
POST /ai/dynamic_path/start
```

请求示例：

```json
{
  "student_id": "S001",
  "goal": "掌握 Python 基础"
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "student_id": "S001",
    "goal": "掌握 Python 基础",
    "path_mode": "dynamic",
    "current_step": {
      "topic": "变量类型转换",
      "learning_tasks": [],
      "practice_tasks": []
    },
    "candidate_sequence": []
  }
}
```

#### 5.2 生成下一步动态任务

接口：

```text
POST /ai/dynamic_path/next
```

请求示例：

```json
{
  "student_id": "S001",
  "goal": "掌握 Python 基础",
  "current_topic": "变量类型转换"
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "path_state": "remediate",
    "next_topic": "变量类型转换",
    "reason": "最近连续两题错误，需要暂停推进并进行补救。",
    "learning_tasks": [],
    "practice_tasks": [],
    "decision": {
      "state": "remediate"
    }
  }
}
```

### 6. 一键多 Agent 学习闭环

接口：

```text
POST /ai/multi_agent_learning_loop
```

功能：

一键执行规划、审核、RAG 资料、RAG 题目、答题评估、学情分析、推荐、补救规划和总结。

学生未提交答案时，请求中不传 `submitted_answers`，接口会返回 `waiting_for_answers`。

```json
{
  "user_input": "帮我3天掌握LZW算法，生成计划、资料、题目，并形成学习闭环",
  "student_id": "S001",
  "student_profile": {
    "grade": "大二",
    "major": "智能科学与技术",
    "course": "多媒体信息处理",
    "level": "基础较弱",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
  },
  "extra_data": {
    "topic": "LZW算法",
    "days": 3,
    "count": 3
  }
}
```

学生提交答案后，把答案放入 `extra_data.submitted_answers`：

```json
{
  "user_input": "帮我3天掌握LZW算法，生成计划、资料、题目，并形成学习闭环",
  "student_id": "S001",
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "learning_style": "喜欢通俗解释和例子"
  },
  "extra_data": {
    "topic": "LZW算法",
    "days": 3,
    "count": 3,
    "submitted_answers": {
      "1": "A",
      "2": "字典编码",
      "3": "LZW通过动态构建字典来压缩重复字符串"
    }
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "loop_type": "multi_agent_learning_loop",
    "status": "waiting_for_answers",
    "topic": "LZW算法",
    "steps": [],
    "audits": {},
    "quiz": {},
    "summary": "总结 Agent 输出"
  }
}
```

### 7. 智能错题诊断与错题本

错题能力包含 4 个接口：答错后生成诊断、查询学生错题本、查看单道错题详情、提交变式题答案并判断是否修复。

#### 7.1 生成错因诊断

接口：

```text
POST /ai/mistake/diagnose
```

功能：

根据题目、学生答案和判分理由生成错因诊断、补救微课、推荐练习和同类变式题，并写入错题本。

请求示例：

```json
{
  "student_id": "S001",
  "question": {
    "id": 1,
    "knowledge_point": "LZW编码字典更新",
    "type": "选择题",
    "question": "LZW编码过程中，什么时候会向字典加入新短语？",
    "options": ["A. 读到新组合时", "B. 每读一个字符", "C. 输出结束后", "D. 解码完成后"],
    "answer": "A",
    "analysis": "LZW会在发现当前组合不在字典中时，将新组合加入字典。"
  },
  "user_answer": "B",
  "difficulty": "简单",
  "judge_reason": "学生把字典更新时机理解成每读一个字符都会更新。",
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "weak_points": ["LZW算法"],
    "learning_style": "喜欢通俗解释和例子"
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "mistake_id": "生成的错题ID",
    "student_id": "S001",
    "knowledge_point": "LZW编码字典更新",
    "error_types": ["概念不清", "审题错误"],
    "diagnosis": "错因诊断文本",
    "missing_points": ["LZW编码字典更新"],
    "remediation_micro_lesson": {},
    "recommended_practice": "建议练习内容",
    "variant_questions": [],
    "sources": [],
    "status": "未修复"
  }
}
```

#### 7.2 查询学生错题本

接口：

```text
GET /ai/mistake_book/{student_id}
```

可选查询参数：

```text
status=未修复
status=已修复
```

返回示例：

```json
{
  "success": true,
  "data": {
    "student_id": "S001",
    "count": 1,
    "mistakes": []
  }
}
```

#### 7.3 查询单道错题详情

接口：

```text
GET /ai/mistake/{mistake_id}
```

返回该错题的题目信息、学生答案、标准答案、错因诊断、补救微课、变式题和修复状态。

#### 7.4 提交变式题答案

接口：

```text
POST /ai/mistake/retry
```

请求示例：

```json
{
  "mistake_id": "错题ID",
  "variant_index": 1,
  "user_answer": "LZW在发现当前字符串加下一个字符组成的新短语不在字典中时，会把该新短语加入字典。"
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "mistake_id": "错题ID",
    "status": "已修复",
    "correct": true,
    "reason": "变式题判分理由",
    "message": "该错题已修复。",
    "retry_result": {
      "variant_index": 1,
      "correct": true
    }
  }
}
```

### 8. 学情分析

接口：

```text
POST /ai/analyze_status
```

功能：

根据做题记录进行知识追踪分析，并生成学情分析和学习建议。

请求示例：

```json
{
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "learning_style": "喜欢通俗解释和例子"
  },
  "records": [
    {"knowledge_point": "LZW算法", "question_type": "选择题", "correct": false},
    {"knowledge_point": "LZW算法", "question_type": "填空题", "correct": true},
    {"knowledge_point": "JPEG压缩", "question_type": "简答题", "correct": false}
  ]
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "statistics": [],
    "weak_points": [],
    "basic_points": [],
    "mastered_points": [],
    "ai_analysis": "模型生成的学情分析"
  }
}
```

### 9. 推荐下一步学习内容

接口：

```text
POST /ai/recommend_next
```

功能：

根据薄弱知识点和已掌握知识点，推荐下一步学习内容。

请求示例：

```json
{
  "student_profile": {
    "level": "基础较弱",
    "course": "多媒体信息处理",
    "goal": "期末复习",
    "weak_points": ["LZW算法", "JPEG压缩"],
    "learning_style": "喜欢通俗解释和例子"
  },
  "weak_points": ["LZW算法"],
  "mastered_points": ["颜色直方图"]
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "recommendation": "模型生成的下一步学习建议"
  }
}
```

## 前端调用示例

### JavaScript `fetch`

```javascript
const response = await fetch("http://127.0.0.1:8000/ai/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    question: "LZW算法是什么？",
    student_profile: {
      level: "基础较弱",
      course: "多媒体信息处理",
      goal: "期末复习",
      weak_points: ["LZW算法"],
      learning_style: "喜欢通俗解释和例子"
    }
  })
});

const result = await response.json();
console.log(result.data.answer);
```

### PowerShell 调试

```powershell
$body = @{
    question = "LZW算法是什么？"
    student_profile = @{
        level = "基础较弱"
        course = "多媒体信息处理"
        goal = "期末复习"
        weak_points = @("LZW算法")
        learning_style = "喜欢通俗解释和例子"
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ai/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## 模块单独运行

除了通过 API 调用，也可以单独运行部分模块进行测试。

### 测试模型客户端

```powershell
python spark\spark_llm.py
```

### 测试多智能体调度器

```powershell
python spark\agent_manager.py
```

### 测试多 Agent 工作流

```powershell
python spark\workflow_manager.py
```

### 测试一键多 Agent 学习闭环

```powershell
python spark\multi_agent_learning_loop.py
```

### 测试智能错题诊断

```powershell
python spark\mistake_diagnosis.py
```

### 构建课程知识库

```powershell
python spark\build_knowledge_base.py
```

### 测试 RAG 问答

```powershell
python spark\test_rag.py
```

### 测试 Self-RAG 可信课程生成

```powershell
python spark\test_trusted_rag.py
```

### 测试学生画像记忆

```powershell
python spark\test_student_memory.py
```

### 测试知识追踪

```powershell
python spark\knowledge_tracing.py
```

### 测试学习资料生成

```powershell
python spark\resource_generator.py
```

### 测试题目生成

```powershell
python spark\quiz_generator.py
```

### 测试学习路径生成

```powershell
python spark\learning_path_generator.py
```

### 测试动态学习路径

```powershell
python spark\dynamic_learning_path.py
```

### 测试学情分析

```powershell
python spark\learning_analysis.py
```

## 常见问题

### 1. 提示找不到 `SPARK_API_PASSWORD`

检查 `.local-data/config/spark.env` 是否存在，并确认里面包含：

```env
SPARK_API_PASSWORD=你的讯飞星火API密码
```

### 2. 提示缺少 `fastapi` 或 `uvicorn`

说明依赖没有安装，运行：

```powershell
pip install -r requirements.txt
```

### 3. 启动服务时提示端口被占用

如果 `8000` 端口被占用，可以换一个端口：

```powershell
python -m uvicorn spark.ai_api:app --host 127.0.0.1 --port 8001
```

访问地址也要改成：

```text
http://127.0.0.1:8001/docs
```

### 4. 生成资料时间比较长

`generate_resource` 会分多段调用模型，依次生成大纲、章节、练习题和答案，所以耗时会比普通问答更长。

### 5. 题目接口返回的 `quiz` 不是对象

题目生成接口会尝试把模型输出解析为 JSON。如果模型没有严格输出 JSON，接口会把原始文本保留在 `quiz` 和 `raw` 中，前端可以优先读取 `raw` 做展示。

### 6. 安装 `sentence-transformers` 时出现 SSL 错误

如果看到类似：

```text
SSLError: UNEXPECTED_EOF_WHILE_READING
Could not fetch URL https://pypi.org/simple/sentence-transformers/
```

通常是网络或证书链问题，可以换国内镜像：

```powershell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple sentence-transformers numpy python-pptx pypdf python-docx
```

### 7. 运行 RAG 时出现 `torch` 和 `transformers` 版本不兼容

如果看到类似：

```text
AttributeError: module 'torch' has no attribute 'float8_e8m0fnu'
```

说明当前 `torch`、`transformers`、`sentence-transformers` 版本不匹配。可以优先使用一组较稳定的版本：

```powershell
pip uninstall -y transformers sentence-transformers
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple transformers==4.44.2 sentence-transformers==3.0.1
```

## 推荐开发流程

1. 从 `spark/.env.example` 创建并配置 `.local-data/config/spark.env`
2. 安装依赖
3. 启动 FastAPI 服务
4. 打开 `/docs` 测试接口
5. 前端根据接口文档接入 `/ai/...` 路由
6. 如果某个 AI 能力需要调整效果，优先修改对应模块里的 Prompt
7. 如果要启用课程资料问答，先执行 `python spark\build_knowledge_base.py`
8. 如果要启用学生画像，先初始化 `student_memory.py` 中的数据库

对应关系：

```text
学习问答        personalized_chat.py
RAG问答         knowledge_base/rag_answer.py
Self-RAG可信生成 trusted_course_generator.py
学习资料生成    resource_generator.py
RAG资料生成     knowledge_base/rag_resource.py
题目生成        quiz_generator.py
学习路径生成    learning_path_generator.py
动态学习路径    dynamic_learning_path.py
学情分析        learning_analysis.py
知识追踪        knowledge_tracing.py
学生画像记忆    student_memory.py
智能错题诊断    mistake_diagnosis.py
多Agent工作流   workflow_manager.py
学习闭环        multi_agent_learning_loop.py
下一步推荐      agent_manager.py
Agent总调度     agent_manager.py
接口封装        ai_api.py
模型调用        spark_llm.py
```
