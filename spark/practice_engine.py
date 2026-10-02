# practice_engine.py

import json
import re
import time
import uuid
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple


try:
    from .quiz_generator import generate_quiz
    from .student_memory import (
        init_db,
        get_student_profile,
        add_learning_record
    )
    from .dynamic_learning_path import generate_next_learning_step
    from .spark_llm import SparkX2Client
except ImportError:
    from quiz_generator import generate_quiz
    from student_memory import (
        init_db,
        get_student_profile,
        add_learning_record
    )
    from dynamic_learning_path import generate_next_learning_step
    from spark_llm import SparkX2Client


DB_PATH = os.getenv(
    "STUDENT_DB_PATH",
    str(Path(__file__).resolve().parent.parent / ".local-data" / "data" / "student_learning.db"),
)


# =========================
# 一、根据学生基础决定题量和难度
# =========================

def decide_question_count(student_profile: Dict[str, Any]) -> int:
    """
    根据学生基础水平决定题目数量。
    基础越弱，题量越少，避免一次性压力太大。
    基础越好，题量越多，用于检测掌握程度。
    """
    level = student_profile.get("level", "")

    if any(word in level for word in ["零基础", "基础较弱", "较弱", "初学"]):
        return 3

    if any(word in level for word in ["基础一般", "一般", "中等", "普通"]):
        return 5

    if any(word in level for word in ["基础较好", "较好", "良好"]):
        return 7

    if any(word in level for word in ["优秀", "熟练", "掌握较好", "很强"]):
        return 10

    return 5


def decide_difficulty(student_profile: Dict[str, Any], topic: str) -> str:
    """
    根据学生基础和薄弱点决定题目难度。
    如果当前知识点是薄弱点，优先生成简单题。
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

    if any(word in level for word in ["优秀", "熟练", "掌握较好", "很强"]):
        return "较难"

    return "简单"


def decide_question_types(student_profile: Dict[str, Any]) -> List[str]:
    """
    根据学生基础决定题型。
    基础弱：先选择题、填空题。
    基础一般：加入简答题。
    基础较好：加入计算题。
    """
    level = student_profile.get("level", "")

    if any(word in level for word in ["零基础", "基础较弱", "较弱", "初学"]):
        return ["选择题", "填空题"]

    if any(word in level for word in ["基础一般", "一般", "中等", "普通"]):
        return ["选择题", "填空题", "简答题"]

    return ["选择题", "填空题", "简答题", "计算题"]


# =========================
# 二、解析大模型生成的 JSON
# =========================

def extract_json(text: str) -> Dict[str, Any]:
    """
    从大模型返回内容中提取 JSON。
    有时候模型可能在 JSON 前后多输出文字，这里做容错处理。
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.S)

    if not match:
        raise ValueError("模型输出中没有找到合法 JSON。原始输出如下：\n" + text)

    json_text = match.group(0)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败：{e}\n原始 JSON：\n{json_text}")


def normalize_questions(
    quiz_data: Dict[str, Any],
    count: int,
    default_knowledge_point: str = ""
) -> List[Dict[str, Any]]:
    """
    统一题目格式，并限制题目数量。
    新增 knowledge_point 字段，用于追踪细分知识点掌握情况。
    """
    questions = quiz_data.get("questions", [])

    if not questions:
        raise ValueError("题目生成失败：questions 为空。")

    normalized = []

    for item in questions[:count]:
        q = {
            "id": item.get("id"),
            "knowledge_point": (
                item.get("knowledge_point")
                or item.get("sub_knowledge_point")
                or item.get("topic")
                or default_knowledge_point
            ),
            "type": item.get("type", "未知题型"),
            "question": item.get("question", ""),
            "options": item.get("options", []),
            "answer": item.get("answer", ""),
            "analysis": item.get("analysis", "")
        }

        if not q["question"]:
            continue

        normalized.append(q)

    if not normalized:
        raise ValueError("题目格式不正确，没有可用题目。")

    return normalized


# =========================
# 三、题库存储，可选但推荐
# =========================

