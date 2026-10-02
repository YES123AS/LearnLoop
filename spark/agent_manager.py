from typing import Dict, Any, List

try:
    from .personalized_chat import personalized_answer
    from .resource_generator import generate_learning_resource
    from .knowledge_base.rag_answer import rag_answer
    from .knowledge_base.rag_resource import generate_rag_resource
    from .trusted_course_generator import generate_trusted_answer, generate_trusted_resource
    from .learning_path_generator import generate_learning_path
    from .learning_analysis import analyze_learning_status
    from .student_memory import get_learning_records, get_student_profile
    from .workflow_manager import detect_workflow_intent, workflow_dispatcher
    from .langgraph_learning_loop import (
        multi_agent_learning_loop,
        multi_agent_learning_loop_by_student,
    )
    from .spark_llm import SparkX2Client
except ImportError:
    from personalized_chat import personalized_answer
    from resource_generator import generate_learning_resource
    from knowledge_base.rag_answer import rag_answer
    from knowledge_base.rag_resource import generate_rag_resource
    from trusted_course_generator import generate_trusted_answer, generate_trusted_resource
    from learning_path_generator import generate_learning_path
    from learning_analysis import analyze_learning_status
    from student_memory import get_learning_records, get_student_profile
    from workflow_manager import detect_workflow_intent, workflow_dispatcher
    from langgraph_learning_loop import (
        multi_agent_learning_loop,
        multi_agent_learning_loop_by_student,
    )
    from spark_llm import SparkX2Client


def detect_intent(user_input: str) -> str:
    """
    简单意图识别：
    根据用户输入中的关键词判断应该调用哪个 Agent。
    """

    if any(word in user_input for word in ["学习闭环", "完整闭环", "多Agent", "多 Agent", "协同学习", "规划资源题目评估推荐"]):
        return "learning_loop"

    if any(word in user_input for word in ["生成资料", "学习资料", "讲义", "复习资料", "知识点总结"]):
        return "resource"

    if any(word in user_input for word in ["学习计划", "学习路径", "安排", "规划", "几天学会"]):
        return "plan"

    if any(word in user_input for word in ["分析", "薄弱点", "正确率", "掌握情况", "学情"]):
        return "evaluate"

    if any(word in user_input for word in ["推荐", "下一步", "接下来学什么", "复习什么"]):
        return "recommend"

    return "qa"


def recommend_next_content(
    student_profile: Dict[str, Any],
    weak_points: List[str],
    mastered_points: List[str] = None
) -> str:
    """
    推荐 Agent：
    根据学生薄弱点和学习目标，推荐下一步学习内容。
    """

    if mastered_points is None:
        mastered_points = []

    weak_text = "、".join(weak_points) if weak_points else "暂无"
    mastered_text = "、".join(mastered_points) if mastered_points else "暂无"

    prompt = f"""
你是一个个性化学习推荐助手，请根据学生情况推荐下一步学习内容。

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}

当前掌握情况：
- 薄弱知识点：{weak_text}
- 已掌握知识点：{mastered_text}

推荐要求：
1. 优先推荐薄弱或待强化知识点相关内容。
2. 推荐顺序要从基础到进阶。
3. 如果薄弱知识点中包含掌握度、近期表现或建议难度，请结合这些信息推荐。
4. 每个推荐内容要说明推荐理由。
5. 给出简单的学习任务。
6. 控制在500字以内。

请按照下面格式输出：

一、优先学习内容

二、推荐理由

三、具体学习任务

四、预计学习效果
"""

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的个性化学习推荐助手。",
        temperature=0.5,
        max_tokens=1000,
        thinking="disabled"
    )

    return result


