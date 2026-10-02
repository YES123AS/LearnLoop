import json
import mimetypes
import os
import re
import shutil
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .knowledge_base.document_loader import load_documents_from_folder
    from .knowledge_base.text_splitter import split_documents
    from .knowledge_base.vector_store import SimpleVectorStore
    from .agent_manager import recommend_next_content
    from .learning_analysis import analyze_learning_status
    from .learning_path_generator import generate_learning_path
    from .quiz_generator import generate_rag_quiz
    from .spark_llm import SparkX2Client
    from .trusted_course_generator import generate_trusted_answer, generate_trusted_resource
    from .langgraph_learning_loop import (
        multi_agent_learning_loop,
        multi_agent_learning_loop_by_student,
    )
    from .dynamic_learning_path import (
        generate_dynamic_initial_path_by_student,
        generate_next_learning_step,
    )
    from .mistake_diagnosis import (
        create_mistake_diagnosis_from_wrong_answer,
        evaluate_mistake_retry,
        get_mistake_book,
        get_mistake_detail,
    )
except ImportError:
    from knowledge_base.document_loader import load_documents_from_folder
    from knowledge_base.text_splitter import split_documents
    from knowledge_base.vector_store import SimpleVectorStore
    from agent_manager import recommend_next_content
    from learning_analysis import analyze_learning_status
    from learning_path_generator import generate_learning_path
    from quiz_generator import generate_rag_quiz
    from spark_llm import SparkX2Client
    from trusted_course_generator import generate_trusted_answer, generate_trusted_resource
    from langgraph_learning_loop import (
        multi_agent_learning_loop,
        multi_agent_learning_loop_by_student,
    )
    from dynamic_learning_path import (
        generate_dynamic_initial_path_by_student,
        generate_next_learning_step,
    )
    from mistake_diagnosis import (
        create_mistake_diagnosis_from_wrong_answer,
        evaluate_mistake_retry,
        get_mistake_book,
        get_mistake_detail,
    )


app = FastAPI(
    title="Personalized Learning AI API",
    description="面向前端的个性化学习 AI 能力接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., description="学生问题")
    student_profile: Dict[str, Any] = Field(default_factory=dict)


class ResourceRequest(BaseModel):
    topic: str = Field(..., description="学习资料主题")
    student_profile: Dict[str, Any] = Field(default_factory=dict)
    resource_type: str = Field(default="完整学习资料")
    output_file: Optional[str] = Field(default=None, description="可选输出文件路径")
    fast_mode: bool = Field(default=True, description="是否使用快速本地可信检查，关闭后会额外调用模型做严格检查")


class QuizRequest(BaseModel):
    topic: str = Field(..., description="出题知识点")
    student_profile: Dict[str, Any] = Field(default_factory=dict)
    question_types: List[str] = Field(default_factory=lambda: ["选择题", "填空题", "简答题"])
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="简单")


class PathRequest(BaseModel):
    goal: str = Field(..., description="学习目标")
    student_profile: Dict[str, Any] = Field(default_factory=dict)
    days: int = Field(default=7, ge=1, le=60)


class DynamicPathStartRequest(BaseModel):
    student_id: str = Field(..., description="学生ID")
    goal: str = Field(..., description="动态学习目标")


class DynamicPathNextRequest(BaseModel):
    student_id: str = Field(..., description="学生ID")
    goal: str = Field(..., description="学习目标")
    current_topic: Optional[str] = Field(default=None, description="当前练习知识点")


class AnalyzeStatusRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(default_factory=list)
    student_profile: Dict[str, Any] = Field(default_factory=dict)


class RecommendNextRequest(BaseModel):
    student_profile: Dict[str, Any] = Field(default_factory=dict)
    weak_points: Optional[List[str]] = None
    mastered_points: List[str] = Field(default_factory=list)


class LearningLoopRequest(BaseModel):
    user_input: str = Field(..., description="学生自然语言学习需求")
    student_profile: Dict[str, Any] = Field(default_factory=dict, description="学生画像")
    student_id: Optional[str] = Field(default=None, description="可选学生ID")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外参数，例如 topic/days/submitted_answers/use_rag")


