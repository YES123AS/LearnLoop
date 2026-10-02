from pathlib import Path
from typing import Any, Dict, List, Optional
import time

try:
    from .spark_llm import SparkX2Client
    from .trusted_course_generator import generate_trusted_resource
except ImportError:
    from spark_llm import SparkX2Client
    from trusted_course_generator import generate_trusted_resource


OUTPUT_FILE = "learning_resource.md"


def safe_chat(
    client: SparkX2Client,
    prompt: str,
    title: str,
    max_tokens: int = 900,
    temperature: float = 0.6,
    retry: int = 3
) -> str:
    """
    安全调用大模型：
    1. 每次只生成一小段
    2. 失败后自动重试
    3. 多次失败后返回错误提示，不让整个程序直接崩掉
    """
    last_error = None

    for i in range(retry):
        try:
            print(f"\n正在生成：{title}，第 {i + 1} 次尝试...")

            result = client.chat(
                user_input=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking="disabled"
            )

            if result and result.strip():
                print(f"{title} 生成成功")
                return result.strip()

            last_error = "模型返回了空内容"

        except Exception as e:
            last_error = e
            print(f"{title} 生成失败：{e}")

            # 第一次失败等 3 秒，第二次失败等 6 秒，第三次失败等 9 秒
            time.sleep(3 * (i + 1))

    return f"【{title} 生成失败】\n原因：{last_error}"


def save_section(file_path: str, section_title: str, content: str) -> None:
    """
    每生成一段，就立即追加写入文件。
    这样即使后面某一段失败，前面成功的内容也不会丢失。
    """
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n## {section_title}\n\n")
        f.write(content)
        f.write("\n")


def build_student_context(student_profile: Optional[Dict[str, Any]]) -> str:
    if not student_profile:
        return "学生信息：未提供，请按初学者水平生成。"

    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"

    return f"""
学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}
""".strip()


def generate_outline(
    client: SparkX2Client,
    topic: str,
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资源"
) -> str:
    student_context = build_student_context(student_profile)
    prompt = f"""
请为《{topic}》生成{resource_type}大纲。

{student_context}

要求：
1. 只生成大纲。
2. 不要写详细讲解。
3. 使用 Markdown 格式。
4. 控制在 500 字以内。
5. 内容要符合学生基础和学习风格。
"""
    return safe_chat(client, prompt, "学习资源大纲", max_tokens=600)


def generate_chapter(
    client: SparkX2Client,
    topic: str,
    chapter_title: str,
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资源"
) -> str:
    student_context = build_student_context(student_profile)
    prompt = f"""
请为《{topic}》生成一个章节的{resource_type}内容。

当前章节：{chapter_title}

{student_context}

要求：
1. 只生成当前章节，不要生成其他章节。
2. 语言通俗、直接，难度符合学生基础。
3. 结构包括：核心概念、简单解释、一个小例子。
4. 使用 Markdown 格式。
5. 控制在 800 字以内。
"""
    return safe_chat(client, prompt, chapter_title, max_tokens=900)


def generate_exercises(
    client: SparkX2Client,
    topic: str,
    student_profile: Optional[Dict[str, Any]] = None
) -> str:
    student_context = build_student_context(student_profile)
    prompt = f"""
请为《{topic}》生成练习题。

{student_context}

要求：
1. 生成 5 道选择题。
2. 生成 3 道简答题。
3. 题目要优先覆盖学生薄弱知识点。
4. 暂时不要给答案。
5. 使用 Markdown 格式。
6. 控制在 600 字以内。
"""
    return safe_chat(client, prompt, "练习题", max_tokens=700)


def generate_answers(
    client: SparkX2Client,
    topic: str,
    student_profile: Optional[Dict[str, Any]] = None
) -> str:
    student_context = build_student_context(student_profile)
    prompt = f"""
请为《{topic}》生成练习题参考答案。

{student_context}

要求：
1. 给出 5 道选择题答案。
2. 给出 3 道简答题参考答案。
3. 解释要简洁。
4. 使用 Markdown 格式。
5. 控制在 600 字以内。
"""
    return safe_chat(client, prompt, "参考答案", max_tokens=700)


def generate_plain_learning_resource(
    topic: str,
    output_file: str = OUTPUT_FILE,
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资源"
) -> str:
    """
    普通学习资料生成：保留作为备用。
    分多次请求模型，每次生成一小段。
    每生成成功一段，就立即保存到 Markdown 文件。
    """
    client = SparkX2Client()

    # 先清空旧文件
    Path(output_file).write_text(f"# {topic} {resource_type}\n", encoding="utf-8")

    # 1. 生成大纲
    outline = generate_outline(client, topic, student_profile, resource_type)
    save_section(output_file, "一、学习资源大纲", outline)

    # 2. 生成章节内容
    chapters: List[str] = [
        "第一章 基础概念",
        "第二章 核心原理",
        "第三章 关键步骤",
        "第四章 示例讲解",
        "第五章 常见问题与应用"
    ]

    for chapter_title in chapters:
        chapter_content = generate_chapter(
            client,
            topic,
            chapter_title,
            student_profile,
            resource_type
        )
        save_section(output_file, chapter_title, chapter_content)

    # 3. 生成练习题
    exercises = generate_exercises(client, topic, student_profile)
    save_section(output_file, "三、练习题", exercises)

    # 4. 生成参考答案
    answers = generate_answers(client, topic, student_profile)
    save_section(output_file, "四、参考答案", answers)

    print(f"\n普通资料生成结束。结果已保存到：{output_file}")
    return output_file


def generate_rag_learning_resource(
    topic: str,
    output_file: str = OUTPUT_FILE,
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资源",
    top_k: int = 5,
    fast_checks: Optional[bool] = None,
) -> str:
    """
    RAG + Self-RAG 式可信学习资料生成。
    """
    result = generate_trusted_resource(
        topic=topic,
        output_file=output_file,
        student_profile=student_profile,
        resource_type=resource_type,
        top_k=top_k,
        fast_checks=fast_checks,
    )

    return result["output_file"]


def generate_learning_resource(
    topic: str,
    output_file: str = OUTPUT_FILE,
    student_profile: Optional[Dict[str, Any]] = None,
    resource_type: str = "学习资源",
    fast_checks: Optional[bool] = None,
) -> str:
    """
    默认学习资料生成入口。
    强制使用课程知识库 RAG 生成，避免普通大模型脱离课程资料。
    """
    return generate_rag_learning_resource(
        topic=topic,
        output_file=output_file,
        student_profile=student_profile,
        resource_type=resource_type,
        top_k=5,
        fast_checks=fast_checks,
    )


if __name__ == "__main__":
    topic = "Python基础"
    generate_learning_resource(topic, OUTPUT_FILE)
