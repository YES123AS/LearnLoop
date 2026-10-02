# workflow_manager.py

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional


try:
    from .learning_path_generator import generate_learning_path
    from .resource_generator import generate_learning_resource
    from .quiz_generator import generate_rag_quiz
    from .learning_analysis import analyze_learning_status
    from .spark_llm import SparkX2Client
except ImportError:
    from learning_path_generator import generate_learning_path
    from resource_generator import generate_learning_resource
    from quiz_generator import generate_rag_quiz
    from learning_analysis import analyze_learning_status
    from spark_llm import SparkX2Client


def recommend_next_content(*args, **kwargs):
    """
    运行时导入推荐 Agent，避免 agent_manager 与 workflow_manager 循环导入。
    """
    try:
        from .agent_manager import recommend_next_content as _recommend_next_content
    except ImportError:
        from agent_manager import recommend_next_content as _recommend_next_content

    return _recommend_next_content(*args, **kwargs)


# =========================
# 一、基础工具函数
# =========================

def safe_filename(text: str) -> str:
    """
    把中文或特殊字符处理成安全文件名。
    """
    text = re.sub(r'[\\/:*?"<>|]', "_", text)
    text = text.strip()
    return text[:30] if text else "学习资源"


def extract_days(user_input: str, default_days: int = 3) -> int:
    """
    从用户输入中提取学习天数。
    例如：
    - 3天掌握LZW算法 -> 3
    - 帮我安排5天学习计划 -> 5
    """
    match = re.search(r"(\d+)\s*天", user_input)
    if match:
        return int(match.group(1))
    return default_days


def extract_topic(user_input: str, extra_data: Dict[str, Any] = None) -> str:
    """
    提取学习主题。
    优先使用 extra_data["topic"]。
    如果没有，就从用户输入中做简单提取。
    """
    if extra_data and extra_data.get("topic"):
        return extra_data["topic"]

    patterns = [
        r"学习(.+)",
        r"掌握(.+)",
        r"复习(.+)",
        r"讲解(.+)",
        r"练习(.+)",
        r"生成(.+?)的",
        r"关于(.+?)的",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_input)
        if match:
            topic = match.group(1)
            topic = re.sub(r"(学习计划|学习资料|题目|练习题|讲解|视频|图解)", "", topic)
            topic = topic.strip("，。！？、 ")
            if topic:
                return topic

    return user_input.strip()


def decide_question_count(student_profile: Dict[str, Any]) -> int:
    """
    根据学生基础决定题目数量。
    """
    level = student_profile.get("level", "")

    if any(word in level for word in ["零基础", "基础较弱", "较弱", "初学"]):
        return 3

    if any(word in level for word in ["基础一般", "一般", "中等", "普通"]):
        return 5

    if any(word in level for word in ["基础较好", "较好", "良好"]):
        return 7

    if any(word in level for word in ["优秀", "熟练", "掌握较好"]):
        return 10

    return 5


def decide_difficulty(student_profile: Dict[str, Any], topic: str) -> str:
    """
    根据学生基础和薄弱点决定题目难度。
    """
    level = student_profile.get("level", "")
    weak_points = student_profile.get("weak_points", [])

    if topic in weak_points:
        return "简单"

    if any(word in level for word in ["零基础", "基础较弱", "较弱", "初学"]):
        return "简单"

    if any(word in level for word in ["基础一般", "一般", "中等", "普通"]):
        return "中等"

    if any(word in level for word in ["基础较好", "较好", "良好"]):
        return "中等"

    if any(word in level for word in ["优秀", "熟练", "掌握较好"]):
        return "较难"

    return "简单"


def decide_question_types(student_profile: Dict[str, Any]) -> List[str]:
    """
    根据学生基础决定题型。
    """
    level = student_profile.get("level", "")

    if any(word in level for word in ["零基础", "基础较弱", "较弱", "初学"]):
        return ["选择题", "填空题"]

    if any(word in level for word in ["基础一般", "一般", "中等", "普通"]):
        return ["选择题", "填空题", "简答题"]

    return ["选择题", "填空题", "简答题", "计算题"]


# =========================
# 二、工作流意图识别
# =========================

