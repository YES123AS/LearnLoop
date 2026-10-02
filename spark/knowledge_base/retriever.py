# knowledge_base/retriever.py

from pathlib import Path
from typing import Any, List, Dict

import numpy as np
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from .vector_store import SimpleVectorStore


DEFAULT_VECTOR_DB_DIR = str(
    Path(__file__).resolve().parents[2] / ".local-data" / "vector_db"
)


class KnowledgeRetriever:
    """
    知识库检索器
    """

    def __init__(self, db_dir: str = DEFAULT_VECTOR_DB_DIR):
        self.vector_store = SimpleVectorStore(db_dir=db_dir)
        self.chunks, self.embeddings = self.vector_store.load()

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        检索与用户问题最相关的 top_k 个知识片段
        """
        query_embedding = self.vector_store.model.encode(
            [query],
            normalize_embeddings=True
        )[0]

        # 因为向量已经归一化，所以点积就等价于余弦相似度
        scores = np.dot(self.embeddings, query_embedding)

        top_indices = scores.argsort()[::-1][:top_k]

        results = []

        for index in top_indices:
            chunk = self.chunks[int(index)].copy()
            chunk["score"] = float(scores[index])
            results.append(chunk)

        return results


class LangChainKnowledgeRetriever(BaseRetriever):
    """LangChain adapter around the existing vector store.

    Keeping the current embeddings and on-disk format makes this a safe first
    RAG migration step while exposing the standard Retriever Runnable API.
    """

    legacy_retriever: Any
    top_k: int = 5
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        results = self.legacy_retriever.retrieve(query, top_k=self.top_k)
        documents = []
        for item in results:
            metadata = {key: value for key, value in item.items() if key != "content"}
            documents.append(
                Document(
                    page_content=item.get("content", ""),
                    metadata=metadata,
                )
            )
        return documents


def create_langchain_retriever(
    db_dir: str = DEFAULT_VECTOR_DB_DIR,
    top_k: int = 5,
) -> LangChainKnowledgeRetriever:
    """Create the standard LangChain retriever used by migrated RAG paths."""
    return LangChainKnowledgeRetriever(
        legacy_retriever=KnowledgeRetriever(db_dir=db_dir),
        top_k=top_k,
    )


def documents_to_results(documents: List[Document]) -> List[Dict]:
    """Convert LangChain Documents for legacy renderers during migration."""
    return [
        {**document.metadata, "content": document.page_content}
        for document in documents
    ]


def format_retrieved_context(results: List[Dict]) -> str:
    """
    把检索结果整理成大模型容易理解的上下文
    """
    context_parts = []

    for i, item in enumerate(results, start=1):
        context_parts.append(
            f"【资料{i}】\n"
            f"来源文件：{item['file_name']}\n"
            f"相关度：{item['score']:.4f}\n"
            f"内容：\n{item['content']}"
        )

    return "\n\n".join(context_parts)
