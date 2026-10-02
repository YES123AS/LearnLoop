"""LangGraph implementation of the multi-agent learning loop.

The public functions intentionally match ``multi_agent_learning_loop.py`` so
FastAPI and callers can migrate without changing their request/response
contracts. Legacy domain functions remain reusable LangGraph node services.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_DIR = BASE_DIR.parent / ".local-data" / "data"
DEFAULT_CHECKPOINT_DB = Path(
    os.getenv("LANGGRAPH_CHECKPOINT_DB", str(LOCAL_DATA_DIR / "langgraph_checkpoints.db"))
)
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")


class LearningLoopState(TypedDict, total=False):
    workflow_id: str
    user_input: str
    student_id: Optional[str]
    student_profile: Dict[str, Any]
    db_path: str
    extra_data: Dict[str, Any]
    topic: str
    days: int
    question_count: int
    difficulty: str
    question_types: List[str]
    resource_file: str
    started_at: str
    finished_at: Optional[str]
    status: str
    message: str
    steps: List[Dict[str, Any]]
    audits: Dict[str, Any]
    audit_history: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    quiz: Dict[str, Any]
    submitted_answers: Dict[str, Any]
    answer_records: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    weak_points: List[str]
    mastered_points: List[str]
    recommendation: Any
    remedial_plan: Any
    summary: str


@dataclass(frozen=True)
class LearningLoopServices:
    """Injectable node services keep graph orchestration independently testable."""

    prepare: Callable[[LearningLoopState], Dict[str, Any]]
    plan: Callable[[LearningLoopState], Dict[str, Any]]
    resource: Callable[[LearningLoopState], Dict[str, Any]]
    quiz: Callable[[LearningLoopState], Dict[str, Any]]
    evaluate: Callable[[LearningLoopState], List[Dict[str, Any]]]
    analyze: Callable[[LearningLoopState], Dict[str, Any]]
    recommend: Callable[[LearningLoopState], Dict[str, Any]]
    remedial: Callable[[LearningLoopState], Dict[str, Any]]
    summarize: Callable[[LearningLoopState, Dict[str, Any]], str]
    parse_quiz: Callable[[Any], Dict[str, Any]]
    timeline_item: Callable[..., Dict[str, Any]]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_default_services() -> LearningLoopServices:
    """Adapt the existing domain functions into LangGraph node services."""
    try:
        from .learning_analysis import analyze_learning_status
        from .learning_path_generator import generate_learning_path
        from .multi_agent_learning_loop import (
            build_timeline_item,
            evaluate_submitted_answers,
            parse_quiz_result,
            read_resource_result,
            recommend_next_content_runtime,
            run_loop_step,
            run_step_with_audit,
            summarize_loop_result,
        )
        from .quiz_generator import generate_rag_quiz
        from .resource_generator import generate_learning_resource
        from .workflow_manager import (
            decide_difficulty,
            decide_question_count,
            decide_question_types,
            extract_days,
            extract_topic,
            safe_filename,
        )
    except ImportError:
        from learning_analysis import analyze_learning_status
        from learning_path_generator import generate_learning_path
        from multi_agent_learning_loop import (
            build_timeline_item,
            evaluate_submitted_answers,
            parse_quiz_result,
            read_resource_result,
            recommend_next_content_runtime,
            run_loop_step,
            run_step_with_audit,
            summarize_loop_result,
        )
        from quiz_generator import generate_rag_quiz
        from resource_generator import generate_learning_resource
        from workflow_manager import (
            decide_difficulty,
            decide_question_count,
            decide_question_types,
            extract_days,
            extract_topic,
            safe_filename,
        )

    def prepare(state: LearningLoopState) -> Dict[str, Any]:
        extra = state.get("extra_data", {})
        profile = state.get("student_profile", {})
        user_input = state.get("user_input", "")
        topic = extra.get("topic") or extract_topic(user_input, extra)
        days = int(extra.get("days", extract_days(user_input, default_days=3)))
        count = int(extra.get("count", decide_question_count(profile)))
        difficulty = str(extra.get("difficulty", decide_difficulty(profile, topic)))
        question_types = list(extra.get("question_types", decide_question_types(profile)))
        output_dir = Path(
            extra.get("output_dir")
            or os.getenv("LOOP_OUTPUT_DIR", str(LOCAL_DATA_DIR / "loop_outputs"))
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return {
            "topic": topic,
            "days": days,
            "question_count": count,
            "difficulty": difficulty,
            "question_types": question_types,
            "resource_file": str(output_dir / f"{safe_filename(topic)}_闭环学习资料.md"),
        }

    def plan(state: LearningLoopState) -> Dict[str, Any]:
        return run_step_with_audit(
            step_name="学习路径规划",
            agent_name="规划 Agent",
            func=generate_learning_path,
            audit_title="学习路径",
            audit_criteria=[
                "路径应符合学生基础和学习目标。",
                "学习任务应有先后顺序。",
                "内容应覆盖用户指定主题。",
            ],
            max_retry=2,
            workflow_id=state["workflow_id"],
            goal=f"{state['days']}天掌握{state['topic']}",
            student_profile=state["student_profile"],
            days=state["days"],
        )

    def resource(state: LearningLoopState) -> Dict[str, Any]:
        return run_step_with_audit(
            step_name="RAG可信学习资料生成",
            agent_name="资源 Agent",
            func=generate_learning_resource,
            audit_title="学习资料",
            audit_criteria=[
                "资料应围绕课程内容生成。",
                "资料应适合学生基础。",
                "资料应包含核心概念、解释、例子和练习建议。",
            ],
            max_retry=2,
            result_transform=read_resource_result,
            workflow_id=state["workflow_id"],
            topic=state["topic"],
            output_file=state["resource_file"],
            student_profile=state["student_profile"],
            resource_type="闭环学习资料",
        )

    def quiz(state: LearningLoopState) -> Dict[str, Any]:
        return run_step_with_audit(
            step_name="RAG可信练习题生成",
            agent_name="题目 Agent",
            func=generate_rag_quiz,
            audit_title="练习题",
            audit_criteria=[
                "题目应包含题干、答案和解析。",
                "题目应包含细分知识点 knowledge_point。",
                "题目数量应符合要求。",
                "选择题应包含 A、B、C、D 四个选项。",
            ],
            max_retry=2,
            result_transform=parse_quiz_result,
            workflow_id=state["workflow_id"],
            topic=state["topic"],
            student_profile=state["student_profile"],
            question_types=state["question_types"],
            count=state["question_count"],
            difficulty=state["difficulty"],
            top_k=8,
        )

    def evaluate(state: LearningLoopState) -> List[Dict[str, Any]]:
        return evaluate_submitted_answers(
            submitted_answers=state["submitted_answers"],
            quiz_data=state["quiz"],
            student_id=state.get("student_id"),
            default_topic=state["topic"],
            difficulty=state["difficulty"],
            student_profile=state["student_profile"],
            db_path=state["db_path"],
        )

    def analyze(state: LearningLoopState) -> Dict[str, Any]:
        return run_loop_step(
            step_name="答题评估与学情分析",
            agent_name="评估 Agent",
            func=analyze_learning_status,
            workflow_id=state["workflow_id"],
            records=state["answer_records"],
            student_profile=state["student_profile"],
        )

    def recommend(state: LearningLoopState) -> Dict[str, Any]:
        return run_loop_step(
            step_name="下一步推荐",
            agent_name="推荐 Agent",
            func=recommend_next_content_runtime,
            workflow_id=state["workflow_id"],
            student_profile=state["student_profile"],
            weak_points=state.get("weak_points") or state["student_profile"].get("weak_points", []),
            mastered_points=state.get("mastered_points") or state["student_profile"].get("mastered_points", []),
        )

    def remedial(state: LearningLoopState) -> Dict[str, Any]:
        weak_points = state.get("weak_points", [])
        goal = (
            f"补救薄弱知识点：{'、'.join(weak_points)}"
            if weak_points
            else f"巩固当前知识点：{state['topic']}"
        )
        return run_loop_step(
            step_name="薄弱点补救路径",
            agent_name="补救规划 Agent",
            func=generate_learning_path,
            workflow_id=state["workflow_id"],
            goal=goal,
            student_profile=state["student_profile"],
            days=int(state.get("extra_data", {}).get("remedial_days", 3)),
        )

    def summarize(state: LearningLoopState, result: Dict[str, Any]) -> str:
        return summarize_loop_result(
            state["user_input"],
            state["student_profile"],
            result,
        )

    return LearningLoopServices(
        prepare=prepare,
        plan=plan,
        resource=resource,
        quiz=quiz,
        evaluate=evaluate,
        analyze=analyze,
        recommend=recommend,
        remedial=remedial,
        summarize=summarize,
        parse_quiz=parse_quiz_result,
        timeline_item=build_timeline_item,
    )


def state_to_result(state: LearningLoopState) -> Dict[str, Any]:
    """Map graph state back to the API's established response contract."""
    result = {
        "workflow_id": state.get("workflow_id"),
        "loop_type": "multi_agent_learning_loop",
        "orchestrator": "langgraph",
        "status": state.get("status", "running"),
        "student_id": state.get("student_id"),
        "topic": state.get("topic"),
        "days": state.get("days"),
        "question_count": state.get("question_count"),
        "difficulty": state.get("difficulty"),
        "question_types": state.get("question_types", []),
        "started_at": state.get("started_at"),
        "finished_at": state.get("finished_at"),
        "steps": state.get("steps", []),
        "audits": state.get("audits", {}),
        "audit_history": state.get("audit_history", {}),
        "timeline": state.get("timeline", []),
        "quiz": state.get("quiz", {}),
    }
    for key in (
        "message",
        "summary",
        "answer_records",
        "analysis",
        "weak_points",
        "mastered_points",
        "recommendation",
        "remedial_plan",
    ):
        if key in state:
            result[key] = state[key]
    return result


