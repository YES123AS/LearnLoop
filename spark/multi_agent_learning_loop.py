import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from .learning_path_generator import generate_learning_path
    from .resource_generator import generate_learning_resource
    from .quiz_generator import generate_rag_quiz
    from .learning_analysis import analyze_learning_status
    from .student_memory import (
        DB_PATH,
        add_learning_record,
        get_student_profile,
        init_db,
    )
    from .spark_llm import SparkX2Client
    from .workflow_manager import (
        decide_difficulty,
        decide_question_count,
        decide_question_types,
        extract_days,
        extract_topic,
        safe_filename,
    )
    from .mistake_diagnosis import create_mistake_diagnosis_from_wrong_answer
    from .utils.json_utils import safe_json_loads
    from .utils.logger_utils import get_logger
except ImportError:
    from learning_path_generator import generate_learning_path
    from resource_generator import generate_learning_resource
    from quiz_generator import generate_rag_quiz
    from learning_analysis import analyze_learning_status
    from student_memory import (
        DB_PATH,
        add_learning_record,
        get_student_profile,
        init_db,
    )
    from spark_llm import SparkX2Client
    from workflow_manager import (
        decide_difficulty,
        decide_question_count,
        decide_question_types,
        extract_days,
        extract_topic,
        safe_filename,
    )
    from mistake_diagnosis import create_mistake_diagnosis_from_wrong_answer
    from utils.json_utils import safe_json_loads
    from utils.logger_utils import get_logger


logger = get_logger("multi_agent_loop", "logs/multi_agent_loop.log")


def run_loop_step(
    step_name: str,
    agent_name: str,
    func: Callable,
    *args,
    workflow_id: str = "",
    **kwargs,
) -> Dict[str, Any]:
    """
    统一执行闭环中的单个 Agent 步骤。
    """
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{workflow_id}] START {step_name} - {agent_name}")

    try:
        result = func(*args, **kwargs)
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{workflow_id}] SUCCESS {step_name} - {agent_name}")
        return {
            "step_name": step_name,
            "agent_name": agent_name,
            "status": "success",
            "result": result,
            "error": None,
            "started_at": start_time,
            "finished_at": end_time,
        }
    except Exception as error:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.error(f"[{workflow_id}] FAILED {step_name} - {agent_name}: {error}")
        return {
            "step_name": step_name,
            "agent_name": agent_name,
            "status": "failed",
            "result": None,
            "error": str(error),
            "started_at": start_time,
            "finished_at": end_time,
        }


def audit_with_llm(
    title: str,
    content: Any,
    criteria: List[str],
) -> Dict[str, Any]:
    """
    审核 Agent：检查计划、资料或题目是否满足基本要求。
    """
    client = SparkX2Client()

    prompt = f"""
你是多 Agent 学习系统中的审核 Agent。
请审核下面内容是否满足要求。

审核对象：
{title}

待审核内容：
{json.dumps(content, ensure_ascii=False, indent=2) if not isinstance(content, str) else content}

审核标准：
{chr(10).join(f"{index + 1}. {item}" for index, item in enumerate(criteria))}

请只输出 JSON，不要输出 Markdown，不要输出解释性文字。
格式如下：
{{
  "passed": true,
  "score": 0.9,
  "issues": [],
  "suggestions": ["改进建议1"]
}}
"""

    try:
        result = client.chat(
            user_input=prompt,
            system_prompt="你是严格但务实的学习内容审核助手。",
            temperature=0.1,
            max_tokens=700,
            thinking="disabled",
        )
        data = safe_json_loads(result)
        if isinstance(data, dict) and "passed" in data:
            return data
    except Exception as error:
        return {
            "passed": False,
            "score": 0.0,
            "status": "audit_failed",
            "issues": [f"审核 Agent 调用失败：{error}"],
            "suggestions": ["建议重新生成或人工检查。"],
        }

    return {
        "passed": False,
        "score": 0.0,
        "status": "audit_parse_failed",
        "issues": ["审核结果解析失败。"],
        "suggestions": ["建议重新生成或人工检查。"],
    }


def is_audit_passed(audit: Dict[str, Any], min_score: float = 0.75) -> bool:
    """
    判断审核是否真正通过。
    """
    try:
        score = float(audit.get("score", 0))
    except (TypeError, ValueError):
        score = 0.0

    return (
        isinstance(audit, dict)
        and audit.get("passed") is True
        and score >= min_score
    )