class MistakeDiagnoseRequest(BaseModel):
    student_id: str = Field(..., description="学生ID")
    question: Dict[str, Any] = Field(..., description="题目信息")
    user_answer: Any = Field(..., description="学生答案")
    difficulty: str = Field(default="简单", description="题目难度")
    judge_reason: str = Field(default="", description="判分理由")
    student_profile: Dict[str, Any] = Field(default_factory=dict, description="学生画像")


class MistakeRetryRequest(BaseModel):
    mistake_id: str = Field(..., description="错题ID")
    variant_index: int = Field(default=1, ge=1, description="变式题序号，从1开始")
    user_answer: Any = Field(..., description="学生对变式题的答案")


def _raise_ai_error(error: Exception) -> None:
    traceback.print_exc()
    raise HTTPException(
        status_code=500,
        detail={
            "success": False,
            "message": str(error)
        }
    )


def _parse_json_if_possible(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
LOCAL_ROOT = PROJECT_ROOT / ".local-data"
DATA_DIR = Path(os.getenv("LEARNLOOP_DATA_DIR", str(LOCAL_ROOT / "data")))
DOCS_DIR = Path(os.getenv("COURSE_DOCS_DIR", str(BASE_DIR / "docs")))
VECTOR_DB_DIR = Path(os.getenv("VECTOR_DB_DIR", str(LOCAL_ROOT / "vector_db")))
GENERATED_OUTPUT_DIR = Path(
    os.getenv("GENERATED_OUTPUT_DIR", str(DATA_DIR / "generated"))
)
SUPPORTED_KB_SUFFIXES = {".pdf", ".pptx", ".docx", ".txt"}
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_CHAT_UPLOAD_SIZE = 20 * 1024 * 1024


def _safe_upload_name(filename: str) -> str:
    name = Path(filename or "").name.strip()
    if not name:
      raise HTTPException(status_code=400, detail={"success": False, "message": "文件名不能为空"})

    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe_stem = re.sub(r'[<>:"/\\\\|?*\\x00-\\x1f]', "_", stem).strip(" ._")
    if not safe_stem:
        safe_stem = "knowledge_file"
    return f"{safe_stem}{suffix}"


def _list_knowledge_files() -> List[Dict[str, Any]]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(DOCS_DIR.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_KB_SUFFIXES:
            stat = path.stat()
            files.append({
                "name": path.name,
                "suffix": path.suffix.lower(),
                "size": stat.st_size,
                "updated_at": stat.st_mtime,
            })
    return files


def _parse_profile_form(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _save_upload_to_docs(upload: UploadFile) -> Dict[str, Any]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_upload_name(upload.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in SUPPORTED_KB_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "知识库文件仅支持 pdf、pptx、docx 或 txt。"}
        )

    target = DOCS_DIR / safe_name
    with target.open("wb") as out_file:
        shutil.copyfileobj(upload.file, out_file)

    return {
        "name": safe_name,
        "size": target.stat().st_size,
        "path": str(target.resolve())
    }


def _build_image_prompt(question: str, student_profile: Dict[str, Any], filename: str) -> str:
    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"
    user_question = question.strip() or "请识别图片内容，并结合课程学习给出讲解。"
    return f"""
请先识别上传图片中的主要内容，再回答学生的问题。

学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}

图片文件名：{filename}

学生问题：
{user_question}

回答要求：
1. 先概括图片里能看到的学习内容或题目信息。
2. 再结合学生问题作答。
3. 如果图片是题目，请给出解题思路、答案和易错点。
4. 如果图片内容不清楚，请明确说明哪些信息无法识别，并建议学生重新上传更清晰图片。
5. 回答要适合学生当前基础，尽量通俗、有条理。
"""


def _vector_db_status() -> Dict[str, Any]:
    chunks_path = VECTOR_DB_DIR / "chunks.json"
    embeddings_path = VECTOR_DB_DIR / "embeddings.npy"
    chunk_count = 0
    if chunks_path.exists():
        try:
            chunk_count = len(json.loads(chunks_path.read_text(encoding="utf-8")))
        except Exception:
            chunk_count = 0
    return {
        "exists": chunks_path.exists() and embeddings_path.exists(),
        "chunk_count": chunk_count,
        "chunks_file": str(chunks_path.resolve()),
        "embeddings_file": str(embeddings_path.resolve()),
    }


def _rebuild_knowledge_base() -> Dict[str, Any]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    documents = load_documents_from_folder(str(DOCS_DIR))
    if not documents:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "docs 文件夹中没有可用文档，无法构建知识库。"}
        )

    chunks = split_documents(documents=documents, chunk_size=500, overlap=80)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "文档未解析出有效文本，无法构建知识库。"}
        )

    vector_store = SimpleVectorStore(db_dir=str(VECTOR_DB_DIR))
    vector_store.build(chunks)
    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "vector_db": _vector_db_status(),
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "AI API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"success": True, "status": "ok"}


