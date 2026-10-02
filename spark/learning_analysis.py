from typing import List, Dict, Any

try:
    from .spark_llm import SparkX2Client
    from .knowledge_tracing import analyze_knowledge_tracing
except ImportError:
    from spark_llm import SparkX2Client
    from knowledge_tracing import analyze_knowledge_tracing


def build_analysis_prompt(
    student_profile: Dict[str, Any],
    analysis_result: List[Dict[str, Any]]
) -> str:
    """
    构造学情分析 Prompt，让大模型根据统计结果生成学习建议。
    """

    weak_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] in ["薄弱", "待强化"]
    ]

    basic_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] == "基本掌握"
    ]

    mastered_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] == "掌握较好"
    ]

    analysis_text = ""

    for item in analysis_result:
        analysis_text += (
            f"- {item['knowledge_point']}："
            f"共做{item['total']}题，"
            f"答对{item['correct']}题，"
            f"总体正确率{int(item['accuracy'] * 100)}%，"
            f"近期正确率{int(item.get('recent_accuracy', 0) * 100)}%，"
            f"难度表现{item.get('difficulty_score', 0)}，"
            f"作答速度{item.get('speed_score', 0)}，"
            f"稳定性{item.get('stability_score', 0)}，"
            f"综合掌握度{item.get('mastery_score', 0)}，"
            f"掌握情况：{item['mastery_level']}，"
            f"建议下次题目难度：{item.get('next_difficulty', '中等')}\n"
        )

    prompt = f"""
你是一个个性化学习分析助手，请根据学生历史答题序列和知识追踪结果，分析学生当前学习情况，并给出后续学习建议。

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}

知识追踪分析结果：
{analysis_text}

系统初步判断：
- 薄弱或待强化知识点：{"、".join(weak_points) if weak_points else "暂无"}
- 基本掌握知识点：{"、".join(basic_points) if basic_points else "暂无"}
- 掌握较好知识点：{"、".join(mastered_points) if mastered_points else "暂无"}

说明：
综合掌握度 mastery_score 不是单纯正确率，而是综合考虑总体正确率、近期正确率、题目难度、作答速度和表现稳定性后得到的动态掌握概率。

生成要求：
1. 先总结学生整体学习情况。
2. 明确指出薄弱和待强化知识点。
3. 分析薄弱原因，语言要通俗。
4. 给出后续学习建议。
5. 给出下一步推荐学习内容。
6. 结合建议题目难度进行推荐。
7. 不要输出太长，控制在600字以内。
8. 适合前端直接展示。

请按照下面格式输出：

一、整体学习情况

二、薄弱知识点分析

三、后续学习建议

四、下一步推荐内容
"""
    return prompt


def analyze_learning_status(
    records: List[Dict[str, Any]],
    student_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    学情分析主函数：
    1. 基于历史答题序列计算知识追踪得分
    2. 判断掌握情况
    3. 调用大模型生成个性化分析建议
    """

    analysis_result = analyze_knowledge_tracing(records)

    weak_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] in ["薄弱", "待强化"]
    ]

    basic_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] == "基本掌握"
    ]

    mastered_points = [
        item["knowledge_point"]
        for item in analysis_result
        if item["mastery_level"] == "掌握较好"
    ]

    prompt = build_analysis_prompt(
        student_profile=student_profile,
        analysis_result=analysis_result
    )

    client = SparkX2Client()

    ai_analysis = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的学情分析助手，擅长根据学生历史学习序列分析薄弱点并给出学习建议。",
        temperature=0.5,
        max_tokens=1200,
        thinking="disabled"
    )

    return {
        "statistics": analysis_result,
        "weak_points": weak_points,
        "basic_points": basic_points,
        "mastered_points": mastered_points,
        "ai_analysis": ai_analysis
    }


if __name__ == "__main__":
    student_profile = {
        "level": "基础较弱",
        "course": "多媒体信息处理",
        "goal": "期末复习",
        "learning_style": "喜欢通俗解释和例子"
    }

    records = [
        {
            "knowledge_point": "LZW算法",
            "question_type": "选择题",
            "correct": False,
            "answer_time": 35,
            "difficulty": "简单",
            "submit_time": "2026-06-01 10:00:00",
        },
        {
            "knowledge_point": "LZW算法",
            "question_type": "填空题",
            "correct": False,
            "answer_time": 50,
            "difficulty": "简单",
            "submit_time": "2026-06-01 10:05:00",
        },
        {
            "knowledge_point": "LZW算法",
            "question_type": "简答题",
            "correct": True,
            "answer_time": 80,
            "difficulty": "中等",
            "submit_time": "2026-06-01 10:10:00",
        },

        {
            "knowledge_point": "JPEG压缩",
            "question_type": "选择题",
            "correct": False,
            "answer_time": 25,
            "difficulty": "简单",
            "submit_time": "2026-06-01 10:15:00",
        },
        {
            "knowledge_point": "JPEG压缩",
            "question_type": "简答题",
            "correct": False,
            "answer_time": 160,
            "difficulty": "中等",
            "submit_time": "2026-06-01 10:20:00",
        },

        {
            "knowledge_point": "颜色直方图",
            "question_type": "选择题",
            "correct": True,
            "answer_time": 25,
            "difficulty": "简单",
            "submit_time": "2026-06-01 10:25:00",
        },
        {
            "knowledge_point": "颜色直方图",
            "question_type": "填空题",
            "correct": True,
            "answer_time": 50,
            "difficulty": "中等",
            "submit_time": "2026-06-01 10:30:00",
        },
        {
            "knowledge_point": "颜色直方图",
            "question_type": "简答题",
            "correct": True,
            "answer_time": 90,
            "difficulty": "困难",
            "submit_time": "2026-06-01 10:35:00",
        },
    ]

    result = analyze_learning_status(
        records=records,
        student_profile=student_profile
    )

    print(result)