def init_question_bank(db_path: str = DB_PATH) -> None:
    """
    初始化题库表。
    生成出来的题目先存入 question_bank，方便后续追踪。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        question_id TEXT PRIMARY KEY,
        knowledge_point TEXT NOT NULL,
        question_type TEXT,
        difficulty TEXT,
        question TEXT NOT NULL,
        options TEXT,
        answer TEXT,
        analysis TEXT,
        source TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_questions_to_bank(
    topic: str,
    difficulty: str,
    questions: List[Dict[str, Any]],
    source: str = "AI生成",
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    把生成的题目保存到 question_bank。
    返回带 question_id 的题目列表。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    saved_questions = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for q in questions:
        question_id = "Q_" + uuid.uuid4().hex[:12]

        cursor.execute("""
        INSERT INTO question_bank (
            question_id,
            knowledge_point,
            question_type,
            difficulty,
            question,
            options,
            answer,
            analysis,
            source,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            q.get("knowledge_point") or topic,
            q["type"],
            difficulty,
            q["question"],
            json.dumps(q["options"], ensure_ascii=False),
            str(q["answer"]),
            q["analysis"],
            source,
            now
        ))

        q = q.copy()
        q["question_id"] = question_id
        saved_questions.append(q)

    conn.commit()
    conn.close()

    return saved_questions


# =========================
# 四、学生真实作答和判分
# =========================

def show_question(index: int, question: Dict[str, Any]) -> None:
    """
    在终端展示题目。
    """
    print("\n" + "=" * 60)
    print(f"第 {index} 题：{question['type']}")
    print(question["question"])

    options = question.get("options", [])

    if options:
        print("\n选项：")
        for option in options:
            print(option)


def normalize_answer(answer: str) -> str:
    """
    标准化答案，方便选择题、填空题判断。
    """
    return str(answer).strip().upper().replace(" ", "").replace("。", "")


def judge_objective_answer(
    question: Dict[str, Any],
    user_answer: str
) -> Tuple[bool, str]:
    """
    判断选择题、填空题。
    """
    standard_answer = str(question.get("answer", ""))

    user = normalize_answer(user_answer)
    standard = normalize_answer(standard_answer)

    # 选择题只取 A/B/C/D
    if question["type"] == "选择题":
        if user:
            user = user[0]
        if standard:
            standard = standard[0]

    correct = user == standard

    reason = "客观题自动判分"

    return correct, reason


def judge_subjective_answer(
    question: Dict[str, Any],
    user_answer: str
) -> Tuple[bool, str]:
    """
    判断简答题、计算题。
    使用大模型根据参考答案进行判分。
    """
    prompt = f"""
请判断学生答案是否正确。

题目：
{question.get("question", "")}

题型：
{question.get("type", "")}

参考答案：
{question.get("answer", "")}

参考解析：
{question.get("analysis", "")}

学生答案：
{user_answer}

判分要求：
1. 如果学生答案表达不同但意思正确，也算正确。
2. 如果学生答案只答对一部分，算错误。
3. 只输出 JSON，不要输出 Markdown，不要输出其他文字。

输出格式：
{{
  "correct": true,
  "reason": "判分理由"
}}
"""

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个严格但公平的学习题目判分助手。",
        temperature=0.1,
        max_tokens=500,
        thinking="disabled"
    )

    try:
        data = extract_json(result)
        correct = bool(data.get("correct", False))
        reason = data.get("reason", "主观题模型判分")
        return correct, reason
    except Exception:
        # 兜底方案：模型判分失败时，用简单包含关系判断
        standard = normalize_answer(question.get("answer", ""))
        user = normalize_answer(user_answer)
        correct = standard in user or user in standard
        return correct, "主观题模型判分失败，使用简单规则兜底判断"


def judge_answer(
    question: Dict[str, Any],
    user_answer: str
) -> Tuple[bool, str]:
    """
    根据题型选择判分方式。
    """
    question_type = question.get("type", "")

    if question_type in ["选择题", "填空题"]:
        return judge_objective_answer(question, user_answer)

    return judge_subjective_answer(question, user_answer)


# =========================
# 五、完整练习流程
# =========================

