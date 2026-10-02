# mistake_diagnosis.py

import json
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from .spark_llm import SparkX2Client
    from .student_memory import DB_PATH, get_student_profile, init_db
    from .trusted_course_generator import retrieve_course_context
except ImportError:
    from spark_llm import SparkX2Client
    from student_memory import DB_PATH, get_student_profile, init_db
    from trusted_course_generator import retrieve_course_context


ERROR_TYPES = [
    "概念不清",
    "步骤遗漏",
    "公式误用",
    "计算错误",
    "审题错误",
    "知识迁移弱",
]


def get_conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def safe_json_loads(text: str) -> Any:
    """
    尽量从大模型输出中解析 JSON。
    兼容 ```json ... ``` 或前后带说明文字的情况。
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


def normalize_answer(answer: Any) -> str:
    return str(answer).strip().upper().replace(" ", "").replace("。", "")


def ensure_mistake_tables(db_path: str = DB_PATH) -> None:
    """
    初始化智能错题本表。
    不修改原来的 learning_record 表，避免影响原系统。
    """
    init_db(db_path)

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wrong_question_book (
        mistake_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        question_id TEXT,
        knowledge_point TEXT NOT NULL,
        question_type TEXT,
        difficulty TEXT,
        question TEXT NOT NULL,
        options TEXT,
        user_answer TEXT,
        standard_answer TEXT,
        standard_analysis TEXT,
        judge_reason TEXT,

        error_types TEXT,
        diagnosis TEXT,
        missing_points TEXT,
        remediation_micro_lesson TEXT,
        recommended_practice TEXT,
        variant_questions TEXT,
        sources TEXT,

        status TEXT DEFAULT '未修复',
        retry_count INTEGER DEFAULT 0,
        last_retry_result TEXT,
        created_at TEXT,
        updated_at TEXT,
        fixed_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def format_student_context(student_profile: Optional[Dict[str, Any]]) -> str:
    if not student_profile:
        return "学生画像：未提供。"

    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"

    return f"""
学生画像：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}
- 已知薄弱点：{weak_points}
""".strip()


def fallback_diagnosis(
    question: Dict[str, Any],
    user_answer: Any,
    judge_reason: str = "",
) -> Dict[str, Any]:
    """
    当大模型诊断失败时，给一个保守兜底结果，保证系统不崩。
    """
    knowledge_point = (
        question.get("knowledge_point")
        or question.get("sub_knowledge_point")
        or question.get("topic")
        or "未知知识点"
    )
    question_type = question.get("type", "未知题型")

    if question_type in ["选择题", "填空题"]:
        error_types = ["概念不清", "审题错误"]
    elif question_type in ["计算题"]:
        error_types = ["步骤遗漏", "计算错误"]
    else:
        error_types = ["概念不清", "知识迁移弱"]

    return {
        "error_types": error_types,
        "diagnosis": f"学生在“{knowledge_point}”相关题目上作答错误，可能存在基础概念理解不清或关键步骤遗漏。",
        "missing_points": [knowledge_point],
        "remediation_micro_lesson": {
            "title": f"{knowledge_point}错题补救微课",
            "target": f"重新理解{knowledge_point}的核心概念和解题步骤。",
            "explanation": "先回到该知识点的基本定义，再按题目解析中的标准步骤重新梳理。",
            "steps": [
                "阅读题干，明确题目考查的知识点。",
                "对照标准答案，找出自己答案缺失或错误的部分。",
                "重新整理该类题的解题步骤。",
                "完成同类变式题，验证是否真正掌握。",
            ],
            "example": question.get("analysis", "暂无示例解析。"),
            "checklist": [
                "我能说出该知识点的基本含义。",
                "我能解释标准答案为什么正确。",
                "我能独立完成一道同类题。",
            ],
        },
        "recommended_practice": "建议先完成2道基础题，再完成1道同类变式题。",
        "variant_questions": [
            {
                "id": 1,
                "knowledge_point": knowledge_point,
                "type": "简答题",
                "question": f"请用自己的话解释：{knowledge_point}的核心思想是什么？",
                "options": [],
                "answer": f"应围绕{knowledge_point}的基本定义、关键步骤和适用场景进行说明。",
                "analysis": "这道题用于检查学生是否真正理解该知识点，而不是只记住原题答案。",
            }
        ],
        "sources": [],
        "diagnosis_mode": "fallback",
        "judge_reason": judge_reason,
    }


def diagnose_wrong_answer(
    question: Dict[str, Any],
    user_answer: Any,
    student_profile: Optional[Dict[str, Any]] = None,
    judge_reason: str = "",
    top_k: int = 6,
) -> Dict[str, Any]:
    """
    错因诊断 Agent：
    1. 读取题目、标准答案、学生答案；
    2. 检索课程资料；
    3. 判断错误类型；
    4. 生成补救微课；
    5. 生成同类变式题。
    """
    knowledge_point = (
        question.get("knowledge_point")
        or question.get("sub_knowledge_point")
        or question.get("topic")
        or "未知知识点"
    )

    question_type = question.get("type", "未知题型")
    standard_answer = question.get("answer", "")
    standard_analysis = question.get("analysis", "")
    options = question.get("options", [])

    context = ""
    sources = []

    try:
        context, sources, _ = retrieve_course_context(
            query=knowledge_point,
            top_k=top_k,
        )
    except Exception:
        context = ""
        sources = []

    student_context = format_student_context(student_profile)

    prompt = f"""
