try:
    from .spark_llm import SparkX2Client
except ImportError:
    from spark_llm import SparkX2Client


def build_learning_path_prompt(
    goal: str,
    student_profile: dict,
    days: int = 7
) -> str:
    weak_points = "、".join(student_profile.get("weak_points", []))

    prompt = f"""
你是一个个性化学习路径规划助手，请根据学生的学习目标和基础情况，为学生生成学习计划。

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}
- 薄弱知识点：{weak_points}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}

路径规划任务：
- 本次具体学习目标：{goal}
- 计划学习天数：{days}天

生成要求：
1. 根据学习目标拆分学习阶段。
2. 每一天都要有明确学习主题。
3. 每一天都要有具体学习任务。
4. 如果涉及学生薄弱知识点，要优先安排复习。
5. 学习顺序要从基础到进阶。
6. 每一天都要安排一个小练习或检测任务。
7. 内容不要太长，适合前端展示。
8. 不要输出无关内容。

请严格按照下面格式输出：

学习目标：
这里写学生的学习目标。

整体学习思路：
这里说明为什么这样安排学习顺序。

学习计划：

第1天：
- 学习主题：
- 学习任务：
- 练习任务：
- 完成标准：

第2天：
- 学习主题：
- 学习任务：
- 练习任务：
- 完成标准：

依次生成到第{days}天。

最后复习建议：
给出简短复习建议。
"""
    return prompt


def generate_learning_path(
    goal: str,
    student_profile: dict,
    days: int = 7
) -> str:
    prompt = build_learning_path_prompt(
        goal=goal,
        student_profile=student_profile,
        days=days
    )

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的个性化学习路径规划助手，擅长根据学生基础和薄弱点制定学习计划。",
        temperature=0.5,
        max_tokens=2000,
        thinking="disabled"
    )

    return result


if __name__ == "__main__":
    student_profile = {
        "level": "基础较弱",
        "course": "多媒体信息处理",
        "goal": "期末复习",
        "weak_points": ["LZW算法", "JPEG压缩"],
        "learning_style": "喜欢通俗解释和例子"
    }

    result = generate_learning_path(
        goal="3天掌握LZW算法",
        student_profile=student_profile,
        days=3
    )

    print(result)
