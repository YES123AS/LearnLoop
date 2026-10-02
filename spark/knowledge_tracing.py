from collections import defaultdict
from typing import Any, Dict, List


DIFFICULTY_WEIGHT = {
    "简单": 0.6,
    "中等": 0.8,
    "困难": 1.0,
    "较难": 1.0,
}


def difficulty_to_score(difficulty: str) -> float:
    """
    将题目难度转换成数值。
    做对困难题更能说明掌握程度。
    """
    return DIFFICULTY_WEIGHT.get(difficulty, 0.7)


def calculate_accuracy(records: List[Dict[str, Any]]) -> float:
    """
    计算总体正确率。
    """
    if not records:
        return 0.0

    correct_count = sum(1 for r in records if r.get("correct", False))
    return correct_count / len(records)


def calculate_recent_accuracy(
    records: List[Dict[str, Any]],
    recent_n: int = 5,
) -> float:
    """
    计算最近几次答题正确率。
    最近表现比很久以前的表现更重要。
    注意：records 最好按 submit_time 从旧到新排序。
    """
    if not records:
        return 0.0

    recent_records = records[-recent_n:]
    correct_count = sum(1 for r in recent_records if r.get("correct", False))
    return correct_count / len(recent_records)


def calculate_difficulty_score(records: List[Dict[str, Any]]) -> float:
    """
    难度得分：
    如果学生能做对更难的题，说明掌握程度更高。
    """
    if not records:
        return 0.0

    total_weight = 0.0
    correct_weight = 0.0

    for r in records:
        difficulty = r.get("difficulty", "简单")
        weight = difficulty_to_score(difficulty)
        total_weight += weight

        if r.get("correct", False):
            correct_weight += weight

    if total_weight == 0:
        return 0.0

    return correct_weight / total_weight


def calculate_speed_score(records: List[Dict[str, Any]]) -> float:
    """
    作答速度得分：
    - 没有 answer_time 时，给默认值 0.7
    - 答对且用时合理，得分较高
    - 答错或用时过长，得分较低
    """
    valid_records = [
        r for r in records
        if r.get("answer_time") is not None
    ]

    if not valid_records:
        return 0.7

    scores = []

    for r in valid_records:
        answer_time = float(r.get("answer_time", 0))
        correct = r.get("correct", False)
        question_type = r.get("question_type", "")

        if "选择" in question_type:
            ideal_time = 30
        elif "填空" in question_type:
            ideal_time = 60
        elif "简答" in question_type:
            ideal_time = 120
        elif "编程" in question_type:
            ideal_time = 300
        else:
            ideal_time = 90

        if not correct:
            scores.append(0.4)
        elif answer_time <= ideal_time:
            scores.append(1.0)
        elif answer_time <= ideal_time * 1.5:
            scores.append(0.8)
        elif answer_time <= ideal_time * 2:
            scores.append(0.6)
        else:
            scores.append(0.5)

    return sum(scores) / len(scores)


def calculate_stability_score(records: List[Dict[str, Any]]) -> float:
    """
    稳定性得分：
    连续做对：高稳定；忽对忽错：中等；连续做错：低稳定。
    """
    if len(records) < 3:
        return 0.6

    recent_records = records[-5:]
    results = [1 if r.get("correct", False) else 0 for r in recent_records]

    changes = 0
    for i in range(1, len(results)):
        if results[i] != results[i - 1]:
            changes += 1

    change_rate = changes / max(1, len(results) - 1)
    stability = 1 - change_rate

    if sum(results) == 0:
        return 0.2

    if sum(results) == len(results):
        return 1.0

    return max(0.2, stability)


def get_mastery_level(mastery_score: float, total: int) -> str:
    """
    根据 mastery_score 判断掌握等级。
    """
    if total < 3:
        return "待观察"

    if mastery_score >= 0.85:
        return "掌握较好"
    if mastery_score >= 0.65:
        return "基本掌握"
    if mastery_score >= 0.45:
        return "待强化"
    return "薄弱"


def recommend_difficulty(mastery_score: float) -> str:
    """
    根据掌握程度推荐下一次题目难度。
    """
    if mastery_score < 0.45:
        return "简单"
    if mastery_score < 0.85:
        return "中等"
    return "困难"


def analyze_knowledge_tracing(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    轻量知识追踪主函数。

    输入：
        学生所有答题记录 records

    输出：
        每个知识点的 mastery_score、mastery_level、推荐难度等
    """
    grouped = defaultdict(list)

    for record in records:
        point = record.get("knowledge_point", "未知知识点")
        grouped[point].append(record)

    result = []

    for point, point_records in grouped.items():
        point_records = sorted(
            point_records,
            key=lambda x: x.get("submit_time", ""),
        )

        total = len(point_records)
        correct_count = sum(1 for r in point_records if r.get("correct", False))

        accuracy = calculate_accuracy(point_records)
        recent_accuracy = calculate_recent_accuracy(point_records)
        difficulty_score = calculate_difficulty_score(point_records)
        speed_score = calculate_speed_score(point_records)
        stability_score = calculate_stability_score(point_records)

        mastery_score = (
            0.45 * accuracy
            + 0.20 * recent_accuracy
            + 0.15 * difficulty_score
            + 0.10 * speed_score
            + 0.10 * stability_score
        )

        result.append({
            "knowledge_point": point,
            "total": total,
            "correct": correct_count,
            "accuracy": round(accuracy, 2),
            "recent_accuracy": round(recent_accuracy, 2),
            "difficulty_score": round(difficulty_score, 2),
            "speed_score": round(speed_score, 2),
            "stability_score": round(stability_score, 2),
            "mastery_score": round(mastery_score, 2),
            "mastery_level": get_mastery_level(mastery_score, total),
            "next_difficulty": recommend_difficulty(mastery_score),
        })

    result.sort(key=lambda x: x["mastery_score"])
    return result


if __name__ == "__main__":
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
            "correct": True,
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
    ]

    result = analyze_knowledge_tracing(records)

    for item in result:
        print(item)