@app.get("/ai/knowledge_base/status")
def ai_knowledge_base_status() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "docs_dir": str(DOCS_DIR.resolve()),
            "supported_suffixes": sorted(SUPPORTED_KB_SUFFIXES),
            "files": _list_knowledge_files(),
            "vector_db": _vector_db_status(),
        }
    }


@app.post("/ai/knowledge_base/upload")
async def ai_upload_knowledge_base(
    files: Optional[List[UploadFile]] = File(default=None),
    single_files: Optional[List[UploadFile]] = File(default=None, alias="file"),
) -> Dict[str, Any]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    uploads = [*(files or []), *(single_files or [])]
    if not uploads:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "请至少上传一个知识库文件，表单字段名应为 files。"}
        )

    saved_files = []
    skipped_files = []

    for upload in uploads:
        safe_name = _safe_upload_name(upload.filename)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in SUPPORTED_KB_SUFFIXES:
            skipped_files.append({
                "name": upload.filename,
                "reason": f"暂不支持 {suffix or '无后缀'} 文件",
            })
            continue

        target = DOCS_DIR / safe_name
        with target.open("wb") as out_file:
            shutil.copyfileobj(upload.file, out_file)

        saved_files.append({
            "name": target.name,
            "size": target.stat().st_size,
            "path": str(target.resolve()),
        })

    if not saved_files:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "没有可用文件被保存，请上传 pdf、pptx、docx 或 txt 文件。",
                "skipped_files": skipped_files,
            }
        )

    rebuild_result = _rebuild_knowledge_base()

    return {
        "success": True,
        "data": {
            "saved_files": saved_files,
            "skipped_files": skipped_files,
            "files": _list_knowledge_files(),
            "rebuild": rebuild_result,
        }
    }


@app.post("/ai/knowledge_base/rebuild")
def ai_rebuild_knowledge_base() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "files": _list_knowledge_files(),
            "rebuild": _rebuild_knowledge_base(),
        }
    }


