import json
import re
from typing import Any, Dict, List, Optional

try:
    from .spark_llm import SparkX2Client
    from .student_memory import (
        DB_PATH,
        init_db,
        get_student_profile,
        get_learning_records,
        get_knowledge_mastery,
    )
except ImportError:
    from spark_llm import SparkX2Client
    from student_memory import (
        DB_PATH,
        init_db,
        get_student_profile,
        get_learning_records,
        get_knowledge_mastery,
    )


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    从大模型返回内容中提取 JSON 对象。
    允许 JSON 前后有少量说明文字。
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.S)

    if not match:
        raise ValueError("模型输出中没有找到合法 JSON：\n" + text)

    return json.loads(match.group(0))


def calc_accuracy(records: List[Dict[str, Any]]) -> Optional[float]:
    """
    计算一组做题记录的正确率。
    """
    if not records:
        return None

    correct_count = sum(1 for item in records if item.get("correct"))
    return round(correct_count / len(records), 2)


def get_recent_records_by_topic(
    records: List[Dict[str, Any]],
    topic: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    获取某个知识点最近的练习记录。
    get_learning_records 默认按 submit_time DESC 排序。
    """
    result = []

    for item in records:
        if item.get("knowledge_point") == topic:
            result.append(item)

        if len(result) >= limit:
            break

    return result


def find_mastery_item(
    mastery_list: List[Dict[str, Any]],
    topic: str,
) -> Optional[Dict[str, Any]]:
    """
    在 knowledge_mastery 中查找指定知识点的掌握情况。
    """
    for item in mastery_list:
        if item.get("knowledge_point") == topic:
            return item
    return None


def format_mastery_text(mastery_list: List[Dict[str, Any]]) -> str:
    """
    把掌握度列表转成 prompt 可读文本。
    """
    if not mastery_list:
        return "暂无历史掌握度数据。"

    lines = []

    for item in mastery_list:
        lines.append(
            f"- {item.get('knowledge_point')}："
            f"共做{item.get('total', 0)}题，"
            f"答对{item.get('correct_count', 0)}题，"
            f"正确率{int(float(item.get('accuracy', 0)) * 100)}%，"
            f"近期正确率{int(float(item.get('recent_accuracy', 0)) * 100)}%，"
            f"综合掌握度{item.get('mastery_score', 0)}，"
            f"掌握情况：{item.get('mastery_level')}，"
            f"建议难度：{item.get('next_difficulty', '中等')}"
        )

    return "\n".join(lines)


def format_recent_records(records: List[Dict[str, Any]], limit: int = 10) -> str:
    """
    把最近做题记录转成 prompt 可读文本。
    """
    if not records:
        return "暂无做题记录。"

    lines = []

    for item in records[:limit]:
        result = "正确" if item.get("correct") else "错误"
        lines.append(
            f"- 知识点：{item.get('knowledge_point')}，"
            f"题型：{item.get('question_type')}，"
            f"难度：{item.get('difficulty')}，"
            f"结果：{result}，"
            f"用时：{item.get('answer_time')}秒，"
            f"提交时间：{item.get('submit_time')}"
        )

    return "\n".join(lines)


def diagnose_path_state(
    student_id: str,
    current_topic: Optional[str] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    根据学生最新练习情况判断下一步路径状态。

    返回三种主要状态：
    1. remediate：补救，说明当前知识点薄弱，不能进入下一个知识点
    2. consolidate：巩固，说明基本掌握，但还需要继续练习
    3. advance：推进，说明掌握较好，可以进入下一个知识点
    """
    init_db(db_path)

    student_profile = get_student_profile(student_id, db_path)

    if student_profile is None:
        raise ValueError(f"未找到学生画像：{student_id}")

    records = get_learning_records(student_id, db_path)
    mastery_list = get_knowledge_mastery(student_id, db_path)

    weak_points = [
        item for item in mastery_list
        if item.get("mastery_level") in ["薄弱", "待强化"]
    ]

    if current_topic:
        current_mastery = find_mastery_item(mastery_list, current_topic)
        recent_topic_records = get_recent_records_by_topic(
            records,
            current_topic,
            limit=5,
        )
        recent_accuracy = calc_accuracy(recent_topic_records)

        if len(recent_topic_records) >= 2:
            if (
                not recent_topic_records[0].get("correct")
                and not recent_topic_records[1].get("correct")
            ):
                return {
                    "state": "remediate",
                    "target_topic": current_topic,
                    "reason": "最近连续两题错误，说明该知识点存在明显理解问题，需要暂停推进并进行补救。",
                    "recent_accuracy": recent_accuracy,
                    "mastery": current_mastery,
                }

        if current_mastery:
            accuracy = float(current_mastery.get("accuracy", 0))
            total = int(current_mastery.get("total", 0))
            mastery_level = current_mastery.get("mastery_level", "")

            if total >= 3 and mastery_level in ["薄弱", "待强化"]:
                return {
                    "state": "remediate",
                    "target_topic": current_topic,
                    "reason": "该知识点综合掌握度较低，系统判定为薄弱或待强化，需要生成针对性补救路径。",
                    "recent_accuracy": recent_accuracy,
                    "mastery": current_mastery,
                }

            if total >= 3 and accuracy >= 0.8:
                return {
                    "state": "advance",
                    "target_topic": current_topic,
                    "reason": "该知识点累计正确率达到80%以上，可以进入后续知识点。",
                    "recent_accuracy": recent_accuracy,
                    "mastery": current_mastery,
                }

        if recent_accuracy is not None and len(recent_topic_records) >= 3:
            if 0.6 <= recent_accuracy < 0.8:
                return {
                    "state": "consolidate",
                    "target_topic": current_topic,
                    "reason": "最近练习正确率处于60%-80%，说明基本理解但还不稳定，需要继续巩固。",
                    "recent_accuracy": recent_accuracy,
                    "mastery": current_mastery,
                }

            if recent_accuracy < 0.6:
                return {
                    "state": "remediate",
                    "target_topic": current_topic,
                    "reason": "最近练习正确率低于60%，说明当前知识点仍然薄弱，需要补救学习。",
                    "recent_accuracy": recent_accuracy,
                    "mastery": current_mastery,
                }

        return {
            "state": "consolidate",
            "target_topic": current_topic,
            "reason": "当前知识点练习数据较少，系统先安排少量巩固练习，再决定是否推进。",
            "recent_accuracy": recent_accuracy,
            "mastery": current_mastery,
        }

    if weak_points:
        first_weak = weak_points[0]
        return {
            "state": "remediate",
            "target_topic": first_weak.get("knowledge_point"),
            "reason": "系统检测到存在薄弱或待强化知识点，优先进行补救。",
            "recent_accuracy": None,
            "mastery": first_weak,
        }

    return {
        "state": "advance",
        "target_topic": None,
        "reason": "暂无明显薄弱知识点，可以继续推进新知识。",
        "recent_accuracy": None,
        "mastery": None,
    }


def build_initial_dynamic_path_prompt(
    goal: str,
    student_profile: Dict[str, Any],
    mastery_list: List[Dict[str, Any]],
) -> str:
    """
    初始路径只生成当前阶段和候选知识点队列。
    """
    mastery_text = format_mastery_text(mastery_list)
    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"

    prompt = f"""
你是一个个性化动态学习路径规划助手。

你的任务不是一次性生成完整学习计划，而是生成“动态学习路径”的初始状态。

学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}
- 已知薄弱点：{weak_points}

历史掌握情况：
{mastery_text}

本次学习目标：
{goal}

请你输出 JSON，不要输出 Markdown，不要输出解释性文字。

输出格式如下：

{{
  "goal": "{goal}",
  "path_mode": "dynamic",
  "current_step": {{
    "topic": "当前首先学习的知识点",
    "reason": "为什么先学这个",
    "learning_tasks": [
      "学习任务1",
      "学习任务2"
    ],
    "practice_tasks": [
      {{
        "knowledge_point": "练习对应的细分知识点",
        "question_type": "选择题/填空题/简答题/计算题",
        "difficulty": "简单/中等/较难",
        "count": 3
      }}
    ],
    "completion_condition": "进入下一步的条件"
  }},
  "candidate_sequence": [
    "候选知识点1",
    "候选知识点2",
    "候选知识点3"
  ],
  "dynamic_adjustment_rule": "每轮练习后，根据正确率、连续错误次数和知识点掌握度动态决定补救、巩固或推进"
}}
"""
    return prompt


def generate_dynamic_initial_path(
    goal: str,
    student_profile: Dict[str, Any],
    mastery_list: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    生成动态学习路径的初始状态。
    """
    if mastery_list is None:
        mastery_list = []

    prompt = build_initial_dynamic_path_prompt(
        goal=goal,
        student_profile=student_profile,
        mastery_list=mastery_list,
    )

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的动态学习路径规划助手，擅长根据学生画像和掌握度生成当前阶段任务。",
        temperature=0.4,
        max_tokens=1200,
        thinking="disabled",
    )

    try:
        return extract_json_object(result)
    except Exception:
        return {
            "goal": goal,
            "path_mode": "dynamic",
            "current_step": {
                "topic": goal,
                "reason": "模型 JSON 解析失败，使用兜底路径。",
                "learning_tasks": ["先学习该目标的基础概念", "完成基础例题理解"],
                "practice_tasks": [
                    {
                        "knowledge_point": goal,
                        "question_type": "选择题",
                        "difficulty": "简单",
                        "count": 3,
                    }
                ],
                "completion_condition": "基础题正确率达到80%以上",
            },
            "candidate_sequence": [],
            "dynamic_adjustment_rule": "每轮练习后根据正确率动态调整",
            "raw": result,
        }


def generate_dynamic_initial_path_by_student(
    student_id: str,
    goal: str,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    根据 student_id 自动读取画像和掌握度，生成初始动态路径。
    """
    init_db(db_path)

    student_profile = get_student_profile(student_id, db_path)

    if student_profile is None:
        raise ValueError(f"未找到学生画像：{student_id}")

    mastery_list = get_knowledge_mastery(student_id, db_path)

    result = generate_dynamic_initial_path(
        goal=goal,
        student_profile=student_profile,
        mastery_list=mastery_list,
    )

    result["student_id"] = student_id
    return result


def build_next_step_prompt(
    goal: str,
    student_profile: Dict[str, Any],
    decision: Dict[str, Any],
    mastery_list: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    current_topic: Optional[str] = None,
) -> str:
    mastery_text = format_mastery_text(mastery_list)
    recent_text = format_recent_records(records, limit=10)

    state = decision.get("state")
    target_topic = decision.get("target_topic")
    reason = decision.get("reason")

    prompt = f"""
你是一个个性化学习路径动态调整助手。

系统已经根据学生做题结果做出路径判断：

- 当前路径状态：{state}
- 当前练习知识点：{current_topic or "未指定"}
- 下一步目标知识点：{target_topic or "由你根据目标和掌握度决定"}
- 系统判断原因：{reason}

状态含义：
- remediate：补救。说明学生当前知识点薄弱，不能进入新知识点。
- consolidate：巩固。说明学生基本掌握，但还不稳定，需要继续练习。
- advance：推进。说明学生掌握较好，可以进入后续知识点。

学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}

总学习目标：
{goal}

知识点掌握情况：
{mastery_text}

最近做题记录：
{recent_text}

请根据以上信息，生成“下一步学习路径”。
注意：
1. 不要一次性生成完整多天计划。
2. 只生成下一轮学习任务。
3. 如果状态是 remediate，必须围绕薄弱知识点拆成更细的补救任务。
4. 如果状态是 consolidate，安排巩固练习和变式题。
5. 如果状态是 advance，安排下一个逻辑知识点。
6. practice_tasks 中的 knowledge_point 必须是细分知识点，不能总是写大主题。
7. 只输出 JSON，不要输出 Markdown，不要输出其他解释。

输出格式：

{{
  "path_state": "remediate/consolidate/advance",
  "next_topic": "下一步学习主题",
  "reason": "为什么这样调整",
  "learning_tasks": [
    "学习任务1",
    "学习任务2",
    "学习任务3"
  ],
  "practice_tasks": [
    {{
      "knowledge_point": "细分知识点1",
      "question_type": "选择题",
      "difficulty": "简单",
      "count": 3
    }},
    {{
      "knowledge_point": "细分知识点2",
      "question_type": "填空题",
      "difficulty": "简单",
      "count": 2
    }}
  ],
  "resource_need": [
    "需要补充的资料1",
    "需要补充的资料2"
  ],
  "completion_condition": "完成本轮任务后，什么条件下可以进入下一步",
  "next_check_rule": "下一轮系统如何判断是否继续调整"
}}
"""
    return prompt


def fallback_next_step(
    goal: str,
    decision: Dict[str, Any],
    current_topic: Optional[str] = None,
) -> Dict[str, Any]:
    """
    大模型返回异常时的兜底策略。
    """
    state = decision.get("state", "consolidate")
    target_topic = decision.get("target_topic") or current_topic or goal

    if state == "remediate":
        return {
            "path_state": "remediate",
            "next_topic": target_topic,
            "reason": decision.get("reason", "当前知识点掌握较弱，需要补救。"),
            "learning_tasks": [
                f"重新学习 {target_topic} 的基础概念",
                f"整理 {target_topic} 的常见错误点",
                f"完成 {target_topic} 的基础例题",
            ],
            "practice_tasks": [
                {
                    "knowledge_point": target_topic,
                    "question_type": "选择题",
                    "difficulty": "简单",
                    "count": 3,
                },
                {
                    "knowledge_point": target_topic,
                    "question_type": "填空题",
                    "difficulty": "简单",
                    "count": 2,
                },
            ],
            "resource_need": [
                f"{target_topic} 基础讲解",
                f"{target_topic} 易错点总结",
            ],
            "completion_condition": "本知识点最近5题正确率达到80%以上",
            "next_check_rule": "练习后重新读取 knowledge_mastery 和最近做题记录",
        }

    if state == "advance":
        return {
            "path_state": "advance",
            "next_topic": "下一个相关知识点",
            "reason": decision.get("reason", "当前知识点掌握较好，可以推进。"),
            "learning_tasks": [
                "学习下一个知识点的基本概念",
                "完成基础例题",
                "进行小测检测",
            ],
            "practice_tasks": [
                {
                    "knowledge_point": "下一个相关知识点",
                    "question_type": "选择题",
                    "difficulty": "中等",
                    "count": 3,
                }
            ],
            "resource_need": ["新知识点基础资料"],
            "completion_condition": "新知识点正确率达到80%以上",
            "next_check_rule": "练习后继续动态判断",
        }

    return {
        "path_state": "consolidate",
        "next_topic": target_topic,
        "reason": decision.get("reason", "当前知识点基本掌握，但还需要巩固。"),
        "learning_tasks": [
            f"复习 {target_topic} 的核心概念",
            f"完成 {target_topic} 的变式练习",
            f"总结 {target_topic} 的解题方法",
        ],
        "practice_tasks": [
            {
                "knowledge_point": target_topic,
                "question_type": "简答题",
                "difficulty": "中等",
                "count": 2,
            },
            {
                "knowledge_point": target_topic,
                "question_type": "选择题",
                "difficulty": "中等",
                "count": 3,
            },
        ],
        "resource_need": [
            f"{target_topic} 巩固练习",
            f"{target_topic} 变式题",
        ],
        "completion_condition": "连续练习正确率达到80%以上",
        "next_check_rule": "练习后继续动态判断",
    }


def generate_next_learning_step(
    student_id: str,
    goal: str,
    current_topic: Optional[str] = None,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    每轮练习结束后调用，根据学生最新做题数据动态生成下一步学习路径。
    """
    init_db(db_path)

    student_profile = get_student_profile(student_id, db_path)

    if student_profile is None:
        raise ValueError(f"未找到学生画像：{student_id}")

    records = get_learning_records(student_id, db_path)
    mastery_list = get_knowledge_mastery(student_id, db_path)

    decision = diagnose_path_state(
        student_id=student_id,
        current_topic=current_topic,
        db_path=db_path,
    )

    prompt = build_next_step_prompt(
        goal=goal,
        student_profile=student_profile,
        decision=decision,
        mastery_list=mastery_list,
        records=records,
        current_topic=current_topic,
    )

    client = SparkX2Client()

    result = client.chat(
        user_input=prompt,
        system_prompt="你是一个专业的动态学习路径调整助手，擅长根据练习反馈生成下一步学习任务。",
        temperature=0.4,
        max_tokens=1500,
        thinking="disabled",
    )

    try:
        data = extract_json_object(result)
    except Exception:
        data = fallback_next_step(
            goal=goal,
            decision=decision,
            current_topic=current_topic,
        )
        data["raw"] = result

    data["student_id"] = student_id
    data["goal"] = goal
    data["current_topic"] = current_topic
    data["decision"] = decision

    return data


if __name__ == "__main__":
    result = generate_next_learning_step(
        student_id="S001",
        goal="掌握 Python 基础",
        current_topic="变量类型转换",
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