def build_learning_loop_graph(
    services: Optional[LearningLoopServices] = None,
    checkpointer: Any = None,
):
    """Build the explicit, inspectable LangGraph state machine."""
    services = services or create_default_services()

    def prepare_node(state: LearningLoopState) -> Dict[str, Any]:
        prepared = services.prepare(state)
        return {
            **prepared,
            "status": "running",
            "steps": state.get("steps", []),
            "audits": state.get("audits", {}),
            "audit_history": state.get("audit_history", {}),
            "timeline": state.get("timeline", []),
        }

    def audited_node(
        state: LearningLoopState,
        runner: Callable[[LearningLoopState], Dict[str, Any]],
        audit_key: str,
        order: int,
    ) -> Dict[str, Any]:
        output = runner(state)
        step = output["step"]
        audit = output.get("audit")
        return {
            "steps": [*state.get("steps", []), step],
            "audits": {**state.get("audits", {}), audit_key: audit},
            "audit_history": {
                **state.get("audit_history", {}),
                audit_key: output.get("audit_history", []),
            },
            "timeline": [
                *state.get("timeline", []),
                services.timeline_item(
                    order=order,
                    step=step,
                    audit=audit,
                    retry_count=output.get("retry_count", 0),
                ),
            ],
        }

    def plan_node(state: LearningLoopState) -> Dict[str, Any]:
        return audited_node(state, services.plan, "plan", 1)

    def resource_node(state: LearningLoopState) -> Dict[str, Any]:
        return audited_node(state, services.resource, "resource", 2)

    def quiz_node(state: LearningLoopState) -> Dict[str, Any]:
        update = audited_node(state, services.quiz, "quiz", 3)
        quiz_step = update["steps"][-1]
        update["quiz"] = services.parse_quiz(quiz_step.get("result"))
        return update

    def waiting_summary_node(state: LearningLoopState) -> Dict[str, Any]:
        update: Dict[str, Any] = {
            "status": "waiting_for_answers",
            "message": "计划、资料和题目已经生成，等待学生提交答案。",
        }
        preview = state_to_result({**state, **update})
        update["summary"] = services.summarize(state, preview)
        return update

    def await_answers_node(state: LearningLoopState) -> Dict[str, Any]:
        answers = state.get("submitted_answers")
        if not answers:
            answers = interrupt(
                {
                    "workflow_id": state["workflow_id"],
                    "status": "waiting_for_answers",
                    "message": state.get("message", "等待学生提交答案。"),
                    "question_count": len(state.get("quiz", {}).get("questions", [])),
                }
            )
        if not isinstance(answers, dict) or not answers:
            raise ValueError("submitted_answers 必须是非空对象，键为题目ID，值为学生答案。")
        return {"submitted_answers": answers, "status": "running"}

    def route_after_quiz(state: LearningLoopState) -> str:
        return "ready" if state.get("submitted_answers") else "wait"

    def evaluate_node(state: LearningLoopState) -> Dict[str, Any]:
        return {"answer_records": services.evaluate(state)}

    def analysis_node(state: LearningLoopState) -> Dict[str, Any]:
        step = services.analyze(state)
        analysis = step.get("result") if step.get("status") == "success" else {}
        analysis = analysis if isinstance(analysis, dict) else {}
        return {
            "steps": [*state.get("steps", []), step],
            "analysis": analysis,
            "weak_points": analysis.get("weak_points", []),
            "mastered_points": analysis.get("mastered_points", []),
        }

    def recommend_node(state: LearningLoopState) -> Dict[str, Any]:
        step = services.recommend(state)
        return {
            "steps": [*state.get("steps", []), step],
            "recommendation": step.get("result") if step.get("status") == "success" else None,
        }

    def remedial_node(state: LearningLoopState) -> Dict[str, Any]:
        step = services.remedial(state)
        return {
            "steps": [*state.get("steps", []), step],
            "remedial_plan": step.get("result") if step.get("status") == "success" else None,
        }

    def final_summary_node(state: LearningLoopState) -> Dict[str, Any]:
        update: Dict[str, Any] = {
            "status": "closed_loop_completed",
            "finished_at": _now(),
            "message": "学习闭环已完成。",
        }
        result = state_to_result({**state, **update})
        update["summary"] = services.summarize(state, result)
        return update

    builder = StateGraph(LearningLoopState)
    builder.add_node("prepare", prepare_node)
    builder.add_node("plan", plan_node)
    builder.add_node("resource", resource_node)
    builder.add_node("quiz", quiz_node)
    builder.add_node("waiting_summary", waiting_summary_node)
    builder.add_node("await_answers", await_answers_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("analyze", analysis_node)
    builder.add_node("recommend", recommend_node)
    builder.add_node("remedial", remedial_node)
    builder.add_node("final_summary", final_summary_node)
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "plan")
    builder.add_edge("plan", "resource")
    builder.add_edge("resource", "quiz")
    builder.add_conditional_edges(
        "quiz",
        route_after_quiz,
        {"ready": "await_answers", "wait": "waiting_summary"},
    )
    builder.add_edge("waiting_summary", "await_answers")
    builder.add_edge("await_answers", "evaluate")
    builder.add_edge("evaluate", "analyze")
    builder.add_edge("analyze", "recommend")
    builder.add_edge("recommend", "remedial")
    builder.add_edge("remedial", "final_summary")
    builder.add_edge("final_summary", END)
    return builder.compile(checkpointer=checkpointer)