@app.post("/ai/chat")
def ai_chat(request: ChatRequest) -> Dict[str, Any]:
    try:
        result = generate_trusted_answer(
            question=request.question,
            student_profile=request.student_profile,
            top_k=6
        )
        return {
            "success": True,
            "data": {
                "answer": result["answer"],
                "sources": result.get("sources", []),
                "candidate_sources": result.get("candidate_sources", []),
                "retrieval_check": result.get("retrieval_check"),
                "grounding_check": result.get("grounding_check"),
                "mode": result.get("mode"),
                "trust_level": result.get("trust_level", "unknown"),
                "fallback_reason": result.get("fallback_reason", ""),
            }
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/chat/upload")
async def ai_chat_upload(
    file: UploadFile = File(...),
    question: str = Form(default=""),
    student_profile: str = Form(default="{}")
) -> Dict[str, Any]:
    try:
        filename = Path(file.filename or "attachment").name
        suffix = Path(filename).suffix.lower()
        profile = _parse_profile_form(student_profile)
        user_question = question.strip() or "请结合这个附件进行学习辅导。"

        if suffix in SUPPORTED_KB_SUFFIXES:
            saved_file = _save_upload_to_docs(file)
            rebuild_info = _rebuild_knowledge_base()
            result = generate_trusted_answer(
                question=user_question,
                student_profile=profile,
                top_k=8
            )
            return {
                "success": True,
                "data": {
                    "answer": result["answer"],
                    "sources": result.get("sources", []),
                    "candidate_sources": result.get("candidate_sources", []),
                    "retrieval_check": result.get("retrieval_check"),
                    "grounding_check": result.get("grounding_check"),
                    "mode": "file_rag",
                    "rag_mode": result.get("mode"),
                    "trust_level": result.get("trust_level", "unknown"),
                    "fallback_reason": result.get("fallback_reason", ""),
                    "attachment": {
                        "name": saved_file["name"],
                        "type": "document",
                        "size": saved_file["size"]
                    },
                    "knowledge_base": rebuild_info
                }
            }

        if suffix in SUPPORTED_IMAGE_SUFFIXES:
            image_bytes = await file.read()
            if len(image_bytes) > MAX_CHAT_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail={"success": False, "message": "图片过大，请上传 20MB 以内的图片。"}
                )
            mime_type = file.content_type or mimetypes.guess_type(filename)[0] or "image/png"
            prompt = _build_image_prompt(user_question, profile, filename)
            client = SparkX2Client()
            answer = client.chat_with_image(
                user_input=prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                temperature=0.4,
                max_tokens=2400,
                thinking="disabled"
            )
            return {
                "success": True,
                "data": {
                    "answer": answer,
                    "sources": [],
                    "mode": "image_understanding",
                    "trust_level": "low",
                    "fallback_reason": "图片理解结果由 AI 根据上传图片生成，未经过课程知识库依据性检查。",
                    "attachment": {
                        "name": filename,
                        "type": "image",
                        "size": len(image_bytes),
                        "mime_type": mime_type
                    }
                }
            }

        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "暂不支持该附件类型。文件支持 pdf、pptx、docx、txt；图片支持 png、jpg、jpeg、webp、bmp。"
            }
        )
    except HTTPException:
        raise
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/generate_resource")
def ai_generate_resource(request: ResourceRequest) -> Dict[str, Any]:
    try:
        output_file = request.output_file
        if not output_file:
            GENERATED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = str(GENERATED_OUTPUT_DIR / "trusted_learning_resource.md")

        result = generate_trusted_resource(
            topic=request.topic,
            output_file=output_file,
            student_profile=request.student_profile,
            resource_type=request.resource_type,
            top_k=5,
            fast_checks=request.fast_mode,
        )

        return {
            "success": True,
            "data": {
                "topic": request.topic,
                "resource_type": request.resource_type,
                "output_file": str(Path(result["output_file"]).resolve()),
                "content": result["resource"],
                "sources": result.get("sources", []),
                "candidate_sources": result.get("candidate_sources", []),
                "retrieval_check": result.get("retrieval_check"),
                "grounding_check": result.get("grounding_check"),
                "mode": result.get("mode"),
                "trust_level": result.get("trust_level", "unknown"),
                "fallback_reason": result.get("fallback_reason", ""),
                "fast_mode": request.fast_mode,
            }
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/generate_quiz")
def ai_generate_quiz(request: QuizRequest) -> Dict[str, Any]:
    try:
        result = generate_rag_quiz(
            topic=request.topic,
            student_profile=request.student_profile,
            question_types=request.question_types,
            count=request.count,
            difficulty=request.difficulty,
            top_k=8
        )

        return {
            "success": True,
            "data": {
                "quiz": _parse_json_if_possible(result),
                "raw": result
            }
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/generate_path")
def ai_generate_path(request: PathRequest) -> Dict[str, Any]:
    try:
        path = generate_learning_path(
            goal=request.goal,
            student_profile=request.student_profile,
            days=request.days
        )
        return {
            "success": True,
            "data": {
                "path": path
            }
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/dynamic_path/start")
def ai_dynamic_path_start(request: DynamicPathStartRequest) -> Dict[str, Any]:
    """
    生成动态学习路径的初始阶段。
    不一次性生成完整计划，只生成当前第一步和候选知识点队列。
    """
    try:
        result = generate_dynamic_initial_path_by_student(
            student_id=request.student_id,
            goal=request.goal
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/dynamic_path/next")
def ai_dynamic_path_next(request: DynamicPathNextRequest) -> Dict[str, Any]:
    """
    每轮练习后调用，根据最新做题记录和掌握度动态生成下一步学习任务。
    """
    try:
        result = generate_next_learning_step(
            student_id=request.student_id,
            goal=request.goal,
            current_topic=request.current_topic
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/analyze_status")
def ai_analyze_status(request: AnalyzeStatusRequest) -> Dict[str, Any]:
    try:
        if not request.records:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "records 不能为空，至少需要一条做题记录。"
                }
            )

        analysis = analyze_learning_status(
            records=request.records,
            student_profile=request.student_profile
        )

        return {
            "success": True,
            "data": analysis
        }
    except HTTPException:
        raise
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/recommend_next")
def ai_recommend_next(request: RecommendNextRequest) -> Dict[str, Any]:
    try:
        weak_points = request.weak_points
        if weak_points is None:
            weak_points = request.student_profile.get("weak_points", [])

        recommendation = recommend_next_content(
            student_profile=request.student_profile,
            weak_points=weak_points,
            mastered_points=request.mastered_points
        )

        return {
            "success": True,
            "data": {
                "recommendation": recommendation
            }
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/multi_agent_learning_loop")
def ai_multi_agent_learning_loop(request: LearningLoopRequest) -> Dict[str, Any]:
    """
    一键多 Agent 学习闭环：
    规划、审核、RAG资料、RAG题目、评估、推荐、补救规划和总结。
    """
    try:
        if request.student_id and not request.student_profile:
            result = multi_agent_learning_loop_by_student(
                user_input=request.user_input,
                student_id=request.student_id,
                extra_data=request.extra_data
            )
        else:
            result = multi_agent_learning_loop(
                user_input=request.user_input,
                student_profile=request.student_profile,
                student_id=request.student_id,
                extra_data=request.extra_data
            )

        return {
            "success": True,
            "data": result
        }
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/mistake/diagnose")
def ai_mistake_diagnose(request: MistakeDiagnoseRequest) -> Dict[str, Any]:
    """
    单独进行错因诊断。
    适合前端在学生答错某道题后立即调用。
    """
    try:
        result = create_mistake_diagnosis_from_wrong_answer(
            student_id=request.student_id,
            question=request.question,
            user_answer=request.user_answer,
            difficulty=request.difficulty,
            judge_reason=request.judge_reason,
            student_profile=request.student_profile or None,
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as error:
        _raise_ai_error(error)


@app.get("/ai/mistake_book/{student_id}")
def ai_get_mistake_book(
    student_id: str,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    获取学生错题本。
    status 可选：未修复 / 已修复
    """
    try:
        result = get_mistake_book(
            student_id=student_id,
            status=status,
        )

        return {
            "success": True,
            "data": {
                "student_id": student_id,
                "count": len(result),
                "mistakes": result,
            },
        }

    except Exception as error:
        _raise_ai_error(error)


@app.get("/ai/mistake/{mistake_id}")
def ai_get_mistake_detail(mistake_id: str) -> Dict[str, Any]:
    """
    获取单道错题的完整诊断详情。
    """
    try:
        result = get_mistake_detail(mistake_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": f"未找到错题：{mistake_id}",
                },
            )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise
    except Exception as error:
        _raise_ai_error(error)


@app.post("/ai/mistake/retry")
def ai_mistake_retry(request: MistakeRetryRequest) -> Dict[str, Any]:
    """
    学生完成变式题后，判断错题是否修复。
    """
    try:
        result = evaluate_mistake_retry(
            mistake_id=request.mistake_id,
            variant_index=request.variant_index,
            user_answer=request.user_answer,
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as error:
        _raise_ai_error(error)
