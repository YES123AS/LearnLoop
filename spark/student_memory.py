# student_memory.py

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from .knowledge_tracing import analyze_knowledge_tracing
except ImportError:
    from knowledge_tracing import analyze_knowledge_tracing


DB_PATH = os.getenv(
    "STUDENT_DB_PATH",
    str(Path(__file__).resolve().parent.parent / ".local-data" / "data" / "student_learning.db"),
)


def get_conn(db_path: str = DB_PATH):
    """
    获取数据库连接
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_knowledge_mastery_columns(conn) -> None:
    """
    兼容旧数据库：如果 knowledge_mastery 表已经存在，就自动补齐知识追踪字段。
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type = 'table' AND name = 'knowledge_mastery'
    """)
    if cursor.fetchone() is None:
        return

    cursor.execute("PRAGMA table_info(knowledge_mastery)")
    existing_columns = {row["name"] for row in cursor.fetchall()}

    columns = {
        "recent_accuracy": "REAL DEFAULT 0",
        "difficulty_score": "REAL DEFAULT 0",
        "speed_score": "REAL DEFAULT 0",
        "stability_score": "REAL DEFAULT 0",
        "mastery_score": "REAL DEFAULT 0",
        "next_difficulty": "TEXT DEFAULT '中等'",
    }

    for column_name, column_sql in columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE knowledge_mastery ADD COLUMN {column_name} {column_sql}"
            )


def init_db(db_path: str = DB_PATH) -> None:
    """
    初始化数据库表
    第一次运行项目时执行一次即可
    """
    conn = get_conn(db_path)
    cursor = conn.cursor()

    # 1. 学生画像表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_profile (
        student_id TEXT PRIMARY KEY,
        grade TEXT,
        major TEXT,
        course TEXT,
        level TEXT,
        goal TEXT,
        learning_style TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # 2. 学习记录表：每做一道题，就插入一条记录
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        knowledge_point TEXT NOT NULL,
        question_type TEXT,
        correct INTEGER NOT NULL,
        answer_time REAL,
        difficulty TEXT,
        question_id TEXT,
        user_answer TEXT,
        standard_answer TEXT,
        submit_time TEXT,
        FOREIGN KEY(student_id) REFERENCES student_profile(student_id)
    )
    """)

    # 3. 知识点掌握情况表：由 learning_record 自动统计更新
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_mastery (
        student_id TEXT NOT NULL,
        knowledge_point TEXT NOT NULL,
        total INTEGER NOT NULL,
        correct_count INTEGER NOT NULL,
        accuracy REAL NOT NULL,
        recent_accuracy REAL DEFAULT 0,
        difficulty_score REAL DEFAULT 0,
        speed_score REAL DEFAULT 0,
        stability_score REAL DEFAULT 0,
        mastery_score REAL DEFAULT 0,
        mastery_level TEXT NOT NULL,
        next_difficulty TEXT DEFAULT '中等',
        last_practice_time TEXT,
        updated_at TEXT,
        PRIMARY KEY(student_id, knowledge_point),
        FOREIGN KEY(student_id) REFERENCES student_profile(student_id)
    )
    """)
    ensure_knowledge_mastery_columns(conn)

    conn.commit()
    conn.close()

    print("[OK] 学生画像数据库初始化完成。")


def create_or_update_student_profile(
    student_id: str,
    grade: str = "未知",
    major: str = "未知",
    course: str = "未知",
    level: str = "未知",
    goal: str = "未知",
    learning_style: str = "未知",
    db_path: str = DB_PATH
) -> None:
    """
    创建或更新学生画像
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO student_profile (
        student_id, grade, major, course, level, goal, learning_style, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(student_id) DO UPDATE SET
        grade = excluded.grade,
        major = excluded.major,
        course = excluded.course,
        level = excluded.level,
        goal = excluded.goal,
        learning_style = excluded.learning_style,
        updated_at = excluded.updated_at
    """, (
        student_id,
        grade,
        major,
        course,
        level,
        goal,
        learning_style,
        now,
        now
    ))

    conn.commit()
    conn.close()

    print(f"[OK] 学生画像已保存：{student_id}")


def get_student_profile(
    student_id: str,
    db_path: str = DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    获取学生画像，并自动附带 weak_points、mastered_points
    这样可以直接传给你原来的 personalized_answer、generate_learning_path 等函数
    """
    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM student_profile
    WHERE student_id = ?
    """, (student_id,))

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    profile = dict(row)
    ensure_knowledge_mastery_columns(conn)

    # 查询薄弱知识点
    cursor.execute("""
    SELECT knowledge_point, mastery_score, next_difficulty FROM knowledge_mastery
    WHERE student_id = ? AND mastery_level IN ('薄弱', '待强化')
    ORDER BY mastery_score ASC, accuracy ASC
    """, (student_id,))

    weak_rows = cursor.fetchall()
    weak_points = [item["knowledge_point"] for item in weak_rows]

    # 查询掌握较好的知识点
    cursor.execute("""
    SELECT knowledge_point FROM knowledge_mastery
    WHERE student_id = ? AND mastery_level = '掌握较好'
    ORDER BY mastery_score DESC, accuracy DESC
    """, (student_id,))

    mastered_points = [item["knowledge_point"] for item in cursor.fetchall()]

    profile["weak_points"] = weak_points
    profile["mastered_points"] = mastered_points
    profile["weak_point_details"] = [
        {
            "knowledge_point": item["knowledge_point"],
            "mastery_score": item["mastery_score"],
            "next_difficulty": item["next_difficulty"],
        }
        for item in weak_rows
    ]

    conn.close()
    return profile


def add_learning_record(
    student_id: str,
    knowledge_point: str,
    question_type: str,
    correct: bool,
    answer_time: float = None,
    difficulty: str = "简单",
    question_id: str = None,
    user_answer: str = None,
    standard_answer: str = None,
    db_path: str = DB_PATH
) -> None:
    """
    添加一条做题记录。
    每次学生提交答案后，调用这个函数。
    添加记录后，会自动更新该知识点的掌握情况。
    """
    submit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO learning_record (
        student_id,
        knowledge_point,
        question_type,
        correct,
        answer_time,
        difficulty,
        question_id,
        user_answer,
        standard_answer,
        submit_time
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        knowledge_point,
        question_type,
        1 if correct else 0,
        answer_time,
        difficulty,
        question_id,
        user_answer,
        standard_answer,
        submit_time
    ))

    conn.commit()
    conn.close()

    update_knowledge_mastery(
        student_id=student_id,
        knowledge_point=knowledge_point,
        db_path=db_path
    )

    print(f"[OK] 已记录做题结果：{student_id} - {knowledge_point}")


def update_knowledge_mastery(
    student_id: str,
    knowledge_point: str,
    db_path: str = DB_PATH
) -> None:
    """
    根据学习记录，使用轻量知识追踪模型更新某个学生某个知识点的掌握情况。
    """
    conn = get_conn(db_path)
    cursor = conn.cursor()
    ensure_knowledge_mastery_columns(conn)

    cursor.execute("""
    SELECT *
    FROM learning_record
    WHERE student_id = ? AND knowledge_point = ?
    ORDER BY submit_time ASC
    """, (student_id, knowledge_point))

    rows = cursor.fetchall()
    records = []

    for row in rows:
        item = dict(row)
        item["correct"] = bool(item["correct"])
        records.append(item)

    if not records:
        conn.close()
        return

    tracing_result = analyze_knowledge_tracing(records)

    if not tracing_result:
        conn.close()
        return

    item = tracing_result[0]

    cursor.execute("""
    SELECT MAX(submit_time) AS last_practice_time
    FROM learning_record
    WHERE student_id = ? AND knowledge_point = ?
    """, (student_id, knowledge_point))

    row = cursor.fetchone()
    last_practice_time = row["last_practice_time"] if row else None

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO knowledge_mastery (
        student_id,
        knowledge_point,
        total,
        correct_count,
        accuracy,
        recent_accuracy,
        difficulty_score,
        speed_score,
        stability_score,
        mastery_score,
        mastery_level,
        next_difficulty,
        last_practice_time,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(student_id, knowledge_point) DO UPDATE SET
        total = excluded.total,
        correct_count = excluded.correct_count,
        accuracy = excluded.accuracy,
        recent_accuracy = excluded.recent_accuracy,
        difficulty_score = excluded.difficulty_score,
        speed_score = excluded.speed_score,
        stability_score = excluded.stability_score,
        mastery_score = excluded.mastery_score,
        mastery_level = excluded.mastery_level,
        next_difficulty = excluded.next_difficulty,
        last_practice_time = excluded.last_practice_time,
        updated_at = excluded.updated_at
    """, (
        student_id,
        knowledge_point,
        item["total"],
        item["correct"],
        item["accuracy"],
        item["recent_accuracy"],
        item["difficulty_score"],
        item["speed_score"],
        item["stability_score"],
        item["mastery_score"],
        item["mastery_level"],
        item["next_difficulty"],
        last_practice_time,
        updated_at
    ))

    conn.commit()
    conn.close()


