import json

try:
    from .spark_llm import SparkX2Client
    from .trusted_course_generator import generate_trusted_quiz
except ImportError:
    from spark_llm import SparkX2Client
    from trusted_course_generator import generate_trusted_quiz


def build_quiz_prompt(
    topic: str,
    student_profile: dict,
    question_types: list,
    count: int = 5,
    difficulty: str = "简单"
) -> str:
    weak_points = "、".join(student_profile.get("weak_points", []))
    question_types_text = "、".join(question_types)

    prompt = f"""
你是一个个性化题目生成助手，请根据学生情况生成学习检测题。

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}

出题任务：
- 知识点：{topic}
- 题目类型：{question_types_text}
- 题目数量：{count}道
- 题目难度：{difficulty}

出题要求：
1. 题目必须围绕指定知识点。
2. 题目难度要符合学生基础水平。
3. 如果该知识点属于学生薄弱点，题目要更偏基础理解和关键步骤。
4. 选择题必须提供4个选项，选项用A、B、C、D表示。
5. 填空题要有明确标准答案。
6. 简答题要给出参考答案和解析。
7. 计算题要给出计算过程和最终答案。
8. 每道题都必须包含答案和解析。
9. 不要输出 Markdown。
10. 不要输出多余解释，只输出 JSON。
11. 每道题必须包含 knowledge_point 字段，表示本题考查的细分知识点。
12. knowledge_point 不要总是写大主题，要尽量具体，例如“变量类型转换”“input输入类型”“for循环遍历”等。

请严格按照下面 JSON 格式输出：

{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": 1,
      "knowledge_point": "本题考查的细分知识点，例如：变量类型转换",
      "type": "选择题",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "analysis": "答案解析"
    }},
    {{
      "id": 2,
      "knowledge_point": "本题考查的细分知识点",
      "type": "填空题",
      "question": "题目内容",
      "options": [],
      "answer": "标准答案",
      "analysis": "答案解析"
    }},
    {{
      "id": 3,
      "knowledge_point": "本题考查的细分知识点",
      "type": "简答题",
      "question": "题目内容",
      "options": [],
      "answer": "参考答案",
      "analysis": "答案解析"
    }},
    {{
      "id": 4,
      "knowledge_point": "本题考查的细分知识点",
      "type": "计算题",
      "question": "题目内容",
      "options": [],
      "answer": "最终答案",
      "analysis": "详细计算过程"
    }}
  ]
}}
"""
    return prompt
def generate_plain_quiz(
    topic: str,
    student_profile: dict,
    question_types: list,
    count: int = 5,
    difficulty: str = "简单"
) -> str:
    """
    普通大模型出题：保留作为备用，不建议课程工作流默认使用。
    """
    prompt = build_quiz_prompt(
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=count,
        difficulty=difficulty
    )

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的学习检测题生成助手，擅长生成结构化题目、答案和解析。",
        temperature=0.4,
        max_tokens=2000,
        thinking="disabled"
    )

    return result


def _strip_code_fence(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _try_parse_quiz_json(text: str):
    cleaned = _strip_code_fence(text)
    attempts = [cleaned]

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")
    if object_start >= 0 and object_end > object_start:
        attempts.append(cleaned[object_start:object_end + 1])

    for candidate in attempts:
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None


def _has_questions(quiz) -> bool:
    return (
        isinstance(quiz, dict)
        and isinstance(quiz.get("questions"), list)
        and len(quiz["questions"]) > 0
    )


def generate_rag_quiz(
    topic: str,
    student_profile: dict,
    question_types: list,
    count: int = 5,
    difficulty: str = "简单",
    top_k: int = 5
) -> str:
    """
    RAG + Self-RAG 式可信出题。
    返回 JSON 字符串，兼容原来的 API 解析逻辑。
    """
    result = generate_trusted_quiz(
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=count,
        difficulty=difficulty,
        top_k=top_k
    )

    trusted_quiz = result.get("quiz", {}) if isinstance(result, dict) else {}
    if _has_questions(trusted_quiz):
        return json.dumps(trusted_quiz, ensure_ascii=False, indent=2)

    fallback_reason = ""
    if isinstance(result, dict):
        fallback_reason = result.get("message") or ""
    if not fallback_reason and isinstance(trusted_quiz, dict):
        fallback_reason = trusted_quiz.get("parse_error") or trusted_quiz.get("message") or ""
    if not fallback_reason:
        fallback_reason = "可信知识库链路未返回可用题目，已切换到普通出题兜底。"

    fallback_raw = generate_plain_quiz(
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=count,
        difficulty=difficulty
    )
    fallback_quiz = _try_parse_quiz_json(fallback_raw)

    if isinstance(fallback_quiz, dict):
        fallback_quiz.setdefault("topic", topic)
        fallback_quiz.setdefault("difficulty", difficulty)
        fallback_quiz["rag_mode"] = "plain_fallback"
        fallback_quiz["fallback_reason"] = fallback_reason
        return json.dumps(fallback_quiz, ensure_ascii=False, indent=2)

    return json.dumps({
        "topic": topic,
        "difficulty": difficulty,
        "rag_mode": "plain_fallback",
        "questions": [],
        "parse_error": "普通出题兜底输出不是合法 JSON",
        "fallback_reason": fallback_reason,
        "raw": fallback_raw
    }, ensure_ascii=False, indent=2)


def generate_quiz(
    topic: str,
    student_profile: dict,
    question_types: list,
    count: int = 5,
    difficulty: str = "简单"
) -> str:
    """
    默认题目生成入口。
    强制调用课程知识库 RAG，避免旧调用路径绕过课程资料。
    """
    return generate_rag_quiz(
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=count,
        difficulty=difficulty,
        top_k=8
    )

if __name__ == "__main__":
    student_profile = {
        "level": "基础较弱",
        "goal": "期末复习",
        "weak_points": ["LZW算法", "JPEG压缩"],
        "learning_style": "喜欢通俗解释和例子"
    }

    result = generate_quiz(
        topic="LZW算法",
        student_profile=student_profile,
        question_types=["选择题", "填空题", "简答题"],
        count=5,
        difficulty="简单"
    )

    print(result)