def detect_workflow_intent(user_input: str) -> str:
    """
    判断是否需要多 Agent 协作。
    返回：
    - full_learning_workflow：完整学习闭环
    - review_workflow：复习闭环
    - diagnosis_workflow：学情诊断闭环
    - single_agent：普通单 Agent 任务
    """

    full_keywords = [
        "学会", "掌握", "从零学习", "完整学习", "帮我安排学习并出题",
        "学习计划和题目", "资料和题目", "计划资料题目",
        "学习计划、学习资料和练习题", "学习计划、学习资料", "学习资料和练习题",
        "计划、资料和题目", "计划、资料和练习题"
    ]

    review_keywords = [
        "复习", "备考", "期末", "考试", "巩固"
    ]

    diagnosis_keywords = [
        "分析我的薄弱点", "学情分析", "哪里不会", "掌握情况",
        "正确率", "根据我的做题情况"
    ]

    if any(word in user_input for word in diagnosis_keywords):
        return "diagnosis_workflow"

    has_plan_need = any(word in user_input for word in ["学习计划", "学习路径", "安排", "规划"])
    has_resource_need = any(word in user_input for word in ["学习资料", "复习资料", "资料", "讲义"])
    has_quiz_need = any(word in user_input for word in ["题目", "练习题", "出题", "检测题"])
    has_learning_goal = any(word in user_input for word in ["掌握", "学会", "从零学习", "完整学习"])

    if (has_plan_need and has_resource_need) or (has_plan_need and has_quiz_need):
        return "full_learning_workflow"

    if extract_days(user_input, default_days=0) > 0 and has_learning_goal:
        return "full_learning_workflow"

    if any(word in user_input for word in full_keywords):
        return "full_learning_workflow"

    if any(word in user_input for word in review_keywords):
        return "review_workflow"

    return "single_agent"


# =========================
# 三、单个 Agent 步骤执行器
# =========================

