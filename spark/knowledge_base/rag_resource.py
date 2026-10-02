import os
from pathlib import Path
from typing import Any, Dict

try:
    from ..spark_llm import SparkX2Client
except ImportError:
    from spark_llm import SparkX2Client

from .retriever import (
    create_langchain_retriever,
    documents_to_results,
    format_retrieved_context,
)


def generate_rag_resource(
    topic: str,
    student_profile: Dict[str, Any] = None,
    top_k: int = 6
) -> Dict[str, Any]:
    """
    基于课程知识库生成学习资料。
    """

    if student_profile is None:
        student_profile = {}

    db_dir = os.getenv(
        "VECTOR_DB_DIR",
        str(Path(__file__).resolve().parents[2] / ".local-data" / "vector_db"),
    )
    retriever = create_langchain_retriever(db_dir=db_dir, top_k=top_k)
    results = documents_to_results(retriever.invoke(topic))
    context = format_retrieved_context(results)

    prompt = f"""
你是一个课程学习资料生成助手。
请根据下面课程资料，为学生生成《{topic}》学习资料。

课程资料：
{context}

学生信息：
- 基础水平：{student_profile.get("level", "未知")}
- 学习目标：{student_profile.get("goal", "未知")}
- 学习风格：{student_profile.get("learning_style", "未知")}

生成要求：
1. 内容必须主要来自课程资料。
2. 先给核心概念。
3. 再给通俗解释。
4. 再给关键步骤。
5. 最后给一个简单例子。
6. 不要编造课程资料中没有的内容。
"""

    client = SparkX2Client()

    answer = client.chat(
        user_input=prompt,
        system_prompt="你是一个严谨的课程资料生成助手。",
        temperature=0.4,
        max_tokens=2000,
        thinking="disabled"
    )

    sources = [
        {
            "file_name": item["file_name"],
            "score": item["score"],
            "content_preview": item["content"][:120]
        }
        for item in results
    ]

    return {
        "resource": answer,
        "sources": sources
    }
