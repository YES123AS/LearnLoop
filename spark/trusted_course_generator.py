import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .spark_llm import SparkX2Client
    from .knowledge_base.retriever import (
        create_langchain_retriever,
        documents_to_results,
        format_retrieved_context,
    )
except ImportError:
    from spark_llm import SparkX2Client
    from knowledge_base.retriever import (
        create_langchain_retriever,
        documents_to_results,
        format_retrieved_context,
    )


DEFAULT_DB_DIR = os.getenv(
    "VECTOR_DB_DIR",
    str(Path(__file__).resolve().parent.parent / ".local-data" / "vector_db"),
)
CHECK_STATUSES = {"passed", "failed", "unknown"}
DEFAULT_FAST_RESOURCE_CHECKS = True
DEFAULT_FAST_RETRIEVAL_MIN_SCORE = 0.18


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, ""))
    except (TypeError, ValueError):
        return default


def safe_json_loads(text: str) -> Any:
    """
    尽量从大模型输出中解析 JSON。
    兼容 ```json ... ``` 或前后带解释文字的情况。
    """
    if not text:
        return None

    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None

    return None


def get_field(obj: Any, *names: str, default: Any = "") -> Any:
    """
    兼容 dict 和对象两种检索结果格式。
    """
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def normalize_confidence(value: Any, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default

    return max(0.0, min(1.0, confidence))


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def normalize_retrieval_check(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一检索相关性检查结果，兼容旧版只返回 relevant 的模型输出。
    """
    relevant = normalize_bool(data.get("relevant", False))
    status = data.get("status")
    if status not in CHECK_STATUSES:
        status = "passed" if relevant else "failed"
    elif status != "passed":
        relevant = False
    elif not relevant:
        status = "failed"

    normalized = dict(data)
    normalized["status"] = status
    normalized["relevant"] = relevant
    normalized["confidence"] = (
        0.0 if status == "unknown"
        else normalize_confidence(data.get("confidence"), default=1.0)
    )
    normalized.setdefault("reason", "无")
    normalized.setdefault("usable_points", [])
    return normalized


def normalize_grounding_check(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一生成依据性检查结果，兼容旧版只返回 grounded 的模型输出。
    """
    grounded = normalize_bool(data.get("grounded", False))
    status = data.get("status")
    if status not in CHECK_STATUSES:
        status = "passed" if grounded else "failed"
    elif status != "passed":
        grounded = False
    elif not grounded:
        status = "failed"

    normalized = dict(data)
    normalized["status"] = status
    normalized["grounded"] = grounded
    normalized["confidence"] = (
        0.0 if status == "unknown"
        else normalize_confidence(data.get("confidence"), default=1.0)
    )
    normalized.setdefault("unsupported_claims", [])
    normalized.setdefault("revision_advice", "无")
    return normalized


def unknown_retrieval_check(reason: str) -> Dict[str, Any]:
    return {
        "status": "unknown",
        "relevant": False,
        "confidence": 0.0,
        "reason": reason,
        "usable_points": [],
    }


def unknown_grounding_check(reason: str) -> Dict[str, Any]:
    return {
        "status": "unknown",
        "grounded": False,
        "confidence": 0.0,
        "unsupported_claims": [],
        "revision_advice": reason,
    }


def check_passed(check_result: Optional[Dict[str, Any]], flag_name: str) -> bool:
    if not check_result:
        return False

    return check_result.get("status") == "passed" and check_result.get(flag_name) is True


def fast_retrieval_relevance_check(
    topic: str,
    task_type: str,
    context: str,
    results: List[Any],
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    资源生成的快速检索检查。
    用本地相似度和上下文长度替代一次远程 LLM 评估，显著减少等待时间。
    """
    if not context or len(context.strip()) < 30 or not results:
        return {
            "status": "failed",
            "relevant": False,
            "confidence": 1.0,
            "reason": "知识库没有检索到足够的课程资料。",
            "usable_points": [],
            "check_mode": "fast_local",
        }

    threshold = DEFAULT_FAST_RETRIEVAL_MIN_SCORE if min_score is None else min_score
    best_score = max(
        (float(get_field(item, "score", "similarity", default=0.0) or 0.0) for item in results),
        default=0.0,
    )
    usable_points = []
    for item in results[:3]:
        content = get_field(item, "content", "text", "page_content", default="")
        if content:
            usable_points.append(str(content).replace("\n", " ")[:80])

    if best_score < threshold:
        return {
            "status": "failed",
            "relevant": False,
            "confidence": 0.85,
            "reason": f"最高检索相似度 {best_score:.4f} 低于快速模式阈值 {threshold:.2f}。",
            "usable_points": usable_points,
            "check_mode": "fast_local",
        }

    return {
        "status": "passed",
        "relevant": True,
        "confidence": min(0.95, max(0.65, best_score)),
        "reason": (
            f"快速模式：本地向量检索命中 {len(results)} 段课程资料，"
            f"最高相似度 {best_score:.4f}，跳过远程相关性评估以提升速度。"
        ),
        "usable_points": usable_points,
        "check_mode": "fast_local",
    }


def fast_generation_grounded_check(
    topic: str,
    generated_text: str,
    context: str,
) -> Dict[str, Any]:
    """
    资源生成的快速依据性检查。
    它不做逐条事实审计，只确认生成结果非空且使用了检索资料流程。
    """
    if not generated_text or len(generated_text.strip()) < 80:
        return {
            "status": "failed",
            "grounded": False,
            "confidence": 0.8,
            "unsupported_claims": ["生成内容过短或为空，无法作为完整学习资料。"],
            "revision_advice": "建议重新生成学习资料。",
            "check_mode": "fast_local",
        }

    if not context or len(context.strip()) < 30:
        return unknown_grounding_check("快速模式无法检查依据性：课程资料上下文为空。")

    return {
        "status": "passed",
        "grounded": True,
        "confidence": 0.72,
        "unsupported_claims": [],
        "revision_advice": (
            "快速模式已跳过远程逐条依据性审计；如需更严格可信性检查，"
            "调用接口时传 fast_mode=false。"
        ),
        "check_mode": "fast_local",
    }


def build_student_context(student_profile: Optional[Dict[str, Any]]) -> str:
    if not student_profile:
        return "学生信息：未提供，请按初学者水平生成。"

    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"

    return f"""
学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}
""".strip()


def build_low_confidence_notice(retrieval_check: Optional[Dict[str, Any]] = None) -> str:
    """
    知识库没有命中或检索检查未通过时，明确告知回答可信度较低。
    """
    reason = "知识库中没有找到足够相关的课程资料。"
    if isinstance(retrieval_check, dict):
        reason = retrieval_check.get("reason") or reason

    return f"""【可信度提示】
当前知识库没有检索到足够可靠的课程资料，或检索可信性检查未通过。

原因：{reason}

下面回答主要由 AI 基于通用知识生成，可信度相对较低，可能与课程教材、老师课件或考试要求不完全一致。
建议你上传更多权威资料，例如课程课件、教材章节、教师讲义、课堂笔记或标准答案，并重新构建知识库，以提高回答可信度。

"""


def build_medium_confidence_notice() -> str:
    return """【可信度提示】
系统检索到了相关课程资料，但生成内容的依据性检查未完全通过。以下回答可作为学习参考，建议结合课程课件或教材进一步确认。

"""


def get_check_reason(check_result: Optional[Dict[str, Any]], default: str) -> str:
    if isinstance(check_result, dict):
        return check_result.get("reason") or check_result.get("revision_advice") or default
    return default


def generate_low_confidence_answer(
    question: str,
    student_profile: Optional[Dict[str, Any]],
    retrieval_check: Optional[Dict[str, Any]],
    client: Optional[SparkX2Client] = None,
) -> str:
    """
    知识库不足时调用普通大模型兜底，但必须加低可信度提示。
    """
    if client is None:
        client = SparkX2Client()

    student_context = build_student_context(student_profile)
    notice = build_low_confidence_notice(retrieval_check)

    prompt = f"""
你是一个个性化学习助手。当前课程知识库没有提供足够可靠的依据，
因此你可以基于通用知识回答学生问题，但必须保持谨慎。

学生问题：
{question}

{student_context}

回答要求：
1. 不要声称内容来自课程资料。
2. 不要编造“来源依据”。
3. 如果问题很简单，例如问候、基础计算、常识问题，可以直接简洁回答。
4. 如果问题属于课程知识，请用通俗语言解释，并提醒学生以教材、课件或老师要求为准。
5. 回答要适合学生当前基础。
6. 不要输出 Markdown 表格。
"""

    answer = client.chat(
        user_input=prompt,
        system_prompt="你是一个谨慎的个性化学习助手。当前没有可靠知识库依据时，应明确说明可信度较低。",
        temperature=0.6,
        max_tokens=1600,
        thinking="disabled",
    )

    return notice + answer


def build_sources(results: List[Any]) -> List[Dict[str, Any]]:
    """
    把检索结果整理成前端和答辩都容易展示的来源依据。
    """
    sources = []

    for index, item in enumerate(results, start=1):
        metadata = get_field(item, "metadata", default={}) or {}

        file_name = (
            get_field(item, "file_name", default="")
            or metadata.get("file_name", "")
            or metadata.get("source", "")
            or metadata.get("filename", "")
            or "未知资料"
        )

        score = get_field(item, "score", "similarity", default=None)
        content = (
            get_field(item, "content", "text", "page_content", default="")
            or metadata.get("content", "")
        )

        sources.append({
            "id": index,
            "file_name": file_name,
            "score": score,
            "preview": str(content)[:160].replace("\n", " "),
        })

    return sources


def need_retrieval(task_type: str, query: str) -> bool:
    """
    Self-RAG 检查器 1：判断当前任务是否需要检索。
    课程问答、课程资料、练习题和解析默认强制检索。
    """
    course_tasks = {
        "qa",
        "answer",
        "resource",
        "quiz",
        "exercise",
        "review",
        "explanation",
        "learning_resource",
    }

    if task_type in course_tasks:
        return True

    keywords = [
        "课程", "知识点", "讲义", "课件", "教材", "复习",
        "题目", "练习题", "答案解析", "学习资料",
    ]

    return any(word in query for word in keywords)


def retrieve_course_context(
    query: str,
    top_k: int = 6,
    db_dir: str = DEFAULT_DB_DIR,
) -> Tuple[str, List[Dict[str, Any]], List[Any]]:
    """
    从课程知识库中检索资料。
    """
    try:
        retriever = create_langchain_retriever(db_dir=db_dir, top_k=top_k)
        results = documents_to_results(retriever.invoke(query))
    except Exception as error:
        print(f"[WARN] 知识库检索失败，进入低可信 AI 兜底：{error}")
        return "", [], []

    context = format_retrieved_context(results)
    sources = build_sources(results)

    return context, sources, results


def check_retrieval_relevance(
    topic: str,
    task_type: str,
    context: str,
    client: Optional[SparkX2Client] = None,
) -> Dict[str, Any]:
    """
    Self-RAG 检查器 2：判断检索资料是否能支撑当前任务。
    """
    if not context or len(context.strip()) < 30:
        return {
            "status": "failed",
            "relevant": False,
            "confidence": 1.0,
            "reason": "知识库没有检索到足够的课程资料。",
            "usable_points": [],
        }

    if client is None:
        client = SparkX2Client()

    prompt = f"""
你是课程知识库检索质量评估器。
请判断下面检索到的课程资料是否足以支撑当前任务。

当前主题：
{topic}

任务类型：
{task_type}

检索资料：
{context}

请只输出 JSON，不要输出 Markdown，不要输出解释文字。
格式如下：
{{
  "status": "passed",
  "relevant": true,
  "confidence": 0.95,
  "reason": "判断理由",
  "usable_points": ["可用于生成的要点1", "可用于生成的要点2"]
}}

判断标准：
1. status 只能是 passed、failed、unknown 三者之一。
2. 如果资料和主题明显相关，且足以支撑当前任务，status 为 passed，relevant 为 true。
3. 如果资料只包含零散关键词，但无法支撑讲解、出题或答案解析，status 为 failed，relevant 为 false。
4. 如果无法判断，status 为 unknown，relevant 为 false，confidence 为 0.0。
5. usable_points 只能写检索资料中明确出现或能直接推出的内容。
"""

    try:
        result = client.chat(
            user_input=prompt,
            system_prompt="你是严格的课程资料相关性检查器。",
            temperature=0.0,
            max_tokens=600,
            thinking="disabled",
        )
        data = safe_json_loads(result)

        if isinstance(data, dict) and "relevant" in data:
            return normalize_retrieval_check(data)

    except Exception as error:
        return unknown_retrieval_check(f"相关性检查器调用失败，可信性未知：{error}")

    return unknown_retrieval_check("相关性检查器结果解析失败，可信性未知。")


def check_generation_grounded(
    topic: str,
    generated_text: str,
    context: str,
    client: Optional[SparkX2Client] = None,
) -> Dict[str, Any]:
    """
    Self-RAG 检查器 3：判断生成内容是否依据课程资料。
    """
    if client is None:
        client = SparkX2Client()

    prompt = f"""
你是课程内容事实性检查器。
请判断“生成内容”是否严格依据“课程资料”。

主题：
{topic}

课程资料：
{context}

生成内容：
{generated_text}

请只输出 JSON，不要输出 Markdown。
格式如下：
{{
  "status": "passed",
  "grounded": true,
  "confidence": 0.95,
  "unsupported_claims": [],
  "revision_advice": "如果有不依据资料的内容，说明如何修改；如果没有，写：无需修改。"
}}

判断标准：
1. status 只能是 passed、failed、unknown 三者之一。
2. 如果生成内容中的核心知识点都能从课程资料中找到依据，status 为 passed，grounded 为 true。
3. 如果出现课程资料中没有的定义、步骤、公式、结论、例子，status 为 failed，grounded 为 false。
4. 如果无法判断，status 为 unknown，grounded 为 false，confidence 为 0.0。
5. unsupported_claims 列出不受资料支持的内容。
"""

    try:
        result = client.chat(
            user_input=prompt,
            system_prompt="你是严格的课程内容依据性检查器。",
            temperature=0.0,
            max_tokens=800,
            thinking="disabled",
        )
        data = safe_json_loads(result)

        if isinstance(data, dict) and "grounded" in data:
            return normalize_grounding_check(data)

    except Exception as error:
        return unknown_grounding_check(f"依据性检查器调用失败，可信性未知：{error}")

    return unknown_grounding_check("依据性检查器结果解析失败，可信性未知。")


def generate_trusted_answer(
    question: str,
    student_profile: Optional[Dict[str, Any]] = None,
    top_k: int = 6,
    db_dir: str = DEFAULT_DB_DIR,
) -> Dict[str, Any]:
    """
    基于课程资料的可信问答。
    """
    client = SparkX2Client()
    task_type = "qa"

    if not need_retrieval(task_type, question):
        return {
            "mode": "plain",
            "trust_level": "unknown",
            "answer": "该问题不属于课程知识生成任务，未触发课程知识库检索。",
            "sources": [],
            "candidate_sources": [],
            "retrieval_check": None,
            "grounding_check": None,
            "fallback_reason": "",
        }

    context, sources, _ = retrieve_course_context(question, top_k=top_k, db_dir=db_dir)
    retrieval_check = check_retrieval_relevance(
        topic=question,
        task_type=task_type,
        context=context,
        client=client,
    )

    if not check_passed(retrieval_check, "relevant"):
        fallback_reason = get_check_reason(
            retrieval_check,
            "知识库资料不足，已切换为普通 AI 兜底回答。"
        )
        fallback_answer = generate_low_confidence_answer(
            question=question,
            student_profile=student_profile,
            retrieval_check=retrieval_check,
            client=client,
        )

        return {
            "mode": "llm_fallback",
            "trust_level": "low",
            "answer": fallback_answer,
            "sources": [],
            "candidate_sources": sources,
            "retrieval_check": retrieval_check,
            "grounding_check": None,
            "fallback_reason": fallback_reason,
        }

    student_context = build_student_context(student_profile)

    prompt = f"""
你是一个可信课程问答助手。
请严格依据课程资料回答学生问题。

学生问题：
{question}

{student_context}

课程资料：
{context}

回答要求：
1. 只能根据课程资料回答。
2. 不要编造课程资料中没有的内容。
3. 先给通俗解释，再给正式解释。
4. 如果适合，可以给一个简单例子，但例子必须服务于课程资料中的知识点。
5. 最后写“来源依据”，列出你主要依据的资料编号，例如：[1]、[2]。
"""

    answer = client.chat(
        user_input=prompt,
        system_prompt="你是严格依据课程资料回答问题的学习助手。",
        temperature=0.3,
        max_tokens=1600,
        thinking="disabled",
    )

    grounding_check = check_generation_grounded(
        topic=question,
        generated_text=answer,
        context=context,
        client=client,
    )

    trust_level = "high" if check_passed(grounding_check, "grounded") else "medium"
    if trust_level == "medium":
        answer = build_medium_confidence_notice() + answer

    return {
        "mode": "self_rag",
        "trust_level": trust_level,
        "answer": answer,
        "sources": sources,
        "candidate_sources": [],
        "retrieval_check": retrieval_check,
        "grounding_check": grounding_check,
        "fallback_reason": "",
    }


def generate_trusted_resource(
    topic: str,
    output_file: str = "trusted_learning_resource.md",
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资料",
    top_k: int = 5,
    db_dir: str = DEFAULT_DB_DIR,
    fast_checks: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    基于课程资料生成可信学习资料，并保存为 Markdown。
    """
    client = SparkX2Client()
    task_type = "resource"
    if fast_checks is None:
        fast_checks = env_flag("SPARK_FAST_RESOURCE_CHECKS", DEFAULT_FAST_RESOURCE_CHECKS)

    context, sources, results = retrieve_course_context(topic, top_k=top_k, db_dir=db_dir)
    if fast_checks:
        retrieval_check = fast_retrieval_relevance_check(
            topic=topic,
            task_type=task_type,
            context=context,
            results=results,
            min_score=env_float("SPARK_FAST_RETRIEVAL_MIN_SCORE", DEFAULT_FAST_RETRIEVAL_MIN_SCORE),
        )
    else:
        retrieval_check = check_retrieval_relevance(
            topic=topic,
            task_type=task_type,
            context=context,
            client=client,
        )

    if not check_passed(retrieval_check, "relevant"):
        student_context = build_student_context(student_profile)
        notice = build_low_confidence_notice(retrieval_check)
        fallback_reason = get_check_reason(
            retrieval_check,
            "知识库资料不足，已切换为普通 AI 兜底生成。"
        )

        prompt = f"""
你是一个学习资料生成助手。当前课程知识库没有检索到足够可靠的资料，
请基于通用知识为学生生成《{topic}》的{resource_type}。

{student_context}

生成要求：
1. 开头不要写“来源于课程资料”。
2. 不要编造教材来源、课件来源或引用编号。
3. 内容要适合学生基础。
4. 结构清晰，使用 Markdown。
5. 最后提醒学生：建议上传课件、教材、教师讲义或权威资料，以便生成更可信的课程资料。

请按下面结构输出：
# {topic} {resource_type}

## 一、核心概念
## 二、通俗解释
## 三、关键步骤
## 四、例子讲解
## 五、易错点
## 六、练习建议
## 七、可信度说明
"""

        fallback_resource = client.chat(
            user_input=prompt,
            system_prompt="你是谨慎的学习资料生成助手。没有知识库依据时，必须说明内容由 AI 生成，可信度较低。",
            temperature=0.6,
            max_tokens=2600,
            thinking="disabled",
        )

        content = notice + fallback_resource
        Path(output_file).write_text(content, encoding="utf-8")

        return {
            "mode": "llm_fallback",
            "trust_level": "low",
            "resource": content,
            "output_file": output_file,
            "sources": [],
            "candidate_sources": sources,
            "retrieval_check": retrieval_check,
            "grounding_check": None,
            "fallback_reason": fallback_reason,
        }

    student_context = build_student_context(student_profile)

    prompt = f"""
你是一个可信课程资料生成助手。
请严格依据课程资料，为学生生成《{topic}》的{resource_type}。

{student_context}

课程资料：
{context}

生成要求：
1. 内容必须严格来自课程资料。
2. 不要补充课程资料之外的定义、公式、步骤或结论。
3. 语言要适合学生基础。
4. 使用 Markdown 格式。
5. 结构必须包括：
   # 标题
   ## 一、核心概念
   ## 二、通俗解释
   ## 三、关键步骤或原理
   ## 四、例子讲解
   ## 五、易错点
   ## 六、练习建议
   ## 七、来源依据
6. 来源依据部分要用 [1]、[2] 这种编号列出。
"""

    resource = client.chat(
        user_input=prompt,
        system_prompt="你是严格依据课程资料生成学习资料的助手。",
        temperature=0.3,
        max_tokens=2600,
        thinking="disabled",
    )

    if fast_checks:
        grounding_check = fast_generation_grounded_check(
            topic=topic,
            generated_text=resource,
            context=context,
        )
    else:
        grounding_check = check_generation_grounded(
            topic=topic,
            generated_text=resource,
            context=context,
            client=client,
        )

    source_text = "\n\n## 八、系统检索来源\n"
    for source in sources:
        source_text += f"- [{source['id']}] {source['file_name']}，相关度：{source.get('score')}\n"

    check_text = f"""

## 九、可信性检查

- 检索检查状态：{retrieval_check.get("status")}
- 检索相关性：{retrieval_check.get("relevant")}
- 检索置信度：{retrieval_check.get("confidence")}
- 检索说明：{retrieval_check.get("reason")}
- 检索检查模式：{retrieval_check.get("check_mode", "llm")}
- 生成检查状态：{grounding_check.get("status")}
- 生成依据性：{grounding_check.get("grounded")}
- 生成置信度：{grounding_check.get("confidence")}
- 修改建议：{grounding_check.get("revision_advice")}
- 生成检查模式：{grounding_check.get("check_mode", "llm")}
"""

    final_content = resource + source_text + check_text
    trust_level = "high" if check_passed(grounding_check, "grounded") else "medium"
    if trust_level == "medium":
        final_content = build_medium_confidence_notice() + final_content

    Path(output_file).write_text(final_content, encoding="utf-8")

    return {
        "mode": "self_rag",
        "trust_level": trust_level,
        "resource": final_content,
        "output_file": output_file,
        "sources": sources,
        "candidate_sources": [],
        "retrieval_check": retrieval_check,
        "grounding_check": grounding_check,
        "fallback_reason": "",
    }


def generate_trusted_quiz(
    topic: str,
    student_profile: Optional[Dict[str, Any]],
    question_types: List[str],
    count: int = 5,
    difficulty: str = "简单",
    top_k: int = 8,
    db_dir: str = DEFAULT_DB_DIR,
) -> Dict[str, Any]:
    """
    基于课程资料生成可信练习题。
    """
    client = SparkX2Client()
    task_type = "quiz"

    context, sources, _ = retrieve_course_context(topic, top_k=top_k, db_dir=db_dir)
    retrieval_check = check_retrieval_relevance(
        topic=topic,
        task_type=task_type,
        context=context,
        client=client,
    )

    if not check_passed(retrieval_check, "relevant"):
        return {
            "mode": "self_rag",
            "quiz": {
                "topic": topic,
                "difficulty": difficulty,
                "rag_mode": "self_rag",
                "questions": [],
            },
            "raw": "",
            "sources": sources,
            "retrieval_check": retrieval_check,
            "grounding_check": None,
            "message": "知识库中没有找到足够相关的课程资料，或检索可信性检查未通过/未知，未生成题目，避免普通大模型编题。",
        }

    student_context = build_student_context(student_profile)
    question_types_text = "、".join(question_types)

    prompt = f"""
你是一个可信课程题目生成助手。
请严格依据课程资料生成练习题。

知识点：
{topic}

题目类型：
{question_types_text}

题目数量：
{count}

题目难度：
{difficulty}

{student_context}

课程资料：
{context}

请只输出 JSON，不要输出 Markdown，不要输出解释文字。

JSON 格式如下：
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "rag_mode": "self_rag",
  "questions": [
    {{
      "id": 1,
      "knowledge_point": "本题考查的细分知识点",
      "type": "选择题",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "analysis": "答案解析，必须说明依据课程资料中的哪一点",
      "source_basis": ["[1]", "[2]"]
    }}
  ]
}}

出题要求：
1. 题目必须来自课程资料。
2. 不能编造课程资料之外的知识点。
3. 选择题必须有 A、B、C、D 四个选项。
4. 填空题、简答题、计算题也必须有答案和解析。
5. 每道题都必须有 knowledge_point 和 source_basis 字段。
6. knowledge_point 要写细分知识点，不要总是写大主题。
7. 如果课程资料不足以支持某类题，不要硬编。
"""

    raw = client.chat(
        user_input=prompt,
        system_prompt="你是严格依据课程资料生成题目的助手。",
        temperature=0.2,
        max_tokens=2400,
        thinking="disabled",
    )

    quiz = safe_json_loads(raw)
    if not isinstance(quiz, dict):
        quiz = {
            "topic": topic,
            "difficulty": difficulty,
            "rag_mode": "self_rag",
            "questions": [],
            "parse_error": "模型输出不是合法 JSON",
            "raw": raw,
        }

    grounding_check = check_generation_grounded(
        topic=topic,
        generated_text=json.dumps(quiz, ensure_ascii=False),
        context=context,
        client=client,
    )

    quiz["sources"] = sources
    quiz["retrieval_check"] = retrieval_check
    quiz["grounding_check"] = grounding_check

    return {
        "mode": "self_rag",
        "quiz": quiz,
        "raw": raw,
        "sources": sources,
        "retrieval_check": retrieval_check,
        "grounding_check": grounding_check,
    }
