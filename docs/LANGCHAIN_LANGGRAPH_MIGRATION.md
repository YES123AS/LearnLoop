# LangChain / LangGraph 渐进迁移说明

## 目标

迁移遵循“接口稳定、内部替换、可测试、可回退”的原则。现有 FastAPI
请求和响应字段保持兼容，避免要求前端与后端在同一次提交中整体重写。

## 当前阶段：基础设施与学习闭环

本阶段已经完成：

1. 使用 `langchain-openai` 的 `ChatOpenAI` 适配讯飞星火兼容接口。
2. 保留 `SparkX2Client` 外观，但普通 `chat()` 调用已经进入 LangChain。
3. 使用 `StateGraph` 实现多 Agent 学习闭环。
4. 使用 `interrupt()` 在生成题目后暂停工作流。
5. 使用 SQLite Checkpointer 持久化工作流状态。
6. 使用 `workflow_id` 作为 LangGraph `thread_id` 恢复工作流。
7. 将节点依赖抽象为 `LearningLoopServices`，允许不访问模型的单元测试。

## 当前图结构

```text
START
  -> prepare
  -> plan
  -> resource
  -> quiz
  -> [已有答案?]
       -> 是: await_answers
       -> 否: waiting_summary -> await_answers (interrupt)
  -> evaluate
  -> analyze
  -> recommend
  -> remedial
  -> final_summary
  -> END
```

首次调用不传 `submitted_answers` 时，接口返回：

```json
{
  "workflow_id": "...",
  "status": "waiting_for_answers",
  "orchestrator": "langgraph"
}
```

提交答案时必须复用首次返回的 `workflow_id`：

```json
{
  "user_input": "继续完成学习闭环",
  "student_profile": {},
  "extra_data": {
    "workflow_id": "首次调用返回的ID",
    "submitted_answers": {
      "1": "A",
      "2": "JPEG"
    }
  }
}
```

图会从 `await_answers` 节点恢复，不会重新生成路径、资料和题目。

## 模块职责

- `spark/langchain_runtime.py`：模型供应商边界、消息转换和 LCEL Chain。
- `spark/langgraph_learning_loop.py`：状态定义、节点、边、检查点和兼容入口。
- `spark/multi_agent_learning_loop.py`：现有领域操作，迁移期间作为节点服务复用。
- `spark/spark_llm.py`：旧调用方兼容层，逐步缩小职责。

## 后续迁移顺序

### 第二阶段：结构化输出

- 将审核结果、题目、错因诊断改为 Pydantic Schema。
- 使用 `with_structured_output()` 取代手工截取 JSON。
- 将审核意见写入状态，并在重试生成时反馈给生成节点。

### 第三阶段：RAG 标准化

- 文档统一转换为 LangChain `Document`。
- 将现有向量检索包装成 `BaseRetriever`，先保持原向量数据兼容。
- 再评估是否迁移到 FAISS、Chroma 或其他向量库。

### 第四阶段：其他工作流

- 将动态学习路径迁移为独立 StateGraph。
- 将错题诊断和变式题修复迁移为子图。
- 将普通问答改为可组合的检索、生成、核验 Runnable。

### 第五阶段：生产化

- 将同步 SQLite Checkpointer 替换为适合部署环境的持久化方案。
- 增加 LangSmith 或兼容 OpenTelemetry 的链路追踪。
- 增加节点超时、重试策略、幂等键和敏感数据脱敏。

## 测试

图测试使用依赖注入和内存 Checkpointer，不调用真实模型：

```powershell
python -m unittest tests.test_langgraph_learning_loop -v
```

真实模型与 RAG 的集成测试应单独执行，避免普通单元测试消耗 API 配额。