你是智能教学系统中的错因诊断 Agent。
请根据题目、标准答案、学生答案和课程资料，分析学生答错的原因，并生成补救微课和同类变式题。

学生信息：
{student_context}

题目信息：
- 知识点：{knowledge_point}
- 题型：{question_type}
- 题目：{question.get("question", "")}
- 选项：{json.dumps(options, ensure_ascii=False)}
- 标准答案：{standard_answer}
- 标准解析：{standard_analysis}
- 学生答案：{user_answer}
- 判分理由：{judge_reason}

课程资料：
{context}

可选错误类型只能从下面选择：
{json.dumps(ERROR_TYPES, ensure_ascii=False)}

请只输出 JSON，不要输出 Markdown，不要输出解释性文字。

JSON 格式如下：
{{
  "error_types": ["概念不清", "步骤遗漏"],
  "diagnosis": "用通俗语言说明学生为什么错。",
  "missing_points": ["学生缺失或混淆的知识点1", "学生缺失或混淆的知识点2"],
  "remediation_micro_lesson": {{
    "title": "补救微课标题",
    "target": "本微课要解决什么问题",
    "explanation": "面向学生的通俗讲解",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "example": "结合原题或简单例子的讲解",
    "checklist": ["自查点1", "自查点2", "自查点3"]
  }},
  "recommended_practice": "下一步练习建议",
  "variant_questions": [
    {{
      "id": 1,
      "knowledge_point": "{knowledge_point}",
      "type": "选择题",
      "question": "同类变式题题干",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "analysis": "答案解析"
    }},
    {{
      "id": 2,
      "knowledge_point": "{knowledge_point}",
      "type": "填空题",
      "question": "同类变式题题干",
      "options": [],
      "answer": "标准答案",
      "analysis": "答案解析"
    }},
    {{
      "id": 3,
      "knowledge_point": "{knowledge_point}",
      "type": "简答题",
      "question": "同类变式题题干",
      "options": [],
      "answer": "参考答案",
      "analysis": "答案解析"
    }}
  ]
}}