def run_practice_session(
    student_id: str,
    topic: str
) -> Dict[str, Any]:
    """
    完整练习流程：
    1. 读取学生画像
    2. 根据基础决定题量、难度、题型
    3. 调用 quiz_generator 生成题目
    4. 学生真实作答
    5. 自动判分
    6. 保存学习记录
    """
    init_db()
    init_question_bank()

    student_profile = get_student_profile(student_id)

    if student_profile is None:
        raise ValueError(f"未找到学生画像：{student_id}，请先创建学生画像。")

    question_count = decide_question_count(student_profile)
    difficulty = decide_difficulty(student_profile, topic)
    question_types = decide_question_types(student_profile)

    print("\n[INFO] 当前学生画像：")
    print(f"学生ID：{student_id}")
    print(f"基础水平：{student_profile.get('level', '未知')}")
    print(f"学习目标：{student_profile.get('goal', '未知')}")
    print(f"薄弱知识点：{student_profile.get('weak_points', [])}")

    print("\n[INFO] 本次练习配置：")
    print(f"练习知识点：{topic}")
    print(f"题目数量：{question_count}")
    print(f"题目难度：{difficulty}")
    print(f"题目类型：{question_types}")

    print("\n[INFO] 正在生成题目，请稍等...")

    quiz_text = generate_quiz(
        topic=topic,
        student_profile=student_profile,
        question_types=question_types,
        count=question_count,
        difficulty=difficulty
    )

    quiz_data = extract_json(quiz_text)
    questions = normalize_questions(
        quiz_data=quiz_data,
        count=question_count,
        default_knowledge_point=topic
    )

    questions = save_questions_to_bank(
        topic=topic,
        difficulty=difficulty,
        questions=questions,
        source="AI生成"
    )

    print(f"\n[OK] 题目生成完成，共 {len(questions)} 道。")
    print("\n请开始作答。")

    correct_count = 0
    answer_records = []

    for index, question in enumerate(questions, start=1):
        show_question(index, question)

        start_time = time.time()
        user_answer = input("\n请输入你的答案：").strip()
        answer_time = round(time.time() - start_time, 2)

        correct, judge_reason = judge_answer(question, user_answer)

        if correct:
            correct_count += 1
            print("\n判分结果：正确")
        else:
            print("\n判分结果：错误")

        print(f"标准答案：{question.get('answer', '')}")
        print(f"解析：{question.get('analysis', '')}")
        print(f"判分说明：{judge_reason}")

        record_knowledge_point = question.get("knowledge_point") or topic

        add_learning_record(
            student_id=student_id,
            knowledge_point=record_knowledge_point,
            question_type=question.get("type", "未知题型"),
            correct=correct,
            answer_time=answer_time,
            difficulty=difficulty,
            question_id=question.get("question_id"),
            user_answer=user_answer,
            standard_answer=str(question.get("answer", ""))
        )

        answer_records.append({
            "question_id": question.get("question_id"),
            "knowledge_point": record_knowledge_point,
            "question_type": question.get("type"),
            "user_answer": user_answer,
            "standard_answer": question.get("answer"),
            "correct": correct,
            "answer_time": answer_time,
            "judge_reason": judge_reason
        })

    accuracy = round(correct_count / len(questions), 2)

    print("\n" + "=" * 60)
    print("本次练习结束")
    print(f"总题数：{len(questions)}")
    print(f"答对：{correct_count}")
    print(f"正确率：{int(accuracy * 100)}%")

    if accuracy >= 0.8:
        suggestion = "本知识点掌握较好，可以提高题目难度。"
    elif accuracy >= 0.6:
        suggestion = "本知识点基本掌握，建议继续做中等难度题巩固。"
    else:
        suggestion = "本知识点仍然薄弱，建议先回到学习资料重新复习基础概念。"

    print(f"学习建议：{suggestion}")

    try:
        dynamic_next_step = generate_next_learning_step(
            student_id=student_id,
            goal=student_profile.get("goal", topic),
            current_topic=topic
        )

        print("\n" + "=" * 60)
        print("动态路径调整结果：")
        print(json.dumps(dynamic_next_step, ensure_ascii=False, indent=2))

    except Exception as error:
        dynamic_next_step = {
            "error": str(error),
            "message": "动态路径生成失败，但本次练习记录已经保存。"
        }

    return {
        "student_id": student_id,
        "topic": topic,
        "question_count": len(questions),
        "difficulty": difficulty,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "suggestion": suggestion,
        "records": answer_records,
        "dynamic_next_step": dynamic_next_step
    }


if __name__ == "__main__":
    student_id = input("请输入学生ID，例如 S001：").strip()
    topic = input("请输入练习知识点，例如 LZW算法：").strip()

    result = run_practice_session(
        student_id=student_id,
        topic=topic
    )

    print("\n程序返回结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