def agent_dispatcher(
    user_input: str,
    student_profile: Dict[str, Any],
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    多智能体调度器：
    1. 先判断是否是复杂任务
    2. 如果是复杂任务，调用多 Agent 工作流
    3. 如果不是复杂任务，继续使用原来的单 Agent 分发
    """

    if extra_data is None:
        extra_data = {}

    intent = detect_intent(user_input)

    if intent == "learning_loop":
        return multi_agent_learning_loop(
            user_input=user_input,
            student_profile=student_profile,
            student_id=extra_data.get("student_id"),
            extra_data=extra_data
        )

    workflow_intent = detect_workflow_intent(user_input)

    if workflow_intent != "single_agent":
        return workflow_dispatcher(
            user_input=user_input,
            student_profile=student_profile,
            extra_data=extra_data
        )

    if intent == "qa":
        rag_result = generate_trusted_answer(
            question=user_input,
            student_profile=student_profile,
            top_k=6
        )

        return {
            "agent": "Self-RAG可信问答 Agent",
            "intent": intent,
            "result": rag_result["answer"],
            "sources": rag_result.get("sources", []),
            "candidate_sources": rag_result.get("candidate_sources", []),
            "retrieval_check": rag_result.get("retrieval_check"),
            "grounding_check": rag_result.get("grounding_check"),
            "mode": rag_result.get("mode"),
            "trust_level": rag_result.get("trust_level", "unknown"),
            "fallback_reason": rag_result.get("fallback_reason", ""),
        }

    elif intent == "resource":
        topic = extra_data.get("topic", user_input)

        rag_result = generate_trusted_resource(
            topic=topic,
            student_profile=student_profile,
            resource_type=extra_data.get("resource_type", "学习资料"),
            output_file=extra_data.get("output_file", "trusted_learning_resource.md"),
            top_k=8
        )

        return {
            "agent": "Self-RAG可信资源 Agent",
            "intent": intent,
            "result": rag_result["resource"],
            "output_file": rag_result["output_file"],
            "sources": rag_result.get("sources", []),
            "candidate_sources": rag_result.get("candidate_sources", []),
            "retrieval_check": rag_result.get("retrieval_check"),
            "grounding_check": rag_result.get("grounding_check"),
            "mode": rag_result.get("mode"),
            "trust_level": rag_result.get("trust_level", "unknown"),
            "fallback_reason": rag_result.get("fallback_reason", ""),
        }

    elif intent == "plan":
        goal = extra_data.get("goal", user_input)
        days = extra_data.get("days", 3)

        result = generate_learning_path(
            goal=goal,
            student_profile=student_profile,
            days=days
        )

        return {
            "agent": "规划 Agent",
            "intent": intent,
            "result": result
        }

    elif intent == "evaluate":
        records = extra_data.get("records", [])

        if not records:
            return {
                "agent": "评估 Agent",
                "intent": intent,
                "result": "缺少做题记录，无法进行学情分析。"
            }

        result = analyze_learning_status(
            records=records,
            student_profile=student_profile
        )

        return {
            "agent": "评估 Agent",
            "intent": intent,
            "result": result
        }

    elif intent == "recommend":
        weak_points = extra_data.get("weak_points")

        if weak_points is None:
            weak_point_details = student_profile.get("weak_point_details", [])
            weak_points = [
                f"{item['knowledge_point']}，掌握度{item.get('mastery_score', 0)}，建议难度{item.get('next_difficulty', '中等')}"
                for item in weak_point_details
            ]

        if not weak_points:
            weak_points = student_profile.get("weak_points", [])

        mastered_points = extra_data.get("mastered_points", [])

        result = recommend_next_content(
            student_profile=student_profile,
            weak_points=weak_points,
            mastered_points=mastered_points
        )

        return {
            "agent": "推荐 Agent",
            "intent": intent,
            "result": result
        }

    else:
        return {
            "agent": "未知 Agent",
            "intent": intent,
            "result": "暂时无法识别用户意图。"
        }


def agent_dispatcher_by_student(
    user_input: str,
    student_id: str,
    extra_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    根据 student_id 自动读取学生画像，再调用原来的 agent_dispatcher。
    学情分析场景会自动从数据库读取做题记录。
    """

    if extra_data is None:
        extra_data = {}

    student_profile = get_student_profile(student_id)

    if student_profile is None:
        return {
            "agent": "系统",
            "intent": "unknown",
            "result": f"未找到学生 {student_id} 的画像，请先创建学生画像。"
        }

    intent = detect_intent(user_input)

    if intent == "learning_loop":
        extra_data["student_id"] = student_id

    if intent == "evaluate":
        extra_data["records"] = get_learning_records(student_id)

    return agent_dispatcher(
        user_input=user_input,
        student_profile=student_profile,
        extra_data=extra_data
    )


if __name__ == "__main__":
    student_profile = {
        "level": "基础较弱",
        "course": "多媒体信息处理",
        "goal": "期末复习",
        "weak_points": ["LZW算法", "JPEG压缩"],
        "learning_style": "喜欢通俗解释和例子"
    }

    user_input = "帮我生成LZW算法的学习资料"

    result = agent_dispatcher(
        user_input=user_input,
        student_profile=student_profile,
        extra_data={
            "topic": "LZW算法",
            "resource_type": "完整学习资料"
        }
    )

    print(result)