要求：
1. error_types 必须从给定错误类型中选择。
2. diagnosis 要明确指出学生错在哪里。
3. remediation_micro_lesson 要像一个小型补救课程。
4. variant_questions 必须围绕同一个知识点，但不要简单复制原题。
5. 如果课程资料不足，也不要编造课程之外的内容，可以给基础补救建议。
"""

    try:
        client = SparkX2Client()
        raw = client.chat(
            user_input=prompt,
            system_prompt="你是严格、准确、擅长教学诊断的错因分析助手。",
            temperature=0.2,
            max_tokens=2200,
            thinking="disabled",
        )

        data = safe_json_loads(raw)

        if not isinstance(data, dict):
            return fallback_diagnosis(question, user_answer, judge_reason)

        error_types = data.get("error_types", [])
        if not isinstance(error_types, list):
            error_types = []

        data["error_types"] = [
            item for item in error_types
            if item in ERROR_TYPES
        ] or ["概念不清"]

        if not isinstance(data.get("variant_questions"), list):
            data["variant_questions"] = []

        data["sources"] = sources
        data["diagnosis_mode"] = "llm_rag"
        data["judge_reason"] = judge_reason

        return data

    except Exception:
        return fallback_diagnosis(question, user_answer, judge_reason)


def save_mistake_record(
    student_id: str,
    question: Dict[str, Any],
    user_answer: Any,
    diagnosis: Dict[str, Any],
    difficulty: str = "简单",
    judge_reason: str = "",
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    保存错题诊断结果到 wrong_question_book。
    """
    ensure_mistake_tables(db_path)

    mistake_id = "M_" + uuid.uuid4().hex[:12]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    knowledge_point = (
        question.get("knowledge_point")
        or question.get("sub_knowledge_point")
        or question.get("topic")
        or "未知知识点"
    )

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO wrong_question_book (
        mistake_id,
        student_id,
        question_id,
        knowledge_point,
        question_type,
        difficulty,
        question,
        options,
        user_answer,
        standard_answer,
        standard_analysis,
        judge_reason,
        error_types,
        diagnosis,
        missing_points,
        remediation_micro_lesson,
        recommended_practice,
        variant_questions,
        sources,
        status,
        retry_count,
        last_retry_result,
        created_at,
        updated_at,
        fixed_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mistake_id,
        student_id,
        str(question.get("question_id") or question.get("id") or ""),
        knowledge_point,
        question.get("type", "未知题型"),
        difficulty,
        question.get("question", ""),
        json.dumps(question.get("options", []), ensure_ascii=False),
        str(user_answer),
        str(question.get("answer", "")),
        str(question.get("analysis", "")),
        judge_reason,
        json.dumps(diagnosis.get("error_types", []), ensure_ascii=False),
        diagnosis.get("diagnosis", ""),
        json.dumps(diagnosis.get("missing_points", []), ensure_ascii=False),
        json.dumps(diagnosis.get("remediation_micro_lesson", {}), ensure_ascii=False),
        diagnosis.get("recommended_practice", ""),
        json.dumps(diagnosis.get("variant_questions", []), ensure_ascii=False),
        json.dumps(diagnosis.get("sources", []), ensure_ascii=False),
        "未修复",
        0,
        "",
        now,
        now,
        None,
    ))

    conn.commit()
    conn.close()

    return {
        "mistake_id": mistake_id,
        "student_id": student_id,
        "knowledge_point": knowledge_point,
        "question_type": question.get("type", "未知题型"),
        "difficulty": difficulty,
        "question": question.get("question", ""),
        "user_answer": str(user_answer),
        "standard_answer": str(question.get("answer", "")),
        "status": "未修复",
        **diagnosis,
    }