def run_step_with_audit(
    step_name: str,
    agent_name: str,
    func: Callable,
    audit_title: str,
    audit_criteria: List[str],
    max_retry: int = 2,
    result_transform: Optional[Callable] = None,
    workflow_id: str = "",
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    执行 Agent 步骤，并在审核不通过时自动重试生成。
    """
    audit_history = []
    step: Dict[str, Any] = {}
    audit: Optional[Dict[str, Any]] = None

    for retry_index in range(max_retry + 1):
        step = run_loop_step(
            step_name,
            agent_name,
            func,
            *args,
            workflow_id=workflow_id,
            **kwargs,
        )

        if step["status"] != "success":
            return {
                "step": step,
                "audit": None,
                "retry_count": retry_index,
                "audit_history": audit_history,
                "final_status": "step_failed",
            }

        content_for_audit = step["result"]

        if result_transform:
            try:
                content_for_audit = result_transform(step["result"])
            except Exception as error:
                content_for_audit = str(step["result"])
                step["transform_error"] = str(error)

        audit = audit_with_llm(
            title=audit_title,
            content=content_for_audit,
            criteria=audit_criteria,
        )

        audit_history.append(audit)

        if is_audit_passed(audit):
            return {
                "step": step,
                "audit": audit,
                "retry_count": retry_index,
                "audit_history": audit_history,
                "final_status": "success",
            }

        logger.warning(
            f"[{workflow_id}] AUDIT_RETRY {step_name} "
            f"{retry_index + 1}/{max_retry}"
        )

    return {
        "step": step,
        "audit": audit,
        "retry_count": max_retry,
        "audit_history": audit_history,
        "final_status": "audit_failed_after_retry",
    }


def build_step_summary(
    step: Dict[str, Any],
    audit: Optional[Dict[str, Any]] = None,
    retry_count: int = 0,
) -> str:
    """
    生成前端展示用的简短说明。
    """
    if step.get("status") == "failed":
        return f"{step.get('agent_name')} 执行失败：{step.get('error')}"

    if audit is not None and not audit.get("passed"):
        return f"{step.get('agent_name')} 已生成内容，但审核未通过。"

    if retry_count > 0:
        return f"{step.get('agent_name')} 重试 {retry_count} 次后审核通过。"

    return f"{step.get('agent_name')} 执行成功。"


def build_timeline_item(
    order: int,
    step: Dict[str, Any],
    audit: Optional[Dict[str, Any]] = None,
    retry_count: int = 0,
) -> Dict[str, Any]:
    """
    把 Agent 执行结果转换成前端可视化 timeline 节点。
    """
    audit_status = "not_required"
    audit_score = None

    if audit is not None:
        audit_status = "passed" if audit.get("passed") else "failed"
        audit_score = audit.get("score")

    if step.get("status") == "failed":
        display_status = "failed"
    elif audit is not None and not audit.get("passed"):
        display_status = "audit_failed"
    elif retry_count > 0:
        display_status = "success_after_retry"
    else:
        display_status = "success"

    return {
        "step_id": f"step_{order:02d}",
        "order": order,
        "agent_name": step.get("agent_name"),
        "step_name": step.get("step_name"),
        "status": display_status,
        "raw_status": step.get("status"),
        "audit_status": audit_status,
        "audit_score": audit_score,
        "retry_count": retry_count,
        "started_at": step.get("started_at"),
        "finished_at": step.get("finished_at"),
        "error": step.get("error"),
        "summary": build_step_summary(step, audit, retry_count),
    }


def read_resource_result(result: Any) -> str:
    """
    读取资源 Agent 输出内容，供审核 Agent 使用。
    """
    if isinstance(result, dict) and result.get("resource"):
        return str(result["resource"])[:6000]

    path = result.get("output_file") if isinstance(result, dict) else result

    try:
        return Path(path).read_text(encoding="utf-8")[:6000]
    except Exception:
        return str(result)


def normalize_answer(answer: Any) -> str:
    """
    标准化答案，方便客观题比较。
    """
    return str(answer).strip().upper().replace(" ", "").replace("。", "")


def parse_quiz_result(quiz_result: Any) -> Dict[str, Any]:
    """
    把 RAG 题目生成结果解析为 dict。
    """
    if isinstance(quiz_result, dict):
        if "quiz" in quiz_result and isinstance(quiz_result["quiz"], dict):
            return quiz_result["quiz"]
        return quiz_result

    if isinstance(quiz_result, str):
        data = safe_json_loads(quiz_result)
        if isinstance(data, dict):
            return data

    return {
        "topic": "未知知识点",
        "difficulty": "简单",
        "questions": [],
        "raw": quiz_result,
    }


def build_question_lookup(questions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    支持用 id、question_id 或顺序号匹配学生提交答案。
    """
    lookup = {}

    for index, question in enumerate(questions, start=1):
        keys = {
            str(index),
            str(question.get("id", "")),
            str(question.get("question_id", "")),
        }
        for key in keys:
            if key:
                lookup[key] = question

    return lookup


def judge_answer(question: Dict[str, Any], user_answer: Any) -> Tuple[bool, str]:
    """
    自动判分。
    客观题使用规则判分，主观题优先调用模型，失败时使用简单包含关系兜底。
    """
    question_type = question.get("type", "")
    standard_answer = question.get("answer", "")

    if question_type in ["选择题", "填空题"]:
        user = normalize_answer(user_answer)
        standard = normalize_answer(standard_answer)

        if question_type == "选择题":
            user = user[0] if user else ""
            standard = standard[0] if standard else ""

        return user == standard, "客观题规则判分"

    client = SparkX2Client()
    prompt = f"""
请判断学生答案是否正确。

题目：
{question.get("question", "")}

题型：
{question_type}

参考答案：
{standard_answer}

参考解析：
{question.get("analysis", "")}

学生答案：
{user_answer}

请只输出 JSON：
{{
  "correct": true,
  "reason": "判分理由"
}}
"""

    try:
        result = client.chat(
            user_input=prompt,
            system_prompt="你是严格但公平的学习题目判分助手。",
            temperature=0.1,
            max_tokens=500,
            thinking="disabled",
        )
        data = safe_json_loads(result)
        if isinstance(data, dict):
            return bool(data.get("correct", False)), data.get("reason", "主观题模型判分")
    except Exception:
        pass

    user = normalize_answer(user_answer)
    standard = normalize_answer(standard_answer)
    correct = bool(user and standard and (user in standard or standard in user))
    return correct, "主观题模型判分失败，使用简单包含关系兜底"


def evaluate_submitted_answers(
    submitted_answers: Dict[str, Any],
    quiz_data: Dict[str, Any],
    student_id: Optional[str],
    default_topic: str,
    difficulty: str,
    db_path: str = DB_PATH,
    student_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    评估学生提交答案，并在有 student_id 时写入学生记忆。
    """
    questions = quiz_data.get("questions", [])
    question_lookup = build_question_lookup(questions)
    answer_records = []

    for answer_key, user_answer in submitted_answers.items():
        question = question_lookup.get(str(answer_key))

        if question is None:
            answer_records.append({
                "question_id": str(answer_key),
                "knowledge_point": default_topic,
                "question_type": "未知题型",
                "user_answer": user_answer,
                "standard_answer": "",
                "correct": False,
                "answer_time": None,
                "judge_reason": "没有找到对应题目，无法判分。",
            })
            continue

        correct, judge_reason = judge_answer(question, user_answer)
        knowledge_point = question.get("knowledge_point") or default_topic
        question_type = question.get("type", "未知题型")
        question_id = question.get("question_id") or str(question.get("id", answer_key))

        record = {
            "question_id": question_id,
            "knowledge_point": knowledge_point,
            "question_type": question_type,
            "user_answer": user_answer,
            "standard_answer": question.get("answer", ""),
            "correct": correct,
            "answer_time": None,
            "difficulty": difficulty,
            "judge_reason": judge_reason,
        }
        answer_records.append(record)

        if student_id:
            add_learning_record(
                student_id=student_id,
                knowledge_point=knowledge_point,
                question_type=question_type,
                correct=correct,
                answer_time=None,
                difficulty=difficulty,
                question_id=str(question_id),
                user_answer=str(user_answer),
                standard_answer=str(question.get("answer", "")),
                db_path=db_path,
            )

            if not correct:
                try:
                    mistake_diagnosis = create_mistake_diagnosis_from_wrong_answer(
                        student_id=student_id,
                        question=question,
                        user_answer=user_answer,
                        difficulty=difficulty,
                        judge_reason=judge_reason,
                        student_profile=student_profile,
                        db_path=db_path,
                    )
                    record["mistake_diagnosis"] = mistake_diagnosis
                except Exception as error:
                    record["mistake_diagnosis"] = {
                        "status": "failed",
                        "error": str(error),
                    }

    return answer_records


def recommend_next_content_runtime(
    student_profile: Dict[str, Any],
    weak_points: List[str],
    mastered_points: Optional[List[str]] = None,
) -> str:
    """
    运行时导入推荐 Agent，避免和 agent_manager 形成循环导入。
    """
    try:
        from .agent_manager import recommend_next_content
    except ImportError:
        from agent_manager import recommend_next_content

    return recommend_next_content(
        student_profile=student_profile,
        weak_points=weak_points,
        mastered_points=mastered_points or [],
    )


def summarize_loop_result(
    user_input: str,
    student_profile: Dict[str, Any],
    loop_result: Dict[str, Any],
) -> str:
    """
    总结 Agent：整合所有 Agent 输出。
    """
    client = SparkX2Client()

    prompt = f"""
你是多 Agent 学习闭环系统的总结 Agent。
请把下面的闭环执行结果整理成适合学生和前端展示的总结。

学生需求：
{user_input}

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}

闭环结果：
{json.dumps(loop_result, ensure_ascii=False, indent=2)}

输出要求：
1. 说明已完成哪些 Agent 步骤。
2. 如果状态是 waiting_for_answers，提醒学生完成题目并提交答案。
3. 如果状态是 closed_loop_completed，总结答题结果、薄弱点、推荐内容和补救计划。
4. 控制在 700 字以内。
5. 不要输出 JSON，直接输出自然语言。
"""

    return client.chat(
        user_input=prompt,
        system_prompt="你是专业的多 Agent 学习闭环总结助手。",
        temperature=0.4,
        max_tokens=1000,
        thinking="disabled",
    )


def multi_agent_learning_loop(
    user_input: str,
    student_profile: Dict[str, Any],
    student_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    一键多 Agent 学习闭环：
    规划 -> 审核 -> RAG资料 -> 审核 -> RAG题目 -> 审核
    -> 等待答题 / 评估 -> 推荐 -> 补救规划 -> 总结。
    """
    if extra_data is None:
        extra_data = {}

    if student_id:
        init_db(db_path)

    topic = extra_data.get("topic") or extract_topic(user_input, extra_data)
    days = extra_data.get("days", extract_days(user_input, default_days=3))
    question_count = extra_data.get("count", decide_question_count(student_profile))
    difficulty = extra_data.get("difficulty", decide_difficulty(student_profile, topic))
    question_types = extra_data.get("question_types", decide_question_types(student_profile))
    submitted_answers = extra_data.get("submitted_answers")
    workflow_id = extra_data.get("workflow_id") or str(uuid.uuid4())
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_dir = Path(extra_data.get("output_dir", "loop_outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    resource_file = output_dir / f"{safe_filename(topic)}_闭环学习资料.md"

    loop_result: Dict[str, Any] = {
        "workflow_id": workflow_id,
        "loop_type": "multi_agent_learning_loop",
        "status": "running",
        "student_id": student_id,
        "topic": topic,
        "days": days,
        "question_count": question_count,
        "difficulty": difficulty,
        "question_types": question_types,
        "started_at": started_at,
        "finished_at": None,
        "steps": [],
        "audits": {},
        "audit_history": {},
        "timeline": [],
    }

    plan_result = run_step_with_audit(
        step_name="学习路径规划",
        agent_name="规划 Agent",
        func=generate_learning_path,
        audit_title="学习路径",
        audit_criteria=[
            "路径应符合学生基础和学习目标。",
            "学习任务应有先后顺序。",
            "内容应覆盖用户指定主题。",
        ],
        max_retry=2,
        workflow_id=workflow_id,
        goal=f"{days}天掌握{topic}",
        student_profile=student_profile,
        days=days,
    )
    loop_result["steps"].append(plan_result["step"])
    loop_result["audits"]["plan"] = plan_result["audit"]
    loop_result["audit_history"]["plan"] = plan_result["audit_history"]
    loop_result["timeline"].append(
        build_timeline_item(
            order=1,
            step=plan_result["step"],
            audit=plan_result["audit"],
            retry_count=plan_result["retry_count"],
        )
    )

    resource_result = run_step_with_audit(
        step_name="RAG可信学习资料生成",
        agent_name="资源 Agent",
        func=generate_learning_resource,
        audit_title="学习资料",
        audit_criteria=[
            "资料应围绕课程内容生成。",
            "资料应适合学生基础。",
            "资料应包含核心概念、解释、例子和练习建议。",
        ],
        max_retry=2,
        result_transform=read_resource_result,
        workflow_id=workflow_id,
        topic=topic,
        output_file=str(resource_file),
        student_profile=student_profile,
        resource_type="闭环学习资料",
    )
    loop_result["steps"].append(resource_result["step"])
    loop_result["audits"]["resource"] = resource_result["audit"]
    loop_result["audit_history"]["resource"] = resource_result["audit_history"]
    loop_result["timeline"].append(
        build_timeline_item(
            order=2,
            step=resource_result["step"],
            audit=resource_result["audit"],
            retry_count=resource_result["retry_count"],
        )
    )

    quiz_result = run_step_with_audit(
        step_name="RAG可信练习题生成",
        agent_name="题目 Agent",
        func=generate_rag_quiz,
        audit_title="练习题",
        audit_criteria=[
            "题目应包含题干。",
            "题目应包含答案。",
            "题目应包含解析。",
            "题目应包含细分知识点 knowledge_point。",
            "题目数量应符合要求。",
            "选择题应包含 A、B、C、D 四个选项。",
        ],
        max_retry=2,
        result_transform=parse_quiz_result,
        workflow_id=workflow_id,
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=question_count,
        difficulty=difficulty,
        top_k=8,
    )
    loop_result["steps"].append(quiz_result["step"])
    loop_result["audits"]["quiz"] = quiz_result["audit"]
    loop_result["audit_history"]["quiz"] = quiz_result["audit_history"]
    loop_result["timeline"].append(
        build_timeline_item(
            order=3,
            step=quiz_result["step"],
            audit=quiz_result["audit"],
            retry_count=quiz_result["retry_count"],
        )
    )

    quiz_data = parse_quiz_result(quiz_result["step"]["result"])
    loop_result["quiz"] = quiz_data

    if not submitted_answers:
        loop_result["status"] = "waiting_for_answers"
        loop_result["message"] = "计划、资料和题目已经生成，等待学生提交答案。"
        loop_result["summary"] = summarize_loop_result(user_input, student_profile, loop_result)
        return loop_result

    answer_records = evaluate_submitted_answers(
        submitted_answers=submitted_answers,
        quiz_data=quiz_data,
        student_id=student_id,
        default_topic=topic,
        difficulty=difficulty,
        db_path=db_path,
        student_profile=student_profile,
    )
    loop_result["answer_records"] = answer_records

    step_evaluate = run_loop_step(
        step_name="答题评估与学情分析",
        agent_name="评估 Agent",
        func=analyze_learning_status,
        records=answer_records,
        student_profile=student_profile,
    )
    loop_result["steps"].append(step_evaluate)

    analysis = step_evaluate["result"] if step_evaluate["status"] == "success" else {}
    weak_points = analysis.get("weak_points", []) if isinstance(analysis, dict) else []
    mastered_points = analysis.get("mastered_points", []) if isinstance(analysis, dict) else []

    step_recommend = run_loop_step(
        step_name="下一步推荐",
        agent_name="推荐 Agent",
        func=recommend_next_content_runtime,
        student_profile=student_profile,
        weak_points=weak_points or student_profile.get("weak_points", []),
        mastered_points=mastered_points or student_profile.get("mastered_points", []),
    )
    loop_result["steps"].append(step_recommend)

    remedial_goal = (
        f"补救薄弱知识点：{'、'.join(weak_points)}"
        if weak_points else f"巩固当前知识点：{topic}"
    )
    step_remedial_plan = run_loop_step(
        step_name="薄弱点补救路径",
        agent_name="补救规划 Agent",
        func=generate_learning_path,
        goal=remedial_goal,
        student_profile=student_profile,
        days=extra_data.get("remedial_days", 3),
    )
    loop_result["steps"].append(step_remedial_plan)

    loop_result["status"] = "closed_loop_completed"
    loop_result["summary"] = summarize_loop_result(user_input, student_profile, loop_result)

    return loop_result


def multi_agent_learning_loop_by_student(
    user_input: str,
    student_id: str,
    extra_data: Optional[Dict[str, Any]] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    根据 student_id 自动读取学生画像，再执行多 Agent 学习闭环。
    """
    if extra_data is None:
        extra_data = {}

    init_db(db_path)
    student_profile = get_student_profile(student_id, db_path)

    if student_profile is None:
        raise ValueError(f"未找到学生 {student_id} 的画像，请先创建学生画像。")

    return multi_agent_learning_loop(
        user_input=user_input,
        student_profile=student_profile,
        student_id=student_id,
        extra_data=extra_data,
        db_path=db_path,
    )


if __name__ == "__main__":
    profile = {
        "grade": "大二",
        "major": "智能科学与技术",
        "course": "多媒体信息处理",
        "level": "基础较弱",
        "goal": "期末复习",
        "weak_points": ["LZW算法", "JPEG压缩"],
        "learning_style": "喜欢通俗解释和例子",
    }

    result = multi_agent_learning_loop(
        user_input="帮我3天掌握LZW算法，生成计划、资料、题目，并形成学习闭环",
        student_profile=profile,
        student_id="S001",
        extra_data={
            "topic": "LZW算法",
            "days": 3,
            "count": 3,
        },
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