def get_learning_records(
    student_id: str,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    获取某个学生的所有做题记录。
    这个函数可以直接给 learning_analysis.py 使用。
    """
    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM learning_record
    WHERE student_id = ?
    ORDER BY submit_time DESC
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    records = []

    for row in rows:
        item = dict(row)
        item["correct"] = bool(item["correct"])
        records.append(item)

    return records


def get_knowledge_mastery(
    student_id: str,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    获取某个学生所有知识点的掌握情况
    """
    conn = get_conn(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM knowledge_mastery
    WHERE student_id = ?
    ORDER BY mastery_score ASC, accuracy ASC
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_student_report(
    student_id: str,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    获取完整学生学习报告：
    画像 + 知识点掌握情况 + 学习记录
    """
    profile = get_student_profile(student_id, db_path)
    mastery = get_knowledge_mastery(student_id, db_path)
    records = get_learning_records(student_id, db_path)

    return {
        "profile": profile,
        "mastery": mastery,
        "records": records
    }


if __name__ == "__main__":
    # 1. 初始化数据库
    init_db()

    # 2. 创建一个测试学生
    create_or_update_student_profile(
        student_id="S001",
        grade="大二",
        major="智能科学与技术",
        course="多媒体信息处理",
        level="基础较弱",
        goal="期末复习",
        learning_style="喜欢通俗解释和例子"
    )

    # 3. 模拟学生做题记录
    add_learning_record(
        student_id="S001",
        knowledge_point="LZW算法",
        question_type="选择题",
        correct=False,
        answer_time=35,
        difficulty="简单"
    )

    add_learning_record(
        student_id="S001",
        knowledge_point="LZW算法",
        question_type="填空题",
        correct=False,
        answer_time=50,
        difficulty="简单"
    )

    add_learning_record(
        student_id="S001",
        knowledge_point="LZW算法",
        question_type="简答题",
        correct=True,
        answer_time=80,
        difficulty="中等"
    )

    add_learning_record(
        student_id="S001",
        knowledge_point="JPEG压缩",
        question_type="选择题",
        correct=True,
        answer_time=25,
        difficulty="简单"
    )

    # 4. 查看学生画像
    profile = get_student_profile("S001")
    print("\n学生画像：")
    print(profile)

    # 5. 查看知识点掌握情况
    mastery = get_knowledge_mastery("S001")
    print("\n知识点掌握情况：")
    for item in mastery:
        print(item)