def create_mistake_diagnosis_from_wrong_answer(
    student_id: str,
    question: Dict[str, Any],
    user_answer: Any,
    difficulty: str = "简单",
    judge_reason: str = "",
    student_profile: Optional[Dict[str, Any]] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    一站式入口：
    学生答错后，调用这个函数完成：
    错因诊断 -> 补救微课 -> 变式题 -> 保存错题本。
    """
    if student_profile is None:
        student_profile = get_student_profile(student_id, db_path) or {}

    diagnosis = diagnose_wrong_answer(
        question=question,
        user_answer=user_answer,
        student_profile=student_profile,
        judge_reason=judge_reason,
    )

    return save_mistake_record(
        student_id=student_id,
        question=question,
        user_answer=user_answer,
        diagnosis=diagnosis,
        difficulty=difficulty,
        judge_reason=judge_reason,
        db_path=db_path,
    )


def parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default

    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


def row_to_mistake(row: sqlite3.Row) -> Dict[str, Any]:
    item = dict(row)

    item["options"] = parse_json_field(item.get("options"), [])
    item["error_types"] = parse_json_field(item.get("error_types"), [])
    item["missing_points"] = parse_json_field(item.get("missing_points"), [])
    item["remediation_micro_lesson"] = parse_json_field(
        item.get("remediation_micro_lesson"),
        {},
    )
    item["variant_questions"] = parse_json_field(item.get("variant_questions"), [])
    item["sources"] = parse_json_field(item.get("sources"), [])
    item["last_retry_result"] = parse_json_field(item.get("last_retry_result"), {})

    return item


def get_mistake_book(
    student_id: str,
    status: Optional[str] = None,
    db_path: str = DB_PATH,
) -> List[Dict[str, Any]]:
    """
    获取学生错题本。
    status 可选：未修复 / 已修复
    """
    ensure_mistake_tables(db_path)

    conn = get_conn(db_path)
    cursor = conn.cursor()

    if status:
        cursor.execute("""
        SELECT *
        FROM wrong_question_book
        WHERE student_id = ? AND status = ?
        ORDER BY created_at DESC
        """, (student_id, status))
    else:
        cursor.execute("""
        SELECT *
        FROM wrong_question_book
        WHERE student_id = ?
        ORDER BY created_at DESC
        """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    return [row_to_mistake(row) for row in rows]


def get_mistake_detail(
    mistake_id: str,
    db_path: str = DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    获取单道错题的完整诊断详情。
    """
    ensure_mistake_tables(db_path)

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM wrong_question_book
    WHERE mistake_id = ?
    """, (mistake_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row_to_mistake(row)


def judge_variant_answer(
    question: Dict[str, Any],
    user_answer: Any,
) -> Tuple[bool, str]:
    """
    判断变式题答案。
    选择题、填空题用规则；
    主观题用大模型，失败时用包含关系兜底。
    """
    question_type = question.get("type", "")
    standard_answer = question.get("answer", "")

    if question_type in ["选择题", "填空题"]:
        user = normalize_answer(user_answer)
        standard = normalize_answer(standard_answer)

        if question_type == "选择题":
            user = user[0] if user else ""
            standard = standard[0] if standard else ""

        return user == standard, "变式题客观题规则判分"

    prompt = f"""
请判断学生对变式题的回答是否正确。

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
        client = SparkX2Client()
        raw = client.chat(
            user_input=prompt,
            system_prompt="你是严格但公平的补救练习判分助手。",
            temperature=0.1,
            max_tokens=500,
            thinking="disabled",
        )
        data = safe_json_loads(raw)
        if isinstance(data, dict):
            return bool(data.get("correct", False)), data.get("reason", "变式题模型判分")
    except Exception:
        pass

    user = normalize_answer(user_answer)
    standard = normalize_answer(standard_answer)
    correct = bool(user and standard and (user in standard or standard in user))
    return correct, "模型判分失败，使用简单包含关系兜底"


def evaluate_mistake_retry(
    mistake_id: str,
    variant_index: int,
    user_answer: Any,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    学生完成变式题后，判断是否修复该错题。
    variant_index 从 1 开始。
    """
    mistake = get_mistake_detail(mistake_id, db_path)

    if mistake is None:
        raise ValueError(f"未找到错题记录：{mistake_id}")

    variant_questions = mistake.get("variant_questions", [])

    if not variant_questions:
        raise ValueError("该错题没有可用的变式题。")

    if variant_index < 1 or variant_index > len(variant_questions):
        raise ValueError(f"variant_index 超出范围，应在 1 到 {len(variant_questions)} 之间。")

    question = variant_questions[variant_index - 1]
    correct, reason = judge_variant_answer(question, user_answer)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_status = "已修复" if correct else "未修复"

    retry_result = {
        "variant_index": variant_index,
        "question": question,
        "user_answer": str(user_answer),
        "correct": correct,
        "reason": reason,
        "time": now,
    }

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE wrong_question_book
    SET
        status = ?,
        retry_count = retry_count + 1,
        last_retry_result = ?,
        updated_at = ?,
        fixed_at = CASE WHEN ? = '已修复' THEN ? ELSE fixed_at END
    WHERE mistake_id = ?
    """, (
        new_status,
        json.dumps(retry_result, ensure_ascii=False),
        now,
        new_status,
        now,
        mistake_id,
    ))

    conn.commit()
    conn.close()

    return {
        "mistake_id": mistake_id,
        "status": new_status,
        "correct": correct,
        "reason": reason,
        "message": "该错题已修复。" if correct else "该错题仍未修复，建议继续学习补救微课并再做变式题。",
        "retry_result": retry_result,
    }


if __name__ == "__main__":
    sample_question = {
        "id": 1,
        "knowledge_point": "LZW算法",
        "type": "简答题",
        "question": "请简述 LZW 编码中字典更新的基本过程。",
        "options": [],
        "answer": "LZW 编码会先初始化基础字符字典，然后不断寻找当前最长匹配串，输出其编码，并把新串加入字典。",
        "analysis": "关键点包括：初始化字典、最长匹配、输出编码、加入新串。",
    }

    result = create_mistake_diagnosis_from_wrong_answer(
        student_id="S001",
        question=sample_question,
        user_answer="就是把字符压缩一下",
        difficulty="简单",
        judge_reason="答案过于笼统，缺少字典初始化和最长匹配过程。",
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