def run_step(
    step_name: str,
    agent_name: str,
    func: Callable,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    执行一个 Agent 步骤。
    好处：
    1. 统一记录步骤状态
    2. 某个 Agent 失败时不会让整个程序直接崩掉
    3. 前端可以清晰展示每个 Agent 的执行结果
    """
    print(f"\n[WORKFLOW] 正在执行：{step_name} - {agent_name}")

    try:
        result = func(*args, **kwargs)

        return {
            "step_name": step_name,
            "agent_name": agent_name,
            "status": "success",
            "result": result,
            "error": None
        }

    except Exception as e:
        return {
            "step_name": step_name,
            "agent_name": agent_name,
            "status": "failed",
            "result": None,
            "error": str(e)
        }


# =========================
# 四、结果整合 Agent
# =========================

def summarize_workflow_result(
    user_input: str,
    student_profile: Dict[str, Any],
    workflow_result: Dict[str, Any]
) -> str:
    """
    协调总结 Agent：
    把多个 Agent 的输出整理成适合前端展示的最终结果。
    """
    client = SparkX2Client()

    prompt = f"""
你是一个多智能体学习系统的协调总结助手。
请根据多个 Agent 的执行结果，为学生整理一个清晰的最终学习方案。

学生原始需求：
{user_input}

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{"、".join(student_profile.get("weak_points", [])) if student_profile.get("weak_points") else "暂无"}
- 学习风格：{student_profile.get("learning_style", "未知")}

多 Agent 执行结果：
{json.dumps(workflow_result, ensure_ascii=False, indent=2)}

整理要求：
1. 先说明本次系统调用了哪些 Agent。
2. 再总结学习计划、学习资料、练习题、学情分析、推荐内容。
3. 如果某个 Agent 失败，要说明失败原因，但不要影响整体表达。
4. 语言要适合学生直接阅读。
5. 控制在 800 字以内。
6. 不要输出 JSON，直接输出自然语言总结。

请按照下面格式输出：

一、本次任务完成情况

二、学习安排

三、学习资料

四、练习检测

五、后续建议
"""

    summary = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的多智能体学习系统协调助手。",
        temperature=0.4,
        max_tokens=1200,
        thinking="disabled"
    )

    return summary


# =========================
# 五、完整学习工作流
# =========================

def full_learning_workflow(
    user_input: str,
    student_profile: Dict[str, Any],
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    完整学习工作流：
    适合用户说：
    - 帮我3天掌握LZW算法
    - 我想学会JPEG压缩，给我计划、资料和题目
    - 帮我从零学习Python基础
    """
    if extra_data is None:
        extra_data = {}

    topic = extract_topic(user_input, extra_data)
    days = extra_data.get("days", extract_days(user_input, default_days=3))

    question_count = extra_data.get("count", decide_question_count(student_profile))
    difficulty = extra_data.get("difficulty", decide_difficulty(student_profile, topic))
    question_types = extra_data.get("question_types", decide_question_types(student_profile))

    output_dir = Path("workflow_outputs")
    output_dir.mkdir(exist_ok=True)

    resource_file = output_dir / f"{safe_filename(topic)}_学习资料.md"

    workflow_result = {
        "workflow_type": "full_learning_workflow",
        "topic": topic,
        "days": days,
        "question_count": question_count,
        "difficulty": difficulty,
        "question_types": question_types,
        "steps": []
    }

    # 1. 规划 Agent：生成学习路径
    step_plan = run_step(
        step_name="学习路径规划",
        agent_name="规划 Agent",
        func=generate_learning_path,
        goal=f"{days}天掌握{topic}",
        student_profile=student_profile,
        days=days
    )
    workflow_result["steps"].append(step_plan)

    # 2. 资源 Agent：生成学习资料
    step_resource = run_step(
        step_name="学习资料生成",
        agent_name="资源 Agent",
        func=generate_learning_resource,
        topic=topic,
        output_file=str(resource_file),
        student_profile=student_profile,
        resource_type="完整学习资料"
    )
    workflow_result["steps"].append(step_resource)

    # 3. 题目 Agent：生成练习题
    step_quiz = run_step(
        step_name="RAG练习题生成",
        agent_name="可信题目 Agent",
        func=generate_rag_quiz,
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=question_count,
        difficulty=difficulty
    )
    workflow_result["steps"].append(step_quiz)

    # 4. 推荐 Agent：推荐下一步学习内容
    step_recommend = run_step(
        step_name="下一步推荐",
        agent_name="推荐 Agent",
        func=recommend_next_content,
        student_profile=student_profile,
        weak_points=student_profile.get("weak_points", []),
        mastered_points=student_profile.get("mastered_points", [])
    )
    workflow_result["steps"].append(step_recommend)

    # 5. 总结 Agent：整合多个 Agent 的输出
    summary = summarize_workflow_result(
        user_input=user_input,
        student_profile=student_profile,
        workflow_result=workflow_result
    )

    workflow_result["summary"] = summary

    return workflow_result


# =========================
# 六、复习工作流
# =========================

def review_workflow(
    user_input: str,
    student_profile: Dict[str, Any],
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    复习工作流：
    适合用户说：
    - 帮我复习LZW算法
    - 期末复习JPEG压缩
    - 帮我整理复习资料并出题
    """
    if extra_data is None:
        extra_data = {}

    topic = extract_topic(user_input, extra_data)
    days = extra_data.get("days", extract_days(user_input, default_days=2))

    question_count = extra_data.get("count", decide_question_count(student_profile))
    difficulty = extra_data.get("difficulty", decide_difficulty(student_profile, topic))
    question_types = extra_data.get("question_types", decide_question_types(student_profile))

    output_dir = Path("workflow_outputs")
    output_dir.mkdir(exist_ok=True)

    resource_file = output_dir / f"{safe_filename(topic)}_复习资料.md"

    workflow_result = {
        "workflow_type": "review_workflow",
        "topic": topic,
        "days": days,
        "question_count": question_count,
        "difficulty": difficulty,
        "question_types": question_types,
        "steps": []
    }

    # 1. 资源 Agent：先生成复习资料
    step_resource = run_step(
        step_name="复习资料生成",
        agent_name="资源 Agent",
        func=generate_learning_resource,
        topic=topic,
        output_file=str(resource_file),
        student_profile=student_profile,
        resource_type="复习资料"
    )
    workflow_result["steps"].append(step_resource)

    # 2. 规划 Agent：生成短期复习计划
    step_plan = run_step(
        step_name="复习计划生成",
        agent_name="规划 Agent",
        func=generate_learning_path,
        goal=f"{days}天复习{topic}",
        student_profile=student_profile,
        days=days
    )
    workflow_result["steps"].append(step_plan)

    # 3. 题目 Agent：生成检测题
    step_quiz = run_step(
        step_name="RAG复习检测题生成",
        agent_name="可信题目 Agent",
        func=generate_rag_quiz,
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=question_count,
        difficulty=difficulty
    )
    workflow_result["steps"].append(step_quiz)

    # 4. 推荐 Agent：给出复习建议
    step_recommend = run_step(
        step_name="复习建议生成",
        agent_name="推荐 Agent",
        func=recommend_next_content,
        student_profile=student_profile,
        weak_points=student_profile.get("weak_points", []),
        mastered_points=student_profile.get("mastered_points", [])
    )
    workflow_result["steps"].append(step_recommend)

    summary = summarize_workflow_result(
        user_input=user_input,
        student_profile=student_profile,
        workflow_result=workflow_result
    )

    workflow_result["summary"] = summary

    return workflow_result


# =========================
# 七、学情诊断工作流
# =========================

def diagnosis_workflow(
    user_input: str,
    student_profile: Dict[str, Any],
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    学情诊断工作流：
    适合用户说：
    - 帮我分析薄弱点，并推荐下一步学习
    - 根据我的做题情况生成补救计划
    - 分析我的掌握情况
    """
    if extra_data is None:
        extra_data = {}

    records = extra_data.get("records", [])

    workflow_result = {
        "workflow_type": "diagnosis_workflow",
        "steps": []
    }

    if not records:
        workflow_result["steps"].append({
            "step_name": "学情分析",
            "agent_name": "评估 Agent",
            "status": "failed",
            "result": None,
            "error": "缺少做题记录，无法进行学情分析。"
        })
        workflow_result["summary"] = "缺少做题记录，无法进行学情分析。请先完成练习题，再进行学情诊断。"
        return workflow_result

    # 1. 评估 Agent：分析学情
    step_evaluate = run_step(
        step_name="学情分析",
        agent_name="评估 Agent",
        func=analyze_learning_status,
        records=records,
        student_profile=student_profile
    )
    workflow_result["steps"].append(step_evaluate)

    weak_points = []

    if step_evaluate["status"] == "success":
        weak_points = step_evaluate["result"].get("weak_points", [])

    # 2. 推荐 Agent：根据薄弱点推荐下一步
    step_recommend = run_step(
        step_name="薄弱点推荐",
        agent_name="推荐 Agent",
        func=recommend_next_content,
        student_profile=student_profile,
        weak_points=weak_points or student_profile.get("weak_points", []),
        mastered_points=student_profile.get("mastered_points", [])
    )
    workflow_result["steps"].append(step_recommend)

    # 3. 规划 Agent：如果有薄弱点，生成补救计划
    if weak_points:
        topic = "、".join(weak_points)

        step_plan = run_step(
            step_name="薄弱点补救计划",
            agent_name="规划 Agent",
            func=generate_learning_path,
            goal=f"补救薄弱知识点：{topic}",
            student_profile=student_profile,
            days=3
        )
        workflow_result["steps"].append(step_plan)

        # 4. 题目 Agent：针对第一个薄弱点生成练习题
        first_weak_point = weak_points[0]
        question_count = decide_question_count(student_profile)
        difficulty = "简单"
        question_types = decide_question_types(student_profile)

        step_quiz = run_step(
            step_name="RAG薄弱点强化练习",
            agent_name="可信题目 Agent",
            func=generate_rag_quiz,
            topic=first_weak_point,
            student_profile=student_profile,
            question_types=question_types,
            count=question_count,
            difficulty=difficulty
        )
        workflow_result["steps"].append(step_quiz)

    summary = summarize_workflow_result(
        user_input=user_input,
        student_profile=student_profile,
        workflow_result=workflow_result
    )

    workflow_result["summary"] = summary

    return workflow_result


# =========================
# 八、统一工作流入口
# =========================

def workflow_dispatcher(
    user_input: str,
    student_profile: Dict[str, Any],
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    多 Agent 工作流总入口。
    """
    if extra_data is None:
        extra_data = {}

    workflow_intent = detect_workflow_intent(user_input)

    if workflow_intent == "full_learning_workflow":
        return full_learning_workflow(
            user_input=user_input,
            student_profile=student_profile,
            extra_data=extra_data
        )

    if workflow_intent == "review_workflow":
        return review_workflow(
            user_input=user_input,
            student_profile=student_profile,
            extra_data=extra_data
        )

    if workflow_intent == "diagnosis_workflow":
        return diagnosis_workflow(
            user_input=user_input,
            student_profile=student_profile,
            extra_data=extra_data
        )

    return {
        "workflow_type": "single_agent",
        "summary": "该请求不需要多 Agent 工作流处理，建议交给原 agent_dispatcher 处理。",
        "steps": []
    }


if __name__ == "__main__":
    student_profile = {
        "grade": "大二",
        "major": "智能科学与技术",
        "course": "多媒体信息处理",
        "level": "基础较弱",
        "goal": "期末复习",
        "weak_points": ["LZW算法", "JPEG压缩"],
        "learning_style": "喜欢通俗解释和例子"
    }

    user_input = "帮我3天掌握LZW算法，生成学习计划、学习资料和练习题"

    result = workflow_dispatcher(
        user_input=user_input,
        student_profile=student_profile,
        extra_data={
            "topic": "LZW算法",
            "days": 3
        }
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