_GRAPH_LOCK = threading.Lock()
_GRAPH = None
_CHECKPOINT_CONNECTION: Optional[sqlite3.Connection] = None


def get_learning_loop_graph():
    """Return the process-wide graph backed by a lightweight SQLite saver."""
    global _GRAPH, _CHECKPOINT_CONNECTION
    if _GRAPH is not None:
        return _GRAPH
    with _GRAPH_LOCK:
        if _GRAPH is None:
            _CHECKPOINT_CONNECTION = sqlite3.connect(
                DEFAULT_CHECKPOINT_DB,
                check_same_thread=False,
            )
            saver = SqliteSaver(_CHECKPOINT_CONNECTION)
            _GRAPH = build_learning_loop_graph(checkpointer=saver)
    return _GRAPH


def multi_agent_learning_loop(
    user_input: str,
    student_profile: Dict[str, Any],
    student_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    *,
    graph: Any = None,
) -> Dict[str, Any]:
    """Run or resume the LangGraph workflow using the existing public contract."""
    try:
        from .student_memory import DB_PATH as DEFAULT_STUDENT_DB
    except ImportError:
        from student_memory import DB_PATH as DEFAULT_STUDENT_DB

    extra = dict(extra_data or {})
    supplied_workflow_id = extra.get("workflow_id")
    workflow_id = str(supplied_workflow_id or uuid.uuid4())
    submitted_answers = extra.get("submitted_answers")
    runtime = graph or get_learning_loop_graph()
    config = {"configurable": {"thread_id": workflow_id}}

    snapshot = runtime.get_state(config)
    if snapshot.values:
        saved_state = dict(snapshot.values)
        if snapshot.next and "await_answers" in snapshot.next:
            if not submitted_answers:
                return state_to_result(saved_state)
            runtime.invoke(Command(resume=submitted_answers), config=config)
            return state_to_result(dict(runtime.get_state(config).values))
        if saved_state.get("status") == "closed_loop_completed":
            return state_to_result(saved_state)

    initial_state: LearningLoopState = {
        "workflow_id": workflow_id,
        "user_input": user_input,
        "student_id": student_id,
        "student_profile": student_profile,
        "db_path": db_path or DEFAULT_STUDENT_DB,
        "extra_data": extra,
        "started_at": _now(),
        "finished_at": None,
        "status": "running",
        "steps": [],
        "audits": {},
        "audit_history": {},
        "timeline": [],
    }
    if submitted_answers:
        initial_state["submitted_answers"] = submitted_answers

    runtime.invoke(initial_state, config=config)
    return state_to_result(dict(runtime.get_state(config).values))


def multi_agent_learning_loop_by_student(
    user_input: str,
    student_id: str,
    extra_data: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    *,
    graph: Any = None,
) -> Dict[str, Any]:
    """Load the student profile and run/resume the LangGraph workflow."""
    try:
        from .student_memory import DB_PATH, get_student_profile, init_db
    except ImportError:
        from student_memory import DB_PATH, get_student_profile, init_db

    resolved_db = db_path or DB_PATH
    init_db(resolved_db)
    profile = get_student_profile(student_id, resolved_db)
    if profile is None:
        raise ValueError(f"未找到学生 {student_id} 的画像，请先创建学生画像。")
    return multi_agent_learning_loop(
        user_input=user_input,
        student_profile=profile,
        student_id=student_id,
        extra_data=extra_data,
        db_path=resolved_db,
        graph=graph,
    )


__all__ = [
    "LearningLoopServices",
    "LearningLoopState",
    "build_learning_loop_graph",
    "get_learning_loop_graph",
    "multi_agent_learning_loop",
    "multi_agent_learning_loop_by_student",
    "state_to_result",
]
