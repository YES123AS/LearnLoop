try:
    from .spark_llm import SparkX2Client
except ImportError:
    from spark_llm import SparkX2Client


def build_personalized_prompt(question: str, student_profile: dict) -> str:
    weak_points = "、".join(student_profile.get("weak_points", []))

    prompt = f"""
你是一个个性化学习助手，请根据学生的基础情况回答问题。

学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}

回答要求：
1. 回答要适合学生当前基础。
2. 如果学生基础较弱，要用通俗语言解释。
3. 先给直观理解，再给正式解释。
4. 尽量举一个简单例子。
5. 如果问题涉及学生薄弱知识点，要重点讲解。
6. 最后给出下一步学习建议。
7. 不要回答与学习无关的内容。

学生问题：
{question}
"""
    return prompt


def personalized_answer(question: str, student_profile: dict) -> str:
    prompt = build_personalized_prompt(question, student_profile)

    client = SparkX2Client()

    answer = client.chat_stream(
        user_input=prompt,
        system_prompt="你是一个专业、耐心、擅长因材施教的个性化学习助手。",
        temperature=0.7,
        thinking="disabled"
    )

    return answer




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

    question = "我不懂LZW算法，能不能简单讲讲？"

    answer = personalized_answer(question, student_profile)

    print(answer)
