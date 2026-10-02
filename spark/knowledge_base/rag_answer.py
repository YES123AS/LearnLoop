# knowledge_base/rag_answer.py

import os
from pathlib import Path
from typing import Dict, Any

try:
    from ..spark_llm import SparkX2Client
except ImportError:
    from spark_llm import SparkX2Client

from .retriever import (
    create_langchain_retriever,
    documents_to_results,
    format_retrieved_context,
)


def build_rag_prompt(
    question: str,
    retrieved_context: str,
    student_profile: Dict[str, Any] = None
) -> str:
    """
    构造 RAG Prompt
    """

    if student_profile is None:
        student_profile = {}

    weak_points = "、".join(student_profile.get("weak_points", [])) or "暂无"

    prompt = f"""
你是一个基于课程知识库的个性化学习助手。
请你严格参考下面的课程资料回答学生问题。

学生信息：
- 年级：{student_profile.get("grade", "未知")}
- 专业：{student_profile.get("major", "未知")}
- 当前课程：{student_profile.get("course", "未知")}
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 薄弱知识点：{weak_points}
- 学习风格：{student_profile.get("learning_style", "未知")}

课程资料：
{retrieved_context}

学生问题：
{question}

回答要求：
1. 必须优先依据课程资料回答。
2. 如果课程资料中没有相关内容，要明确说明“资料中没有直接提到”，不要编造。
3. 如果学生基础较弱，请先用通俗语言解释，再给正式解释。
4. 如果涉及学生薄弱知识点，请重点讲解。
5. 最后给出一个简单例子或学习建议。
6. 回答要清晰、有条理，适合学生学习。
"""
    return prompt


def rag_answer(
    question: str,
    student_profile: Dict[str, Any] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    RAG 问答主函数：
    1. 检索课程资料
    2. 构造 Prompt
    3. 调用大模型生成回答
    4. 返回答案和引用来源
    """

    db_dir = os.getenv(
        "VECTOR_DB_DIR",
        str(Path(__file__).resolve().parents[2] / ".local-data" / "vector_db"),
    )
    retriever = create_langchain_retriever(db_dir=db_dir, top_k=top_k)
    retrieved_results = documents_to_results(retriever.invoke(question))

    retrieved_context = format_retrieved_context(retrieved_results)

    prompt = build_rag_prompt(
        question=question,
        retrieved_context=retrieved_context,
        student_profile=student_profile
    )

    client = SparkX2Client()

    answer = client.chat(
        user_input=prompt,
        system_prompt="你是一个严谨的课程学习助手，只能根据给定课程资料进行解释和教学。",
        temperature=0.4,
        max_tokens=1800,
        thinking="disabled"
    )

    sources = [
        {
            "file_name": item["file_name"],
            "score": item["score"],
            "content_preview": item["content"][:120]
        }
        for item in retrieved_results
    ]

    return {
        "answer": answer,
        "sources": sources
    }
